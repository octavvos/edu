from decimal import Decimal

from rest_framework import serializers

from apps.payouts.models import PayoutRequest


class PayoutRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = PayoutRequest
        fields = ("id", "amount", "status", "note", "created_at", "processed_at")
        read_only_fields = ("id", "status", "note", "created_at", "processed_at")


class PayoutRequestCreateSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=14, decimal_places=2, min_value=Decimal("0.01"))
