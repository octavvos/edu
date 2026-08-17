from rest_framework import serializers

from apps.communication.models import Comment


class CommentSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source="user.full_name", read_only=True)
    replies = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = (
            "id", "user", "user_name", "text", "is_question", "status",
            "helpful_count", "parent", "replies", "created_at",
        )
        read_only_fields = ("status", "helpful_count", "created_at")

    def get_replies(self, obj):
        if obj.parent_id is not None:
            return []
        return CommentSerializer(obj.replies.filter(status="published"), many=True).data


class CommentCreateSerializer(serializers.Serializer):
    text = serializers.CharField()
    is_question = serializers.BooleanField(default=False)
    parent = serializers.UUIDField(required=False, allow_null=True, default=None)
