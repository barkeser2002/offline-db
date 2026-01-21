import pytest
from django.contrib.auth import get_user_model
from content.models import Anime, Review
from users.models import Badge, UserBadge
from users.services import check_badges
from rest_framework.test import APIClient

User = get_user_model()

@pytest.mark.django_db
def test_review_creation():
    user = User.objects.create_user(username='reviewer', password='password')
    anime = Anime.objects.create(title='Test Anime')

    review = Review.objects.create(user=user, anime=anime, rating=9, text='Great show!')

    assert review.user == user
    assert review.anime == anime
    assert review.rating == 9

@pytest.mark.django_db
def test_critic_badge_awarding():
    user = User.objects.create_user(username='critic', password='password')
    anime = Anime.objects.create(title='Badge Anime')

    # Ensure badge exists (seeded by migration)
    badge_slug = 'critic'
    # Manually check if badge exists, as tests might run in transaction isolation where migrations apply
    # but let's verify logic.

    # Create review
    Review.objects.create(user=user, anime=anime, rating=10, text='Masterpiece')

    # Check badges
    check_badges(user)

    assert UserBadge.objects.filter(user=user, badge__slug=badge_slug).exists()

@pytest.mark.django_db
def test_review_api():
    client = APIClient()
    user = User.objects.create_user(username='api_user', password='password')
    client.force_authenticate(user=user)
    anime = Anime.objects.create(title='API Anime')

    data = {
        'anime': anime.id,
        'rating': 8,
        'text': 'Good via API'
    }

    response = client.post('/api/content/reviews/', data)
    assert response.status_code == 201
    assert Review.objects.count() == 1
    assert Review.objects.first().user == user

@pytest.mark.django_db
def test_duplicate_review_prevention_api():
    client = APIClient()
    user = User.objects.create_user(username='spammer', password='password')
    client.force_authenticate(user=user)
    anime = Anime.objects.create(title='Spam Anime')

    Review.objects.create(user=user, anime=anime, rating=1, text='First')

    data = {
        'anime': anime.id,
        'rating': 1,
        'text': 'Second'
    }

    response = client.post('/api/content/reviews/', data)
    assert response.status_code == 400  # Should fail unique constraint
