"""
Credit service — the single source of truth for all credit operations.

Rules
-----
* 1 credit costs the end-user $0.005 (half a cent at wholesale).
* Credits are stored as Decimal with 3 decimal places.
* Every credit movement writes an immutable CreditTransaction row.
* debit() is atomic: it checks balance, deducts and writes the ledger
  row inside one DB flush so the caller may commit or roll back.

Credit Packs (for purchase)
---------------------------
CREDIT_PACKS is the canonical list of plans offered on the /credits page.
"""
from __future__ import annotations

import logging
from decimal import Decimal
from typing import Optional

from app import db
from app.models import CreditTransaction, CreditWallet, OperationPricing

logger = logging.getLogger(__name__)

# USD per credit (wholesale cost passed through to the user at 1× markup)
USD_PER_CREDIT = Decimal('0.005')

# ---------------------------------------------------------------------------
# Credit packs available for purchase
# ---------------------------------------------------------------------------
CREDIT_PACKS = [
    {
        'id': 'starter',
        'label': 'Starter Pack',
        'credits': 1_000,
        'price_usd': 5.00,
        'price_cents': 500,
        'discount_pct': 0,
        'highlight': False,
        'description': 'Perfect for trying things out',
    },
    {
        'id': 'pro',
        'label': 'Pro Pack',
        'credits': 5_000,
        'price_usd': 22.50,
        'price_cents': 2250,
        'discount_pct': 10,
        'highlight': True,
        'description': 'Most popular — great value',
    },
    {
        'id': 'studio',
        'label': 'Studio Pack',
        'credits': 20_000,
        'price_usd': 80.00,
        'price_cents': 8000,
        'discount_pct': 20,
        'highlight': False,
        'description': 'For power users and studios',
    },
    {
        'id': 'enterprise',
        'label': 'Enterprise Pack',
        'credits': 100_000,
        'price_usd': 350.00,
        'price_cents': 35000,
        'discount_pct': 30,
        'highlight': False,
        'description': 'Maximum scale, maximum savings',
    },
]

_PACK_BY_ID = {p['id']: p for p in CREDIT_PACKS}


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _get_or_create_wallet(user_id: str) -> CreditWallet:
    """Return the user's wallet, creating one lazily if it doesn't exist."""
    wallet = CreditWallet.query.filter_by(user_id=user_id).with_for_update().first()
    if wallet is None:
        wallet = CreditWallet(user_id=user_id)
        db.session.add(wallet)
        db.session.flush()
    return wallet


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def get_balance(user_id: str) -> float:
    """Return current credit balance as a float (no lock required)."""
    wallet = CreditWallet.query.filter_by(user_id=user_id).first()
    return float(wallet.balance) if wallet else 0.0


def get_wallet(user_id: str) -> dict:
    """Return wallet info as a dict, creating the wallet if absent."""
    with db.session.begin_nested():
        wallet = _get_or_create_wallet(user_id)
    return wallet.to_dict()


def get_pricing_table() -> list[dict]:
    """Return all active operation prices, ordered by credits cost desc."""
    rows = (
        OperationPricing.query
        .filter_by(is_active=True)
        .order_by(OperationPricing.credits_per_request.desc())
        .all()
    )
    return [r.to_dict() for r in rows]


def check_sufficient(user_id: str, operation_key: str) -> tuple[bool, float]:
    """
    Return (can_afford, cost_in_credits).
    Does NOT debit the wallet — call debit() to actually spend.
    """
    pricing = OperationPricing.query.filter_by(
        operation_key=operation_key, is_active=True
    ).first()
    if pricing is None:
        return False, 0.0
    cost = float(pricing.credits_per_request)
    balance = get_balance(user_id)
    return balance >= cost, cost


def debit(
    user_id: str,
    operation_key: str,
    description: Optional[str] = None,
    extra: Optional[dict] = None,
) -> tuple[bool, str, float]:
    """
    Spend credits for one AI operation.

    Returns
    -------
    (success, message, balance_after)
    """
    pricing = OperationPricing.query.filter_by(
        operation_key=operation_key, is_active=True
    ).first()
    if pricing is None:
        return False, f'Unknown operation: {operation_key}', 0.0

    cost = Decimal(str(pricing.credits_per_request))

    wallet = _get_or_create_wallet(user_id)
    if wallet.balance < cost:
        return (
            False,
            f'Insufficient credits. Need {float(cost):.3f}, have {float(wallet.balance):.3f}.',
            float(wallet.balance),
        )

    wallet.balance -= cost
    wallet.lifetime_spent += cost

    tx = CreditTransaction(
        user_id=user_id,
        tx_type=CreditTransaction.TYPE_DEBIT,
        amount=-cost,
        balance_after=wallet.balance,
        operation_key=operation_key,
        description=description or pricing.display_name,
        extra=extra,
    )
    db.session.add(tx)
    db.session.flush()
    return True, 'ok', float(wallet.balance)


def add_credits(
    user_id: str,
    credits: float,
    tx_type: str,
    description: Optional[str] = None,
    reference_id: Optional[str] = None,
    extra: Optional[dict] = None,
) -> float:
    """
    Add credits to a user's wallet (purchase, refund, promo, admin grant).

    Returns the new balance.
    """
    amount = Decimal(str(credits))
    if amount <= 0:
        raise ValueError('credits must be positive')

    wallet = _get_or_create_wallet(user_id)
    wallet.balance += amount
    wallet.lifetime_earned += amount

    tx = CreditTransaction(
        user_id=user_id,
        tx_type=tx_type,
        amount=amount,
        balance_after=wallet.balance,
        description=description,
        reference_id=reference_id,
        extra=extra,
    )
    db.session.add(tx)
    db.session.flush()
    return float(wallet.balance)


def purchase_pack(user_id: str, pack_id: str) -> tuple[bool, str, float]:
    """
    Prototype purchase: adds credits for the chosen pack immediately
    (no real payment processing — a real implementation would call
    Stripe / PayPal and only credit on webhook confirmation).

    Returns (success, message, new_balance).
    """
    pack = _PACK_BY_ID.get(pack_id)
    if pack is None:
        return False, f'Unknown pack: {pack_id}', get_balance(user_id)

    new_balance = add_credits(
        user_id=user_id,
        credits=pack['credits'],
        tx_type=CreditTransaction.TYPE_PURCHASE,
        description=f"Purchased {pack['label']} ({pack['credits']:,} credits)",
        reference_id=f"pack:{pack_id}",
        extra={'pack_id': pack_id, 'price_usd': pack['price_usd']},
    )
    return True, f"{pack['credits']:,} credits added to your wallet.", new_balance


def get_transactions(
    user_id: str,
    page: int = 1,
    per_page: int = 20,
) -> dict:
    """Return paginated transaction history for a user."""
    pagination = (
        CreditTransaction.query
        .filter_by(user_id=user_id)
        .order_by(CreditTransaction.created_at.desc())
        .paginate(page=page, per_page=per_page, error_out=False)
    )
    return {
        'items': [tx.to_dict() for tx in pagination.items],
        'total': pagination.total,
        'page': pagination.page,
        'pages': pagination.pages,
        'per_page': per_page,
    }
