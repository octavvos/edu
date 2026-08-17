from rest_framework import generics, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts import services
from apps.accounts.api.serializers import (
    DeviceSerializer,
    EmailRegisterSerializer,
    OTPRequestSerializer,
    OTPVerifySerializer,
    PasswordLoginSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    RefreshRequestSerializer,
    TokenResponseSerializer,
    TwoFactorConfirmSerializer,
    UserProfileSerializer,
    UserSessionSerializer,
    UserSettingsSerializer,
)
from apps.accounts.models import OTPPurpose
from apps.accounts.selectors import get_active_sessions
from apps.accounts.throttles import OTPRequestThrottle
from apps.core.exceptions import DomainError
from apps.core.utils import get_client_ip


class RegisterEmailView(generics.CreateAPIView):
    """POST /api/v1/auth/register — email + parol (1.3-band ikkinchi usul)."""

    permission_classes = [AllowAny]
    serializer_class = EmailRegisterSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            user = services.register_with_email(**serializer.validated_data)
        except DomainError as exc:
            return Response({"detail": exc.detail}, status=exc.status_code)
        return Response(UserProfileSerializer(user).data, status=status.HTTP_201_CREATED)


class OTPSendView(APIView):
    """POST /api/v1/auth/otp/send"""

    permission_classes = [AllowAny]
    throttle_classes = [OTPRequestThrottle]

    def post(self, request):
        serializer = OTPRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            services.request_otp(
                phone=serializer.validated_data["phone"],
                purpose=serializer.validated_data["purpose"],
                ip_address=get_client_ip(request),
            )
        except DomainError as exc:
            return Response({"detail": exc.detail}, status=exc.status_code)
        return Response({"detail": "OTP yuborildi"}, status=status.HTTP_200_OK)


class OTPVerifyView(APIView):
    """POST /api/v1/auth/otp/verify — telefon orqali kirish/ro'yxatdan o'tish (bitta oqim)."""

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = OTPVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            _user, tokens = services.register_or_login_with_phone(
                phone=serializer.validated_data["phone"],
                code=serializer.validated_data["code"],
                device_id=serializer.validated_data.get("device_id"),
                ip_address=get_client_ip(request),
                user_agent=request.META.get("HTTP_USER_AGENT", ""),
            )
        except DomainError as exc:
            return Response({"detail": exc.detail}, status=exc.status_code)
        return Response(TokenResponseSerializer(tokens).data)


class LoginView(APIView):
    """POST /api/v1/auth/login — email/telefon + parol."""

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PasswordLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            _user, tokens = services.login_with_password(
                identifier=serializer.validated_data["identifier"],
                password=serializer.validated_data["password"],
                device_id=serializer.validated_data.get("device_id"),
                otp_code=serializer.validated_data.get("otp_code"),
                ip_address=get_client_ip(request),
                user_agent=request.META.get("HTTP_USER_AGENT", ""),
            )
        except DomainError as exc:
            return Response({"detail": exc.detail}, status=exc.status_code)
        return Response(TokenResponseSerializer(tokens).data)


class RefreshView(APIView):
    """
    POST /api/v1/auth/refresh — A-02/A-03: rotation bilan.
    simplejwt ROTATE_REFRESH_TOKENS + BLACKLIST_AFTER_ROTATION allaqachon
    qayta ishlatilgan tokenni rad etadi; bu yerda UserSession yozuvi ham
    yangi jti bilan yangilanadi.
    """

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RefreshRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            old_token = RefreshToken(serializer.validated_data["refresh"])
        except TokenError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_401_UNAUTHORIZED)

        old_jti = old_token["jti"]
        new_token = RefreshToken(str(old_token))
        new_token.set_jti()
        new_token.set_exp()
        new_token.set_iat()
        old_token.blacklist()

        from apps.accounts.models import UserSession

        UserSession.objects.filter(refresh_jti=old_jti).update(refresh_jti=str(new_token["jti"]))

        return Response({"access": str(new_token.access_token), "refresh": str(new_token)})


class LogoutView(APIView):
    def post(self, request):
        serializer = RefreshRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            token = RefreshToken(serializer.validated_data["refresh"])
        except TokenError:
            return Response(status=status.HTTP_204_NO_CONTENT)
        services.logout(user=request.user, refresh_jti=str(token["jti"]))
        token.blacklist()
        return Response(status=status.HTTP_204_NO_CONTENT)


class SessionListView(generics.ListAPIView):
    """GET /api/v1/auth/sessions — A-08."""

    serializer_class = UserSessionSerializer

    def get_queryset(self):
        return get_active_sessions(self.request.user)


class SessionRevokeView(APIView):
    """DELETE /api/v1/auth/sessions/{id} — A-08: masofadan uzish."""

    def delete(self, request, session_id):
        from apps.accounts.models import UserSession

        session = UserSession.objects.filter(id=session_id, user=request.user).first()
        if not session:
            return Response(status=status.HTTP_404_NOT_FOUND)
        services.revoke_session(session=session)
        return Response(status=status.HTTP_204_NO_CONTENT)


class TwoFactorSetupView(APIView):
    """POST /api/v1/auth/2fa/setup — A-06: TOTP provisioning URI qaytaradi."""

    def post(self, request):
        from django_otp.plugins.otp_totp.models import TOTPDevice

        device, _ = TOTPDevice.objects.get_or_create(
            user=request.user, confirmed=False, defaults={"name": "default"},
        )
        return Response({"provisioning_uri": device.config_url})


class TwoFactorConfirmView(APIView):
    """POST /api/v1/auth/2fa/confirm"""

    def post(self, request):
        from django_otp.plugins.otp_totp.models import TOTPDevice

        serializer = TwoFactorConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        device = TOTPDevice.objects.filter(user=request.user, confirmed=False).first()
        if not device or not device.verify_token(serializer.validated_data["token"]):
            return Response({"detail": "Kod noto'g'ri"}, status=status.HTTP_400_BAD_REQUEST)
        device.confirmed = True
        device.save(update_fields=["confirmed"])
        request.user.totp_enabled = True
        request.user.save(update_fields=["totp_enabled"])
        return Response({"detail": "2FA yoqildi"})


class PasswordResetRequestView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        from apps.accounts.selectors import find_user_by_identifier

        user = find_user_by_identifier(serializer.validated_data["identifier"])
        if user:
            from apps.notifications.tasks import send_password_reset_link

            send_password_reset_link.delay(user_id=str(user.id))
        # Foydalanuvchi mavjudligini oshkor qilmaslik uchun har doim 200 qaytaramiz
        return Response({"detail": "Agar hisob mavjud bo'lsa, havola yuborildi"})


class PasswordResetConfirmView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        # Token tekshiruvi apps.notifications tokenizer'i orqali amalga oshiriladi
        from apps.accounts.services import AuthError
        from apps.notifications.tokens import verify_password_reset_token

        try:
            user = verify_password_reset_token(serializer.validated_data["token"])
        except AuthError as exc:
            return Response({"detail": exc.detail}, status=exc.status_code)
        user.set_password(serializer.validated_data["new_password"])
        user.save(update_fields=["password"])
        return Response({"detail": "Parol yangilandi"})


# ---------------------------------------------------------------------------
# /api/v1/me/*
# ---------------------------------------------------------------------------

class MeProfileView(generics.RetrieveUpdateAPIView):
    """U-01: shaxsiy ma'lumotlar."""

    serializer_class = UserProfileSerializer

    def get_object(self):
        return self.request.user


class MeSettingsView(generics.RetrieveUpdateAPIView):
    """U-02: sozlamalar."""

    serializer_class = UserSettingsSerializer

    def get_object(self):
        return self.request.user


class MeDevicesView(generics.ListAPIView):
    serializer_class = DeviceSerializer

    def get_queryset(self):
        return self.request.user.devices.filter(is_active=True)


class MeCoursesView(APIView):
    """U-03: davom etayotgan / tugatilgan / saqlangan kurslar — enrollment app'ga delegatsiya."""

    def get(self, request):
        from apps.enrollment.selectors import get_my_courses_grouped

        return Response(get_my_courses_grouped(request.user))


class MeCertificatesView(APIView):
    """U-04: sertifikatlar arxivi."""

    def get(self, request):
        from apps.certificates.selectors import get_user_certificates

        return Response(get_user_certificates(request.user))


class MePaymentsView(APIView):
    """U-05: to'lovlar tarixi."""

    def get(self, request):
        from apps.payments.selectors import get_user_orders

        return Response(get_user_orders(request.user))


class MeDeletionRequestView(APIView):
    """U-06: akkauntni o'chirish so'rovi."""

    def post(self, request):
        services.request_account_deletion(user=request.user)
        return Response({"detail": "So'rov qabul qilindi. 30 kundan so'ng hisob anonimlashtiriladi."})
