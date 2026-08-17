from rest_framework import serializers


class CheckoutSerializer(serializers.Serializer):
    course_id = serializers.UUIDField()
    promo_code = serializers.CharField(required=False, allow_blank=True, default="")


class PromoValidateSerializer(serializers.Serializer):
    code = serializers.CharField()
    course_id = serializers.UUIDField()


class RefundSerializer(serializers.Serializer):
    reason = serializers.CharField(required=False, allow_blank=True, default="")
