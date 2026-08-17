"""
I-01 / P01-P10: Payme Merchant API wrapper.
Hujjat: https://developer.help.paycom.uz/

Payme ikki yo'nalishda ishlaydi:
  1) Checkout URL — foydalanuvchi shu URL'ga yo'naltiriladi (biz generatsiya qilamiz).
  2) Webhook (JSON-RPC, Basic Auth) — Payme bizning /payments/webhooks/payme/
     endpoint'imizga CheckPerformTransaction / CreateTransaction /
     PerformTransaction / CancelTransaction / CheckTransaction chaqiradi.
     Webhook handler'ning o'zi apps/payments/api/views.py'da — bu yerda
     faqat protokol darajasidagi yordamchi funksiyalar.
"""

import base64
import binascii

from django.conf import settings

CHECKOUT_BASE_URL = "https://checkout.paycom.uz"

# Payme JSON-RPC standart xato kodlari
ERROR_INVALID_AMOUNT = -31001
ERROR_TRANSACTION_NOT_FOUND = -31003
ERROR_UNABLE_TO_PERFORM = -31008
ERROR_ORDER_NOT_FOUND = -31050
ERROR_ORDER_ALREADY_PAID = -31051


def build_checkout_url(*, order_id: str, amount_tiyin: int, return_url: str | None = None) -> str:
    """
    amount Payme'da tiyin (so'mning 1/100) hisobida yuboriladi.
    account[order_id] orqali bizning Order.id webhook'da qaytib keladi.
    """
    params = f"m={settings.PAYME_MERCHANT_ID};ac.order_id={order_id};a={amount_tiyin}"
    if return_url:
        params += f";c={return_url}"
    encoded = base64.b64encode(params.encode()).decode()
    prefix = "test" if settings.PAYME_TEST_MODE else "checkout"
    return f"{CHECKOUT_BASE_URL.replace('checkout', prefix, 1)}/{encoded}"


def verify_basic_auth(auth_header: str | None) -> bool:
    """P-04 bilan bog'liq: webhook so'rovi haqiqatan Payme'dan kelganini tekshirish."""
    if not auth_header or not auth_header.startswith("Basic "):
        return False
    try:
        decoded = base64.b64decode(auth_header[len("Basic "):]).decode()
        _login, _, secret = decoded.partition(":")
    except (binascii.Error, ValueError):
        return False
    return secret == settings.PAYME_SECRET_KEY
