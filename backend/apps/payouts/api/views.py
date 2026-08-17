from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.exceptions import DomainError
from apps.payouts import services
from apps.payouts.api.serializers import PayoutRequestCreateSerializer, PayoutRequestSerializer
from apps.payouts.models import PayoutRequest
from apps.payouts.selectors import get_teacher_balance


class PayoutRequestListCreateView(APIView):
    """TE-04: GET — mening payout so'rovlarim, POST — yangi so'rov."""

    def get(self, request):
        qs = PayoutRequest.objects.filter(teacher=request.user).order_by("-created_at")
        return Response({
            "balance": str(get_teacher_balance(request.user)),
            "requests": PayoutRequestSerializer(qs, many=True).data,
        })

    def post(self, request):
        serializer = PayoutRequestCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            payout = services.request_payout(teacher=request.user, amount=serializer.validated_data["amount"])
        except DomainError as exc:
            return Response({"detail": exc.detail}, status=exc.status_code)
        return Response(PayoutRequestSerializer(payout).data, status=status.HTTP_201_CREATED)
