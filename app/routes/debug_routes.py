"""Debug routes for troubleshooting"""
from flask import Blueprint, jsonify
from flask_login import current_user

debug_bp = Blueprint('debug', __name__, url_prefix='/api/debug')

@debug_bp.route('/whoami', methods=['GET'])
def whoami():
    """Return current authenticated user info"""
    if current_user.is_authenticated:
        return jsonify({
            'authenticated': True,
            'user_id': current_user.id,
            'email': current_user.email,
            'username': current_user.username
        })
    else:
        return jsonify({
            'authenticated': False
        })
