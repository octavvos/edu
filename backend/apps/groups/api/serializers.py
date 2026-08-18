from rest_framework import serializers

from apps.core.models import get_i18n_value
from apps.groups.models import (
    AttendanceStatus,
    Group,
    GroupMembership,
    GroupSchedule,
    JoinRequest,
    Weekday,
)


class ScheduleSerializer(serializers.ModelSerializer):
    weekday_label = serializers.CharField(source="get_weekday_display", read_only=True)

    class Meta:
        model = GroupSchedule
        fields = ["id", "weekday", "weekday_label", "start_time", "end_time", "room", "online_url"]


class ScheduleWriteSerializer(serializers.Serializer):
    weekday = serializers.ChoiceField(choices=Weekday.choices)
    start_time = serializers.TimeField()
    end_time = serializers.TimeField()
    room = serializers.CharField(max_length=60, required=False, allow_blank=True)
    online_url = serializers.URLField(required=False, allow_blank=True)


class StudentBriefSerializer(serializers.Serializer):
    """O'quvchi haqidagi mentor ko'radigan qisqa ma'lumot."""

    id = serializers.UUIDField(read_only=True)
    username = serializers.CharField(read_only=True)
    first_name = serializers.CharField(read_only=True)
    last_name = serializers.CharField(read_only=True)
    display_name = serializers.CharField(read_only=True)
    status = serializers.CharField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)


class GroupPublicSerializer(serializers.ModelSerializer):
    """Ro'yxatdan o'tish formasi uchun — autentifikatsiyasiz ko'rinadi."""

    course_title = serializers.SerializerMethodField()
    schedules = ScheduleSerializer(many=True, read_only=True)
    has_free_seats = serializers.BooleanField(read_only=True)

    class Meta:
        model = Group
        fields = ["id", "name", "code", "course_title", "schedules", "capacity", "has_free_seats",
                  "starts_on"]

    def get_course_title(self, obj) -> str:
        lang = self.context.get("lang", "uz")
        return get_i18n_value(obj.course, "title", lang)


class GroupDetailSerializer(GroupPublicSerializer):
    mentor_name = serializers.CharField(source="mentor.display_name", read_only=True, default="")
    active_members_count = serializers.IntegerField(read_only=True)

    class Meta(GroupPublicSerializer.Meta):
        fields = [*GroupPublicSerializer.Meta.fields, "mentor_name", "active_members_count",
                  "is_open_for_registration", "is_active", "ends_on"]


class GroupCreateSerializer(serializers.Serializer):
    course_id = serializers.UUIDField()
    name = serializers.CharField(max_length=120)
    code = serializers.SlugField(max_length=60)
    mentor_id = serializers.UUIDField(required=False, allow_null=True)
    capacity = serializers.IntegerField(min_value=1, max_value=500, default=30)
    starts_on = serializers.DateField(required=False, allow_null=True)
    ends_on = serializers.DateField(required=False, allow_null=True)


class MembershipSerializer(serializers.ModelSerializer):
    student = StudentBriefSerializer(read_only=True)

    class Meta:
        model = GroupMembership
        fields = ["id", "student", "status", "joined_at"]


class JoinRequestSerializer(serializers.ModelSerializer):
    student = StudentBriefSerializer(read_only=True)
    group_name = serializers.CharField(source="group.name", read_only=True)
    group_code = serializers.CharField(source="group.code", read_only=True)

    class Meta:
        model = JoinRequest
        fields = ["id", "student", "group", "group_name", "group_code", "status",
                  "review_note", "created_at", "reviewed_at"]
        read_only_fields = fields


class TransferSerializer(serializers.Serializer):
    student_id = serializers.UUIDField()
    from_group_id = serializers.UUIDField()
    to_group_id = serializers.UUIDField()


class RejectSerializer(serializers.Serializer):
    note = serializers.CharField(max_length=255, required=False, allow_blank=True)


class AttendanceRowSerializer(serializers.Serializer):
    """apps.groups.attendance.AttendanceRow — kunlik varaqa qatori."""

    student_id = serializers.CharField(read_only=True)
    username = serializers.CharField(read_only=True)
    display_name = serializers.CharField(read_only=True)
    status = serializers.CharField(read_only=True, allow_null=True)
    note = serializers.CharField(read_only=True, allow_blank=True)


class AttendanceSummaryRowSerializer(serializers.Serializer):
    """apps.groups.attendance.AttendanceSummaryRow — umumiy hisob."""

    student_id = serializers.CharField(read_only=True)
    username = serializers.CharField(read_only=True)
    display_name = serializers.CharField(read_only=True)
    present = serializers.IntegerField(read_only=True)
    late = serializers.IntegerField(read_only=True)
    excused = serializers.IntegerField(read_only=True)
    absent = serializers.IntegerField(read_only=True)
    total = serializers.IntegerField(read_only=True)
    attendance_percent = serializers.FloatField(read_only=True)


class AttendanceRecordWriteSerializer(serializers.Serializer):
    student_id = serializers.UUIDField()
    status = serializers.ChoiceField(choices=AttendanceStatus.choices)
    note = serializers.CharField(max_length=255, required=False, allow_blank=True, default="")


class AttendanceMarkSerializer(serializers.Serializer):
    date = serializers.DateField()
    records = AttendanceRecordWriteSerializer(many=True, allow_empty=False)


class LeaderboardRowSerializer(serializers.Serializer):
    """apps.groups.leaderboard.LeaderboardRow bilan mos."""

    rank = serializers.IntegerField(read_only=True)
    student_id = serializers.CharField(read_only=True)
    username = serializers.CharField(read_only=True)
    display_name = serializers.CharField(read_only=True)
    total_score = serializers.IntegerField(read_only=True)
    graded_count = serializers.IntegerField(read_only=True)
