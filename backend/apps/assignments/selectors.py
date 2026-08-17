from apps.assignments.models import Submission


def get_mentor_queue(mentor):
    """Mentor kabineti — unga biriktirilgan tekshiriladigan topshiriqlar."""
    return Submission.objects.filter(mentor=mentor).exclude(status="accepted").select_related("homework", "user")


def get_gradebook(course):
    """H-06: baholar jurnali — CSV/XLSX eksport uchun manba."""
    return (
        Submission.objects.filter(homework__lesson__module__course=course)
        .select_related("user", "homework", "grade")
        .order_by("user__full_name", "homework__lesson__order")
    )


def get_user_submissions(*, user, course):
    return Submission.objects.filter(user=user, homework__lesson__module__course=course).select_related("homework", "grade")
