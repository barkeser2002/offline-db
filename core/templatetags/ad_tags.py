from django import template
from analytics.models import AdSlot
from django.utils.safestring import mark_safe

register = template.Library()

@register.simple_tag
def get_ad(position):
    try:
        ad = AdSlot.objects.filter(position=position, is_active=True).first()
        return mark_safe(ad.content) if ad else ""
    except:
        return ""
