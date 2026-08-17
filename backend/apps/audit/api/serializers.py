from rest_framework import serializers

from apps.audit.models import AuditLog


class AuditLogSerializer(serializers.ModelSerializer):
    actor_display = serializers.CharField(source="actor.__str__", read_only=True)

    class Meta:
        model = AuditLog
        fields = (
            "id", "actor", "actor_display", "action", "object_type", "object_id",
            "before", "after", "ip_address", "user_agent", "created_at",
        )
        read_only_fields = fields
