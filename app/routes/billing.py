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
POST /billing/paypal/checkout  – create PayPal order (login required)
POST /billing/paypal/capture   – capture PayPal order (login required)
POST /billing/paypal/subscribe – create PayPal subscription (login required)
POST /billing/paypal/webhook   – PayPal webhook receiver (CSRF-exempt)
GET  /billing/return    – payment return page
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
from app.paypal import get_paypal_client

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
        return None, None  # handled by caller
    price_id, mode = mapping[plan]
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

    valid_plans = {'pro_monthly', 'pro_annual', 'tokens'}
    if plan not in valid_plans:
        return jsonify({'error': f"Unknown plan '{plan}'"}), 400

    price_id, mode = _price_id_for_plan(plan)
    if not price_id:
        logger.error("Stripe price ID for plan '%s' is not configured.", plan)
        return jsonify({'error': 'Billing is not configured yet. Please contact support.'}), 500

    if not current_app.config.get('STRIPE_SECRET_KEY'):
        logger.error("STRIPE_SECRET_KEY is not set.")
        return jsonify({'error': 'Billing is not configured yet. Please contact support.'}), 500

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

# ---------------------------------------------------------------------------
# PayPal Checkout Routes
# ---------------------------------------------------------------------------

@billing_bp.route('/paypal/checkout', methods=['POST'])
@login_required
def paypal_checkout():
    """
    Create a PayPal order for subscription or one-time purchase.
    Body (JSON): { "plan": "pro_monthly" | "pro_annual" | "tokens" }
    Returns: { "order_id": "<paypal_order_id>" }
    """
    data = request.get_json(silent=True) or {}
    plan = data.get('plan', '').strip()

    valid_plans = {'pro_monthly', 'pro_annual', 'tokens'}
    if plan not in valid_plans:
        return jsonify({'error': f"Unknown plan '{plan}'"}), 400

    # Check PayPal is configured
    if not current_app.config.get('PAYPAL_CLIENT_ID'):
        logger.error("PAYPAL_CLIENT_ID is not set")
        return jsonify({'error': 'PayPal is not configured. Please contact support.'}), 500

    try:
        paypal = get_paypal_client()
        base = request.host_url.rstrip('/')
        return_url = f"{base}/billing/return?plan={plan}"
        cancel_url = f"{base}/billing/cancel"
        
        order_id = paypal.create_order(plan, str(current_user.id), return_url, cancel_url)
        
        if not order_id:
            return jsonify({'error': 'Failed to create PayPal order'}), 500
        
        logger.info(f"PayPal order created for user {current_user.id}: {order_id}")
        return jsonify({'order_id': order_id})
    except Exception as e:
        logger.error(f"PayPal order creation error: {e}")
        return jsonify({'error': str(e)}), 500


@billing_bp.route('/paypal/capture', methods=['POST'])
@login_required
def paypal_capture():
    """
    Capture a PayPal order to complete payment.
    Body (JSON): { "order_id": "<paypal_order_id>" }
    Returns: { "status": "success|error", "message": "..." }
    """
    data = request.get_json(silent=True) or {}
    order_id = data.get('order_id', '').strip()

    if not order_id:
        return jsonify({'error': 'Order ID is required'}), 400

    try:
        paypal = get_paypal_client()
        result = paypal.capture_order(order_id)
        
        if not result:
            return jsonify({'status': 'error', 'message': 'Failed to capture order'}), 400
        
        # Get purchase unit info
        purchase_units = result.get('purchase_units', [])
        if purchase_units:
            custom_id = purchase_units[0].get('custom_id', '')
            
            # For token purchases, add tokens to user
            if custom_id == str(current_user.id):
                plan_param = request.args.get('plan', 'tokens')
                if plan_param in ['tokens', 'pro_monthly', 'pro_annual']:
                    current_user.token_balance = (current_user.token_balance or 0) + TOKEN_PACK_AMOUNT
                    db.session.commit()
                    logger.info(f"User {current_user.id} purchased token pack via PayPal (+{TOKEN_PACK_AMOUNT} tokens)")
        
        return jsonify({'status': 'success', 'message': 'Payment captured successfully'})
    except Exception as e:
        logger.error(f"PayPal order capture error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@billing_bp.route('/paypal/subscribe', methods=['POST'])
@login_required
def paypal_subscribe():
    """
    Create a PayPal subscription.
    Body (JSON): { "plan": "pro_monthly" | "pro_annual" }
    Returns: { "subscription_url": "<paypal_subscription_url>" }
    """
    data = request.get_json(silent=True) or {}
    plan = data.get('plan', '').strip()

    subscription_plans = {'pro_monthly', 'pro_annual'}
    if plan not in subscription_plans:
        return jsonify({'error': f"Unknown subscription plan '{plan}'"}), 400

    try:
        paypal = get_paypal_client()
        
        # Create billing plan if needed (in production, these could be cached/pre-created)
        plan_id = paypal.create_billing_plan(plan)
        if not plan_id:
            return jsonify({'error': 'Failed to create subscription plan'}), 500
        
        # Create subscription
        subscription_id = paypal.create_subscription(
            plan_id, 
            str(current_user.id),
            current_user.email
        )
        
        if not subscription_id:
            return jsonify({'error': 'Failed to create subscription'}), 500
        
        # Store subscription ID
        current_user.paypal_subscription_id = subscription_id
        current_user.paypal_email = current_user.email
        db.session.commit()
        
        logger.info(f"PayPal subscription created for user {current_user.id}: {subscription_id}")
        
        # Get subscription approval link
        try:
            sub_details = paypal.get_subscription(subscription_id)
            approval_url = sub_details.get('links', [])
            for link in approval_url:
                if link.get('rel') == 'approve':
                    return jsonify({'subscription_url': link.get('href')})
        except:
            pass
        
        return jsonify({'status': 'created', 'subscription_id': subscription_id})
    except Exception as e:
        logger.error(f"PayPal subscription creation error: {e}")
        return jsonify({'error': str(e)}), 500


@billing_bp.route('/paypal/webhook', methods=['POST'])
def paypal_webhook():
    """
    Receive PayPal webhook events (CSRF-exempt).
    PayPal sends subscription and payment notifications here.
    """
    try:
        # Get webhook headers
        transmission_id = request.headers.get('Paypal-Transmission-Id', '')
        transmission_time = request.headers.get('Paypal-Transmission-Time', '')
        cert_url = request.headers.get('Paypal-Cert-Url', '')
        actual_sig = request.headers.get('Paypal-Transmission-Sig', '')
        
        event = request.get_json()
        event_type = event.get('event_type', '')
        
        # Log the webhook
        logger.info(f"PayPal webhook received: {event_type}")
        
        # Check if already processed
        event_id = event.get('id', '')
        if event_id and WebhookEvent.query.filter_by(source='paypal', event_id=event_id).first():
            logger.debug(f"PayPal webhook already processed: {event_id}")
            return jsonify({'status': 'already_processed'}), 200
        
        # Verify webhook (optional but recommended)
        webhook_id = current_app.config.get('PAYPAL_WEBHOOK_ID', '')
        if webhook_id:
            paypal = get_paypal_client()
            if not paypal.verify_webhook_signature(webhook_id, event, transmission_id, transmission_time, cert_url, actual_sig):
                logger.warning(f"PayPal webhook verification failed")
                abort(401)
        
        # Handle specific event types
        resource = event.get('resource', {})
        
        if event_type == 'CHECKOUT.ORDER.APPROVED':
            _on_paypal_order_approved(resource)
        elif event_type == 'CHECKOUT.ORDER.COMPLETED':
            _on_paypal_order_completed(resource)
        elif event_type == 'BILLING.SUBSCRIPTION.CREATED':
            _on_paypal_subscription_created(resource)
        elif event_type == 'BILLING.SUBSCRIPTION.UPDATED':
            _on_paypal_subscription_updated(resource)
        elif event_type == 'BILLING.SUBSCRIPTION.CANCELLED':
            _on_paypal_subscription_cancelled(resource)
        elif event_type == 'PAYMENT.CAPTURE.COMPLETED':
            _on_paypal_payment_completed(resource)
        elif event_type == 'PAYMENT.CAPTURE.DENIED':
            _on_paypal_payment_denied(resource)
        
        # Store webhook event for idempotency
        if event_id:
            db.session.add(WebhookEvent(source='paypal', event_id=event_id))
            db.session.commit()
        
        return jsonify({'status': 'ok'}), 200
    except Exception as e:
        logger.exception(f"PayPal webhook error: {e}")
        return jsonify({'status': 'error', 'detail': str(e)}), 200


@billing_bp.route('/return')
def paypal_return():
    """PayPal return page after user approves payment."""
    return render_template('billing/success.html')


# ---------------------------------------------------------------------------
# PayPal Event Handlers
# ---------------------------------------------------------------------------

def _on_paypal_order_approved(resource: dict) -> None:
    """Handle when a PayPal order is approved."""
    logger.info(f"PayPal order approved: {resource.get('id')}")


def _on_paypal_order_completed(resource: dict) -> None:
    """Handle when a PayPal order is completed."""
    order_id = resource.get('id')
    custom_id = resource.get('custom_id', '')
    
    try:
        user = User.query.get(custom_id)
        if user:
            user.paypal_customer_id = order_id
            user.token_balance = (user.token_balance or 0) + TOKEN_PACK_AMOUNT
            db.session.commit()
            logger.info(f"User {user.id} completed PayPal payment: +{TOKEN_PACK_AMOUNT} tokens")
    except Exception as e:
        logger.error(f"Error processing PayPal order completion: {e}")


def _on_paypal_subscription_created(resource: dict) -> None:
    """Handle when a PayPal subscription is created."""
    subscription_id = resource.get('id')
    custom_id = resource.get('custom_id', '')
    status = resource.get('status', 'PENDING')
    
    try:
        user = User.query.get(custom_id)
        if user:
            user.paypal_subscription_id = subscription_id
            # Set to active only if subscription is approved
            if status in ['ACTIVE', 'APPROVAL_PENDING']:
                user.subscription_status = 'active'
                user.subscription_tier = 'pro'
            db.session.commit()
            logger.info(f"User {user.id} PayPal subscription created: {subscription_id} ({status})")
    except Exception as e:
        logger.error(f"Error processing PayPal subscription creation: {e}")


def _on_paypal_subscription_updated(resource: dict) -> None:
    """Handle when a PayPal subscription is updated."""
    subscription_id = resource.get('id')
    status = resource.get('status', '')
    
    try:
        user = User.query.filter_by(paypal_subscription_id=subscription_id).first()
        if user:
            if status == 'ACTIVE':
                user.subscription_status = 'active'
                user.subscription_tier = 'pro'
                # Parse billing cycle end date
                billing_info = resource.get('billing_info', {})
                if billing_info and 'next_billing_time' in billing_info:
                    next_billing = billing_info['next_billing_time']
                    if isinstance(next_billing, str):
                        try:
                            user.subscription_period_end = datetime.fromisoformat(next_billing.replace('Z', '+00:00'))
                        except:
                            pass
            elif status == 'SUSPENDED':
                user.subscription_status = 'past_due'
            
            db.session.commit()
            logger.info(f"User {user.id} PayPal subscription updated: status={status}")
    except Exception as e:
        logger.error(f"Error processing PayPal subscription update: {e}")


def _on_paypal_subscription_cancelled(resource: dict) -> None:
    """Handle when a PayPal subscription is cancelled."""
    subscription_id = resource.get('id')
    
    try:
        user = User.query.filter_by(paypal_subscription_id=subscription_id).first()
        if user:
            user.subscription_status = 'canceled'
            user.subscription_tier = 'free'
            user.subscription_period_end = None
            db.session.commit()
            logger.info(f"User {user.id} PayPal subscription cancelled: {subscription_id}")
    except Exception as e:
        logger.error(f"Error processing PayPal subscription cancellation: {e}")


def _on_paypal_payment_completed(resource: dict) -> None:
    """Handle when a PayPal payment capture is completed."""
    logger.info(f"PayPal payment completed: {resource.get('id')}")


def _on_paypal_payment_denied(resource: dict) -> None:
    """Handle when a PayPal payment capture is denied."""
    logger.warning(f"PayPal payment denied: {resource.get('id')}")