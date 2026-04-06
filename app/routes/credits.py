"""
Credits blueprint — handles both the dashboard page and the JSON API.

Page routes
-----------
GET  /credits                    – Credits dashboard (login required)

API routes  (all under /api/credits)
-------------------------------------
GET  /api/credits/balance        – Current wallet balance
GET  /api/credits/transactions   – Paginated transaction history
GET  /api/credits/pricing        – Full operation pricing table
POST /api/credits/purchase       – Prototype purchase (no real payment)
POST /api/credits/admin-topup    – Admin: grant credits to any user
"""
import logging

from flask import Blueprint, jsonify, render_template, request
from flask_login import current_user, login_required

from app import db
from app.services import credit_service
from app.services.credit_service import CREDIT_PACKS

logger = logging.getLogger(__name__)

credits_bp = Blueprint('credits', __name__)


# ---------------------------------------------------------------------------
# Dashboard page
# ---------------------------------------------------------------------------

@credits_bp.route('/credits')
@login_required
def dashboard():
    wallet = credit_service.get_wallet(current_user.id)
    db.session.commit()
    pricing = credit_service.get_pricing_table()
    txs = credit_service.get_transactions(current_user.id, page=1, per_page=10)
    return render_template(
        'credits.html',
        active_nav='/credits',
        wallet=wallet,
        credit_packs=CREDIT_PACKS,
        pricing=pricing,
        recent_txs=txs['items'],
    )


# ---------------------------------------------------------------------------
# JSON API
# ---------------------------------------------------------------------------

@credits_bp.route('/api/credits/balance')
@login_required
def api_balance():
    wallet = credit_service.get_wallet(current_user.id)
    db.session.commit()
    return jsonify({'ok': True, 'wallet': wallet})


@credits_bp.route('/api/credits/transactions')
@login_required
def api_transactions():
    try:
        page = max(1, int(request.args.get('page', 1)))
        per_page = min(100, max(1, int(request.args.get('per_page', 20))))
    except (ValueError, TypeError):
        page, per_page = 1, 20

    result = credit_service.get_transactions(current_user.id, page=page, per_page=per_page)
    return jsonify({'ok': True, **result})


@credits_bp.route('/api/credits/pricing')
def api_pricing():
    return jsonify({'ok': True, 'pricing': credit_service.get_pricing_table()})


@credits_bp.route('/api/credits/purchase', methods=['POST'])
@login_required
def api_purchase():
    data = request.get_json(silent=True) or {}
    pack_id = data.get('pack_id', '').strip()

    if not pack_id:
        return jsonify({'ok': False, 'error': 'pack_id is required'}), 400

    success, message, new_balance = credit_service.purchase_pack(current_user.id, pack_id)
    if success:
        db.session.commit()
        return jsonify({'ok': True, 'message': message, 'balance': new_balance})

    db.session.rollback()
    return jsonify({'ok': False, 'error': message}), 400


@credits_bp.route('/api/credits/admin-topup', methods=['POST'])
@login_required
def api_admin_topup():
    if not current_user.has_permission('manage_users'):
        return jsonify({'ok': False, 'error': 'Forbidden'}), 403

    data = request.get_json(silent=True) or {}
    target_user_id = data.get('user_id', '').strip()
    try:
        credits = float(data.get('credits', 0))
    except (ValueError, TypeError):
        credits = 0.0

    if not target_user_id or credits <= 0:
        return jsonify({'ok': False, 'error': 'user_id and positive credits are required'}), 400

    from app.models import User
    target = User.query.get(target_user_id)
    if not target:
        return jsonify({'ok': False, 'error': 'User not found'}), 404

    new_balance = credit_service.add_credits(
        user_id=target_user_id,
        credits=credits,
        tx_type='admin_grant',
        description=f'Admin grant by {current_user.email}',
        extra={'granted_by': current_user.id},
    )
    db.session.commit()
    return jsonify({'ok': True, 'balance': new_balance})
