"""
Barcha app'lar shu yerdagi abstrakt modellardan meros oladi.
TZ 5.5.1 (D01, D02, D04, D10) — kelajakka tayyorlik bo'yicha majburiy qarorlar:

    D-01  UUID primary key barcha asosiy modellarda
    D-02  organization_id (nullable) — B2B qo'shilganda migratsiyasiz ishlaydi
    D-04  JSONB i18n maydonlar (CharField emas)
    D-10  Barcha vaqtlar UTC'da (settings.USE_TZ = True + TIME_ZONE = "UTC")
"""

import uuid

from django.conf import settings
from django.db import models


class UUIDModel(models.Model):
    """D-01: butun tizim UUID PK bilan quriladi — int->UUID migratsiyasidan qochish uchun."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class Meta:
        abstract = True


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class OrgScopedModel(models.Model):
    """
    D-02: hozircha MVP B2C2B (marketplace) — organization har doim null.
    B2B (v2.0) qo'shilganda bu maydon orqali tashkilotga tegishli
    yozuvlarni ajratish mumkin bo'ladi, migratsiya kerak bo'lmaydi.
    """

    organization_id = models.UUIDField(null=True, blank=True, db_index=True)

    class Meta:
        abstract = True


class BaseModel(UUIDModel, TimeStampedModel):
    """Ko'pchilik domain modellari shu klassdan meros oladi."""

    class Meta:
        abstract = True


class OrgScopedBaseModel(BaseModel, OrgScopedModel):
    class Meta:
        abstract = True


def i18n_field(**kwargs):
    """
    D-04: JSONB i18n maydon — {"uz": "...", "uz_cyrl": "...", "ru": "...", "en": "..."}
    shaklida saqlanadi. settings.CONTENT_LANGUAGES bilan mos.
    """
    kwargs.setdefault("default", dict)
    kwargs.setdefault("blank", True)
    return models.JSONField(**kwargs)


def resolve_i18n(value, lang: str) -> str:
    """i18n lug'atidan berilgan til uchun qiymatni oladi, bo'lmasa uz'ga fallback."""
    if not isinstance(value, dict):
        return value or ""
    return value.get(lang) or value.get(settings.LANGUAGE_CODE) or next(iter(value.values()), "")


def get_i18n_value(obj, field_name: str, lang: str) -> str:
    """Obyektning i18n JSONB maydonini tilga qarab ochadi."""
    return resolve_i18n(getattr(obj, field_name, None), lang)


class StatusChoices(models.TextChoices):
    """Umumiy holat (draft/pending/published) — Course, kabi modellarda ishlatiladi."""

    DRAFT = "draft", "Qoralama"
    PENDING_MODERATION = "pending_moderation", "Moderatsiyada"
    PUBLISHED = "published", "Nashr etilgan"
    REJECTED = "rejected", "Rad etilgan"
    ARCHIVED = "archived", "Arxivlangan"
