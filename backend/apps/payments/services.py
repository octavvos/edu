"""
P01-P10: to'lov oqimi. Payme JSON-RPC webhook protokoli sodda va
hujjatlashtirilgan holda amalga oshirilgan — production'ga chiqishdan
oldin barcha chekka holatlar (masalan bir vaqtda ikkita CreateTransaction)
uchun qo'shimcha concurrency testlaridan o'tkazish tavsiya etiladi.
"""

from decimal import Decimal

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from apps.core.events import EVENT_PAYMENT_REFUNDED, EVENT_PAYMENT_SUCCEEDED, publish
from apps.core.exceptions import DomainError
from apps.payments.models import LedgerAccount, LedgerEntry, Order, OrderStatus, Payment, PaymentStatus, Promo


class PaymentError(DomainError):
    pass


class PaymeRPCError(Exception):
    """Payme JSON-RPC standart xato formatiga mos."""

    def __init__(self, code: int, message: str):
        self.code = code
        self.message = message
        super().__init__(message)


# ---------------------------------------------------------------------------
# Order / checkout
# ---------------------------------------------------------------------------

@transaction.atomic
def create_order(*, user, course, promo_code: str = "", idempotency_key: str | None = None) -> Order:
    """P-02: Idempotency-Key bilan takroriy so'rov bir xil Order'ni qaytaradi."""
    if idempotency_key:
        existing = Order.objects.filter(idempotency_key=idempotency_key, user=user).first()
        if existing:
            return existing

    from apps.enrollment.selectors import has_active_enrollment

    if has_active_enrollment(user=user, course=course):
        raise PaymentError("Siz bu kursga allaqachon yozilgansiz", code="already_enrolled")

    amount = course.price
    discount = Decimal("0")
    promo = None
    if promo_code:
        promo = _validate_promo(promo_code, course)
        discount = _calc_discount(promo, amount)
        amount = max(Decimal("0"), amount - discount)

    kwargs = {"user": user, "course": course, "amount": amount, "currency": course.currency,
              "promo": promo, "discount_amount": discount}
    if idempotency_key:
        kwargs["idempotency_key"] = idempotency_key
    return Order.objects.create(**kwargs)


def _validate_promo(code: str, course) -> Promo:
    promo = Promo.objects.filter(code=code).first()
    if not promo:
        raise PaymentError("Promokod topilmadi", code="promo_not_found")
    now = timezone.now()
    if not (promo.valid_from <= now <= promo.valid_until):
        raise PaymentError("Promokod muddati o'tgan", code="promo_expired")
    if promo.usage_limit and promo.used_count >= promo.usage_limit:
        raise PaymentError("Promokod limiti tugagan", code="promo_limit_reached")
    if promo.course_ids and str(course.id) not in promo.course_ids:
        raise PaymentError("Promokod bu kursga tegishli emas", code="promo_not_applicable")
    return promo


def _calc_discount(promo: Promo, amount: Decimal) -> Decimal:
    if promo.discount_type == "percent":
        return amount * promo.value / Decimal("100")
    return min(amount, promo.value)


def preview_promo(*, code: str, course) -> dict:
    """Promo/validate endpoint uchun — Order yaratmasdan chegirmani ko'rsatadi."""
    promo = _validate_promo(code, course)
    discount = _calc_discount(promo, course.price)
    return {"discount_amount": discount, "final_price": course.price - discount}


def initiate_checkout(*, order: Order) -> dict:
    if order.status not in (OrderStatus.CREATED, OrderStatus.FAILED, OrderStatus.EXPIRED):
        raise PaymentError("Buyurtma allaqachon boshqa holatda", code="invalid_order_state")

    if order.amount == 0:
        _mark_order_paid(order, provider_txn_id="promo_full_discount")
        return {"free": True, "order_id": str(order.id)}

    from libs.payme.client import build_checkout_url

    order.status = OrderStatus.PENDING
    order.save(update_fields=["status"])
    url = build_checkout_url(order_id=str(order.id), amount_tiyin=int(order.amount * 100))
    return {"checkout_url": url, "order_id": str(order.id)}


# ---------------------------------------------------------------------------
# Payme JSON-RPC webhook (P02-P04, P09)
# ---------------------------------------------------------------------------

def dispatch_payme_method(method: str, params: dict) -> dict:
    handlers = {
        "CheckPerformTransaction": _payme_check_perform,
        "CreateTransaction": _payme_create_transaction,
        "PerformTransaction": _payme_perform_transaction,
        "CancelTransaction": _payme_cancel_transaction,
        "CheckTransaction": _payme_check_transaction,
        "GetStatement": _payme_get_statement,
    }
    handler = handlers.get(method)
    if not handler:
        raise PaymeRPCError(-32601, "Method not found")
    return handler(params)


def _get_order_from_params(params: dict) -> Order:
    from libs.payme.client import ERROR_ORDER_NOT_FOUND

    order_id = (params.get("account") or {}).get("order_id")
    order = Order.objects.filter(id=order_id).first()
    if not order:
        raise PaymeRPCError(ERROR_ORDER_NOT_FOUND, "Order not found")
    return order


def _payme_check_perform(params: dict) -> dict:
    from libs.payme.client import ERROR_INVALID_AMOUNT, ERROR_ORDER_ALREADY_PAID

    order = _get_order_from_params(params)
    if order.status in (OrderStatus.PAID, OrderStatus.FULFILLED):
        raise PaymeRPCError(ERROR_ORDER_ALREADY_PAID, "Order already paid")
    if int(order.amount * 100) != params.get("amount"):
        raise PaymeRPCError(ERROR_INVALID_AMOUNT, "Invalid amount")
    return {"allow": True}


@transaction.atomic
def _payme_create_transaction(params: dict) -> dict:
    order = _get_order_from_params(params)
    txn_id = params["id"]

    existing = Payment.objects.filter(provider="payme", provider_txn_id=txn_id).first()
    if existing:
        return {
            "create_time": int(existing.created_at.timestamp() * 1000),
            "transaction": str(existing.id), "state": 1,
        }

    payment = Payment.objects.create(
        order=order, provider="payme", provider_txn_id=txn_id,
        status=PaymentStatus.PENDING, raw_payload=params,
    )
    return {"create_time": int(payment.created_at.timestamp() * 1000), "transaction": str(payment.id), "state": 1}


@transaction.atomic
def _payme_perform_transaction(params: dict) -> dict:
    payment = _get_payment_or_raise(params["id"])
    if payment.status == PaymentStatus.SUCCEEDED:
        return {"transaction": str(payment.id), "perform_time": int(payment.performed_at.timestamp() * 1000), "state": 2}

    payment.status = PaymentStatus.SUCCEEDED
    payment.performed_at = timezone.now()
    payment.save(update_fields=["status", "performed_at"])
    _mark_order_paid(payment.order, provider_txn_id=params["id"])

    return {"transaction": str(payment.id), "perform_time": int(payment.performed_at.timestamp() * 1000), "state": 2}


def _get_payment_or_raise(txn_id: str) -> Payment:
    from libs.payme.client import ERROR_TRANSACTION_NOT_FOUND

    payment = Payment.objects.filter(provider="payme", provider_txn_id=txn_id).select_related("order").first()
    if not payment:
        raise PaymeRPCError(ERROR_TRANSACTION_NOT_FOUND, "Transaction not found")
    return payment


def _mark_order_paid(order: Order, *, provider_txn_id: str) -> None:
    order.status = OrderStatus.PAID
    order.save(update_fields=["status"])
    _post_ledger_for_order(order)

    if order.promo_id:
        Promo.objects.filter(id=order.promo_id).update(used_count=models_f("used_count") + 1)

    order.status = OrderStatus.FULFILLED
    order.save(update_fields=["status"])

    publish(
        EVENT_PAYMENT_SUCCEEDED, user_id=str(order.user_id), course_id=str(order.course_id),
        order_id=str(order.id), provider_txn_id=provider_txn_id,
    )


def models_f(field_name: str):
    from django.db.models import F

    return F(field_name)


def _post_ledger_for_order(order: Order) -> None:
    """P-07/P-08: komissiya ajratmasi bilan double-entry yozuv."""
    commission_percent = settings.PLATFORM_COMMISSION_PERCENT  # P-07: admin paneldan sozlanadi
    commission = (order.amount * Decimal(commission_percent) / Decimal("100")).quantize(Decimal("0.01"))
    teacher_share = order.amount - commission

    LedgerEntry.objects.create(
        account=LedgerAccount.PLATFORM_CASH, debit=order.amount, ref_type="order", ref_id=str(order.id),
        memo=f"Order #{order.id} to'lovi",
    )
    LedgerEntry.objects.create(
        account=LedgerAccount.TEACHER_PAYABLE, credit=teacher_share, ref_type="order", ref_id=str(order.id),
        teacher_id=order.course.author_id, memo=f"Order #{order.id} — o'qituvchi ulushi",
    )
    LedgerEntry.objects.create(
        account=LedgerAccount.PLATFORM_COMMISSION, credit=commission, ref_type="order", ref_id=str(order.id),
        memo=f"Order #{order.id} — komissiya {commission_percent}%",
    )


@transaction.atomic
def _payme_cancel_transaction(params: dict) -> dict:
    payment = _get_payment_or_raise(params["id"])
    if payment.status != PaymentStatus.CANCELLED:
        was_succeeded = payment.status == PaymentStatus.SUCCEEDED
        payment.status = PaymentStatus.CANCELLED
        payment.cancelled_at = timezone.now()
        payment.save(update_fields=["status", "cancelled_at"])
        if was_succeeded:
            _reverse_ledger_for_order(payment.order)
            payment.order.status = OrderStatus.REFUNDED
            payment.order.save(update_fields=["status"])
            publish(EVENT_PAYMENT_REFUNDED, user_id=str(payment.order.user_id), order_id=str(payment.order.id))

    return {
        "transaction": str(payment.id),
        "cancel_time": int(payment.cancelled_at.timestamp() * 1000),
        "state": -1,
    }


def _reverse_ledger_for_order(order: Order) -> None:
    commission_percent = settings.PLATFORM_COMMISSION_PERCENT
    commission = (order.amount * Decimal(commission_percent) / Decimal("100")).quantize(Decimal("0.01"))
    teacher_share = order.amount - commission

    LedgerEntry.objects.create(
        account=LedgerAccount.PLATFORM_CASH, credit=order.amount, ref_type="refund", ref_id=str(order.id),
        memo=f"Order #{order.id} qaytarish",
    )
    LedgerEntry.objects.create(
        account=LedgerAccount.TEACHER_PAYABLE, debit=teacher_share, ref_type="refund", ref_id=str(order.id),
        teacher_id=order.course.author_id, memo=f"Order #{order.id} qaytarish — o'qituvchi ulushi",
    )
    LedgerEntry.objects.create(
        account=LedgerAccount.PLATFORM_COMMISSION, debit=commission, ref_type="refund", ref_id=str(order.id),
        memo=f"Order #{order.id} qaytarish — komissiya",
    )


def _payme_check_transaction(params: dict) -> dict:
    payment = _get_payment_or_raise(params["id"])
    state = {"pending": 1, "succeeded": 2, "cancelled": -1, "failed": -2}.get(payment.status, 1)
    return {
        "create_time": int(payment.created_at.timestamp() * 1000),
        "perform_time": int(payment.performed_at.timestamp() * 1000) if payment.performed_at else 0,
        "cancel_time": int(payment.cancelled_at.timestamp() * 1000) if payment.cancelled_at else 0,
        "transaction": str(payment.id), "state": state, "reason": None,
    }


def _payme_get_statement(params: dict) -> dict:
    from_ts, to_ts = params.get("from", 0), params.get("to", 0)
    from datetime import datetime, timezone as dt_timezone

    qs = Payment.objects.filter(
        provider="payme",
        created_at__gte=datetime.fromtimestamp(from_ts / 1000, tz=dt_timezone.utc),
        created_at__lte=datetime.fromtimestamp(to_ts / 1000, tz=dt_timezone.utc),
    )
    return {
        "transactions": [
            {"id": p.provider_txn_id, "amount": int(p.order.amount * 100), "state": 2 if p.status == "succeeded" else 1}
            for p in qs
        ],
    }


# ---------------------------------------------------------------------------
# Admin refund (P-05)
# ---------------------------------------------------------------------------

@transaction.atomic
def admin_refund(*, actor, order: Order, reason: str = "") -> Order:
    from apps.audit.services import log_action

    if order.status not in (OrderStatus.PAID, OrderStatus.FULFILLED):
        raise PaymentError("Faqat to'langan buyurtmalarni qaytarish mumkin", code="not_paid")

    payment = order.payments.filter(status=PaymentStatus.SUCCEEDED).first()
    if payment:
        _payme_cancel_transaction({"id": payment.provider_txn_id})
    else:
        order.status = OrderStatus.REFUNDED
        order.save(update_fields=["status"])

    from apps.enrollment.models import Enrollment, EnrollmentStatus

    Enrollment.objects.filter(user=order.user, course=order.course).update(status=EnrollmentStatus.REFUNDED)
    log_action(actor=actor, action="payment.refund", obj=order, after={"reason": reason})
    return order
