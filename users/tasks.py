from celery import shared_task
from django.contrib.auth import get_user_model
import logging
from .services import check_badges, check_chat_badges

logger = logging.getLogger(__name__)
User = get_user_model()

@shared_task(bind=True, max_retries=3)
def calculate_badges_task(self, user_id):
    try:
        user = User.objects.get(id=user_id)
        check_badges(user)
        return f"Badges checked for user {user_id}"
    except User.DoesNotExist:
        return f"User {user_id} not found"
    except Exception as e:
        logger.exception(f"Badge calculation failed for user {user_id}")
        self.retry(exc=e, countdown=60)

@shared_task(bind=True, max_retries=3)
def calculate_chat_badges_task(self, user_id):
    try:
        user = User.objects.get(id=user_id)
        check_chat_badges(user)
        return f"Chat badges checked for user {user_id}"
    except User.DoesNotExist:
        return f"User {user_id} not found"
    except Exception as e:
        logger.exception(f"Chat badge calculation failed for user {user_id}")
        self.retry(exc=e, countdown=60)

@shared_task(bind=True, max_retries=3)
def reevaluate_all_badges_task(self):
    try:
        user_ids = User.objects.values_list('id', flat=True)
        for user_id in user_ids:
            calculate_badges_task.delay(user_id)
            calculate_chat_badges_task.delay(user_id)
        return f"Triggered re-evaluation for {len(user_ids)} users."
    except Exception as e:
        logger.exception("Failed to reevaluate all badges.")
        self.retry(exc=e, countdown=60)
