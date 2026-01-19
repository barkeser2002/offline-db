from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from .models import ShopierPayment
from users.models import User

@csrf_exempt
def shopier_callback(request):
    """
    Callback for Shopier payment.
    Expects POST data with transaction_id and status.
    """
    if request.method == 'POST':
        # Mock Shopier payload parsing
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

    return HttpResponseBadRequest("Invalid method")
