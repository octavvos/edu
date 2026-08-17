from apps.certificates.models import Certificate


def get_user_certificates(user):
    """U-04"""
    certs = Certificate.objects.filter(user=user).select_related("course").order_by("-issued_at")
    return [
        {
            "id": str(c.id), "code": c.code, "course_id": str(c.course_id),
            "course_title": c.course.title, "issued_at": c.issued_at.isoformat(),
            "pdf_url": c.pdf_file.url if c.pdf_file else None,
        }
        for c in certs
    ]
