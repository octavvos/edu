from rest_framework import serializers

from apps.accounts.models import Device, OTPPurpose, User, UserSession


class OTPRequestSerializer(serializers.Serializer):
    phone = serializers.RegexField(r"^\+?\d{9,15}$")
    purpose = serializers.ChoiceField(choices=OTPPurpose.choices, default=OTPPurpose.LOGIN)


class OTPVerifySerializer(serializers.Serializer):
    phone = serializers.RegexField(r"^\+?\d{9,15}$")
    code = serializers.RegexField(r"^\d{6}$")
    device_id = serializers.CharField(required=False, allow_blank=True)


class EmailRegisterSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)
    full_name = serializers.CharField(required=False, allow_blank=True, default="")


class PasswordLoginSerializer(serializers.Serializer):
    identifier = serializers.CharField()  # phone yoki email
    password = serializers.CharField(write_only=True)
    device_id = serializers.CharField(required=False, allow_blank=True)
    otp_code = serializers.CharField(required=False, allow_blank=True)  # 2FA TOTP


class TokenResponseSerializer(serializers.Serializer):
    access = serializers.CharField()
    refresh = serializers.CharField()


class RefreshRequestSerializer(serializers.Serializer):
    refresh = serializers.CharField()


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            "id", "phone", "email", "is_phone_verified", "is_email_verified",
            "full_name", "avatar", "birth_date", "gender", "city",
            "language", "timezone", "theme", "status", "created_at",
        )
        read_only_fields = ("id", "phone", "email", "is_phone_verified", "is_email_verified", "status", "created_at")


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
    new_password = serializers.CharField(min_length=8)


class TwoFactorConfirmSerializer(serializers.Serializer):
    token = serializers.RegexField(r"^\d{6}$")
