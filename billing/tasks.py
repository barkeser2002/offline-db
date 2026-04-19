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
    # Prefetch video files, but no need to prefetch related group/uploader since we only use IDs
    logs = WatchLog.objects.select_related('episode').prefetch_related(
        'episode__video_files'
    ).all()

    for log in logs:
        episode = log.episode
        duration = log.duration

        # Find providers
        videos = episode.video_files.all()
        count = len(videos)

        if count > 0:
            unit_share = duration / count
            for video in videos:
                # Fansub Group Logic
                if video.fansub_group_id:
                    fg_id = video.fansub_group_id
                    fansub_units[fg_id] = fansub_units.get(fg_id, 0) + unit_share
                    total_fansub_units += unit_share

                # Encoder Logic
                if video.uploader_id:
                    enc_id = video.uploader_id
                    encoder_units[enc_id] = encoder_units.get(enc_id, 0) + unit_share
                    total_encoder_units += unit_share

    # 3. Consolidate and Distribute Pools
    user_shares = {} # {user_id: Decimal(share)}

    # Calculate Fansub Shares
    if total_fansub_units > 0:
        groups = FansubGroup.objects.filter(id__in=fansub_units.keys()).select_related('owner')
        group_map = {g.id: g for g in groups}
        for fg_id, units in fansub_units.items():
            group = group_map.get(fg_id)
            if group and group.owner_id:
                share = (Decimal(units) / Decimal(total_fansub_units)) * fansub_pool
                user_shares[group.owner_id] = user_shares.get(group.owner_id, Decimal(0)) + share

    # Calculate Encoder Shares
    if total_encoder_units > 0:
        for enc_id, units in encoder_units.items():
            share = (Decimal(units) / Decimal(total_encoder_units)) * encoder_pool
            user_shares[enc_id] = user_shares.get(enc_id, Decimal(0)) + share

    # 4. Bulk Update Wallets
    if user_shares:
        # Get existing wallets
        wallets = Wallet.objects.filter(user_id__in=user_shares.keys())
        wallet_map = {w.user_id: w for w in wallets}

        # Create missing wallets
        missing_user_ids = set(user_shares.keys()) - set(wallet_map.keys())
        if missing_user_ids:
            new_wallets = [Wallet(user_id=uid) for uid in missing_user_ids]
            Wallet.objects.bulk_create(new_wallets, ignore_conflicts=True)
            # Re-fetch wallets to get the full list with new ones
            wallets = Wallet.objects.filter(user_id__in=user_shares.keys())
            wallet_map = {w.user_id: w for w in wallets}

        # Update balances in memory
        for user_id, share in user_shares.items():
            wallet = wallet_map.get(user_id)
            if wallet:
                wallet.balance = Decimal(wallet.balance) + share

        # Bulk update
        Wallet.objects.bulk_update(wallets, ['balance'])

    # 5. Mark payments as distributed
    payments.update(is_distributed=True)

    return f"Distributed {total_revenue}: {encoder_pool} to Encoders, {fansub_pool} to Fansub Groups."
