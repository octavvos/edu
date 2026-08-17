from apps.enrollment.models import Enrollment, EnrollmentStatus, Progress


def has_active_enrollment(*, user, course) -> bool:
    return Enrollment.objects.filter(
        user=user, course=course, status=EnrollmentStatus.ACTIVE,
    ).exists()


def get_enrollment(*, user, course) -> Enrollment | None:
    return Enrollment.objects.filter(user=user, course=course).first()


def get_my_courses_grouped(user) -> dict:
    """U-03: davom etayotgan / tugatilgan / saqlangan."""
    qs = Enrollment.objects.filter(user=user, status=EnrollmentStatus.ACTIVE).select_related("course")
    in_progress, completed = [], []
    for enrollment in qs:
        item = {
            "enrollment_id": str(enrollment.id), "course_id": str(enrollment.course_id),
            "course_title": enrollment.course.title, "progress_percent": enrollment.progress_percent,
        }
        (completed if enrollment.completed_at else in_progress).append(item)
    return {"in_progress": in_progress, "completed": completed}


def get_course_students(course):
    """TE-02: o'quvchilar ro'yxati — progress, oxirgi faollik, baholar."""
    qs = Enrollment.objects.filter(course=course).select_related("user")
    return [
        {
            "user_id": str(e.user_id), "user_name": e.user.full_name or e.user.phone or e.user.email,
            "progress_percent": e.progress_percent, "status": e.status,
            "enrolled_at": e.starts_at.isoformat(),
        }
        for e in qs
    ]


def get_progress_map(enrollment: Enrollment) -> dict:
    return {str(p.lesson_id): p for p in Progress.objects.filter(enrollment=enrollment)}


def is_lesson_unlocked(*, enrollment: Enrollment, lesson) -> bool:
    """C-05: drip-content shartlarini tekshiradi."""
    from django.utils import timezone

    rule = lesson.unlock_rule or {}
    rule_type = rule.get("type")

    if not rule_type:
        return True
    if rule_type == "date":
        unlock_at = rule.get("unlock_at")
        return bool(unlock_at) and timezone.now().isoformat() >= unlock_at
    if rule_type == "after_lesson":
        prev = Progress.objects.filter(
            enrollment=enrollment, lesson_id=rule.get("lesson_id"), status="completed",
        ).exists()
        return prev
    if rule_type == "min_quiz_score":
        from apps.assessments.selectors import get_best_attempt_score

        score = get_best_attempt_score(enrollment=enrollment, quiz_lesson_id=rule.get("quiz_lesson_id"))
        return score is not None and score >= rule.get("min_percent", 0)
    return True
