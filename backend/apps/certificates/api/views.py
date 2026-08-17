from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.certificates.services import verify_certificate


class CertificateVerifyView(APIView):
    """GET /verify/{code} — G-05: ochiq verifikatsiya, autentifikatsiya talab qilinmaydi."""

    permission_classes = [AllowAny]

    def get(self, request, code):
        result = verify_certificate(code)
        if not result:
            return Response({"valid": False}, status=status.HTTP_404_NOT_FOUND)
        return Response(result)
