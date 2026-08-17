"""TZ 4.8 (G04-G06) — sertifikat generatsiyasi va ochiq verifikatsiya."""

import secrets

from django.conf import settings
from django.db import models

from apps.core.models import BaseModel, i18n_field


def _generate_code() -> str:
    return secrets.token_hex(8).upper()  # 16 xonali unikal kod


class CertificateTemplate(BaseModel):
    """G-06: shablon admin paneldan sozlanadi (logo, imzo, matn, fon)."""

    name = models.CharField(max_length=100)
    logo = models.FileField(upload_to="certificate_templates/", null=True, blank=True)
    signature_image = models.FileField(upload_to="certificate_templates/", null=True, blank=True)
    background_image = models.FileField(upload_to="certificate_templates/", null=True, blank=True)
    text_template = i18n_field()  # "{{full_name}} — {{course_title}} kursini muvaffaqiyatli tugatdi"
    is_default = models.BooleanField(default=False)

    class Meta:
        db_table = "certificates_template"


class Certificate(BaseModel):
    enrollment = models.OneToOneField("enrollment.Enrollment", on_delete=models.CASCADE, related_name="certificate")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="certificates")
    course = models.ForeignKey("courses.Course", on_delete=models.CASCADE, related_name="certificates")
    template = models.ForeignKey(CertificateTemplate, on_delete=models.PROTECT, related_name="certificates")

    code = models.CharField(max_length=32, unique=True, default=_generate_code)  # G-05
    pdf_file = models.FileField(upload_to="certificates/", null=True, blank=True)
    issued_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "certificates_certificate"
        indexes = [models.Index(fields=["code"])]
