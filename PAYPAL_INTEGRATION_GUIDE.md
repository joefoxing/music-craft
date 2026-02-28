# PayPal Payment Integration Setup Guide

This document provides a complete guide to setting up and testing PayPal payment integration on your Joefoxing website.

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [PayPal Account Setup](#paypal-account-setup)
3. [Environment Configuration](#environment-configuration)
4. [Database Migration](#database-migration)
5. [Testing](#testing)
6. [Deployment](#deployment)
7. [Troubleshooting](#troubleshooting)

---

## Prerequisites

- PayPal Business Account (or Personal Account with ability to accept payments)
- Access to PayPal Developer Dashboard
- Python 3.11+
- Flask application running with the latest code

---

## PayPal Account Setup

### Step 1: Create a PayPal Developer App

1. Go to [PayPal Developer Dashboard](https://developer.paypal.com/dashboard/)
2. Sign in with your PayPal account (create one if needed)
3. In the left menu, click **Apps & Credentials**
4. Make sure you're on the **Sandbox** tab (for testing)
5. Under **REST API signature**, click **Create App** in the **Merchant** section
6. Give your app a name (e.g., "Joefoxing Music Generator")
7. Click **Create App**

### Step 2: Get Your Credentials

1. From the Apps & Credentials page, you'll see your app listed
2. Click on your app name to view its details
3. Copy the following credentials:
   - **Client ID** (you'll see "Client ID" label)
   - **Secret** (click "Show" to reveal the secret key)
4. Save these securely - you'll add them to your `.env` file

### Step 3: Set up Webhook Notifications

1. In the Developer Dashboard, go to **Apps & Credentials**
2. Click on your app to view details
3. Scroll down to the **Webhook URL** section
4. Add your webhook URL:
   - For Development: `http://localhost:5000/billing/paypal/webhook`
   - For Staging: `https://your-staging-domain.com/billing/paypal/webhook`
   - For Production: `https://your-production-domain.com/billing/paypal/webhook`
5. Select the following events to listen for:
   - `CHECKOUT.ORDER.APPROVED`
   - `CHECKOUT.ORDER.COMPLETED`
   - `BILLING.SUBSCRIPTION.CREATED`
   - `BILLING.SUBSCRIPTION.UPDATED`
   - `BILLING.SUBSCRIPTION.CANCELLED`
   - `PAYMENT.CAPTURE.COMPLETED`
   - `PAYMENT.CAPTURE.DENIED`
6. Click **Save**
7. Copy the **Webhook ID** and save it

---

## Environment Configuration

### Step 1: Update `.env` File

Add the following PayPal configuration to your `.env` file:

```dotenv
# PayPal Payment Gateway
PAYPAL_CLIENT_ID=your-sandbox-client-id-here
PAYPAL_CLIENT_SECRET=your-sandbox-secret-here
PAYPAL_MODE=sandbox
PAYPAL_WEBHOOK_ID=your-webhook-id-here
```

### Step 2: Verify Configuration

Make sure the following are already in your `.env`:

```dotenv
# Existing Stripe configuration (keep these)
STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
```

### Step 3: For Production Deployment

When deploying to production, update `.env` with live credentials:

```dotenv
PAYPAL_MODE=live
PAYPAL_CLIENT_ID=your-live-client-id-here
PAYPAL_CLIENT_SECRET=your-live-secret-here
PAYPAL_WEBHOOK_ID=your-live-webhook-id-here
```

---

## Database Migration

### Step 1: Apply Migration

Run the Alembic migration to add PayPal fields to the `users` table:

```bash
# In your project directory
docker compose exec app alembic upgrade head
```

Or if running locally:

```bash
# Activate virtual environment
source .venv/Scripts/activate  # or .venv\Scripts\activate on Windows

# Run migration
alembic upgrade head
```

This will add three new columns to the users table:
- `paypal_customer_id` - stores the PayPal customer/order ID
- `paypal_subscription_id` - stores the PayPal subscription ID
- `paypal_email` - stores the PayPal account email

### Step 2: Verify Migration

You can verify the migration was successful by checking the database:

```sql
-- Connect to your PostgreSQL/SQLite database and run:
SELECT paypal_customer_id, paypal_subscription_id, paypal_email 
FROM users LIMIT 1;
```

---

## Testing

### Manual Testing in Sandbox

#### Test 1: One-Time Purchase (Tokens)

1. Navigate to the pricing page: `http://localhost:5000/pricing`
2. Click **Upgrade to Pro** button
3. Select **PayPal** payment method
4. Click the **PayPal** button
5. You'll be redirected to PayPal sandbox
6. You can use sandbox test account credentials:
   - Email: `sb-buyer@personal.example.com`
   - Password: `sandbox_password`
7. Approve the payment
8. You should be redirected back to success page
9. Check the database to verify tokens were added

#### Test 2: Subscription

1. Navigate to pricing page
2. Choose **Monthly** or **Annual** billing
3. Click **Upgrade to Pro**
4. Select **PayPal** payment method
5. Click **PayPal** button
6. Use sandbox credentials to approve
7. User should be subscribed (check user.subscription_tier = 'pro')

#### Test 3: Webhook Notifications

To test webhooks locally, you can use a tunneling service:

```bash
# Using ngrok (install if needed: pip install pyngrok)
ngrok http 5000

# This gives you a URL like: https://xxxx-xx-xxx-xx-xx.ngrok.io
# Update your webhook URL in PayPal dashboard to:
# https://xxxx-xx-xxx-xx-xx.ngrok.io/billing/paypal/webhook
```

Alternatively, use Cloudflare Tunnel if already configured:
```bash
cloudflared tunnel run your-tunnel-id
```

### Automated Testing

```bash
# Run tests (if you have test suite set up)
pytest tests/test_paypal_integration.py -v
```

---

## Deployment

### Before Deploying to Production

1. ✅ Test thoroughly in sandbox mode
2. ✅ Verify all webhook URLs are correct
3. ✅ Make sure SSL/HTTPS is enabled on your domain
4. ✅ Backup your database
5. ✅ Have PayPal support contact info ready

### Step 1: Migrate to Live Mode

1. Request live PayPal credentials from your PayPal account
2. Update `.env` with live credentials:
   ```dotenv
   PAYPAL_MODE=live
   PAYPAL_CLIENT_ID=[your-live-client-id]
   PAYPAL_CLIENT_SECRET=[your-live-secret]
   PAYPAL_WEBHOOK_ID=[your-live-webhook-id]
   ```

### Step 2: Test in Production

Before announcing PayPal support:
1. Make a small test purchase
2. Verify webhook notifications are received
3. Check that user data is updated correctly in database

### Step 3: Monitor

After going live:
- Monitor application logs for PayPal errors
- Check database for transaction records
- Verify webhook notifications are received

---

## API Endpoints

### Creating Orders (for PayPal)

**Endpoint:** `POST /billing/paypal/checkout`

**Request:**
```json
{
  "plan": "pro_monthly"  // or "pro_annual", "tokens"
}
```

**Response:**
```json
{
  "order_id": "7H123456789..."
}
```

### Capturing Orders

**Endpoint:** `POST /billing/paypal/capture`

**Request:**
```json
{
  "order_id": "7H123456789..."
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Payment captured successfully"
}
```

### Creating Subscriptions

**Endpoint:** `POST /billing/paypal/subscribe`

**Request:**
```json
{
  "plan": "pro_monthly"  // or "pro_annual"
}
```

**Response:**
```json
{
  "subscription_url": "https://www.paypal.com/subscribe?..."
}
```

### Webhook Events

**Endpoint:** `POST /billing/paypal/webhook` (CSRF-exempt)

**Handled Events:**
- `CHECKOUT.ORDER.APPROVED` - Order approved
- `CHECKOUT.ORDER.COMPLETED` - Order completed
- `BILLING.SUBSCRIPTION.CREATED` - Subscription created
- `BILLING.SUBSCRIPTION.UPDATED` - Subscription updated
- `BILLING.SUBSCRIPTION.CANCELLED` - Subscription cancelled
- `PAYMENT.CAPTURE.COMPLETED` - Payment captured
- `PAYMENT.CAPTURE.DENIED` - Payment denied

---

## Troubleshooting

### Error: "PayPal is not configured"

**Cause:** PayPal credentials not set in `.env`

**Solution:**
1. Check `.env` file has `PAYPAL_CLIENT_ID` and `PAYPAL_CLIENT_SECRET`
2. Restart the Flask application
3. Verify values are correct (no spaces or typos)

### Error: "Failed to create PayPal order"

**Cause:** Invalid plan name or API issue

**Solution:**
1. Verify plan name is one of: `pro_monthly`, `pro_annual`, `tokens`
2. Check PayPal credentials are correct
3. Check application logs for detailed error message
4. Verify you're using correct API mode (sandbox vs live)

### Webhooks not being received

**Cause:** Webhook URL incorrect or unreachable

**Solution:**
1. Verify webhook URL in PayPal dashboard is correct
2. Make sure domain is publicly accessible
3. Check HTTPS is enabled
4. If testing locally, use ngrok or Cloudflare tunnel
5. Allow webhook endpoint to be CSRF-exempt (check `app/__init__.py`)

### User subscription not updating

**Cause:** Webhook not processed or database issue

**Solution:**
1. Check application logs for webhook errors
2. Verify database migration ran successfully
3. Check that `paypal_subscription_id` column exists in users table
4. Try manually triggering webhook via PayPal dashboard testing tool

### Duplicate Charges

**Cause:** User clicking button multiple times

**Solution:**
- Disable button after first click (already implemented)
- Check user's token balance and subscription status before processing

---

## Security Considerations

1. **Never commit credentials** - Keep `.env` files out of git
2. **Verify webhook signatures** - PayPal implementation already does this
3. **Use HTTPS** - Always use HTTPS in production
4. **Rate limiting** - API endpoints are inherited from Flask app rate limiting
5. **Idempotency** - Webhooks are processed only once (via `WebhookEvent` table)

---

## Support

For issues with PayPal integration:
1. Check application logs: `docker compose logs app`
2. Review PayPal Developer Documentation: https://developer.paypal.com/docs/
3. Contact PayPal Support through developer portal

For issues with the implementation:
1. Check the code in `app/paypal.py`
2. Review endpoints in `app/routes/billing.py`
3. Check pricing template in `app/templates/pricing.html`

---

## Useful Links

- [PayPal Developer Dashboard](https://developer.paypal.com/dashboard/)
- [PayPal Orders API Docs](https://developer.paypal.com/docs/api/orders/v2/)
- [PayPal Billing Plans API](https://developer.paypal.com/docs/api/billing/v1/)
- [PayPal Webhook Documentation](https://developer.paypal.com/docs/api-basics/notifications/webhooks/)

---

**Created:** February 24, 2026
**Last Updated:** February 24, 2026
