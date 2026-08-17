from celery import shared_task


@shared_task(bind=True, max_retries=5, default_retry_delay=30)
def poll_video_status(self, video_asset_id: str):
    """5.7/5.8: Bunny webhook kelmasa ham holatni tekshirib turadi ('media' navbati)."""
    from apps.courses.models import VideoAsset, VideoAssetStatus
    from apps.courses.video_services import refresh_video_status

    asset = VideoAsset.objects.filter(id=video_asset_id).first()
    if not asset:
        return
    refresh_video_status(asset)
    if asset.status in (VideoAssetStatus.UPLOADING, VideoAssetStatus.PROCESSING):
        raise self.retry(countdown=30)
