from django.utils.deprecation import MiddlewareMixin

class SecurityHeadersMiddleware(MiddlewareMixin):
    def process_response(self, request, response):
        # Adding Permissions-Policy header
        response['Permissions-Policy'] = "camera=(), microphone=(), geolocation=()"

        # Let Django SecurityMiddleware handle HSTS if SECURE_HSTS_SECONDS is set
        return response
