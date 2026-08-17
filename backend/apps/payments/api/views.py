from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.exceptions import DomainError
from apps.core.permissions import HasPermission
from apps.payments import services
from apps.payments.api.serializers import CheckoutSerializer, PromoValidateSerializer, RefundSerializer
from apps.payments.selectors import get_user_orders


class CheckoutView(APIView):
    """POST /api/v1/payments/checkout/ — P01-P02."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = CheckoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        from apps.courses.models import Course

        course = Course.objects.filter(id=serializer.validated_data["course_id"]).first()
        if not course:
            return Response(status=status.HTTP_404_NOT_FOUND)

        idempotency_key = request.headers.get("Idempotency-Key")  # P-02
        try:
            order = services.create_order(
                user=request.user, course=course, promo_code=serializer.validated_data["promo_code"],
                idempotency_key=idempotency_key,
            )
            result = services.initiate_checkout(order=order)
        except DomainError as exc:
            return Response({"detail": exc.detail}, status=exc.status_code)
        return Response(result, status=status.HTTP_201_CREATED)


class OrderListView(APIView):
    """GET /api/v1/payments/orders/"""

    def get(self, request):
        return Response(get_user_orders(request.user))


class PromoValidateView(APIView):
    """POST /api/v1/payments/promo/validate/"""

    def post(self, request):
        serializer = PromoValidateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        from apps.courses.models import Course

        course = Course.objects.filter(id=serializer.validated_data["course_id"]).first()
        if not course:
            return Response(status=status.HTTP_404_NOT_FOUND)
        try:
            preview = services.preview_promo(code=serializer.validated_data["code"], course=course)
        except DomainError as exc:
            return Response({"valid": False, "detail": exc.detail}, status=exc.status_code)
        return Response({"valid": True, "discount_amount": str(preview["discount_amount"]),
                          "final_price": str(preview["final_price"])})


class PaymeWebhookView(APIView):
    """
    POST /api/v1/payments/webhooks/payme/ — P03-P04: JSON-RPC, Basic Auth,
    imzo (Basic Auth orqali) tekshiriladi, xom holda saqlanadi.
    """

    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        from libs.payme.client import verify_basic_auth

        if not verify_basic_auth(request.headers.get("Authorization")):
            return Response({"error": {"code": -32504, "message": "Unauthorized"}}, status=status.HTTP_200_OK)

        body = request.data
        method, params, rpc_id = body.get("method"), body.get("params", {}), body.get("id")
        try:
            result = services.dispatch_payme_method(method, params)
            return Response({"result": result, "id": rpc_id})
        except services.PaymeRPCError as exc:
            return Response({"error": {"code": exc.code, "message": exc.message}, "id": rpc_id})


class RefundView(APIView):
    """P-05: admin tasdig'i bilan qaytarish."""

    permission_classes = [HasPermission]
    required_permission = "payment.refund"

    def post(self, request, order_id):
        from apps.payments.models import Order

        order = Order.objects.filter(id=order_id).first()
        if not order:
            return Response(status=status.HTTP_404_NOT_FOUND)
        serializer = RefundSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            services.admin_refund(actor=request.user, order=order, **serializer.validated_data)
        except DomainError as exc:
            return Response({"detail": exc.detail}, status=exc.status_code)
        return Response({"status": order.status})
