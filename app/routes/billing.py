"""
Stripe Checkout / Billing routes.

Plans
-----
- pro_monthly : $15.00 / month  (recurring)
- pro_annual  : $144.00 / year  (recurring, 20 % off)
- tokens      : one-time token-pack purchase (e.g. 100 tokens / $5)

Endpoints
---------
POST /billing/checkout  – create Stripe Checkout Session (login required)
GET  /billing/success   – post-checkout success page
GET  /billing/cancel    – checkout abandoned page
POST /billing/webhook   – Stripe webhook receiver (CSRF-exempt)
POST /billing/portal    – open Stripe Customer Portal (login required)
"""

import logging
from datetime import datetime

import stripe
from flask import (
    Blueprint,
    abort,
    current_app,
    jsonify,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import current_user, login_required

from app import db
from app.models import User, WebhookEvent

logger = logging.getLogger(__name__)

billing_bp = Blueprint('billing', __name__, url_prefix='/billing')

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

TOKEN_PACK_AMOUNT = 100  # tokens granted per pack purchase


def _stripe():
    """Return the stripe module configured with the secret key."""
    stripe.api_key = current_app.config['STRIPE_SECRET_KEY']
    return stripe


def _get_or_create_customer(user: User) -> str:
    """Return existing Stripe customer ID or create a new one."""
    s = _stripe()
    if user.stripe_customer_id:
        return user.stripe_customer_id

    customer = s.Customer.create(
        email=user.email,
        name=user.display_name or user.email,
        metadata={'user_id': str(user.id)},
    )
    user.stripe_customer_id = customer.id
    db.session.commit()
    return customer.id


def _price_id_for_plan(plan: str) -> tuple[str, str]:
    """Return (price_id, mode) for the given plan name."""
    cfg = current_app.config
    mapping = {
        'pro_monthly': (cfg['STRIPE_PRO_MONTHLY_PRICE_ID'], 'subscription'),
        'pro_annual':  (cfg['STRIPE_PRO_ANNUAL_PRICE_ID'],  'subscription'),
        'tokens':      (cfg['STRIPE_TOKEN_PACK_PRICE_ID'],  'payment'),
    }
    if plan not in mapping:
        abort(400, description=f"Unknown plan '{plan}'")
    price_id, mode = mapping[plan]
    if not price_id:
        abort(500, description=f"Price ID for plan '{plan}' is not configured.")
    return price_id, mode


# ---------------------------------------------------------------------------
# Checkout
# ---------------------------------------------------------------------------

@billing_bp.route('/checkout', methods=['POST'])
@login_required
def create_checkout_session():
    """
    Body (JSON): { "plan": "pro_monthly" | "pro_annual" | "tokens" }
    Returns: { "url": "<stripe_checkout_url>" }
    """
    data = request.get_json(silent=True) or {}
    plan = data.get('plan', '').strip()
    price_id, mode = _price_id_for_plan(plan)

    customer_id = _get_or_create_customer(current_user)
    s = _stripe()

    base = request.host_url.rstrip('/')
    success_url = f"{base}{url_for('billing.success')}?session_id={{CHECKOUT_SESSION_ID}}"
    cancel_url  = f"{base}{url_for('billing.cancel')}"

    session_kwargs = dict(
        customer=customer_id,
        mode=mode,
        line_items=[{'price': price_id, 'quantity': 1}],
        success_url=success_url,
        cancel_url=cancel_url,
        metadata={'user_id': str(current_user.id), 'plan': plan},
        allow_promotion_codes=True,
    )

    # For subscriptions, enable the customer portal link on the confirmation page
    if mode == 'subscription':
        session_kwargs['subscription_data'] = {
            'metadata': {'user_id': str(current_user.id), 'plan': plan}
        }

    try:
        session = s.checkout.Session.create(**session_kwargs)
    except stripe.error.StripeError as exc:
        logger.error("Stripe error creating checkout session: %s", exc)
        return jsonify({'error': 'Failed to create checkout session'}), 502

    return jsonify({'url': session.url})


# ---------------------------------------------------------------------------
# Success / Cancel pages
# ---------------------------------------------------------------------------

@billing_bp.route('/success')
def success():
    return render_template('billing/success.html')


@billing_bp.route('/cancel')
def cancel():
    return render_template('billing/cancel.html')


# ---------------------------------------------------------------------------
# Customer Portal
# ---------------------------------------------------------------------------

@billing_bp.route('/portal', methods=['POST'])
@login_required
def customer_portal():
    """Redirect the user to the Stripe Customer Portal."""
    if not current_user.stripe_customer_id:
        # No subscription yet – send them to the pricing page
        return redirect(url_for('pricing.index'))

    s = _stripe()
    return_url = request.host_url.rstrip('/') + url_for('main.dashboard')

    try:
        portal = s.billing_portal.Session.create(
            customer=current_user.stripe_customer_id,
            return_url=return_url,
        )
    except stripe.error.StripeError as exc:
        logger.error("Stripe error creating portal session: %s", exc)
        return jsonify({'error': 'Failed to open billing portal'}), 502

    return redirect(portal.url)


# ---------------------------------------------------------------------------
# Webhook
# ---------------------------------------------------------------------------

@billing_bp.route('/webhook', methods=['POST'])
def webhook():
    """
    Receive Stripe webhook events.
    Signature is verified; events are idempotently processed via WebhookEvent.
    CSRF is exempted for this route in app/__init__.py.
    """
    payload    = request.get_data()
    sig_header = request.headers.get('Stripe-Signature', '')
    secret     = current_app.config['STRIPE_WEBHOOK_SECRET']

    try:
        event = _stripe().Webhook.construct_event(payload, sig_header, secret)
    except stripe.error.SignatureVerificationError:
        logger.warning("Stripe webhook: invalid signature")
        abort(400)
    except Exception as exc:
        logger.error("Stripe webhook: could not parse event: %s", exc)
        abort(400)

    event_id = event['id']

    # Idempotency check
    if WebhookEvent.query.filter_by(source='stripe', event_id=event_id).first():
        return jsonify({'status': 'already_processed'}), 200

    try:
        _handle_event(event)
    except Exception as exc:
        logger.exception("Stripe webhook: error handling event %s: %s", event_id, exc)
        # Return 200 anyway so Stripe doesn't retry on our bug; log for monitoring
        return jsonify({'status': 'error', 'detail': str(exc)}), 200

    db.session.add(WebhookEvent(source='stripe', event_id=event_id))
    db.session.commit()
    return jsonify({'status': 'ok'}), 200


# ---------------------------------------------------------------------------
# Event handlers
# ---------------------------------------------------------------------------

def _handle_event(event: dict) -> None:
    etype = event['type']
    obj   = event['data']['object']

    handlers = {
        'checkout.session.completed':       _on_checkout_completed,
        'customer.subscription.updated':    _on_subscription_updated,
        'customer.subscription.deleted':    _on_subscription_deleted,
        'invoice.payment_succeeded':        _on_invoice_payment_succeeded,
        'invoice.payment_failed':           _on_invoice_payment_failed,
    }

    handler = handlers.get(etype)
    if handler:
        handler(obj)
    else:
        logger.debug("Stripe webhook: unhandled event type %s", etype)


def _user_by_customer(customer_id: str) -> User | None:
    return User.query.filter_by(stripe_customer_id=customer_id).first()


def _on_checkout_completed(session: dict) -> None:
    mode        = session.get('mode')
    customer_id = session.get('customer')
    user        = _user_by_customer(customer_id)

    if not user:
        # Fall back to metadata
        user_id = (session.get('metadata') or {}).get('user_id')
        if user_id:
            user = User.query.get(user_id)
            if user:
                user.stripe_customer_id = customer_id

    if not user:
        logger.warning("checkout.session.completed: no user found for customer %s", customer_id)
        return

    if mode == 'subscription':
        sub_id = session.get('subscription')
        if sub_id:
            s   = _stripe()
            sub = s.Subscription.retrieve(sub_id)
            _apply_subscription(user, sub)

    elif mode == 'payment':
        # Token pack one-time purchase
        user.token_balance = (user.token_balance or 0) + TOKEN_PACK_AMOUNT
        logger.info("User %s purchased token pack (+%d tokens)", user.id, TOKEN_PACK_AMOUNT)

    db.session.flush()


def _on_subscription_updated(sub: dict) -> None:
    customer_id = sub.get('customer')
    user = _user_by_customer(customer_id)
    if not user:
        return
    _apply_subscription(user, sub)
    db.session.flush()


def _on_subscription_deleted(sub: dict) -> None:
    customer_id = sub.get('customer')
    user = _user_by_customer(customer_id)
    if not user:
        return
    user.subscription_status     = 'canceled'
    user.subscription_tier       = 'free'
    user.subscription_period_end = None
    logger.info("User %s subscription canceled", user.id)
    db.session.flush()


def _on_invoice_payment_succeeded(invoice: dict) -> None:
    customer_id = invoice.get('customer')
    user = _user_by_customer(customer_id)
    if not user:
        return
    # Refresh period end from the subscription attached to this invoice
    sub_id = invoice.get('subscription')
    if sub_id:
        sub = _stripe().Subscription.retrieve(sub_id)
        _apply_subscription(user, sub)
        db.session.flush()


def _on_invoice_payment_failed(invoice: dict) -> None:
    customer_id = invoice.get('customer')
    user = _user_by_customer(customer_id)
    if not user:
        return
    user.subscription_status = 'past_due'
    logger.warning("User %s invoice payment failed – status set to past_due", user.id)
    db.session.flush()


# ---------------------------------------------------------------------------
# Shared subscription application helper
# ---------------------------------------------------------------------------

_STATUS_MAP = {
    'active':            'active',
    'trialing':          'active',
    'past_due':          'past_due',
    'canceled':          'canceled',
    'unpaid':            'past_due',
    'incomplete':        'past_due',
    'incomplete_expired':'canceled',
    'paused':            'past_due',
}


def _apply_subscription(user: User, sub: dict) -> None:
    """Sync User fields from a Stripe Subscription object."""
    status   = sub.get('status', 'canceled')
    items    = sub.get('items', {}).get('data', [])
    price_id = items[0]['price']['id'] if items else ''

    cfg = current_app.config
    pro_prices = {
        cfg.get('STRIPE_PRO_MONTHLY_PRICE_ID', ''),
        cfg.get('STRIPE_PRO_ANNUAL_PRICE_ID', ''),
    }

    tier = 'pro' if price_id in pro_prices else 'free'

    period_end_ts = sub.get('current_period_end')
    period_end    = datetime.utcfromtimestamp(period_end_ts) if period_end_ts else None

    user.subscription_status     = _STATUS_MAP.get(status, 'canceled')
    user.subscription_tier       = tier if user.subscription_status == 'active' else 'free'
    user.subscription_period_end = period_end

    logger.info(
        "User %s subscription updated: status=%s tier=%s period_end=%s",
        user.id, user.subscription_status, user.subscription_tier, period_end,
    )
