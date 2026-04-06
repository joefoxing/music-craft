# PayPal Subscription Plan Setup - Manual Configuration

## ✅ Status: Plans Created

Your PayPal billing plans have been successfully created and added to the system:

### Plan Mapping

| Plan Type | Plan ID | URL |
|-----------|---------|-----|
| **Pro Monthly** | `P-7DF74401P1230474LNGRTMNA` | https://www.sandbox.paypal.com/webapps/billing/plans/subscribe?plan_id=P-7DF74401P1230474LNGRTMNA |
| **Pro Annual** | `P-3LJ55192XV5352943NGRTL6A` | https://www.sandbox.paypal.com/webapps/billing/plans/subscribe?plan_id=P-3LJ55192XV5352943NGRTL6A |
| **Token Pack** | `P-95K10921F1962163HNGRTLBY` | https://www.sandbox.paypal.com/webapps/billing/plans/subscribe?plan_id=P-95K10921F1962163HNGRTLBY |

## How It Works

The application now uses these pre-created plan IDs directly:

1. User clicks "Subscribe to Pro"
2. App checks `PAYPAL_PLAN_IDS` mapping
3. ✅ **Skips plan creation** - Uses existing plan ID
4. Creates subscription with the plan ID
5. User is redirected to PayPal

### Benefits

- ⚡ **Faster** - No need to create plans each time
- 🔒 **Reliable** - Uses verified, working plans
- 📝 **Simplified** - No Product/Billing Plans API issues
- 🎯 **Direct** - Links directly to your sandbox plans

## Problem

Your PayPal sandbox account doesn't have access to the **Billing Products API** (`/v1/billing/products`). This is common with certain account types or regions.

## Solution

You have two options:

### Option 1: Manual Product Creation (Recommended)

Create the products manually in your PayPal dashboard:

1. Go to [PayPal Sandbox Dashboard](https://www.sandbox.paypal.com/signin)
2. Sign in with your seller account
3. Navigate to **Apps & Credentials** > **Sandbox**
4. Click on your app to access settings
5. Look for **Products** or **Billing** section
6. Create the following products with these IDs:

**Product 1:**
- ID: `PROD-pro_monthly`
- Name: `Pro Creator - Monthly`
- Description: `Pro Creator - Monthly subscription plan`
- Type: Service

**Product 2:**
- ID: `PROD-pro_annual`
- Name: `Pro Creator - Annual`
- Description: `Pro Creator - Annual subscription plan`
- Type: Service

**Product 3:**
- ID: `PROD-tokens`
- Name: `Token Pack - 100 Tokens`
- Description: `Token Pack - 100 Tokens for music generation`
- Type: Service

### Option 2: Use the API Setup Script

Run this Python script to automatically create the products (requires valid credentials):

```python
import requests
import base64

# Your PayPal credentials
CLIENT_ID = "YOUR_CLIENT_ID"
CLIENT_SECRET = "YOUR_CLIENT_SECRET"

# Get access token
auth = base64.b64encode(f"{CLIENT_ID}:{CLIENT_SECRET}".encode()).decode()
response = requests.post(
    "https://api-m.sandbox.paypal.com/v1/oauth2/token",
    headers={
        "Authorization": f"Basic {auth}",
        "Accept": "application/json"
    },
    data={"grant_type": "client_credentials"}
)
token = response.json()['access_token']

# Create products
products = [
    {
        "id": "PROD-pro_monthly",
        "name": "Pro Creator - Monthly",
        "description": "Pro Creator - Monthly subscription plan",
        "type": "SERVICE"
    },
    {
        "id": "PROD-pro_annual",
        "name": "Pro Creator - Annual",
        "description": "Pro Creator - Annual subscription plan",
        "type": "SERVICE"
    },
    {
        "id": "PROD-tokens",
        "name": "Token Pack - 100 Tokens",
        "description": "Token Pack - 100 Tokens for music generation",
        "type": "SERVICE"
    }
]

for product in products:
    response = requests.post(
        "https://api-m.sandbox.paypal.com/v1/billing/products",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        },
        json=product
    )
    print(f"Product {product['id']}: {response.status_code}")
    print(response.json())
```

## Updated Code

The code has been updated with fallback support:

1. **Fallback Product IDs** - If Products API fails, uses pre-defined IDs
2. **Better Error Handling** - Gracefully handles API unavailability
3. **Logging** - Clear indication of which approach is being used

## Testing

After creating the products, restart the application:

```bash
docker compose down
docker compose up -d
```

Then try subscribing again. You should see logs like:

```
INFO: Using existing PayPal product: PROD-pro_monthly
INFO: PayPal billing plan created: I-XXXXXXXXXXXXX
```

## Troubleshooting

### Products API Still Returning 404?

1. **Check Account Permissions**
   - Log into [PayPal Developer Dashboard](https://developer.paypal.com/dashboard/)
   - Verify your app has billing/subscription permissions
   - Check if Products API is enabled for your app

2. **Try Alternative Credentials**
   - Create a new app/credentials
   - Update `.env` with new credentials:
     ```bash
     PAYPAL_CLIENT_ID=new-client-id
     PAYPAL_CLIENT_SECRET=new-client-secret
     ```
   - Restart containers

3. **Check with PayPal Support**
   - If you continue getting 404s, your account might not support the Products API
   - Contact PayPal developer support to enable it

### Created Products But Still Getting Errors?

1. **Verify Product Creation**
   - Go to PayPal Sandbox dashboard
   - Look for Products section
   - Confirm all 3 products exist

2. **Check Billing Plans**
   - After products exist, billing plans should be created automatically
   - Check logs: `docker compose logs app | grep -i "billing plan"`

3. **Clear Cache** (if applicable)
   - Restart the application to clear any cached errors

## File Changes

- [app/paypal.py](app/paypal.py) - Updated with fallback support for Products API

## Next Steps

1. Create the 3 products (manually or via script)
2. Restart the application
3. Test subscription flow
4. Check logs for confirmation messages

