from django.urls import path

from apps.accounts.api import views

urlpatterns = [
    path("register/", views.RegisterStudentView.as_view(), name="auth-register"),
    path("login/", views.LoginView.as_view(), name="auth-login"),
    path("otp/send/", views.OTPSendView.as_view(), name="auth-otp-send"),
    path("otp/verify/", views.OTPVerifyView.as_view(), name="auth-otp-verify"),
    path("refresh/", views.RefreshView.as_view(), name="auth-refresh"),
    path("logout/", views.LogoutView.as_view(), name="auth-logout"),
    path("2fa/setup/", views.TwoFactorSetupView.as_view(), name="auth-2fa-setup"),
    path("2fa/confirm/", views.TwoFactorConfirmView.as_view(), name="auth-2fa-confirm"),
    path("sessions/", views.SessionListView.as_view(), name="auth-sessions"),
    path("sessions/<uuid:session_id>/", views.SessionRevokeView.as_view(), name="auth-session-revoke"),
    path("password/reset/", views.PasswordResetRequestView.as_view(), name="auth-password-reset"),
    path("password/reset/confirm/", views.PasswordResetConfirmView.as_view(), name="auth-password-reset-confirm"),
]
