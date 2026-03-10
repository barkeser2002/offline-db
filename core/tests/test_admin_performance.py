from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from core.models import SupportTicket

User = get_user_model()

class SupportTicketAdminPerformanceTest(TestCase):
    def setUp(self):
        self.admin_user = User.objects.create_superuser('admin', 'admin@example.com', 'password')
        self.client = Client()
        self.client.force_login(self.admin_user)

        # Create 10 SupportTickets with 10 different users
        for i in range(10):
            user = User.objects.create_user(username=f'user{i}', password='password')
            SupportTicket.objects.create(user=user, subject=f'Subject {i}', message=f'Message {i}')

    def test_supportticket_admin_changelist_performance(self):
        url = reverse('admin:core_supportticket_changelist')

        # Initial request to warm up
        self.client.get(url)

        # Expected queries:
        # 1. Session check
        # 2. User auth
        # 3. COUNT(*)
        # 4. Main query for SupportTicket + select_related('user')
        # Without optimization, this would be ~14 queries.
        with self.assertNumQueries(5):
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)
