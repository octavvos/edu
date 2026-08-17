from datetime import timedelta

from django.db.models import Avg, Count, Sum
from django.utils import timezone


def get_course_analytics(course) -> dict:
    """TE-03: ro'yxatdan o'tganlar, faol o'quvchilar, tugatish darajasi, tashlab ketish nuqtalari."""
    from apps.enrollment.models import Enrollment, EnrollmentStatus, Progress

    enrollments = Enrollment.objects.filter(course=course)
    total = enrollments.count()
    active = enrollments.filter(status=EnrollmentStatus.ACTIVE).count()
    completed = enrollments.filter(completed_at__isnull=False).count()
    completion_rate = round(completed / total * 100, 2) if total else 0

    # Dars bo'yicha tashlab ketish nuqtalari: har bir dars uchun necha nafar
    # o'quvchi shu darsdan keyin to'xtab qolgan (keyingi darsni boshlamagan).
    drop_off = list(
        Progress.objects.filter(enrollment__course=course, status="completed")
        .values("lesson__title", "lesson__order")
        .annotate(completed_count=Count("id"))
        .order_by("lesson__order"),
    )

    return {
        "total_enrollments": total,
        "active_enrollments": active,
        "completion_rate": completion_rate,
        "lesson_completion_funnel": drop_off,
    }


def get_admin_dashboard_summary() -> dict:
    """AD-05: DAU/MAU, yangi ro'yxatdan o'tish, daromad, o'rtacha chek, konversiya voronkasi."""
    from apps.accounts.models import User
    from apps.enrollment.models import Enrollment
    from apps.payments.models import Order, OrderStatus

    now = timezone.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    month_start = today_start - timedelta(days=30)

    dau = User.objects.filter(last_login__gte=today_start).count()
    mau = User.objects.filter(last_login__gte=month_start).count()
    new_registrations = User.objects.filter(created_at__gte=today_start).count()

    revenue_agg = Order.objects.filter(status=OrderStatus.FULFILLED, created_at__gte=month_start).aggregate(
        total=Sum("amount"), avg_check=Avg("amount"), count=Count("id"),
    )

    guests_to_enrolled = Enrollment.objects.filter(starts_at__gte=month_start).count()

    return {
        "dau": dau,
        "mau": mau,
        "new_registrations_today": new_registrations,
        "revenue_last_30d": str(revenue_agg["total"] or 0),
        "average_check": str(revenue_agg["avg_check"] or 0),
        "orders_last_30d": revenue_agg["count"] or 0,
        "enrollments_last_30d": guests_to_enrolled,
    }
