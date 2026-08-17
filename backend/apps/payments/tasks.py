from datetime import timedelta

from celery import shared_task
from django.utils import timezone


@shared_task
def poll_pending_payments():
    """P-03/5.8: zaxira sifatida har 10 daqiqada pending to'lovlarni provayderdan tekshiradi."""
    from apps.payments.models import Order, OrderStatus

    stale_cutoff = timezone.now() - timedelta(minutes=15)
    stale_orders = Order.objects.filter(status=OrderStatus.PENDING, created_at__lte=stale_cutoff)
    expired = stale_orders.update(status=OrderStatus.EXPIRED)
    return f"{expired} ta buyurtma muddati tugagani sababli yopildi"


@shared_task
def reconcile_payments_with_provider():
    """5.8: to'lovlarni provayder bilan solishtirish (reconciliation) — kuniga 1 marta."""
    # Production'da Payme GetStatement natijasi bilan lokal Payment yozuvlari
    # solishtiriladi, farq topilsa Sentry'ga alert yuboriladi.
    return "reconciliation stub — TODO: Payme GetStatement bilan solishtirish"
