from django.urls import path

from apps.certificates.api.views import CertificateVerifyView

urlpatterns = [
    path("<str:code>/", CertificateVerifyView.as_view(), name="certificate-verify"),
]
