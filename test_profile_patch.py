import pytest
from django.urls import reverse
from rest_framework.test import APIClient

@pytest.mark.django_db
def test_profile_patch_bio_and_username(django_user_model):
    client = APIClient()
    user = django_user_model.objects.create_user(username='testuser', password='password', bio='old bio')
    client.force_authenticate(user=user)
    url = reverse('user-profile')

    data = {
        'bio': '<script>alert("xss")</script><b>new bio</b>',
        'username': 'new_user_name'
    }

    response = client.patch(url, data, format='json')
    assert response.status_code == 200

    user.refresh_from_db()
    assert user.bio == 'new bio'
    assert user.username == 'new_user_name'

@pytest.mark.django_db
def test_profile_patch_invalid_username(django_user_model):
    client = APIClient()
    user = django_user_model.objects.create_user(username='testuser', password='password')
    client.force_authenticate(user=user)
    url = reverse('user-profile')

    data = {
        'username': 'invalid username!'
    }

    response = client.patch(url, data, format='json')
    assert response.status_code == 400
    assert 'error' in response.json()
    assert 'alphanumeric' in response.json()['error']

    user.refresh_from_db()
    assert user.username == 'testuser'

@pytest.mark.django_db
def test_profile_patch_duplicate_username(django_user_model):
    client = APIClient()
    django_user_model.objects.create_user(username='existinguser', password='password')
    user = django_user_model.objects.create_user(username='testuser', password='password')
    client.force_authenticate(user=user)
    url = reverse('user-profile')

    data = {
        'username': 'existinguser'
    }

    response = client.patch(url, data, format='json')
    assert response.status_code == 400
    assert 'error' in response.json()
    assert 'already taken' in response.json()['error']

    user.refresh_from_db()
    assert user.username == 'testuser'
