from flask import Blueprint, render_template

pricing_bp = Blueprint('pricing', __name__)

@pricing_bp.route('/pricing')
def index():
    """
    Render the pricing page.
    """
    # active_nav is passed to highlight the sidebar item
    return render_template('pricing.html', active_nav='/pricing')