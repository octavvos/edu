from decimal import Decimal

import pytest

from apps.accounts.tests.factories import UserFactory
from apps.courses.tests.factories import CourseFactory
from apps.payments import services
from apps.payments.models import LedgerAccount, LedgerEntry, Order, OrderStatus
from apps.payouts.selectors import get_teacher_balance

pytestmark = pytest.mark.django_db


def test_create_order_uses_course_price():
    user = UserFactory()
    course = CourseFactory(price=Decimal("150000"))

    order = services.create_order(user=user, course=course)

    assert order.amount == Decimal("150000")
    assert order.status == OrderStatus.CREATED


def test_create_order_is_idempotent():
    user = UserFactory()
    course = CourseFactory(price=Decimal("100000"))

    order1 = services.create_order(user=user, course=course, idempotency_key="fixed-key")
    order2 = services.create_order(user=user, course=course, idempotency_key="fixed-key")

    assert order1.id == order2.id
    assert Order.objects.filter(user=user, course=course).count() == 1


def test_mark_order_paid_posts_balanced_double_entry_ledger(settings):
    settings.PLATFORM_COMMISSION_PERCENT = 30
    user = UserFactory()
    course = CourseFactory(price=Decimal("100000"))
    order = services.create_order(user=user, course=course)

    services._mark_order_paid(order, provider_txn_id="test-txn-1")  # noqa: SLF001 — ichki funksiyani sinash

    entries = LedgerEntry.objects.filter(ref_type="order", ref_id=str(order.id))
    total_debit = sum(e.debit for e in entries)
    total_credit = sum(e.credit for e in entries)
    assert total_debit == total_credit  # double-entry muvozanati

    teacher_balance = get_teacher_balance(course.author)
    assert teacher_balance == Decimal("70000.00")  # 100000 - 30% komissiya

    commission_entry = entries.get(account=LedgerAccount.PLATFORM_COMMISSION)
    assert commission_entry.credit == Decimal("30000.00")
