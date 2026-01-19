import requests
import random
from .models import SiteSettings

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
