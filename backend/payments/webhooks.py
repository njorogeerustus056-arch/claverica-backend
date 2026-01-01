# payments/webhooks.py
"""
Webhook handlers for payment gateways
"""
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.http import HttpResponse, JsonResponse
import json
import logging
from .utils.payment_gateway import PaymentGateway

logger = logging.getLogger(__name__)


@csrf_exempt
@require_POST
def stripe_webhook(request):
    """Handle Stripe webhooks"""
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    
    if not sig_header:
        logger.error("Missing Stripe signature header")
        return HttpResponse(status=400)
    
    result = PaymentGateway.handle_webhook(payload, sig_header)
    
    if result.get('success'):
        return HttpResponse(status=200)
    else:
        logger.error(f"Webhook processing failed: {result.get('error')}")
        return HttpResponse(status=400)


@csrf_exempt
@require_POST
def paypal_webhook(request):
    """Handle PayPal webhooks"""
    try:
        payload = json.loads(request.body)
        event_type = payload.get('event_type')
        
        logger.info(f"PayPal webhook received: {event_type}")
        
        # Handle different PayPal events
        if event_type == 'PAYMENT.CAPTURE.COMPLETED':
            payment_id = payload.get('resource', {}).get('id')
            logger.info(f"Payment completed: {payment_id}")
            
            # Update your database
            # transaction = Transaction.objects.get(gateway_transaction_id=payment_id)
            # transaction.status = 'completed'
            # transaction.save()
            
        elif event_type == 'PAYMENT.CAPTURE.DENIED':
            payment_id = payload.get('resource', {}).get('id')
            logger.warning(f"Payment denied: {payment_id}")
            
        return JsonResponse({'status': 'received'})
        
    except json.JSONDecodeError:
        logger.error("Invalid JSON in PayPal webhook")
        return HttpResponse(status=400)
    except Exception as e:
        logger.error(f"PayPal webhook error: {e}")
        return HttpResponse(status=500)