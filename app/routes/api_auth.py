from __future__ import annotations

import re
from datetime import datetime

from flask import Blueprint, current_app, flash, jsonify, redirect, request, url_for
from flask_login import current_user, login_required, login_user, logout_user
from flask_wtf.csrf import generate_csrf

from app import db, limiter, mail
from app.models import AuthAuditLog, User, get_default_role, UserRole


api_auth_bp = Blueprint("api_auth", __name__)


def _json_body() -> dict:
    data = request.get_json(silent=True)
    return data if isinstance(data, dict) else {}


def _validate_email(email: str) -> bool:
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return re.match(pattern, email) is not None


def _validate_password(password: str) -> tuple[bool, str]:
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter"
    if not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter"
    if not re.search(r"\d", password):
        return False, "Password must contain at least one number"
    return True, "Password is valid"


def _log_auth_event(
    user_id: str | None,
    event_type: str,
    success: bool = True,
    event_data: dict | None = None,
) -> None:
    log = AuthAuditLog(
        user_id=user_id,
        event_type=event_type,
        ip_address=request.remote_addr,
        user_agent=request.user_agent.string,
        success=success,
        event_data=event_data or {},
    )
    db.session.add(log)
    db.session.commit()


def _send_email(subject: str, recipient: str, body: str) -> tuple[bool, str | None]:
    if not current_app.config.get("MAIL_USERNAME") or not current_app.config.get("MAIL_PASSWORD"):
        return False, "Email service not configured"

    try:
        from flask_mail import Message

        msg = Message(
            subject,
            sender=current_app.config.get("MAIL_DEFAULT_SENDER"),
            recipients=[recipient],
        )
        msg.body = body
        mail.send(msg)
        return True, None
    except Exception as e:  # noqa: BLE001
        current_app.logger.error(f"Failed to send email: {e}")
        return False, "Failed to send email"


@api_auth_bp.route("/csrf", methods=["GET"])
def csrf_token():
    return jsonify({"csrf_token": generate_csrf()})


@api_auth_bp.route("/register", methods=["POST"])
@limiter.limit(lambda: current_app.config.get("REGISTER_RATE_LIMIT", "3 per hour"))
def register():
    if current_user.is_authenticated:
        return jsonify({"error": "Already authenticated"}), 400

    data = _json_body()
    email = (data.get("email") or "").lower().strip()
    password = data.get("password") or ""
    display_name = (data.get("display_name") or "").strip() or None

    if not email or not password:
        return jsonify({"error": "Missing required fields"}), 400

    if not _validate_email(email):
        return jsonify({"error": "Invalid email format"}), 400

    is_valid, message = _validate_password(password)
    if not is_valid:
        return jsonify({"error": message}), 400

    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        return jsonify({"error": "Email already registered"}), 409

    user = User(email=email, password=password, display_name=display_name)
    verification_token = user.generate_verification_token()

    db.session.add(user)
    db.session.flush()

    default_role = get_default_role()
    db.session.add(UserRole(user_id=user.id, role_id=default_role.id))
    db.session.commit()

    _log_auth_event(user_id=user.id, event_type="register", success=True, event_data={"email": email})

    verification_url = url_for("api_auth.verify_email_get", token=verification_token, _external=True)
    body = (
        "Welcome to Music Cover Generator!\n\n"
        "Please verify your email by clicking the following link:\n"
        f"{verification_url}\n\n"
        "This link will expire in 24 hours.\n\n"
        "If you didn't create an account, please ignore this email.\n"
    )
    _send_email("Verify Your Email - Music Cover Generator", email, body)

    login_user(user, remember=True)

    return jsonify({"success": True, "user": user.to_dict()}), 201


@api_auth_bp.route("/login", methods=["POST"])
@limiter.limit(lambda: current_app.config.get("LOGIN_RATE_LIMIT", "5 per minute"))
def login():
    if current_user.is_authenticated:
        return jsonify({"error": "Already authenticated", "user": current_user.to_dict()}), 200

    data = _json_body()
    email = (data.get("email") or "").lower().strip()
    password = data.get("password") or ""
    remember = bool(data.get("remember", True))

    if not email or not password:
        return jsonify({"error": "Missing required fields"}), 400

    user = User.query.filter_by(email=email).first()

    _log_auth_event(
        user_id=user.id if user else None,
        event_type="login",
        success=False,
        event_data={"email": email},
    )

    if not user or user.is_locked() or not user.check_password(password):
        if user:
            user.record_login(success=False)
            db.session.commit()
        return jsonify({"error": "Invalid credentials"}), 401

    user.record_login(success=True)
    db.session.commit()

    login_user(user, remember=remember)

    log = (
        AuthAuditLog.query.filter_by(user_id=user.id, event_type="login", success=False)
        .order_by(AuthAuditLog.created_at.desc())
        .first()
    )
    if log:
        log.success = True
        db.session.commit()

    return jsonify({"success": True, "user": user.to_dict()}), 200


@api_auth_bp.route("/logout", methods=["POST"])
@login_required
def logout():
    _log_auth_event(user_id=current_user.id, event_type="logout", success=True)
    logout_user()
    return jsonify({"success": True}), 200


@api_auth_bp.route("/verify/<token>", methods=["GET"])
@limiter.limit("10 per hour")
def verify_email_get(token: str):
    if not token:
        return jsonify({"error": "Missing token"}), 400

    user = User.query.filter_by(verification_token=token).first()
    if not user:
        # Token not found – may have been used or replaced by a newer resend.
        if current_user.is_authenticated and current_user.email_verified:
            flash("Your email is already verified.", "success")
            return redirect(url_for("main.dashboard"))
        flash("Invalid or expired verification token.", "danger")
        if current_user.is_authenticated:
            return redirect(url_for("main.dashboard"))
        return redirect(url_for("auth.login"))

    if not user.verify_email(token):
        flash("Invalid or expired verification token.", "danger")
        if current_user.is_authenticated:
            return redirect(url_for("main.dashboard"))
        return redirect(url_for("auth.login"))

    db.session.commit()
    _log_auth_event(user_id=user.id, event_type="email_verified", success=True)

    if not current_user.is_authenticated:
        login_user(user, remember=True)

    flash("Email verified successfully!", "success")
    return redirect(url_for("main.dashboard"))


@api_auth_bp.route("/verify", methods=["POST"])
@limiter.limit("10 per hour")
def verify_email():
    data = _json_body()
    token = data.get("token")
    if not token:
        return jsonify({"error": "Missing token"}), 400

    user = User.query.filter_by(verification_token=token).first()
    if not user:
        return jsonify({"error": "Invalid or expired token"}), 400

    if not user.verify_email(token):
        return jsonify({"error": "Invalid or expired token"}), 400

    db.session.commit()
    _log_auth_event(user_id=user.id, event_type="email_verified", success=True)

    return jsonify({"success": True}), 200


@api_auth_bp.route("/resend", methods=["POST"])
@login_required
@limiter.limit("3 per hour")
def resend_verification():
    if current_user.email_verified:
        return jsonify({"success": True, "message": "Email already verified"}), 200

    verification_token = current_user.generate_verification_token()
    db.session.commit()

    verification_url = url_for("api_auth.verify_email_get", token=verification_token, _external=True)
    body = (
        "Please verify your email by clicking the following link:\n"
        f"{verification_url}\n\n"
        "This link will expire in 24 hours.\n"
    )
    _send_email("Verify Your Email - Music Cover Generator", current_user.email, body)

    return jsonify({"success": True}), 200


@api_auth_bp.route("/forgot", methods=["POST"])
@limiter.limit(lambda: current_app.config.get("PASSWORD_RESET_RATE_LIMIT", "2 per hour"))
def forgot_password():
    data = _json_body()
    email = (data.get("email") or "").lower().strip()

    if not email or not _validate_email(email):
        return jsonify({"success": True}), 200

    user = User.query.filter_by(email=email).first()
    if user:
        reset_token = user.generate_reset_token()
        db.session.commit()

        _log_auth_event(user_id=user.id, event_type="password_reset_request", success=True, event_data={"email": email})

        reset_url = url_for("api_auth.reset_password", _external=True)
        body = (
            "You requested to reset your password.\n\n"
            "Use the following token to reset your password:\n"
            f"{reset_token}\n\n"
            "Or use the reset endpoint:\n"
            f"{reset_url}\n\n"
            "This token will expire in 1 hour.\n"
        )
        _send_email("Reset Your Password - Music Cover Generator", email, body)

    return jsonify({"success": True}), 200


@api_auth_bp.route("/reset", methods=["POST"])
@limiter.limit(lambda: current_app.config.get("PASSWORD_RESET_RATE_LIMIT", "2 per hour"))
def reset_password():
    data = _json_body()
    token = data.get("token")
    new_password = data.get("new_password") or ""

    if not token or not new_password:
        return jsonify({"error": "Missing required fields"}), 400

    is_valid, message = _validate_password(new_password)
    if not is_valid:
        return jsonify({"error": message}), 400

    user = User.query.filter_by(reset_token=token).first()
    if not user or not user.reset_token_expires_at or user.reset_token_expires_at < datetime.utcnow():
        return jsonify({"error": "Invalid or expired token"}), 400

    if not user.reset_password(token, new_password):
        return jsonify({"error": "Invalid or expired token"}), 400

    db.session.commit()
    _log_auth_event(user_id=user.id, event_type="password_reset", success=True)

    return jsonify({"success": True}), 200


@api_auth_bp.route("/change-password", methods=["POST"])
@login_required
@limiter.limit("5 per hour")
def change_password():
    data = _json_body()
    current_password = data.get("current_password") or ""
    new_password = data.get("new_password") or ""

    if not current_password or not new_password:
        return jsonify({"error": "Missing required fields"}), 400

    if not current_user.check_password(current_password):
        return jsonify({"error": "Invalid credentials"}), 401

    is_valid, message = _validate_password(new_password)
    if not is_valid:
        return jsonify({"error": message}), 400

    current_user.set_password(new_password)
    db.session.commit()

    _log_auth_event(user_id=current_user.id, event_type="password_change", success=True)

    return jsonify({"success": True}), 200


@api_auth_bp.route("/profile", methods=["GET", "PATCH"])
@login_required
def profile():
    if request.method == "GET":
        return jsonify({"user": current_user.to_dict()}), 200

    data = _json_body()

    if "display_name" in data:
        current_user.display_name = (data.get("display_name") or "").strip() or current_user.display_name

    if "avatar_url" in data:
        current_user.avatar_url = data.get("avatar_url")

    if "email" in data:
        new_email = (data.get("email") or "").lower().strip()
        if new_email and new_email != current_user.email:
            if not _validate_email(new_email):
                return jsonify({"error": "Invalid email format"}), 400

            existing_user = User.query.filter_by(email=new_email).first()
            if existing_user and existing_user.id != current_user.id:
                return jsonify({"error": "Email already registered"}), 409

            current_user.email = new_email
            current_user.email_verified = False
            verification_token = current_user.generate_verification_token()

            verification_url = url_for("api_auth.verify_email_get", token=verification_token, _external=True)
            body = (
                "You have changed your email address.\n\n"
                "Please verify your new email by clicking the following link:\n"
                f"{verification_url}\n\n"
                "This link will expire in 24 hours.\n"
            )
            _send_email("Verify Your New Email - Music Cover Generator", new_email, body)

    db.session.commit()

    return jsonify({"success": True, "user": current_user.to_dict()}), 200


@api_auth_bp.route("/sessions", methods=["GET"])
@login_required
def sessions():
    logs = (
        AuthAuditLog.query.filter(
            AuthAuditLog.user_id == current_user.id,
            AuthAuditLog.success.is_(True),
            AuthAuditLog.event_type.in_(["login", "oauth_login_google", "oauth_login_github"]),
        )
        .order_by(AuthAuditLog.created_at.desc())
        .limit(20)
        .all()
    )

    sessions_data = [
        {
            "event_type": log.event_type,
            "ip_address": log.ip_address,
            "user_agent": log.user_agent,
            "created_at": log.created_at.isoformat() if log.created_at else None,
        }
        for log in logs
    ]

    return jsonify({"sessions": sessions_data}), 200
