class SecurityHeadersMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # Referrer-Policy: strict-origin-when-cross-origin
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'

        # Permissions-Policy (camera, microphone deny)
        response['Permissions-Policy'] = 'camera=(), microphone=()'

        return response
