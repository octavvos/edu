"""
I-02: Eskiz.uz SMS gateway wrapper.
Hujjat: https://documenter.getpostman.com/view/663428/RzfmES4z

Token'lar Redis'da keshlanadi (Eskiz token ~30 kun amal qiladi).
"""

import logging

import requests
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)

CACHE_KEY = "eskiz:token"
BASE_URL = "https://notify.eskiz.uz/api"


class EskizClient:
    def __init__(self):
        self.email = getattr(settings, "ESKIZ_EMAIL", "")
        self.password = getattr(settings, "ESKIZ_PASSWORD", "")

    def _get_token(self) -> str:
        token = cache.get(CACHE_KEY)
        if token:
            return token
        resp = requests.post(
            f"{BASE_URL}/auth/login",
            data={"email": self.email, "password": self.password},
            timeout=10,
        )
        resp.raise_for_status()
        token = resp.json()["data"]["token"]
        cache.set(CACHE_KEY, token, timeout=60 * 60 * 24 * 25)
        return token

    def send_sms(self, phone: str, message: str) -> bool:
        try:
            token = self._get_token()
            resp = requests.post(
                f"{BASE_URL}/message/sms/send",
                headers={"Authorization": f"Bearer {token}"},
                data={"mobile_phone": phone.lstrip("+"), "message": message, "from": "4546"},
                timeout=10,
            )
            resp.raise_for_status()
            return True
        except requests.RequestException:
            logger.exception("Eskiz SMS yuborishda xatolik: phone=%s", phone)
            return False
