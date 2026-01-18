from curl_cffi import requests

class CFBypassError(Exception):
    pass

class CFSession:
    def __init__(self, impersonate="chrome110", timeout=15, max_retries=3):
        self.impersonate = impersonate
        self.timeout = timeout
        self.max_retries = max_retries
        self.session = requests.Session()

    def get(self, url, headers=None, **kwargs):
        try:
            response = self.session.get(
                url,
                headers=headers,
                impersonate=self.impersonate,
                timeout=self.timeout,
                **kwargs
            )
            return response
        except Exception as e:
            raise CFBypassError(f"Request failed: {e}")

    def post(self, url, data=None, json=None, headers=None, **kwargs):
        try:
            response = self.session.post(
                url,
                data=data,
                json=json,
                headers=headers,
                impersonate=self.impersonate,
                timeout=self.timeout,
                **kwargs
            )
            return response
        except Exception as e:
            raise CFBypassError(f"Request failed: {e}")
