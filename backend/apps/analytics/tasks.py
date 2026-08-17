from celery import shared_task
from django.utils import timezone


@shared_task
def compute_daily_aggregates():
    """5.8: analitika agregatlari — kechasi 03:00."""
    from apps.analytics.models import DailyAggregate
    from apps.analytics.selectors import get_admin_dashboard_summary

    today = timezone.now().date()
    summary = get_admin_dashboard_summary()
    for metric, value in summary.items():
        try:
            numeric_value = float(value)
        except (TypeError, ValueError):
            continue
        DailyAggregate.objects.update_or_create(
            date=today, metric=metric, dimension={}, defaults={"value": numeric_value},
        )
    return f"{len(summary)} ta metrika {today} uchun hisoblandi"
