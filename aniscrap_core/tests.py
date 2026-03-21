from django.test import TestCase, Client

class SecurityHeadersMiddlewareTest(TestCase):
    def setUp(self):
        self.client = Client()

    def test_security_headers_present(self):
        response = self.client.get('/')
        self.assertIn('Referrer-Policy', response)
        self.assertEqual(response['Referrer-Policy'], 'strict-origin-when-cross-origin')
        self.assertIn('Permissions-Policy', response)
        self.assertEqual(response['Permissions-Policy'], 'camera=(), microphone=()')
