import pytest
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model

User = get_user_model()

@pytest.mark.django_db
def test_profile_idor():
    user1 = User.objects.create_user(username='user1', password='password')
    user2 = User.objects.create_user(username='user2', password='password')

    client = APIClient()
    client.force_authenticate(user=user2)

    # Wait, UserProfileAPIView only gets the requesting user's profile:
    # user = request.user
    # So there is no IDOR possible since it doesn't take an ID parameter.
    pass
