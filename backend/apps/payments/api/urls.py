from django.urls import path

from apps.payments.api import views

urlpatterns = [
    path("checkout/", views.CheckoutView.as_view(), name="payment-checkout"),
    path("orders/", views.OrderListView.as_view(), name="payment-orders"),
    path("orders/<uuid:order_id>/refund/", views.RefundView.as_view(), name="payment-refund"),
    path("promo/validate/", views.PromoValidateView.as_view(), name="payment-promo-validate"),
    path("webhooks/payme/", views.PaymeWebhookView.as_view(), name="payme-webhook"),
]
