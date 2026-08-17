"""
TZ 4.1 (autentifikatsiya), 4.2 (profil), 5.5 (User modeli).
User — RBAC (apps.rbac) va audit (apps.audit) bilan bog'liq poydevor app.
"""

from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils import timezone

from apps.accounts.managers import UserManager
from apps.core.models import TimeStampedModel, UUIDModel


class UserStatus(models.TextChoices):
    ACTIVE = "active", "Faol"
    BLOCKED = "blocked", "Bloklangan"
    PENDING_DELETION = "pending_deletion", "O'chirish kutilmoqda"  # U-06
    ANONYMIZED = "anonymized", "Anonimlashtirilgan"


class Gender(models.TextChoices):
    MALE = "male", "Erkak"
    FEMALE = "female", "Ayol"


class Theme(models.TextChoices):
    LIGHT = "light", "Light"
    DARK = "dark", "Dark"


class User(AbstractBaseUser, PermissionsMixin, UUIDModel, TimeStampedModel):
    """
    D-01: UUID PK. D-02: organization_id (B2B tayyorgarlik). D-12: utm_source.
    USERNAME_FIELD = "phone" — A-01/A-04: asosiy usul telefon+OTP (1.3-band).
    Email+parol bilan ro'yxatdan o'tish `EmailOrPhoneBackend` orqali qo'llab-quvvatlanadi.
    """

    phone = models.CharField(max_length=20, unique=True, null=True, blank=True)
    email = models.EmailField(unique=True, null=True, blank=True)
    is_phone_verified = models.BooleanField(default=False)
    is_email_verified = models.BooleanField(default=False)

    full_name = models.CharField(max_length=150, blank=True)
    avatar = models.FileField(upload_to="avatars/", null=True, blank=True)
    birth_date = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=10, choices=Gender.choices, blank=True)
    city = models.CharField(max_length=100, blank=True)

    language = models.CharField(max_length=10, default="uz")  # U-02
    timezone = models.CharField(max_length=50, default="Asia/Tashkent")  # U-02
    theme = models.CharField(max_length=10, choices=Theme.choices, default=Theme.LIGHT)  # U-02

    status = models.CharField(max_length=20, choices=UserStatus.choices, default=UserStatus.ACTIVE)
    organization_id = models.UUIDField(null=True, blank=True, db_index=True)  # D-02
    utm_source = models.CharField(max_length=255, blank=True)  # D-12

    # A-06: 2FA (TOTP) — admin/super-admin uchun majburiy; TOTPDevice django_otp orqali
    totp_enabled = models.BooleanField(default=False)

    # A-07: 5 marta noto'g'ri urinishdan keyin 15 daqiqaga bloklash
    failed_login_attempts = models.PositiveIntegerField(default=0)
    locked_until = models.DateTimeField(null=True, blank=True)

    # A-09: bir vaqtda ruxsat etilgan qurilmalar soni
    max_active_devices = models.PositiveSmallIntegerField(null=True, blank=True)

    # U-06: akkauntni o'chirish so'rovi — 30 kun grace davri -> anonimizatsiya
    deletion_requested_at = models.DateTimeField(null=True, blank=True)
    anonymized_at = models.DateTimeField(null=True, blank=True)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = "phone"
    REQUIRED_FIELDS: list[str] = []

    class Meta:
        db_table = "accounts_user"
        indexes = [
            models.Index(fields=["email"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self):
        return self.full_name or self.phone or self.email or str(self.id)

    @property
    def is_locked(self) -> bool:
        return bool(self.locked_until and self.locked_until > timezone.now())

    def has_perm_scoped(self, codename: str, scope_type: str = "global", scope_id=None) -> bool:
        """RBAC granular tekshiruv (R-05) — apps.rbac.selectors ga delegatsiya."""
        from apps.rbac.selectors import user_has_permission

        return user_has_permission(self, codename, scope_type=scope_type, scope_id=scope_id)

    def requires_2fa(self) -> bool:
        return self.is_staff or self.is_superuser


class OTPPurpose(models.TextChoices):
    REGISTER = "register", "Ro'yxatdan o'tish"
    LOGIN = "login", "Kirish"
    PASSWORD_RESET = "password_reset", "Parolni tiklash"


class OTPCode(UUIDModel, TimeStampedModel):
    """A-04: 6 raqam, TTL 120 sekund, 3 ta urinish, 1 raqamga soatiga max 3 ta SMS."""

    phone = models.CharField(max_length=20, db_index=True)
    code_hash = models.CharField(max_length=128)
    purpose = models.CharField(max_length=20, choices=OTPPurpose.choices)
    attempts = models.PositiveSmallIntegerField(default=0)
    max_attempts = models.PositiveSmallIntegerField(default=3)
    expires_at = models.DateTimeField()
    used_at = models.DateTimeField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        db_table = "accounts_otp_code"
        indexes = [models.Index(fields=["phone", "purpose", "created_at"])]

    @property
    def is_expired(self) -> bool:
        return timezone.now() > self.expires_at

    @property
    def is_valid(self) -> bool:
        return not self.used_at and not self.is_expired and self.attempts < self.max_attempts


class Device(UUIDModel, TimeStampedModel):
    """A-09: bir vaqtda ruxsat etilgan qurilmalar soni cheklanadi."""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="devices")
    device_id = models.CharField(max_length=255)  # klient tomonidan generatsiya qilinadi
    name = models.CharField(max_length=255, blank=True)  # masalan "Chrome on Windows"
    push_token = models.CharField(max_length=255, blank=True)  # FCM
    is_active = models.BooleanField(default=True)
    last_seen_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "accounts_device"
        constraints = [
            models.UniqueConstraint(fields=["user", "device_id"], name="uniq_user_device"),
        ]


class UserSession(UUIDModel, TimeStampedModel):
    """A-08: faol sessiyalar ro'yxati va ularni masofadan uzish."""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="sessions")
    device = models.ForeignKey(Device, on_delete=models.SET_NULL, null=True, blank=True, related_name="sessions")
    refresh_jti = models.CharField(max_length=64, unique=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=255, blank=True)
    revoked_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "accounts_user_session"

    @property
    def is_active(self) -> bool:
        return self.revoked_at is None


class LoginAttempt(UUIDModel):
    """A-10: barcha kirish urinishlari IP va User-Agent bilan logga yoziladi."""

    created_at = models.DateTimeField(default=timezone.now, db_index=True)
    identifier = models.CharField(max_length=255)  # phone yoki email
    success = models.BooleanField()
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=255, blank=True)
    reason = models.CharField(max_length=100, blank=True)  # "bad_password", "locked", ...

    class Meta:
        db_table = "accounts_login_attempt"
        indexes = [models.Index(fields=["identifier", "created_at"])]
