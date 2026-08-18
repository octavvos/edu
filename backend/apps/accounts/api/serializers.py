from rest_framework import serializers

from apps.accounts.models import Device, OTPPurpose, User, UserSession
from apps.accounts.validators import PASSWORD_MIN_LENGTH, USERNAME_MIN_LENGTH


class OTPRequestSerializer(serializers.Serializer):
    phone = serializers.RegexField(r"^\+?\d{9,15}$")
    purpose = serializers.ChoiceField(choices=OTPPurpose.choices, default=OTPPurpose.LOGIN)


class OTPVerifySerializer(serializers.Serializer):
    phone = serializers.RegexField(r"^\+?\d{9,15}$")
    code = serializers.RegexField(r"^\d{6}$")
    device_id = serializers.CharField(required=False, allow_blank=True)


class StudentRegisterSerializer(serializers.Serializer):
    """O'quvchi ro'yxatdan o'tishi: ism, familiya, username, parol + guruh."""

    first_name = serializers.CharField(max_length=75)
    last_name = serializers.CharField(max_length=75)
    username = serializers.CharField(min_length=USERNAME_MIN_LENGTH, max_length=150)
    password = serializers.CharField(write_only=True, min_length=PASSWORD_MIN_LENGTH)
    group_id = serializers.UUIDField()


class PasswordLoginSerializer(serializers.Serializer):
    identifier = serializers.CharField()  # username (yoki eski hisoblar uchun telefon/email)
    password = serializers.CharField(write_only=True)
    device_id = serializers.CharField(required=False, allow_blank=True)
    otp_code = serializers.CharField(required=False, allow_blank=True)  # 2FA TOTP


class TokenResponseSerializer(serializers.Serializer):
    access = serializers.CharField()
    refresh = serializers.CharField()


class RefreshRequestSerializer(serializers.Serializer):
    refresh = serializers.CharField()


class UserProfileSerializer(serializers.ModelSerializer):
    """
    Frontend shu javobga qarab qaysi panelni ochishni hal qiladi:
    `roles` ichida manager / mentor / student bo'ladi, `status` esa
    o'quvchi hali mentor tasdig'ini kutayotganini bildiradi.
    """

    display_name = serializers.CharField(read_only=True)
    roles = serializers.SerializerMethodField()
    is_pending_approval = serializers.BooleanField(read_only=True)

    class Meta:
        model = User
        fields = (
            "id", "username", "first_name", "last_name", "display_name",
            "phone", "email", "avatar", "birth_date", "gender", "city",
            "language", "timezone", "theme", "status", "is_pending_approval",
            "roles", "created_at",
        )
        read_only_fields = ("id", "username", "phone", "email", "status", "created_at")

    def get_roles(self, obj) -> list[str]:
        from apps.rbac.selectors import get_user_role_codenames

        roles = get_user_role_codenames(obj)
        if obj.is_superuser and "manager" not in roles:
            roles = [*roles, "manager"]
        return roles


class UserSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("language", "timezone", "theme")


class DeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Device
        fields = ("id", "device_id", "name", "is_active", "last_seen_at")


class UserSessionSerializer(serializers.ModelSerializer):
    device = DeviceSerializer(read_only=True)

    class Meta:
        model = UserSession
        fields = ("id", "device", "ip_address", "user_agent", "created_at", "revoked_at")


class PasswordResetRequestSerializer(serializers.Serializer):
    identifier = serializers.CharField()


class PasswordResetConfirmSerializer(serializers.Serializer):
    token = serializers.CharField()
    new_password = serializers.CharField(min_length=PASSWORD_MIN_LENGTH)


class TwoFactorConfirmSerializer(serializers.Serializer):
    token = serializers.RegexField(r"^\d{6}$")
