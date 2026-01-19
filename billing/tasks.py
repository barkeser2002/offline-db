from celery import shared_task
from django.db.models import Sum
from decimal import Decimal
from .models import ShopierPayment
from users.models import WatchLog, Wallet
from content.models import VideoFile, FansubGroup

@shared_task
def calculate_revenue():
    """
    Distributes revenue to Encoders (35%) and Fansub Groups (20%).
    """
    # 1. Get Undistributed Revenue
    payments = ShopierPayment.objects.filter(status='success', is_distributed=False)
    total_revenue = payments.aggregate(Sum('amount'))['amount__sum'] or Decimal(0)

    if total_revenue == 0:
        return "No revenue to distribute."

    encoder_pool = total_revenue * Decimal('0.35')
    fansub_pool = total_revenue * Decimal('0.20')

    # 2. Calculate Weights based on WatchLog
    # We need to attribute watch time to FansubGroups and Encoders.
    # Strategy: Iterate recent WatchLogs (e.g. last 24h, or just use all undistributed logs if we tracked them).
    # For MVP: We distribute based on accumulated watch time for *all* logs that exist (simplified).
    # A better approach would be to track 'processed' logs, but let's stick to a snapshot logic.

    # Aggregate duration per Episode
    # Then map Episode -> FansubGroups/Encoders

    # Dictionary to hold earnings: {user_id: amount}
    encoder_earnings = {}
    fansub_earnings = {}

    # Total "Units" of watch time * availability
    # Unit = Seconds Watched / (Number of Providers for that Episode)
    # If 2 groups subbed an episode, and it was watched for 100s, each gets 50 units.

    total_fansub_units = 0
    total_encoder_units = 0

    fansub_units = {} # {group_id: units}
    encoder_units = {} # {user_id: units}

    # Fetch all logs (in production, filter by date)
    logs = WatchLog.objects.select_related('episode').all()

    for log in logs:
        episode = log.episode
        duration = log.duration

        # Find providers
        videos = VideoFile.objects.filter(episode=episode)
        count = videos.count()

        if count > 0:
            unit_share = duration / count
            for video in videos:
                # Fansub Group Logic
                if video.fansub_group:
                    fg_id = video.fansub_group.id
                    fansub_units[fg_id] = fansub_units.get(fg_id, 0) + unit_share
                    total_fansub_units += unit_share

                # Encoder Logic
                if video.uploader:
                    enc_id = video.uploader.id
                    encoder_units[enc_id] = encoder_units.get(enc_id, 0) + unit_share
                    total_encoder_units += unit_share

    # 3. Distribute Fansub Pool
    if total_fansub_units > 0:
        for fg_id, units in fansub_units.items():
            share = (Decimal(units) / Decimal(total_fansub_units)) * fansub_pool
            try:
                group = FansubGroup.objects.get(id=fg_id)
                if group.owner:
                    wallet, _ = Wallet.objects.get_or_create(user=group.owner)
                    wallet.balance += share
                    wallet.save()
            except FansubGroup.DoesNotExist:
                pass

    # 4. Distribute Encoder Pool
    if total_encoder_units > 0:
        for enc_id, units in encoder_units.items():
            share = (Decimal(units) / Decimal(total_encoder_units)) * encoder_pool
            wallet, _ = Wallet.objects.get_or_create(user_id=enc_id)
            wallet.balance += share
            wallet.save()

    # 5. Mark payments as distributed
    payments.update(is_distributed=True)

    return f"Distributed {total_revenue}: {encoder_pool} to Encoders, {fansub_pool} to Fansub Groups."
