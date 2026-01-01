"""
Payment gateway integration utilities
"""
import stripe
import logging
from django.conf import settings
from decimal import Decimal

logger = logging.getLogger(__name__)

# Initialize Stripe with safe defaults
stripe.api_key = getattr(settings, 'STRIPE_SECRET_KEY', 'sk_test_mock_key_for_development')
stripe_webhook_secret = getattr(settings, 'STRIPE_WEBHOOK_SECRET', 'whsec_mock_secret_for_development')


class PaymentGateway:
    """Abstract payment gateway interface"""
    
    @staticmethod
    def create_payment_intent(amount, currency, customer_id=None, metadata=None):
        """Create a payment intent"""
        try:
            # Use test mode if no real API key
            if 'test' in stripe.api_key or 'mock' in stripe.api_key:
                logger.warning("Using test/mock Stripe API key")
                return {
                    'success': True,
                    'client_secret': 'pi_mock_secret_' + str(id(amount)),
                    'payment_intent_id': 'pi_mock_' + str(id(amount)),
                    'status': 'succeeded',
                    'test_mode': True
                }
            
            intent = stripe.PaymentIntent.create(
                amount=int(amount * 100),  # Convert to cents
                currency=currency.lower(),
                customer=customer_id,
                metadata=metadata or {},
                automatic_payment_methods={
                    'enabled': True,
                }
            )
            return {
                'success': True,
                'client_secret': intent.client_secret,
                'payment_intent_id': intent.id,
                'status': intent.status
            }
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error: {e}")
            return {'success': False, 'error': str(e)}
        except Exception as e:
            logger.error(f"Payment gateway error: {e}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def create_customer(email, name=None):
        """Create a Stripe customer"""
        try:
            # Use test mode if no real API key
            if 'test' in stripe.api_key or 'mock' in stripe.api_key:
                logger.warning("Using test/mock Stripe API key")
                return {
                    'success': True, 
                    'customer_id': f'cus_mock_{email.replace("@", "_")}',
                    'test_mode': True
                }
            
            customer = stripe.Customer.create(
                email=email,
                name=name
            )
            return {'success': True, 'customer_id': customer.id}
        except stripe.error.StripeError as e:
            logger.error(f"Stripe customer creation error: {e}")
            return {'success': False, 'error': str(e)}
        except Exception as e:
            logger.error(f"Customer creation error: {e}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def create_card_token(card_details):
        """Create a card token (frontend should do this)"""
        # Note: Card tokens should be created on frontend using Stripe.js
        # This is for server-side token creation (rarely needed)
        try:
            # Use test mode if no real API key
            if 'test' in stripe.api_key or 'mock' in stripe.api_key:
                logger.warning("Using test/mock Stripe API key")
                return {
                    'success': True, 
                    'token': f'tok_mock_{card_details.get("last4", "4242")}',
                    'test_mode': True
                }
            
            token = stripe.Token.create(
                card={
                    'number': card_details['number'],
                    'exp_month': card_details['exp_month'],
                    'exp_year': card_details['exp_year'],
                    'cvc': card_details['cvc'],
                }
            )
            return {'success': True, 'token': token.id}
        except stripe.error.StripeError as e:
            logger.error(f"Stripe token creation error: {e}")
            return {'success': False, 'error': str(e)}
        except Exception as e:
            logger.error(f"Token creation error: {e}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def handle_webhook(payload, sig_header):
        """Handle Stripe webhooks"""
        try:
            # Skip signature verification in test mode
            if 'mock' in stripe_webhook_secret:
                logger.warning("Skipping webhook signature verification in test mode")
                return {
                    'success': True, 
                    'processed': True,
                    'test_mode': True,
                    'message': 'Test mode - webhook processed without verification'
                }
            
            event = stripe.Webhook.construct_event(
                payload, sig_header, stripe_webhook_secret
            )
            
            # Handle different event types
            if event['type'] == 'payment_intent.succeeded':
                payment_intent = event['data']['object']
                return PaymentGateway._handle_successful_payment(payment_intent)
            elif event['type'] == 'payment_intent.payment_failed':
                payment_intent = event['data']['object']
                return PaymentGateway._handle_failed_payment(payment_intent)
            
            return {'success': True, 'processed': True}
            
        except ValueError as e:
            logger.error(f"Invalid payload: {e}")
            return {'success': False, 'error': 'Invalid payload'}
        except stripe.error.SignatureVerificationError as e:
            logger.error(f"Invalid signature: {e}")
            return {'success': False, 'error': 'Invalid signature'}
        except Exception as e:
            logger.error(f"Webhook error: {e}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def _handle_successful_payment(payment_intent):
        """Handle successful payment"""
        # This should update your database
        logger.info(f"Payment succeeded: {payment_intent['id']}")
        return {
            'success': True,
            'payment_intent_id': payment_intent['id'],
            'amount': payment_intent['amount'] / 100,
            'status': 'succeeded'
        }
    
    @staticmethod
    def _handle_failed_payment(payment_intent):
        """Handle failed payment"""
        logger.warning(f"Payment failed: {payment_intent['id']}")
        return {
            'success': False,
            'payment_intent_id': payment_intent['id'],
            'error': payment_intent.get('last_payment_error', {}).get('message', 'Unknown error')
        }


class CurrencyConverter:
    """Currency conversion utilities"""
    
    EXCHANGE_RATES = {
        'USD': 1.0,
        'EUR': 0.92,
        'GBP': 0.79,
        'KES': 150.0,
        'NGN': 850.0,
        'ZAR': 18.5,
    }
    
    @staticmethod
    def convert(amount, from_currency, to_currency):
        """Convert amount between currencies"""
        if from_currency == to_currency:
            return amount
        
        from_rate = CurrencyConverter.EXCHANGE_RATES.get(from_currency.upper())
        to_rate = CurrencyConverter.EXCHANGE_RATES.get(to_currency.upper())
        
        if not from_rate or not to_rate:
            raise ValueError(f"Unsupported currency: {from_currency} or {to_currency}")
        
        # Convert to USD first, then to target currency
        amount_in_usd = amount / from_rate
        converted_amount = amount_in_usd * to_rate
        
        return Decimal(str(converted_amount)).quantize(Decimal('0.01'))