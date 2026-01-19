from django import template
from django.utils.safestring import mark_safe
from core.models import AdSlot

register = template.Library()

@register.simple_tag(takes_context=True)
def get_ad(context, position):
    """
    Renders an ad for the given position if the user is not premium.
    """
    request = context.get('request')
    if request and request.user.is_authenticated and request.user.is_premium:
        return ""

    try:
        ad = AdSlot.objects.get(position=position, active=True)
        return mark_safe(ad.code)
    except AdSlot.DoesNotExist:
        return ""
