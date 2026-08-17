"""
I-03 / V01-V10, D-11: Bunny Stream wrapper — video transkodlash, HLS, CDN.
Hujjat: https://docs.bunny.net/reference/stream-api-overview

VideoAsset modeli (apps.courses) `provider`, `external_id`, `manifest_url`
maydonlari orqali bu klassdan mustaqil — kelajakda boshqa provayderga
(yoki o'z FFmpeg pipeline'iga, D-11) o'tish shu faylni almashtirish bilan
cheklanadi.
"""

import requests
from django.conf import settings

API_BASE = "https://video.bunnycdn.com/library"


class BunnyStreamClient:
    def __init__(self):
        self.library_id = settings.BUNNY_STREAM_LIBRARY_ID
        self.api_key = settings.BUNNY_STREAM_API_KEY
        self.cdn_hostname = settings.BUNNY_STREAM_CDN_HOSTNAME

    def _headers(self):
        return {"AccessKey": self.api_key, "Content-Type": "application/json"}

    def create_video(self, title: str) -> dict:
        """V-08: chunked upload uchun avval video obyekt yaratiladi."""
        resp = requests.post(
            f"{API_BASE}/{self.library_id}/videos",
            json={"title": title},
            headers=self._headers(),
            timeout=15,
        )
        resp.raise_for_status()
        return resp.json()  # {"guid": "...", ...}

    def get_upload_url(self, video_guid: str) -> str:
        return f"{API_BASE}/{self.library_id}/videos/{video_guid}"

    def get_video_status(self, video_guid: str) -> dict:
        resp = requests.get(
            f"{API_BASE}/{self.library_id}/videos/{video_guid}",
            headers=self._headers(),
            timeout=15,
        )
        resp.raise_for_status()
        return resp.json()

    def get_hls_manifest_url(self, video_guid: str) -> str:
        return f"https://{self.cdn_hostname}/{video_guid}/playlist.m3u8"

    def delete_video(self, video_guid: str) -> bool:
        resp = requests.delete(
            f"{API_BASE}/{self.library_id}/videos/{video_guid}",
            headers=self._headers(),
            timeout=15,
        )
        return resp.ok
