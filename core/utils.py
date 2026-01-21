import requests
import random
from .models import SiteSettings
from django.core.cache import cache
from django.http import HttpResponseForbidden
from functools import wraps

class DeepLTranslator:
    def __init__(self):
        self.settings = SiteSettings.get_solo()
        self.keys = [k.strip() for k in self.settings.deepl_api_keys.split(',') if k.strip()]

    def translate(self, text, target_lang='TR'):
        if not self.keys:
            # Fallback or error
            return f"[No Keys] {text}"

        # Rotate keys (Random selection for simplicity, could be round-robin)
        key = random.choice(self.keys)

        try:
            # DeepL API logic (Free API url for example)
            url = "https://api-free.deepl.com/v2/translate"
            params = {
                "auth_key": key,
                "text": text,
                "target_lang": target_lang
            }
            # response = requests.post(url, data=params) # Commented out to avoid external calls without keys
            # result = response.json()
            # return result['translations'][0]['text']

            return f"[Translated to {target_lang}] {text}"
        except Exception as e:
            return f"[Error] {text}"

def rate_limit_ip(limit=5, period=60):
    """
    Decorator to rate limit views by IP address.
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            ip = request.META.get('REMOTE_ADDR')
            if not ip:
                ip = 'unknown'

            key = f"ratelimit_{ip}_{view_func.__name__}"

            try:
                # Returns the new value
                count = cache.incr(key)
            except ValueError:
                # Key didn't exist
                cache.set(key, 1, period)
                count = 1

            if count > limit:
                return HttpResponseForbidden("Rate limit exceeded")

            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator
