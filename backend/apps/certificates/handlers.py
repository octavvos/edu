from apps.core import events


@events.on(events.EVENT_COURSE_COMPLETED)
def _on_course_completed(enrollment_id: str, **kwargs):
    """G-04: kurs 100% tugatilgan holda avtomatik generatsiya (yakuniy test sharti update_progress'da tekshiriladi)."""
    from apps.certificates.services import issue_certificate
    from apps.courses.models import Course
    from apps.enrollment.models import Enrollment

    enrollment = Enrollment.objects.select_related("course", "user").filter(id=enrollment_id).first()
    if not enrollment:
        return
    course = Course.objects.filter(id=enrollment.course_id, issues_certificate=True).first()
    if course:
        issue_certificate(enrollment=enrollment)
