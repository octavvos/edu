from decimal import Decimal

import pytest

from apps.accounts.tests.factories import UserFactory
from apps.courses.tests.factories import CourseFactory
from apps.payments import services as payment_services
from apps.payouts import services
from apps.payouts.selectors import get_teacher_balance

pytestmark = pytest.mark.django_db


def _pay_for_course(course, buyer, settings, commission_percent=30):
    settings.PLATFORM_COMMISSION_PERCENT = commission_percent
    order = payment_services.create_order(user=buyer, course=course)
    payment_services._mark_order_paid(order, provider_txn_id="txn-1")  # noqa: SLF001
    return order


def test_payout_reduces_teacher_balance_without_double_counting(settings):
    teacher = UserFactory()
    buyer = UserFactory()
    course = CourseFactory(author=teacher, price=Decimal("100000"))
    _pay_for_course(course, buyer, settings)

    assert get_teacher_balance(teacher) == Decimal("70000.00")

    payout = services.request_payout(teacher=teacher, amount=Decimal("70000.00"))
    services.approve_payout(actor=teacher, payout=payout)

    assert get_teacher_balance(teacher) == Decimal("0.00")


def test_request_payout_rejects_amount_over_balance(settings):
    teacher = UserFactory()
    buyer = UserFactory()
    course = CourseFactory(author=teacher, price=Decimal("50000"))
    _pay_for_course(course, buyer, settings)

    with pytest.raises(services.PayoutError):
        services.request_payout(teacher=teacher, amount=Decimal("999999"))
