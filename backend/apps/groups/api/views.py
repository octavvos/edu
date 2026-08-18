from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import User
from apps.courses.models import Course
from apps.groups import selectors, services
from apps.groups.api.serializers import (
    GroupCreateSerializer,
    GroupDetailSerializer,
    GroupPublicSerializer,
    JoinRequestSerializer,
    LeaderboardRowSerializer,
    MembershipSerializer,
    RejectSerializer,
    ScheduleSerializer,
    ScheduleWriteSerializer,
    TransferSerializer,
)
from apps.groups.models import Group, JoinRequest
from apps.rbac.permissions import HasPermission


# ---------------------------------------------------------------------------
# Ochiq (autentifikatsiyasiz) — ro'yxatdan o'tish formasi uchun
# ---------------------------------------------------------------------------

class OpenGroupListView(APIView):
    """Ro'yxatdan o'tishda o'quvchi tanlaydigan guruhlar ro'yxati."""

    permission_classes = [AllowAny]

    @extend_schema(responses=GroupPublicSerializer(many=True))
    def get(self, request):
        groups = selectors.get_open_groups()
        data = GroupPublicSerializer(groups, many=True, context={"request": request}).data
        return Response(data)


# ---------------------------------------------------------------------------
# Manager paneli
# ---------------------------------------------------------------------------

class ManagerGroupListCreateView(APIView):
    permission_classes = [IsAuthenticated, HasPermission]
    required_permission = "group.create"

    @extend_schema(responses=GroupDetailSerializer(many=True))
    def get(self, request):
        groups = (
            Group.objects.select_related("course", "mentor")
            .prefetch_related("schedules")
            .order_by("name")
        )
        return Response(GroupDetailSerializer(groups, many=True, context={"request": request}).data)

    @extend_schema(request=GroupCreateSerializer, responses=GroupDetailSerializer)
    def post(self, request):
        serializer = GroupCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payload = serializer.validated_data

        course = get_object_or_404(Course, id=payload["course_id"])
        mentor = None
        if payload.get("mentor_id"):
            mentor = get_object_or_404(User, id=payload["mentor_id"])

        group = services.create_group(
            course=course, name=payload["name"], code=payload["code"],
            manager=request.user, mentor=mentor, capacity=payload["capacity"],
            starts_on=payload.get("starts_on"), ends_on=payload.get("ends_on"),
        )
        return Response(
            GroupDetailSerializer(group, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )


class ManagerGroupScheduleView(APIView):
    """Dars vaqtlarini belgilash — manager vazifasi."""

    permission_classes = [IsAuthenticated, HasPermission]
    required_permission = "lesson.schedule"

    @extend_schema(request=ScheduleWriteSerializer(many=True), responses=ScheduleSerializer(many=True))
    def put(self, request, group_id):
        group = get_object_or_404(Group, id=group_id)
        serializer = ScheduleWriteSerializer(data=request.data, many=True)
        serializer.is_valid(raise_exception=True)

        services.set_schedule(group=group, slots=serializer.validated_data)
        return Response(ScheduleSerializer(group.schedules.all(), many=True).data)


class ManagerAssignMentorView(APIView):
    permission_classes = [IsAuthenticated, HasPermission]
    required_permission = "group.assign_mentor"

    @extend_schema(responses=GroupDetailSerializer)
    def post(self, request, group_id):
        group = get_object_or_404(Group, id=group_id)
        mentor = get_object_or_404(User, id=request.data.get("mentor_id"))
        services.assign_mentor(group=group, mentor=mentor)
        return Response(GroupDetailSerializer(group, context={"request": request}).data)


# ---------------------------------------------------------------------------
# Mentor paneli
# ---------------------------------------------------------------------------

class MentorGroupListView(APIView):
    permission_classes = [IsAuthenticated, HasPermission]
    required_permission = "group.view_own"

    @extend_schema(responses=GroupDetailSerializer(many=True))
    def get(self, request):
        groups = selectors.get_mentor_groups(request.user)
        return Response(GroupDetailSerializer(groups, many=True, context={"request": request}).data)


class MentorGroupMembersView(APIView):
    permission_classes = [IsAuthenticated, HasPermission]
    required_permission = "group.view_own"

    @extend_schema(responses=MembershipSerializer(many=True))
    def get(self, request, group_id):
        group = get_object_or_404(Group, id=group_id, mentor=request.user)
        members = selectors.get_group_members(group)
        return Response(MembershipSerializer(members, many=True).data)


class MentorGroupLeaderboardView(APIView):
    """GET /api/v1/mentor/groups/{group_id}/leaderboard/ — guruh reytingi."""

    permission_classes = [IsAuthenticated, HasPermission]
    required_permission = "group.view_own"

    @extend_schema(responses=LeaderboardRowSerializer(many=True))
    def get(self, request, group_id):
        from apps.groups.leaderboard import get_group_leaderboard

        group = get_object_or_404(Group, id=group_id, mentor=request.user)
        rows = get_group_leaderboard(group)
        return Response(LeaderboardRowSerializer(rows, many=True).data)


class MentorJoinRequestListView(APIView):
    """Tasdiqlash kutilayotgan ro'yxatdan o'tish so'rovlari."""

    permission_classes = [IsAuthenticated, HasPermission]
    required_permission = "student.approve"

    @extend_schema(responses=JoinRequestSerializer(many=True))
    def get(self, request):
        requests_qs = selectors.get_pending_requests_for_mentor(request.user)
        return Response(JoinRequestSerializer(requests_qs, many=True).data)


class MentorApproveView(APIView):
    permission_classes = [IsAuthenticated, HasPermission]
    required_permission = "student.approve"

    @extend_schema(responses=MembershipSerializer)
    def post(self, request, request_id):
        join_request = get_object_or_404(
            JoinRequest.objects.select_related("group", "student"), id=request_id,
        )
        membership = services.approve_join_request(request_obj=join_request, mentor=request.user)
        return Response(MembershipSerializer(membership).data)


class MentorRejectView(APIView):
    permission_classes = [IsAuthenticated, HasPermission]
    required_permission = "student.approve"

    @extend_schema(request=RejectSerializer, responses=JoinRequestSerializer)
    def post(self, request, request_id):
        join_request = get_object_or_404(
            JoinRequest.objects.select_related("group", "student"), id=request_id,
        )
        serializer = RejectSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        updated = services.reject_join_request(
            request_obj=join_request, mentor=request.user,
            note=serializer.validated_data.get("note", ""),
        )
        return Response(JoinRequestSerializer(updated).data)


class MentorTransferView(APIView):
    """O'quvchini boshqa guruhga ko'chirish."""

    permission_classes = [IsAuthenticated, HasPermission]
    required_permission = "student.transfer"

    @extend_schema(request=TransferSerializer, responses=MembershipSerializer)
    def post(self, request):
        serializer = TransferSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payload = serializer.validated_data

        membership = services.transfer_student(
            student=get_object_or_404(User, id=payload["student_id"]),
            from_group=get_object_or_404(Group, id=payload["from_group_id"]),
            to_group=get_object_or_404(Group, id=payload["to_group_id"]),
            mentor=request.user,
        )
        return Response(MembershipSerializer(membership).data)


class MentorRemoveStudentView(APIView):
    permission_classes = [IsAuthenticated, HasPermission]
    required_permission = "student.remove"

    def post(self, request, group_id, student_id):
        services.remove_student(
            student=get_object_or_404(User, id=student_id),
            group=get_object_or_404(Group, id=group_id),
            mentor=request.user,
        )
        return Response(status=status.HTTP_204_NO_CONTENT)


# ---------------------------------------------------------------------------
# O'quvchi
# ---------------------------------------------------------------------------

class MyGroupView(APIView):
    """O'quvchining joriy guruhi va dars jadvali."""

    permission_classes = [IsAuthenticated]

    @extend_schema(responses=GroupDetailSerializer)
    def get(self, request):
        membership = selectors.get_active_membership(request.user)
        if not membership:
            latest = selectors.get_latest_join_request(request.user)
            return Response({
                "group": None,
                "join_request": JoinRequestSerializer(latest).data if latest else None,
            })
        return Response({
            "group": GroupDetailSerializer(membership.group, context={"request": request}).data,
            "join_request": None,
        })


class MyLeaderboardView(APIView):
    """GET /api/v1/groups/leaderboard/ — o'quvchining o'z guruhi reytingi."""

    permission_classes = [IsAuthenticated]

    @extend_schema(responses=LeaderboardRowSerializer(many=True))
    def get(self, request):
        from apps.groups.leaderboard import get_group_leaderboard

        membership = selectors.get_active_membership(request.user)
        if not membership:
            return Response({"group_name": None, "results": []})

        rows = get_group_leaderboard(membership.group)
        return Response({
            "group_name": membership.group.name,
            "results": LeaderboardRowSerializer(rows, many=True).data,
        })
