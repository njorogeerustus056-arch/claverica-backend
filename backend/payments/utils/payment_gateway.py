"""
Payment gateway integration utilities
"""
import stripe
import logging
from django.conf import settings
from decimal import Decimal, InvalidOperation
from django.db import transaction as db_transaction

logger = logging.getLogger(__name__)

# Initialize Stripe with safe defaults
STRIPE_SECRET_KEY = getattr(settings, 'STRIPE_SECRET_KEY', 'sk_test_mock_key_for_development')
STRIPE_WEBHOOK_SECRET = getattr(settings, 'STRIPE_WEBHOOK_SECRET', 'whsec_mock_secret_for_development')
STRIPE_PUBLISHABLE_KEY = getattr(settings, 'STRIPE_PUBLISHABLE_KEY', 'pk_test_mock_key_for_development')

stripe.api_key = STRIPE_SECRET_KEY


class PaymentGateway:
    """Abstract payment gateway interface"""
    
    @staticmethod
    def create_payment_intent(amount, currency='usd', customer_id=None, metadata=None, 
                              description=None, return_url=None):
        """Create a payment intent"""
        try:
            # Validate amount
            if not isinstance(amount, (Decimal, int, float)):
                raise ValueError("Amount must be a number")
            
            amount_decimal = Decimal(str(amount))
            if amount_decimal <= Decimal('0'):
                raise ValueError("Amount must be greater than 0")
            
            # Use test mode if no real API key
            if 'test' in stripe.api_key or 'mock' in stripe.api_key:
                logger.warning("Using test/mock Stripe API key")
                return {
                    'success': True,
                    'client_secret': f'pi_mock_secret_{int(amount_decimal * 100)}',
                    'payment_intent_id': f'pi_mock_{int(amount_decimal * 100)}',
                    'status': 'requires_payment_method',
                    'test_mode': True,
                    'publishable_key': STRIPE_PUBLISHABLE_KEY
                }
            
            # Prepare parameters
            intent_params = {
                'amount': int(amount_decimal * 100),  # Convert to cents
                'currency': currency.lower(),
                'automatic_payment_methods': {
                    'enabled': True,
                },
                'metadata': metadata or {}
            }
            
            if customer_id:
                intent_params['customer'] = customer_id
            
            if description:
                intent_params['description'] = description
            
            if return_url:
                intent_params['return_url'] = return_url
            
            # Create payment intent
            intent = stripe.PaymentIntent.create(**intent_params)
            
            logger.info(f"Payment intent created: {intent.id} for amount {amount_decimal} {currency}")
            
            return {
                'success': True,
                'client_secret': intent.client_secret,
                'payment_intent_id': intent.id,
                'status': intent.status,
                'publishable_key': STRIPE_PUBLISHABLE_KEY,
                'amount': amount_decimal,
                'currency': currency
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error creating payment intent: {e}")
            return {'success': False, 'error': str(e), 'error_type': 'stripe_error'}
        except ValueError as e:
            logger.error(f"Validation error: {e}")
            return {'success': False, 'error': str(e), 'error_type': 'validation_error'}
        except Exception as e:
            logger.error(f"Payment gateway error: {e}")
            return {'success': False, 'error': str(e), 'error_type': 'server_error'}
    
    @staticmethod
    def retrieve_payment_intent(payment_intent_id):
        """Retrieve payment intent details"""
        try:
            # Use test mode if no real API key
            if 'test' in stripe.api_key or 'mock' in stripe.api_key:
                logger.warning("Using test/mock Stripe API key")
                return {
                    'success': True,
                    'payment_intent_id': payment_intent_id,
                    'status': 'succeeded',
                    'amount': 1000,  # $10.00 in cents
                    'currency': 'usd',
                    'test_mode': True
                }
            
            intent = stripe.PaymentIntent.retrieve(payment_intent_id)
            
            return {
                'success': True,
                'payment_intent_id': intent.id,
                'status': intent.status,
                'amount': intent.amount,
                'currency': intent.currency,
                'customer': intent.customer,
                'metadata': intent.metadata,
                'created': intent.created
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error retrieving payment intent: {e}")
            return {'success': False, 'error': str(e), 'error_type': 'stripe_error'}
        except Exception as e:
            logger.error(f"Error retrieving payment intent: {e}")
            return {'success': False, 'error': str(e), 'error_type': 'server_error'}
    
    @staticmethod
    def create_customer(email, name=None, phone=None, metadata=None):
        """Create a Stripe customer"""
        try:
            # Validate email
            if not email or '@' not in email:
                raise ValueError("Valid email is required")
            
            # Use test mode if no real API key
            if 'test' in stripe.api_key or 'mock' in stripe.api_key:
                logger.warning("Using test/mock Stripe API key")
                return {
                    'success': True, 
                    'customer_id': f'cus_mock_{email.replace("@", "_")}',
                    'test_mode': True,
                    'email': email
                }
            
            # Prepare customer data
            customer_data = {
                'email': email,
                'metadata': metadata or {}
            }
            
            if name:
                customer_data['name'] = name
            
            if phone:
                customer_data['phone'] = phone
            
            # Create customer
            customer = stripe.Customer.create(**customer_data)
            
            logger.info(f"Stripe customer created: {customer.id} for {email}")
            
            return {
                'success': True, 
                'customer_id': customer.id,
                'email': customer.email,
                'name': customer.name,
                'created': customer.created
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe customer creation error: {e}")
            return {'success': False, 'error': str(e), 'error_type': 'stripe_error'}
        except ValueError as e:
            logger.error(f"Validation error: {e}")
            return {'success': False, 'error': str(e), 'error_type': 'validation_error'}
        except Exception as e:
            logger.error(f"Customer creation error: {e}")
            return {'success': False, 'error': str(e), 'error_type': 'server_error'}
    
    @staticmethod
    def create_setup_intent(customer_id=None, metadata=None):
        """Create a setup intent for saving payment methods"""
        try:
            # Use test mode if no real API key
            if 'test' in stripe.api_key or 'mock' in stripe.api_key:
                logger.warning("Using test/mock Stripe API key")
                return {
                    'success': True,
                    'client_secret': f'setup_mock_secret_{customer_id or "anonymous"}',
                    'setup_intent_id': f'setup_mock_{customer_id or "anonymous"}',
                    'test_mode': True
                }
            
            # Prepare setup intent parameters
            setup_params = {
                'payment_method_types': ['card'],
                'metadata': metadata or {}
            }
            
            if customer_id:
                setup_params['customer'] = customer_id
            
            # Create setup intent
            setup_intent = stripe.SetupIntent.create(**setup_params)
            
            logger.info(f"Setup intent created: {setup_intent.id}")
            
            return {
                'success': True,
                'client_secret': setup_intent.client_secret,
                'setup_intent_id': setup_intent.id,
                'status': setup_intent.status
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe setup intent error: {e}")
            return {'success': False, 'error': str(e), 'error_type': 'stripe_error'}
        except Exception as e:
            logger.error(f"Setup intent creation error: {e}")
            return {'success': False, 'error': str(e), 'error_type': 'server_error'}
    
    @staticmethod
    def create_card_token(card_details):
        """Create a card token (frontend should do this)"""
        # Note: Card tokens should be created on frontend using Stripe.js
        # This is for server-side token creation (rarely needed)
        try:
            # Validate card details
            required_fields = ['number', 'exp_month', 'exp_year', 'cvc']
            for field in required_fields:
                if field not in card_details:
                    raise ValueError(f"Missing required field: {field}")
            
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
            
            logger.info(f"Card token created: {token.id}")
            
            return {
                'success': True, 
                'token': token.id,
                'card': {
                    'last4': token.card.last4,
                    'brand': token.card.brand,
                    'exp_month': token.card.exp_month,
                    'exp_year': token.card.exp_year
                }
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe token creation error: {e}")
            return {'success': False, 'error': str(e), 'error_type': 'stripe_error'}
        except ValueError as e:
            logger.error(f"Validation error: {e}")
            return {'success': False, 'error': str(e), 'error_type': 'validation_error'}
        except Exception as e:
            logger.error(f"Token creation error: {e}")
            return {'success': False, 'error': str(e), 'error_type': 'server_error'}
    
    @staticmethod
    def handle_webhook(payload, sig_header):
        """Handle Stripe webhooks"""
        from .models import Transaction, Account, AuditLog
        
        try:
            # Skip signature verification in test mode
            if 'mock' in STRIPE_WEBHOOK_SECRET:
                logger.warning("Skipping webhook signature verification in test mode")
                # Parse the JSON payload
                import json
                event_data = json.loads(payload)
                
                return PaymentGateway._process_webhook_event(event_data, test_mode=True)
            
            # Verify webhook signature
            event = stripe.Webhook.construct_event(
                payload, sig_header, STRIPE_WEBHOOK_SECRET
            )
            
            # Process the verified event
            return PaymentGateway._process_webhook_event(event)
            
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
    def _process_webhook_event(event, test_mode=False):
        """Process webhook event"""
        from .models import Transaction, Account, AuditLog
        
        event_type = event.get('type') if not test_mode else event.get('type', 'payment_intent.succeeded')
        event_id = event.get('id', 'mock_event_id') if not test_mode else 'mock_event_id'
        
        logger.info(f"Processing webhook event: {event_type} (ID: {event_id})")
        
        # Handle different event types
        if event_type == 'payment_intent.succeeded':
            payment_intent = event['data']['object'] if not test_mode else {
                'id': 'pi_mock_success',
                'amount': 1000,
                'currency': 'usd',
                'metadata': {},
                'customer': None
            }
            return PaymentGateway._handle_successful_payment(payment_intent, test_mode)
        
        elif event_type == 'payment_intent.payment_failed':
            payment_intent = event['data']['object'] if not test_mode else {
                'id': 'pi_mock_failed',
                'last_payment_error': {'message': 'Test failure'},
                'metadata': {}
            }
            return PaymentGateway._handle_failed_payment(payment_intent, test_mode)
        
        elif event_type == 'setup_intent.succeeded':
            setup_intent = event['data']['object'] if not test_mode else {
                'id': 'setup_mock_success',
                'metadata': {}
            }
            return PaymentGateway._handle_setup_intent_succeeded(setup_intent, test_mode)
        
        # Log other event types but don't process them
        logger.info(f"Webhook event {event_type} received but not processed")
        return {
            'success': True, 
            'processed': False,
            'event_type': event_type,
            'message': f'Event {event_type} acknowledged but not processed'
        }
    
    @staticmethod
    def _handle_successful_payment(payment_intent, test_mode=False):
        """Handle successful payment - integrate with your models"""
        from .models import Transaction, Account, AuditLog
        
        try:
            payment_intent_id = payment_intent['id']
            amount = Decimal(payment_intent['amount']) / Decimal('100')  # Convert from cents
            currency = payment_intent['currency'].upper()
            metadata = payment_intent.get('metadata', {})
            
            logger.info(f"Payment succeeded: {payment_intent_id} - {amount} {currency}")
            
            # Extract account information from metadata
            account_id = metadata.get('account_id')
            user_id = metadata.get('user_id')
            description = metadata.get('description', 'Stripe payment')
            
            # Log to audit log
            AuditLog.objects.create(
                user_id=user_id if user_id else None,
                action='stripe_payment_succeeded',
                details={
                    'payment_intent_id': payment_intent_id,
                    'amount': str(amount),
                    'currency': currency,
                    'account_id': account_id,
                    'metadata': metadata,
                    'test_mode': test_mode
                }
            )
            
            # Update account balance if account_id is provided
            if account_id:
                try:
                    with db_transaction.atomic():
                        account = Account.objects.get(id=account_id)
                        
                        # Create transaction record
                        transaction = Transaction.objects.create(
                            account=account,
                            amount=amount,
                            currency=currency,
                            transaction_type='deposit',
                            description=f"Stripe payment: {description}",
                            status='completed',
                            from_account=None,
                            to_account=None
                        )
                        
                        # Update account balance
                        account.balance += amount
                        account.save()
                        
                        logger.info(f"Account {account_id} updated with {amount} {currency}")
                        
                except Account.DoesNotExist:
                    logger.error(f"Account {account_id} not found for payment {payment_intent_id}")
                except Exception as e:
                    logger.error(f"Error updating account {account_id}: {e}")
            
            return {
                'success': True,
                'payment_intent_id': payment_intent_id,
                'amount': float(amount),
                'currency': currency,
                'processed': True,
                'account_updated': bool(account_id),
                'test_mode': test_mode
            }
            
        except Exception as e:
            logger.error(f"Error handling successful payment: {e}")
            return {
                'success': False,
                'error': str(e),
                'test_mode': test_mode
            }
    
    @staticmethod
    def _handle_failed_payment(payment_intent, test_mode=False):
        """Handle failed payment"""
        from .models import AuditLog
        
        payment_intent_id = payment_intent['id']
        error_message = payment_intent.get('last_payment_error', {}).get('message', 'Unknown error')
        metadata = payment_intent.get('metadata', {})
        user_id = metadata.get('user_id')
        
        logger.warning(f"Payment failed: {payment_intent_id} - {error_message}")
        
        # Log to audit log
        AuditLog.objects.create(
            user_id=user_id if user_id else None,
            action='stripe_payment_failed',
            details={
                'payment_intent_id': payment_intent_id,
                'error': error_message,
                'metadata': metadata,
                'test_mode': test_mode
            }
        )
        
        return {
            'success': False,
            'payment_intent_id': payment_intent_id,
            'error': error_message,
            'test_mode': test_mode
        }
    
    @staticmethod
    def _handle_setup_intent_succeeded(setup_intent, test_mode=False):
        """Handle successful setup intent (payment method saved)"""
        from .models import AuditLog
        
        setup_intent_id = setup_intent['id']
        metadata = setup_intent.get('metadata', {})
        user_id = metadata.get('user_id')
        
        logger.info(f"Setup intent succeeded: {setup_intent_id}")
        
        # Log to audit log
        AuditLog.objects.create(
            user_id=user_id if user_id else None,
            action='stripe_setup_intent_succeeded',
            details={
                'setup_intent_id': setup_intent_id,
                'metadata': metadata,
                'test_mode': test_mode
            }
        )
        
        return {
            'success': True,
            'setup_intent_id': setup_intent_id,
            'message': 'Payment method saved successfully',
            'test_mode': test_mode
        }


class CurrencyConverter:
    """Currency conversion utilities"""
    
    # Updated exchange rates (example rates)
    EXCHANGE_RATES = {
        'USD': 1.0,
        'EUR': 0.92,
        'GBP': 0.79,
        'KES': 150.0,
        'NGN': 1600.0,  # Updated
        'ZAR': 18.5,
        'CAD': 1.35,
        'AUD': 1.50,
        'JPY': 150.0,
        'CNY': 7.20,
        'INR': 83.0,
    }
    
    @staticmethod
    def convert(amount, from_currency, to_currency):
        """Convert amount between currencies"""
        try:
            # Convert to Decimal for precise calculations
            if not isinstance(amount, Decimal):
                amount = Decimal(str(amount))
            
            # Check if same currency
            from_currency = from_currency.upper()
            to_currency = to_currency.upper()
            
            if from_currency == to_currency:
                return amount
            
            # Get exchange rates
            from_rate = CurrencyConverter.EXCHANGE_RATES.get(from_currency)
            to_rate = CurrencyConverter.EXCHANGE_RATES.get(to_currency)
            
            if not from_rate:
                raise ValueError(f"Unsupported source currency: {from_currency}")
            if not to_rate:
                raise ValueError(f"Unsupported target currency: {to_currency}")
            
            # Convert to USD first, then to target currency
            amount_in_usd = amount / Decimal(str(from_rate))
            converted_amount = amount_in_usd * Decimal(str(to_rate))
            
            # Round to 2 decimal places
            return converted_amount.quantize(Decimal('0.01'))
            
        except InvalidOperation as e:
            raise ValueError(f"Invalid amount: {amount}") from e
        except Exception as e:
            raise ValueError(f"Currency conversion error: {e}") from e
    
    @staticmethod
    def get_supported_currencies():
        """Get list of supported currencies"""
        return list(CurrencyConverter.EXCHANGE_RATES.keys())
    
    @staticmethod
    def get_exchange_rate(from_currency, to_currency):
        """Get exchange rate between two currencies"""
        from_currency = from_currency.upper()
        to_currency = to_currency.upper()
        
        if from_currency == to_currency:
            return Decimal('1.00')
        
        from_rate = CurrencyConverter.EXCHANGE_RATES.get(from_currency)
        to_rate = CurrencyConverter.EXCHANGE_RATES.get(to_currency)
        
        if not from_rate or not to_rate:
            return None
        
        return Decimal(str(to_rate)) / Decimal(str(from_rate))