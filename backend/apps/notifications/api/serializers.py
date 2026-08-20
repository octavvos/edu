from rest_framework import serializers

from apps.notifications.models import NotificationDispatch


class NotificationDispatchSerializer(serializers.ModelSerializer):
    """In-app bildirishnoma qatori — `payload` ichidagi tayyor matn va turni ochadi."""

    text = serializers.SerializerMethodField()
    type = serializers.SerializerMethodField()

    class Meta:
        model = NotificationDispatch
        fields = ("id", "event", "text", "type", "created_at")

    def get_text(self, obj):
        return obj.payload.get("text", "")

    def get_type(self, obj):
        return obj.payload.get("type", "info")
