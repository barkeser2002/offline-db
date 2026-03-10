import pytest
from django.test import Client
from django.urls import reverse

@pytest.mark.django_db
def test_my_rooms_unauthenticated():
    client = Client()
    # The action URL is typically named `basename-action-name`
    # Default router basename for RoomViewSet is `room`
    url = reverse('room-my-rooms')
    # Use follow=True or explicitly request the trailing slash URL
    response = client.get(url, follow=True)
    assert response.status_code == 401, f"Expected 401, got {response.status_code}"
