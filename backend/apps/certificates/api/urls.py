from django.urls import path

from apps.certificates.api.views import CertificateVerifyView

urlpatterns = [
    # /api/v1/certificates/{code}/verify/ — verify_urls.py da /verify/{code}/ ochiq marshruti bilan bir xil logika
    path("<str:code>/verify/", CertificateVerifyView.as_view(), name="certificate-api-verify"),
]
