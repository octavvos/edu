"""TZ 4.10 (P01-P10) — to'lov va monetizatsiya."""

import uuid

from django.conf import settings
from django.db import models

from apps.core.models import BaseModel


class OrderStatus(models.TextChoices):
    """P-10: buyurtma holatlari."""

    CREATED = "created", "Yaratildi"
    PENDING = "pending", "Kutilmoqda"
    PAID = "paid", "To'landi"
    FULFILLED = "fulfilled", "Bajarildi"
    FAILED = "failed", "Muvaffaqiyatsiz"
    EXPIRED = "expired", "Muddati tugagan"
    REFUNDED = "refunded", "Qaytarildi"


class Promo(BaseModel):
    """P-06: promokod."""

    code = models.CharField(max_length=50, unique=True)
    discount_type = models.CharField(max_length=10, choices=[("percent", "Foiz"), ("amount", "Summa")])
    value = models.DecimalField(max_digits=12, decimal_places=2)
    valid_from = models.DateTimeField()
    valid_until = models.DateTimeField()
    usage_limit = models.PositiveIntegerField(null=True, blank=True)
    used_count = models.PositiveIntegerField(default=0)
    course_ids = models.JSONField(default=list, blank=True)  # bo'sh = barcha kurslarga tegishli

    class Meta:
        db_table = "payments_promo"


class Order(BaseModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="orders")
    course = models.ForeignKey("courses.Course", on_delete=models.PROTECT, related_name="orders")
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, default="UZS")
    status = models.CharField(max_length=20, choices=OrderStatus.choices, default=OrderStatus.CREATED)
    # P-02: Idempotency-Key HTTP header'i klient tomonidan istalgan noyob
    # matn sifatida yuborilishi mumkin (UUID bo'lishi shart emas), shuning
    # uchun CharField — UUIDField haqiqiy so'rovlarni rad etib qo'yardi.
    idempotency_key = models.CharField(max_length=128, unique=True, default=uuid.uuid4)
    promo = models.ForeignKey(Promo, on_delete=models.SET_NULL, null=True, blank=True, related_name="orders")
    discount_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    class Meta:
        db_table = "payments_order"
        indexes = [models.Index(fields=["user", "status"])]


class PaymentStatus(models.TextChoices):
    PENDING = "pending", "Kutilmoqda"
    SUCCEEDED = "succeeded", "Muvaffaqiyatli"
    FAILED = "failed", "Muvaffaqiyatsiz"
    CANCELLED = "cancelled", "Bekor qilindi"
    REFUNDED = "refunded", "Qaytarildi"


class Payment(BaseModel):
    """I-01/P01-P04: Payme tranzaksiyasi."""

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="payments")
    provider = models.CharField(max_length=30, default="payme")
    provider_txn_id = models.CharField(max_length=100, blank=True, db_index=True)
    status = models.CharField(max_length=20, choices=PaymentStatus.choices, default=PaymentStatus.PENDING)
    raw_payload = models.JSONField(default=dict, blank=True)  # P-04: webhook xom holda saqlanadi
    performed_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "payments_payment"
        indexes = [models.Index(fields=["provider", "provider_txn_id"])]


class LedgerAccount(models.TextChoices):
    """P-08: double-entry ledger hisob turlari."""

    PLATFORM_CASH = "platform_cash", "Platforma kassasi"
    COURSE_REVENUE = "course_revenue", "Kurs daromadi"
    TEACHER_PAYABLE = "teacher_payable", "O'qituvchiga to'lanadigan"
    PLATFORM_COMMISSION = "platform_commission", "Platforma komissiyasi"
    TEACHER_PAYOUT_CASH = "teacher_payout_cash", "O'qituvchiga to'langan"


class LedgerEntry(BaseModel):
    """
    P-08: barcha pul harakatlari double-entry ko'rinishida. Append-only —
    balans faqat shu jadvaldan hisoblanadi (LedgerEntry yig'indisi), alohida
    balans maydoni saqlanmaydi.
    """

    account = models.CharField(max_length=30, choices=LedgerAccount.choices)
    debit = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    credit = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    ref_type = models.CharField(max_length=50)  # masalan "order", "payout"
    ref_id = models.CharField(max_length=64)
    teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="+",
    )
    memo = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = "payments_ledger_entry"
        indexes = [
            models.Index(fields=["account", "teacher"]),
            models.Index(fields=["ref_type", "ref_id"]),
        ]

    def save(self, *args, **kwargs):
        if self.pk and LedgerEntry.objects.filter(pk=self.pk).exists():
            raise ValueError("LedgerEntry append-only — mavjud yozuvni o'zgartirib bo'lmaydi")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValueError("LedgerEntry append-only — yozuvni o'chirib bo'lmaydi")
