from celery import shared_task
from django.db.models import Sum
from decimal import Decimal
from .models import ShopierPayment
from users.models import WatchLog, Wallet
from content.models import FansubGroup


@shared_task
def calculate_revenue():
    """
    Distributes revenue to Encoders (35%) and Fansub Groups (20%).
    """
    # 1. Get Undistributed Revenue
    payments = ShopierPayment.objects.filter(status="success", is_distributed=False)
    total_revenue = payments.aggregate(Sum("amount"))["amount__sum"] or Decimal(0)

    if total_revenue == 0:
        return "No revenue to distribute."

    encoder_pool = total_revenue * Decimal("0.35")
    fansub_pool = total_revenue * Decimal("0.20")

    # 2. Calculate Weights based on WatchLog
    # We need to attribute watch time to FansubGroups and Encoders.
    # Strategy: Iterate recent WatchLogs (e.g. last 24h, or just use all undistributed logs if we tracked them).
    # For MVP: We distribute based on accumulated watch time for *all* logs that exist (simplified).
    # A better approach would be to track 'processed' logs, but let's stick to a snapshot logic.

    # Aggregate duration per Episode
    # Then map Episode -> FansubGroups/Encoders

    # Dictionary to hold earnings: {user_id: amount}

    # Total "Units" of watch time * availability
    # Unit = Seconds Watched / (Number of Providers for that Episode)
    # If 2 groups subbed an episode, and it was watched for 100s, each gets 50 units.

    total_fansub_units = 0
    total_encoder_units = 0

    fansub_units = {}  # {group_id: units}
    encoder_units = {}  # {user_id: units}

    # Fetch all logs (in production, filter by date)
    # Prefetch video files, but no need to prefetch related group/uploader since we only use IDs
    logs = (
        WatchLog.objects.select_related("episode")
        .prefetch_related("episode__video_files")
        .all()
    )

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

    # 3. Distribute Fansub Pool
    if total_fansub_units > 0:
        # Batch fetch groups to avoid N+1 queries in distribution loop
        groups = FansubGroup.objects.filter(id__in=fansub_units.keys()).select_related(
            "owner"
        )
        group_map = {g.id: g for g in groups}

        # Collect owner user IDs
        owner_ids = set()
        for fg_id in fansub_units:
            group = group_map.get(fg_id)
            if group and group.owner_id:
                owner_ids.add(group.owner_id)

        if owner_ids:
            # Bulk ensure wallets exist
            existing_wallets = Wallet.objects.filter(user_id__in=owner_ids)
            existing_user_ids = set(existing_wallets.values_list("user_id", flat=True))
            missing_user_ids = owner_ids - existing_user_ids

            if missing_user_ids:
                Wallet.objects.bulk_create(
                    [Wallet(user_id=uid) for uid in missing_user_ids]
                )

            # Fetch all wallets for update
            wallets = {
                w.user_id: w for w in Wallet.objects.filter(user_id__in=owner_ids)
            }

            for fg_id, units in fansub_units.items():
                share = (Decimal(units) / Decimal(total_fansub_units)) * fansub_pool
                group = group_map.get(fg_id)
                if group and group.owner_id:
                    wallet = wallets.get(group.owner_id)
                    if wallet:
                        wallet.balance = Decimal(wallet.balance) + share

            Wallet.objects.bulk_update(list(wallets.values()), ["balance"])

    # 4. Distribute Encoder Pool
    if total_encoder_units > 0:
        encoder_ids = set(encoder_units.keys())

        # Bulk ensure wallets exist
        existing_wallets = Wallet.objects.filter(user_id__in=encoder_ids)
        existing_user_ids = set(existing_wallets.values_list("user_id", flat=True))
        missing_user_ids = encoder_ids - existing_user_ids

        if missing_user_ids:
            Wallet.objects.bulk_create(
                [Wallet(user_id=uid) for uid in missing_user_ids]
            )

        # Fetch all wallets for update
        wallets = {w.user_id: w for w in Wallet.objects.filter(user_id__in=encoder_ids)}

        for enc_id, units in encoder_units.items():
            share = (Decimal(units) / Decimal(total_encoder_units)) * encoder_pool
            wallet = wallets.get(enc_id)
            if wallet:
                wallet.balance = Decimal(wallet.balance) + share

        Wallet.objects.bulk_update(list(wallets.values()), ["balance"])

    # 5. Mark payments as distributed
    payments.update(is_distributed=True)

    return f"Distributed {total_revenue}: {encoder_pool} to Encoders, {fansub_pool} to Fansub Groups."
