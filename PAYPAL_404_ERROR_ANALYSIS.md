# PayPal 404 Error Analysis: Billing Plans

## Problem
```
404 Client Error: Not Found for url: https://api-m.sandbox.paypal.com/v1/billing/plans
```

## Root Cause

The error occurs in the `create_billing_plan()` method when attempting to create a PayPal billing plan. The issue is that **PayPal requires a product to exist before you can create a billing plan that references it**.

### Current Flow (Broken)
1. User clicks "Subscribe to Pro"
2. `paypal_subscribe()` route calls `paypal.create_billing_plan(plan)`
3. `create_billing_plan()` attempts POST to `/v1/billing/plans` with a `product_id` like `"PROD-pro_monthly"`
4. **404 Error**: Product doesn't exist; the endpoint can't find it

### Why It Fails

In [app/paypal.py](app/paypal.py#L220), the payload contains:
```python
payload = {
    "product_id": f"PROD-{plan}",  # e.g., "PROD-pro_monthly"
    "name": description,
    ...
}
```

**Problem**: The `product_id` references a product that was never created. PayPal returns 404 because the product doesn't exist.

## Solution

You need to:

1. **Create products first** using the PayPal Products API (`/v1/billing/products`)
2. **Cache the product IDs** in the database to avoid recreating them on every subscription
3. **Use the cached product ID** when creating billing plans

### Implementation Steps

1. Add a new method `create_or_get_product()` to PayPalClient
2. Add methods to track created products (database or cache)
3. Modify `create_billing_plan()` to use existing products
4. Create products on startup or first use

## Files to Modify

- [app/paypal.py](app/paypal.py) - Add product creation logic
- [app/models.py](app/models.py) - Add a table to track PayPal products (optional)
- [app/routes/billing.py](app/routes/billing.py) - Update subscription creation flow

## PayPal API References

- **Products API**: POST `/v1/billing/products`
- **Billing Plans API**: POST `/v1/billing/plans` (requires existing product)
- **Subscriptions API**: POST `/v1/billing/subscriptions` (requires existing plan)

## Testing Notes

After implementing the fix:
1. Verify products are created successfully
2. Verify billing plans are created with correct product_id
3. Verify subscriptions can be created with billing plan_id
4. Test the full subscription flow in sandbox

