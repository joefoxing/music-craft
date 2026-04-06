"""
PayPal integration module for handling orders and subscriptions.
Uses PayPal Orders API (v2) and Billing Plans API.
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

import requests
from flask import current_app

logger = logging.getLogger(__name__)

PAYPAL_API_BASE = {
    'sandbox': 'https://api-m.sandbox.paypal.com',
    'live': 'https://api-m.paypal.com',
}

# Plan amounts (in USD)
PLAN_AMOUNTS = {
    'pro_monthly': '15.00',
    'pro_annual': '144.00',
    'tokens': '5.00',
}

# Plan names for PayPal billing plans
PLAN_NAMES = {
    'pro_monthly': 'Pro Creator - Monthly',
    'pro_annual': 'Pro Creator - Annual',
    'tokens': 'Token Pack - 100 Tokens',
}

# Pre-defined product IDs for fallback when Products API is not available
# These should be created manually in PayPal dashboard or via direct API call
# Format: plan_key -> product_id
PAYPAL_PRODUCT_IDS = {
    'pro_monthly': 'PROD-pro_monthly',
    'pro_annual': 'PROD-pro_annual',
    'tokens': 'PROD-tokens',
}

# Pre-created PayPal billing plan IDs (created manually in PayPal dashboard)
# These are used directly without creating new plans each time
# Format: plan_key -> plan_id
PAYPAL_PLAN_IDS = {
    'pro_monthly': 'P-7DF74401P1230474LNGRTMNA',
    'pro_annual': 'P-3LJ55192XV5352943NGRTL6A',
    'tokens': 'P-95K10921F1962163HNGRTLBY',
}


class PayPalClient:
    """Client for communicating with PayPal API."""
    
    def __init__(self):
        """Initialize PayPal client with credentials from config."""
        self.client_id = current_app.config.get('PAYPAL_CLIENT_ID')
        self.client_secret = current_app.config.get('PAYPAL_CLIENT_SECRET')
        self.mode = current_app.config.get('PAYPAL_MODE', 'sandbox')
        self.base_url = PAYPAL_API_BASE.get(self.mode, PAYPAL_API_BASE['sandbox'])
        self.access_token = None
        self.token_expires_at = None
    
    def _get_access_token(self) -> str:
        """Get a valid PayPal access token."""
        # Return cached token if still valid
        if self.access_token and self.token_expires_at > datetime.utcnow():
            return self.access_token
        
        try:
            response = requests.post(
                f"{self.base_url}/v1/oauth2/token",
                auth=(self.client_id, self.client_secret),
                headers={"Accept": "application/json", "Accept-Language": "en_US"},
                data={"grant_type": "client_credentials"},
                timeout=10
            )
            response.raise_for_status()
            
            data = response.json()
            self.access_token = data['access_token']
            # Token typically expires in 3600 seconds, set expiry to 5 minutes before
            self.token_expires_at = datetime.utcnow() + timedelta(seconds=data.get('expires_in', 3600) - 300)
            
            return self.access_token
        except Exception as e:
            logger.error(f"Failed to get PayPal access token: {e}")
            raise
    
    def _request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make an authenticated request to PayPal API."""
        token = self._get_access_token()
        headers = kwargs.pop('headers', {})
        headers.update({
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        })
        
        url = f"{self.base_url}{endpoint}"
        
        try:
            response = requests.request(
                method,
                url,
                headers=headers,
                timeout=10,
                **kwargs
            )
            response.raise_for_status()
            
            if response.status_code == 204:  # No Content
                return {}
            
            return response.json() if response.text else {}
        except requests.exceptions.RequestException as e:
            # Log the full error response for debugging
            error_detail = ""
            try:
                if hasattr(e.response, 'text'):
                    error_detail = f" Response: {e.response.text}"
            except:
                pass
            logger.error(f"PayPal API request failed: {method} {endpoint}: {e}{error_detail}")
            raise
    
    def create_order(self, plan: str, user_id: str, return_url: str, cancel_url: str = None) -> Optional[str]:
        """
        Create a PayPal order for a one-time purchase (tokens).
        Returns the order ID if successful.
        """
        logger.info(f"Creating PayPal order - Plan: {plan}, User: {user_id}")
        logger.info(f"PLAN_AMOUNTS dict: {PLAN_AMOUNTS}")
        
        if plan not in PLAN_AMOUNTS:
            logger.error(f"Unknown plan: {plan}")
            return None
        
        amount = PLAN_AMOUNTS[plan]
        logger.info(f"Retrieved amount for plan '{plan}': {amount} (type: {type(amount)})")
        description = PLAN_NAMES.get(plan, f"Purchase - {plan}")
        
        # If cancel_url not provided, derive it from return_url
        if not cancel_url:
            cancel_url = return_url.split('?')[0].replace('/billing/paypal/return', '/billing/cancel')
            if cancel_url == return_url.split('?')[0]:  # replacement didn't work
                cancel_url = return_url.split('?')[0]
        
        payload = {
            "intent": "CAPTURE",
            "purchase_units": [
                {
                    "amount": {
                        "currency_code": "USD",
                        "value": amount
                    },
                    "description": description,
                    "custom_id": user_id,
                }
            ],
            "application_context": {
                "brand_name": "Joefoxing",
                "landing_page": "BILLING",
                "user_action": "PAY_NOW",
                "return_url": return_url,
                "cancel_url": cancel_url,
            }
        }
        
        logger.info(f"PayPal order payload: {payload}")
        
        try:
            result = self._request('POST', '/v2/checkout/orders', json=payload)
            order_id = result.get('id')
            logger.info(f"PayPal order created: {order_id}")
            return order_id
        except Exception as e:
            logger.error(f"Failed to create PayPal order: {e}")
            raise
    
    def capture_order(self, order_id: str) -> Optional[Dict[str, Any]]:
        """Capture a PayPal order to complete the payment."""
        try:
            result = self._request('POST', f'/v2/checkout/orders/{order_id}/capture')
            status = result.get('status')
            
            if status in ['APPROVED', 'COMPLETED']:
                logger.info(f"PayPal order captured: {order_id}")
                return result
            else:
                logger.warning(f"PayPal order capture failed with status: {status}")
                return None
        except Exception as e:
            logger.error(f"Failed to capture PayPal order: {e}")
            raise
    
    def get_order(self, order_id: str) -> Optional[Dict[str, Any]]:
        """Get details about a PayPal order."""
        try:
            return self._request('GET', f'/v2/checkout/orders/{order_id}')
        except Exception as e:
            logger.error(f"Failed to get PayPal order details: {e}")
            raise
    
    def create_product(self, plan: str) -> Optional[str]:
        """
        Create a PayPal product for billing plans.
        Returns the product ID if successful or already exists.
        
        Products are required before creating billing plans.
        This method will check for existing products first to avoid duplicates.
        
        If the Products API is not available (e.g., certain sandbox accounts),
        falls back to using pre-defined product IDs.
        """
        if plan not in PLAN_NAMES:
            logger.error(f"Unknown plan: {plan}")
            return None
        
        description = PLAN_NAMES.get(plan, f"Product - {plan}")
        product_id = PAYPAL_PRODUCT_IDS.get(plan, f"PROD-{plan}")
        
        # Try to use existing product first
        try:
            existing = self._get_product_by_id(product_id)
            if existing:
                logger.info(f"Using existing PayPal product: {product_id}")
                return product_id
        except Exception as e:
            logger.debug(f"Could not retrieve product {product_id}: {e}")
            pass
        
        # Try to create new product if retrieval failed
        payload = {
            "id": product_id,
            "name": description,
            "description": description,
            "type": "SERVICE",
            "category": "SOFTWARE"
        }
        
        try:
            result = self._request('POST', '/v1/billing/products', json=payload)
            created_id = result.get('id')
            logger.info(f"PayPal product created: {created_id}")
            return created_id
        except Exception as e:
            logger.warning(f"Could not create PayPal product via API: {e}")
            # If product creation fails (e.g., Products API not available),
            # fall back to using the pre-defined product ID
            if "404" in str(e) or "not available" in str(e).lower():
                logger.info(f"Falling back to pre-defined product ID: {product_id}")
                return product_id
            # If product already exists (409 conflict), try to use it anyway
            elif "409" in str(e) or "DUPLICATE_PRODUCT" in str(e):
                try:
                    existing = self._get_product_by_id(product_id)
                    if existing:
                        return existing
                except:
                    pass
                # If retrieval fails, still return the ID (might work in plan creation)
                logger.info(f"Product already exists, using ID: {product_id}")
                return product_id
            # For other errors, retry or raise
            raise
    
    def _get_product_by_id(self, product_id: str) -> Optional[str]:
        """
        Check if a product exists by ID.
        Returns the product ID if found, None otherwise.
        """
        try:
            result = self._request('GET', f'/v1/billing/products/{product_id}')
            if result.get('id'):
                return result.get('id')
            return None
        except Exception as e:
            logger.debug(f"Product {product_id} not found: {e}")
            return None

    def create_billing_plan(self, plan: str) -> Optional[str]:
        """
        Create a PayPal billing plan for subscriptions.
        Returns the plan ID if successful.
        
        First checks for pre-created plan IDs to avoid unnecessary API calls.
        Then attempts to create or retrieve the required product.
        If the Products API is not available, uses pre-defined product IDs.
        """
        if plan not in PLAN_AMOUNTS:
            logger.error(f"Unknown plan: {plan}")
            return None
        
        # Check if we have a pre-created plan ID (preferred method)
        if plan in PAYPAL_PLAN_IDS:
            plan_id = PAYPAL_PLAN_IDS[plan]
            logger.info(f"Using pre-created PayPal plan ID: {plan_id}")
            return plan_id
        
        # Otherwise, create a new plan (fallback)
        logger.info(f"No pre-created plan ID found for {plan}, creating new plan...")
        
        # Get or create the product (or use fallback product ID)
        product_id = None
        try:
            product_id = self.create_product(plan)
        except Exception as e:
            logger.warning(f"Could not create product, trying fallback: {e}")
            # Use pre-defined product ID as fallback
            product_id = PAYPAL_PRODUCT_IDS.get(plan)
        
        if not product_id:
            logger.error(f"Failed to get product ID for plan: {plan}")
            return None
        
        amount = PLAN_AMOUNTS[plan]
        description = PLAN_NAMES.get(plan, f"Plan - {plan}")
        
        # Determine billing cycles
        if plan == 'pro_monthly':
            interval = 'MONTH'
            interval_count = 1
            cycles = 0  # Infinite
        elif plan == 'pro_annual':
            interval = 'YEAR'
            interval_count = 1
            cycles = 0  # Infinite
        else:
            # One-time plans not handled here
            return None
        
        payload = {
            "product_id": product_id,
            "name": description,
            "description": description,
            "type": "REGULAR",
            "payment_preferences": {
                "auto_bill_amount": "YES",
                "payment_failure_threshold": 3,
                "setup_fee": {
                    "currency_code": "USD",
                    "value": "0"
                }
            },
            "billing_cycles": [
                {
                    "frequency": {
                        "interval_unit": interval,
                        "interval_count": interval_count
                    },
                    "tenure_type": "REGULAR",
                    "sequence": 1,
                    "total_cycles": cycles,
                    "pricing_scheme": {
                        "fixed_price": {
                            "currency_code": "USD",
                            "value": amount
                        }
                    }
                }
            ]
        }
        
        try:
            logger.info(f"Creating billing plan with product {product_id}: {payload}")
            result = self._request('POST', '/v1/billing/plans', json=payload)
            plan_id = result.get('id')
            logger.info(f"PayPal billing plan created: {plan_id}")
            return plan_id
        except Exception as e:
            logger.error(f"Failed to create PayPal billing plan: {e}")
            raise
    
    def create_subscription(self, plan_id: str, user_id: str, email: str) -> Optional[Dict[str, Any]]:
        """
        Create a PayPal subscription for a user.
        Returns a dict with subscription_id and approval_url if successful.
        """
        # Get base URL from config, with fallback
        base_url = current_app.config.get('BASE_URL', 'http://localhost:3001')
        logger.info(f"Using base URL: {base_url}")
        
        payload = {
            "plan_id": plan_id,
            "subscriber": {
                "email_address": email,
            },
            "application_context": {
                "brand_name": "Joefoxing",
                "user_action": "SUBSCRIBE_NOW",
                "return_url": f"{base_url}/billing/return",
                "cancel_url": f"{base_url}/billing/cancel",
            },
            "custom_id": user_id,
        }
        
        logger.info(f"Creating subscription with payload: {payload}")
        
        try:
            result = self._request('POST', '/v1/billing/subscriptions', json=payload)
            subscription_id = result.get('id')
            
            logger.info(f"PayPal API response: {result}")
            
            if not subscription_id:
                logger.error(f"No subscription ID in response: {result}")
                return None
            
            logger.info(f"PayPal subscription created: {subscription_id}")
            
            # Try to get approval link from response
            approval_url = None
            links = result.get('links', [])
            logger.info(f"Links in response: {links}")
            
            for link in links:
                if link.get('rel') == 'approve':
                    approval_url = link.get('href')
                    logger.info(f"Found approve link: {approval_url}")
                    break
            
            # If no approval link in response, construct it manually
            if not approval_url:
                if self.mode == 'sandbox':
                    approval_url = f"https://www.sandbox.paypal.com/checkoutnow?token={subscription_id}"
                else:
                    approval_url = f"https://www.paypal.com/checkoutnow?token={subscription_id}"
                logger.info(f"Using constructed approval URL for subscription {subscription_id}: {approval_url}")
            
            result_dict = {
                'subscription_id': subscription_id,
                'approval_url': approval_url
            }
            logger.info(f"Returning result: {result_dict}")
            return result_dict
        except Exception as e:
            logger.error(f"Failed to create PayPal subscription: {e}", exc_info=True)
            raise
    
    def get_subscription(self, subscription_id: str) -> Optional[Dict[str, Any]]:
        """Get details about a PayPal subscription."""
        try:
            return self._request('GET', f'/v1/billing/subscriptions/{subscription_id}')
        except Exception as e:
            logger.error(f"Failed to get PayPal subscription details: {e}")
            raise
    
    def cancel_subscription(self, subscription_id: str, reason: str = "User canceled subscription") -> bool:
        """Cancel a PayPal subscription."""
        payload = {"reason": reason}
        
        try:
            self._request('POST', f'/v1/billing/subscriptions/{subscription_id}/cancel', json=payload)
            logger.info(f"PayPal subscription canceled: {subscription_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to cancel PayPal subscription: {e}")
            raise
    
    def verify_webhook_signature(self, webhook_id: str, event: Dict[str, Any], 
                                 transmission_id: str, transmission_time: str, 
                                 cert_url: str, actual_sig: str) -> bool:
        """Verify that a webhook event came from PayPal."""
        try:
            # Create the expected signature
            expected_sig_body = f"{transmission_id}|{transmission_time}|{webhook_id}|{int(event.get('create_time', '').timestamp() if isinstance(event.get('create_time'), datetime) else 0)}"
            
            # Verify with PayPal
            payload = {
                "transmission_id": transmission_id,
                "transmission_time": transmission_time,
                "cert_url": cert_url,
                "auth_algo": "SHA256withRSA",
                "transmission_sig": actual_sig,
                "webhook_id": webhook_id,
                "webhook_event": event
            }
            
            result = self._request('POST', '/v1/notifications/verify-webhook-signature', json=payload)
            verification_status = result.get('verification_status')
            
            if verification_status == 'SUCCESS':
                return True
            else:
                logger.warning(f"PayPal webhook verification failed: {verification_status}")
                return False
        except Exception as e:
            logger.error(f"Failed to verify PayPal webhook signature: {e}")
            return False


def get_paypal_client() -> PayPalClient:
    """Factory function to get a PayPal client instance."""
    return PayPalClient()
