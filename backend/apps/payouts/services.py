from django.db import transaction
from django.utils import timezone

from apps.audit.services import log_action
from apps.core.exceptions import DomainError
from apps.payments.models import LedgerAccount, LedgerEntry
from apps.payouts.models import PayoutRequest, PayoutStatus
from apps.payouts.selectors import get_teacher_balance


class PayoutError(DomainError):
    pass


def request_payout(*, teacher, amount) -> PayoutRequest:
    """TE-04: to'lov so'rovi (payout)."""
    balance = get_teacher_balance(teacher)
    if amount > balance:
        raise PayoutError("So'ralgan summa balansdan katta", code="insufficient_balance")
    if amount <= 0:
        raise PayoutError("Summa musbat bo'lishi kerak", code="invalid_amount")
    return PayoutRequest.objects.create(teacher=teacher, amount=amount)


@transaction.atomic
def approve_payout(*, actor, payout: PayoutRequest) -> PayoutRequest:
    if payout.status != PayoutStatus.REQUESTED:
        raise PayoutError("Bu so'rov allaqachon qayta ishlangan", code="already_processed")

    balance = get_teacher_balance(payout.teacher)
    if payout.amount > balance:
        raise PayoutError("Balans yetarli emas", code="insufficient_balance")

    LedgerEntry.objects.create(
        account=LedgerAccount.TEACHER_PAYABLE, debit=payout.amount, ref_type="payout", ref_id=str(payout.id),
        teacher=payout.teacher, memo=f"Payout #{payout.id}",
    )
    LedgerEntry.objects.create(
        account=LedgerAccount.TEACHER_PAYOUT_CASH, credit=payout.amount, ref_type="payout", ref_id=str(payout.id),
        teacher=payout.teacher, memo=f"Payout #{payout.id} — to'landi",
    )

    payout.status = PayoutStatus.PAID
    payout.processed_by = actor
    payout.processed_at = timezone.now()
    payout.save(update_fields=["status", "processed_by", "processed_at"])
    log_action(actor=actor, action="payout.approve", obj=payout, after={"amount": str(payout.amount)})
    return payout


def reject_payout(*, actor, payout: PayoutRequest, note: str = "") -> PayoutRequest:
    payout.status = PayoutStatus.REJECTED
    payout.note = note
    payout.processed_by = actor
    payout.processed_at = timezone.now()
    payout.save(update_fields=["status", "note", "processed_by", "processed_at"])
    return payout
