from apps.payments.models import Order


def get_user_orders(user) -> list[dict]:
    """U-05: to'lovlar tarixi."""
    orders = Order.objects.filter(user=user).select_related("course").order_by("-created_at")
    return [
        {
            "id": str(o.id), "course_title": o.course.title, "amount": str(o.amount),
            "currency": o.currency, "status": o.status, "created_at": o.created_at.isoformat(),
        }
        for o in orders
    ]
