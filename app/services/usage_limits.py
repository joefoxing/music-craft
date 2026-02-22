from datetime import datetime
from typing import Any, Dict, Optional, Tuple

from flask import current_app, request
from flask_login import current_user
from sqlalchemy import func

from app import db
from app.models import UsageEvent


def consume_token(user) -> bool:
    """Deduct one token from the user's balance. Returns True if successful."""
    if (user.token_balance or 0) <= 0:
        return False
    user.token_balance -= 1
    db.session.flush()
    return True


def _is_paid_active(user) -> bool:
    """Return True if the user has an active paid subscription."""
    return (
        getattr(user, 'subscription_status', 'free') == 'active'
        and getattr(user, 'subscription_tier', 'free') == 'pro'
    )


def _window_start_daily(now: datetime) -> datetime:
    return datetime(now.year, now.month, now.day)


def _window_start_monthly(now: datetime) -> datetime:
    return datetime(now.year, now.month, 1)


def _limits_for_actor(is_authenticated: bool) -> Tuple[Optional[int], Optional[int]]:
    if is_authenticated:
        daily = current_app.config.get('FREE_DAILY_LIMIT_USER')
        monthly = current_app.config.get('FREE_MONTHLY_LIMIT_USER')
    else:
        daily = current_app.config.get('FREE_DAILY_LIMIT_ANON')
        monthly = current_app.config.get('FREE_MONTHLY_LIMIT_ANON')

    daily_value: Optional[int] = int(daily) if daily is not None else None
    monthly_value: Optional[int] = int(monthly) if monthly is not None else None
    return daily_value, monthly_value


def _usage_sum(*, user_id: Optional[str], ip_address: Optional[str], since: datetime) -> int:
    q = db.session.query(func.coalesce(func.sum(UsageEvent.units), 0))

    if user_id:
        q = q.filter(UsageEvent.user_id == user_id)
    else:
        q = q.filter(UsageEvent.user_id.is_(None))

    if ip_address:
        q = q.filter(UsageEvent.ip_address == ip_address)

    q = q.filter(UsageEvent.created_at >= since)
    return int(q.scalar() or 0)


def check_allowed(units: int = 1) -> Tuple[bool, Dict[str, Any], int]:
    now = datetime.utcnow()

    is_auth = bool(getattr(current_user, 'is_authenticated', False))
    user_id = current_user.id if is_auth else None
    ip_address = request.headers.get('X-Forwarded-For', request.remote_addr)

    # --- Paid subscription: unlimited usage ---
    if is_auth and _is_paid_active(current_user):
        return True, {'remaining': None, 'plan': 'pro'}, 200

    daily_limit, monthly_limit = _limits_for_actor(is_auth)

    daily_used = _usage_sum(user_id=user_id, ip_address=None if is_auth else ip_address, since=_window_start_daily(now))
    monthly_used = _usage_sum(user_id=user_id, ip_address=None if is_auth else ip_address, since=_window_start_monthly(now))

    daily_exceeded   = daily_limit   is not None and daily_used   + units > daily_limit
    monthly_exceeded = monthly_limit is not None and monthly_used + units > monthly_limit

    if daily_exceeded or monthly_exceeded:
        # --- Token spend fallback ---
        if is_auth and consume_token(current_user):
            return True, {'remaining': None, 'plan': 'token'}, 200

        limit_type = 'daily' if daily_exceeded else 'monthly'
        limit      = daily_limit if daily_exceeded else monthly_limit
        used       = daily_used  if daily_exceeded else monthly_used
        return (
            False,
            {
                'error': 'Usage limit exceeded',
                'limit_type': limit_type,
                'limit': limit,
                'used': used,
                'remaining': max(limit - used, 0),
            },
            429,
        )

    remaining = None
    if daily_limit is not None:
        remaining = max(daily_limit - (daily_used + units), 0)

    return True, {'remaining': remaining}, 200


def record_usage(event_type: str, units: int = 1) -> None:
    is_auth = bool(getattr(current_user, 'is_authenticated', False))
    user_id = current_user.id if is_auth else None
    ip_address = request.headers.get('X-Forwarded-For', request.remote_addr)

    db.session.add(
        UsageEvent(
            event_type=event_type,
            user_id=user_id,
            ip_address=None if is_auth else ip_address,
            units=units,
        )
    )
    db.session.commit()


def is_successful_kie_response(response: Dict[str, Any]) -> bool:
    if not isinstance(response, dict):
        return False
    code = response.get('code')
    if code not in (0, 200):
        return False
    data = response.get('data')
    if isinstance(data, dict) and data.get('taskId'):
        return True
    return True
