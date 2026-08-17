"""V01-V09: video yuklash va transkodlash oqimi (TZ 5.7 sequence diagram)."""

from apps.courses.models import VideoAsset, VideoAssetStatus


def init_video_upload(*, filename: str) -> tuple[VideoAsset, str]:
    """POST /media/upload-init — Bunny'da video obyekt yaratadi, upload URL qaytaradi (V-08 chunked)."""
    from libs.bunny.client import BunnyStreamClient

    client = BunnyStreamClient()
    remote = client.create_video(title=filename)
    asset = VideoAsset.objects.create(
        provider="bunny", external_id=remote["guid"],
        original_filename=filename, status=VideoAssetStatus.UPLOADING,
    )
    upload_url = client.get_upload_url(remote["guid"])
    return asset, upload_url


def refresh_video_status(asset: VideoAsset) -> VideoAsset:
    """Celery 'media' navbatida — V-09: yuklash/transkodlash holati real vaqtda ko'rsatiladi."""
    from libs.bunny.client import BunnyStreamClient

    client = BunnyStreamClient()
    remote = client.get_video_status(asset.external_id)
    # Bunny status kodlari: 0=Created,1=Uploaded,2=Processing,3=Transcoding,4=Finished,5=Error
    status_map = {
        0: VideoAssetStatus.UPLOADING, 1: VideoAssetStatus.UPLOADING,
        2: VideoAssetStatus.PROCESSING, 3: VideoAssetStatus.PROCESSING,
        4: VideoAssetStatus.READY, 5: VideoAssetStatus.FAILED,
    }
    asset.status = status_map.get(remote.get("status"), asset.status)
    asset.duration_seconds = remote.get("length", asset.duration_seconds)
    if asset.status == VideoAssetStatus.READY:
        asset.manifest_url = client.get_hls_manifest_url(asset.external_id)
    asset.save(update_fields=["status", "duration_seconds", "manifest_url"])

    if asset.status == VideoAssetStatus.READY:
        _notify_owner_video_ready(asset)
    return asset


def _notify_owner_video_ready(asset: VideoAsset) -> None:
    lesson = getattr(asset, "lesson", None)
    if not lesson:
        return
    course = lesson.module.course
    from apps.notifications.models import NotificationEvent
    from apps.notifications.tasks import dispatch_notification

    dispatch_notification.delay(
        user_id=str(course.author_id), event=NotificationEvent.VIDEO_READY,
        context={"lesson_id": str(lesson.id)},
    )
