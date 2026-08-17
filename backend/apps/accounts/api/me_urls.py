from django.urls import path

from apps.accounts.api import views

urlpatterns = [
    path("profile/", views.MeProfileView.as_view(), name="me-profile"),
    path("settings/", views.MeSettingsView.as_view(), name="me-settings"),
    path("devices/", views.MeDevicesView.as_view(), name="me-devices"),
    path("courses/", views.MeCoursesView.as_view(), name="me-courses"),
    path("certificates/", views.MeCertificatesView.as_view(), name="me-certificates"),
    path("payments/", views.MePaymentsView.as_view(), name="me-payments"),
    path("delete-request/", views.MeDeletionRequestView.as_view(), name="me-delete-request"),
]
