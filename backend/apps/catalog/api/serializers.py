from rest_framework import serializers

from apps.catalog.models import Category, Review
from apps.core.fields import I18nCharField


class CategorySerializer(serializers.ModelSerializer):
    children = serializers.SerializerMethodField()
    name = I18nCharField()

    class Meta:
        model = Category
        fields = ("id", "slug", "name", "icon", "order", "children")

    def get_children(self, obj):
        by_parent = self.context.get("by_parent", {})
        return CategorySerializer(by_parent.get(obj.id, []), many=True, context=self.context).data


class CourseCardSerializer(serializers.Serializer):
    """K-06 uchun yengil kurs kartochkasi — katalog ro'yxatida ishlatiladi."""

    id = serializers.UUIDField()
    slug = serializers.CharField()
    title = I18nCharField()
    description = I18nCharField()
    price = serializers.DecimalField(max_digits=12, decimal_places=2)
    currency = serializers.CharField()
    level = serializers.CharField()
    level_display = serializers.CharField(source="get_level_display")
    rating_avg = serializers.FloatField()
    rating_count = serializers.IntegerField()
    enrollment_count = serializers.IntegerField()
    cover_image = serializers.CharField(allow_null=True, required=False)


class ReviewSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source="user.display_name", read_only=True)

    class Meta:
        model = Review
        fields = ("id", "course", "user", "user_name", "rating", "comment", "status", "created_at")
        read_only_fields = ("status", "created_at", "user")


class ReviewCreateSerializer(serializers.Serializer):
    rating = serializers.IntegerField(min_value=1, max_value=5)
    comment = serializers.CharField(required=False, allow_blank=True, default="")
