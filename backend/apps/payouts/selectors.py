from decimal import Decimal

from django.db.models import Sum

from apps.payments.models import LedgerAccount, LedgerEntry


def get_teacher_balance(teacher) -> Decimal:
    """
    P-08: balans faqat ledger'dan hisoblanadi. Faqat TEACHER_PAYABLE hisobi
    "hali to'lanmagan qarz"ni bildiradi: sotuvda kredit yoziladi, payout
    to'langanda debit yoziladi. TEACHER_PAYOUT_CASH — alohida audit/hisobot
    hisobi (jami to'langan summa), joriy balansga kirmaydi.
    """
    agg = LedgerEntry.objects.filter(
        account=LedgerAccount.TEACHER_PAYABLE, teacher=teacher,
    ).aggregate(total_credit=Sum("credit"), total_debit=Sum("debit"))
    return (agg["total_credit"] or Decimal("0")) - (agg["total_debit"] or Decimal("0"))


def get_course_earnings(course) -> dict:
    """TE-04: sotuvlar, komissiya, joriy balans (shu kursga tegishli order'lar bo'yicha)."""
    from apps.payments.models import Order, OrderStatus

    order_ids = list(Order.objects.filter(course=course).values_list("id", flat=True).distinct())
    order_id_strs = [str(oid) for oid in order_ids]

    agg = LedgerEntry.objects.filter(
        ref_type="order", ref_id__in=order_id_strs, account=LedgerAccount.TEACHER_PAYABLE,
    ).aggregate(total_earned=Sum("credit"))

    sales_count = Order.objects.filter(course=course, status=OrderStatus.FULFILLED).count()
    return {
        "sales_count": sales_count,
        "total_earned": str(agg["total_earned"] or Decimal("0")),
        "current_balance": str(get_teacher_balance(course.author)),
    }
