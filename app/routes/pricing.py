from flask import Blueprint, render_template
from flask_login import current_user

pricing_bp = Blueprint('pricing', __name__)

@pricing_bp.route('/pricing')
def index():
    """
    Render the pricing page.
    """
    subscription_status = getattr(current_user, 'subscription_status', 'free') if getattr(current_user, 'is_authenticated', False) else None
    subscription_tier   = getattr(current_user, 'subscription_tier', 'free')   if getattr(current_user, 'is_authenticated', False) else None
    token_balance       = getattr(current_user, 'token_balance', 0)             if getattr(current_user, 'is_authenticated', False) else 0

    return render_template(
        'pricing.html',
        active_nav='/pricing',
        subscription_status=subscription_status,
        subscription_tier=subscription_tier,
        token_balance=token_balance,
    )