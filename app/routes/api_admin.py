from __future__ import annotations

from functools import wraps

from flask import Blueprint, current_app, jsonify, request
from flask_login import current_user, login_required

from app import db, limiter
from app.models import AdminSetting, AuthAuditLog, Permission, Role, User, UserRole


api_admin_bp = Blueprint("api_admin", __name__)


def _json_body() -> dict:
    data = request.get_json(silent=True)
    return data if isinstance(data, dict) else {}


def _user_role_names(user: User) -> set[str]:
    role_ids = [ur.role_id for ur in UserRole.query.filter_by(user_id=user.id).all()]
    if not role_ids:
        return set()
    roles = Role.query.filter(Role.id.in_(role_ids)).all()
    return {r.name for r in roles}


def _user_permissions(user: User) -> set[str]:
    role_ids = [ur.role_id for ur in UserRole.query.filter_by(user_id=user.id).all()]
    if not role_ids:
        return set()
    roles = Role.query.filter(Role.id.in_(role_ids)).all()
    perms: set[str] = set()
    for role in roles:
        for perm in role.permissions:
            perms.add(perm.name)
    return perms


def _has_permission(user: User, perm_name: str) -> bool:
    return perm_name in _user_permissions(user)


def require_permission(perm_name: str):
    def decorator(fn):
        @wraps(fn)
        @login_required
        def wrapper(*args, **kwargs):
            if not current_user.is_authenticated:
                return jsonify({"error": "Authentication required"}), 401
            if not _has_permission(current_user, perm_name):
                return jsonify({"error": "Forbidden"}), 403
            return fn(*args, **kwargs)

        return wrapper

    return decorator


def admin_required(fn):
    @wraps(fn)
    @login_required
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated:
            return jsonify({"error": "Authentication required"}), 401
        if not _has_permission(current_user, "view_admin"):
            return jsonify({"error": "Forbidden"}), 403
        return fn(*args, **kwargs)

    return wrapper


@api_admin_bp.route("/me", methods=["GET"])
@admin_required
def me():
    return jsonify({"user": current_user.to_dict(), "roles": sorted(_user_role_names(current_user))}), 200


@api_admin_bp.route("/users", methods=["GET"])
@require_permission("manage_users")
def users_list():
    q = (request.args.get("q") or "").strip().lower()
    limit = min(int(request.args.get("limit", 50)), 200)
    offset = max(int(request.args.get("offset", 0)), 0)

    query = User.query
    if q:
        query = query.filter(User.email.ilike(f"%{q}%"))

    total = query.count()
    users = query.order_by(User.created_at.desc()).offset(offset).limit(limit).all()

    return (
        jsonify(
            {
                "total": total,
                "limit": limit,
                "offset": offset,
                "users": [
                    {
                        **u.to_dict(),
                        "roles": sorted(_user_role_names(u)),
                        "is_locked": u.is_locked(),
                    }
                    for u in users
                ],
            }
        ),
        200,
    )


@api_admin_bp.route("/users/<user_id>", methods=["GET"])
@require_permission("manage_users")
def users_detail(user_id: str):
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "Not found"}), 404

    return (
        jsonify(
            {
                "user": {**user.to_dict(), "roles": sorted(_user_role_names(user)), "is_locked": user.is_locked()},
            }
        ),
        200,
    )


@api_admin_bp.route("/users/<user_id>", methods=["PATCH"])
@require_permission("manage_users")
def users_update(user_id: str):
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "Not found"}), 404

    data = _json_body()

    if "display_name" in data:
        user.display_name = (data.get("display_name") or "").strip() or user.display_name

    if "email_verified" in data:
        user.email_verified = bool(data.get("email_verified"))

    if "unlock" in data and bool(data.get("unlock")):
        user.failed_login_attempts = 0
        user.locked_until = None

    db.session.commit()

    db.session.add(
        AuthAuditLog(
            user_id=current_user.id,
            event_type="admin_user_update",
            ip_address=request.remote_addr,
            user_agent=request.user_agent.string,
            success=True,
            event_data={"target_user_id": user.id},
        )
    )
    db.session.commit()

    return jsonify({"success": True, "user": {**user.to_dict(), "roles": sorted(_user_role_names(user))}}), 200


@api_admin_bp.route("/users/<user_id>/roles", methods=["PUT"])
@require_permission("manage_roles")
def users_set_roles(user_id: str):
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "Not found"}), 404

    data = _json_body()
    role_names = data.get("roles")
    if not isinstance(role_names, list):
        return jsonify({"error": "Missing roles"}), 400

    role_names_set = {str(r).strip() for r in role_names if str(r).strip()}
    roles = Role.query.filter(Role.name.in_(list(role_names_set))).all() if role_names_set else []
    found_names = {r.name for r in roles}
    missing = sorted(role_names_set - found_names)
    if missing:
        return jsonify({"error": "Unknown roles", "missing": missing}), 400

    UserRole.query.filter_by(user_id=user.id).delete()
    for role in roles:
        db.session.add(UserRole(user_id=user.id, role_id=role.id, assigned_by=current_user.id))

    db.session.commit()

    db.session.add(
        AuthAuditLog(
            user_id=current_user.id,
            event_type="admin_role_assignment",
            ip_address=request.remote_addr,
            user_agent=request.user_agent.string,
            success=True,
            event_data={"target_user_id": user.id, "roles": sorted(found_names)},
        )
    )
    db.session.commit()

    return jsonify({"success": True, "user_id": user.id, "roles": sorted(found_names)}), 200


@api_admin_bp.route("/roles", methods=["GET"])
@require_permission("manage_roles")
def roles_list():
    roles = Role.query.order_by(Role.name.asc()).all()
    return (
        jsonify(
            {
                "roles": [
                    {
                        "id": r.id,
                        "name": r.name,
                        "description": r.description,
                        "is_default": r.is_default,
                        "permissions": sorted([p.name for p in r.permissions]),
                    }
                    for r in roles
                ]
            }
        ),
        200,
    )


@api_admin_bp.route("/permissions", methods=["GET"])
@require_permission("manage_roles")
def permissions_list():
    perms = Permission.query.order_by(Permission.name.asc()).all()
    return (
        jsonify(
            {
                "permissions": [
                    {
                        "id": p.id,
                        "name": p.name,
                        "description": p.description,
                    }
                    for p in perms
                ]
            }
        ),
        200,
    )


@api_admin_bp.route("/audit-logs", methods=["GET"])
@require_permission("view_audit_logs")
def audit_logs():
    limit = min(int(request.args.get("limit", 50)), 200)
    offset = max(int(request.args.get("offset", 0)), 0)
    user_id = request.args.get("user_id")
    event_type = request.args.get("event_type")

    query = AuthAuditLog.query
    if user_id:
        query = query.filter(AuthAuditLog.user_id == user_id)
    if event_type:
        query = query.filter(AuthAuditLog.event_type == event_type)

    total = query.count()
    logs = query.order_by(AuthAuditLog.created_at.desc()).offset(offset).limit(limit).all()

    return (
        jsonify(
            {
                "total": total,
                "limit": limit,
                "offset": offset,
                "logs": [
                    {
                        "id": l.id,
                        "user_id": l.user_id,
                        "event_type": l.event_type,
                        "ip_address": l.ip_address,
                        "user_agent": l.user_agent,
                        "success": l.success,
                        "event_data": l.event_data,
                        "created_at": l.created_at.isoformat() if l.created_at else None,
                    }
                    for l in logs
                ],
            }
        ),
        200,
    )


@api_admin_bp.route("/settings", methods=["GET"])
@require_permission("manage_settings")
def settings_list():
    settings = AdminSetting.query.order_by(AdminSetting.key.asc()).all()
    return jsonify({"settings": [s.to_dict() for s in settings]}), 200


@api_admin_bp.route("/settings/<key>", methods=["GET"])
@require_permission("manage_settings")
def settings_get(key: str):
    setting = AdminSetting.query.filter_by(key=key).first()
    if not setting:
        return jsonify({"error": "Not found"}), 404
    return jsonify({"setting": setting.to_dict()}), 200


@api_admin_bp.route("/settings/<key>", methods=["PUT"])
@require_permission("manage_settings")
@limiter.limit(lambda: current_app.config.get("ADMIN_SETTINGS_RATE_LIMIT", "30 per hour"))
def settings_put(key: str):
    data = _json_body()
    if "value" not in data:
        return jsonify({"error": "Missing value"}), 400

    setting = AdminSetting.query.filter_by(key=key).first()
    if not setting:
        setting = AdminSetting(key=key, value=data.get("value"), updated_by=current_user.id)
        db.session.add(setting)
    else:
        setting.value = data.get("value")
        setting.updated_by = current_user.id

    db.session.commit()

    db.session.add(
        AuthAuditLog(
            user_id=current_user.id,
            event_type="admin_setting_update",
            ip_address=request.remote_addr,
            user_agent=request.user_agent.string,
            success=True,
            event_data={"key": key},
        )
    )
    db.session.commit()

    return jsonify({"success": True, "setting": setting.to_dict()}), 200
