"""I-02: Eskiz.uz — OTP va kritik SMS xabarlar uchun asosiy provayder."""

import logging
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class BaseSmsBackend(ABC):
    @abstractmethod
    def send(self, phone: str, message: str) -> bool: ...


class ConsoleSmsBackend(BaseSmsBackend):
    """Lokal ishlab chiqish uchun — SMS console'ga chiqariladi."""

    def send(self, phone: str, message: str) -> bool:
        logger.info("[SMS -> %s] %s", phone, message)
        print(f"[SMS -> {phone}] {message}")  # noqa: T201 — dev-only ko'rinish uchun
        return True


class EskizSmsBackend(BaseSmsBackend):
    """https://eskiz.uz API wrapper — libs/eskiz orqali."""

    def send(self, phone: str, message: str) -> bool:
        from libs.eskiz.client import EskizClient

        return EskizClient().send_sms(phone=phone, message=message)


def get_sms_backend() -> BaseSmsBackend:
    from django.conf import settings
    from django.utils.module_loading import import_string

    backend_path = getattr(settings, "SMS_BACKEND", "apps.notifications.backends.sms.ConsoleSmsBackend")
    return import_string(backend_path)()
