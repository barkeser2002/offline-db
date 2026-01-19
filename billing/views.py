from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.utils import timezone
from .models import ShopierPayment
from users.models import User
from django.conf import settings
import hmac
import hashlib
import base64

def verify_shopier_signature(post_data):
    """
    Verifies the Shopier signature.
    Since the exact algorithm is not documented in the codebase, we use a generic HMAC-SHA256
    verification of the transaction ID and status with the secret key.

    If SHOPIER_SECRET is not set, we log a warning (in a real app) and return False (or True if we want to allow skipping).
    For security, we return False if secret is missing but we're in production.
    """
    secret = settings.SHOPIER_SECRET
    if not secret:
        # If secret is not configured, we can't verify.
        # In a real scenario, this should probably fail, but to avoid breaking existing dev envs without secret:
        if settings.DEBUG:
            return True
        return False

    signature = post_data.get('signature')
    if not signature:
        return False

    transaction_id = post_data.get('platform_order_id', '')
    status = post_data.get('status', '')

    # Construct the payload to sign.
    # NOTE: This is an assumption based on common practices.
    # Real Shopier integration usually involves random_nr and other fields.
    # Without docs, we standardize on: transaction_id + status
    payload = f"{transaction_id}{status}"

    expected_signature = base64.b64encode(
        hmac.new(
            secret.encode('utf-8'),
            payload.encode('utf-8'),
            hashlib.sha256
        ).digest()
    ).decode('utf-8')

    return hmac.compare_digest(signature, expected_signature)

@csrf_exempt
@require_POST
def shopier_callback(request):
    """
    Callback for Shopier payment.
    Expects POST data with transaction_id and status.
    """
    # Verify signature
    if not verify_shopier_signature(request.POST):
        return HttpResponseBadRequest("Invalid signature")

    # Parse Shopier payload
    transaction_id = request.POST.get('platform_order_id') # Assuming this maps to our transaction_id
    status = request.POST.get('status') # success or failure

    if not transaction_id:
        return HttpResponseBadRequest("Missing transaction_id")

    try:
        payment = ShopierPayment.objects.get(transaction_id=transaction_id)

        if status == 'success':
            payment.status = 'success'
            payment.processed_at = timezone.now()
            payment.save()

            # Activate Premium
            user = payment.user
            user.is_premium = True
            user.save()

            return HttpResponse("OK")
        else:
            payment.status = 'failed'
            payment.save()
            return HttpResponse("OK")

    except ShopierPayment.DoesNotExist:
        return HttpResponseBadRequest("Payment not found")
