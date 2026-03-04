from django import template
from django.utils.safestring import mark_safe
from django.core.cache import cache
from core.models import AdSlot

register = template.Library()

@register.simple_tag(takes_context=True)
def get_ad(context, position):
    """
    Renders an ad for the given position if the user is not premium.
    Uses caching to avoid repeated database queries on every page load.
    """
    request = context.get('request')
    if request and request.user.is_authenticated and request.user.is_premium:
        return ""

    cache_key = f'ad_slot_{position}'
    cached_ad_code = cache.get(cache_key)

    if cached_ad_code is not None:
        return mark_safe(cached_ad_code)

    try:
        ad = AdSlot.objects.get(position=position, active=True)
        ad_code = ad.code
        # Cache for 1 hour (3600 seconds)
        cache.set(cache_key, ad_code, 3600)
        return mark_safe(ad_code)
    except AdSlot.DoesNotExist:
        # Cache the miss to avoid repeated queries for non-existent ads
        cache.set(cache_key, "", 3600)
        return ""
