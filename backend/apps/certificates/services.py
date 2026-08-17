import io

from django.conf import settings
from django.core.files.base import ContentFile
from django.template.loader import render_to_string

from apps.core.events import EVENT_CERTIFICATE_ISSUED, publish
from apps.core.models import get_i18n_value


def issue_certificate(*, enrollment):
    """G-04: kurs 100% tugatilgan va yakuniy test o'tilgan holda avtomatik generatsiya."""
    from apps.certificates.models import Certificate, CertificateTemplate

    if hasattr(enrollment, "certificate"):
        return enrollment.certificate

    template = CertificateTemplate.objects.filter(is_default=True).first()
    if not template:
        template = CertificateTemplate.objects.create(
            name="Standart", text_template={"uz": "{{full_name}} — {{course_title}} kursini muvaffaqiyatli tugatdi"},
            is_default=True,
        )

    certificate = Certificate.objects.create(
        enrollment=enrollment, user=enrollment.user, course=enrollment.course, template=template,
    )
    _render_pdf(certificate)

    publish(EVENT_CERTIFICATE_ISSUED, user_id=str(enrollment.user_id), certificate_id=str(certificate.id))
    return certificate


def _render_pdf(certificate) -> None:
    """G-05: Sertifikat PDF + unikal raqam + QR-kod -> ochiq verifikatsiya sahifasi."""
    import qrcode
    from weasyprint import HTML

    verify_url = f"{settings.FRONTEND_BASE_URL}/verify/{certificate.code}"

    qr_img = qrcode.make(verify_url)
    qr_buffer = io.BytesIO()
    qr_img.save(qr_buffer, format="PNG")
    import base64

    qr_base64 = base64.b64encode(qr_buffer.getvalue()).decode()

    lang = certificate.user.language or "uz"
    text_template = get_i18n_value(certificate.template, "text_template", lang)
    body_text = text_template.replace(
        "{{full_name}}", certificate.user.full_name or "",
    ).replace(
        "{{course_title}}", get_i18n_value(certificate.course, "title", lang),
    )

    html_content = render_to_string(
        "certificates/certificate.html",
        {"certificate": certificate, "body_text": body_text, "qr_base64": qr_base64, "verify_url": verify_url},
    )
    pdf_bytes = HTML(string=html_content).write_pdf()
    certificate.pdf_file.save(f"{certificate.code}.pdf", ContentFile(pdf_bytes), save=True)


def verify_certificate(code: str) -> dict | None:
    """G-05: /verify/{code} — ochiq verifikatsiya."""
    from apps.certificates.models import Certificate
    from apps.core.models import get_i18n_value

    certificate = Certificate.objects.select_related("user", "course").filter(code=code.upper()).first()
    if not certificate:
        return None
    return {
        "valid": True,
        "full_name": certificate.user.full_name,
        "course_title": get_i18n_value(certificate.course, "title", "uz"),
        "issued_at": certificate.issued_at.isoformat(),
        "code": certificate.code,
    }
