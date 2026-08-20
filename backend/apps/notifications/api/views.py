from django.utils.dateparse import parse_datetime
from drf_spectacular.utils import extend_schema
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.notifications.api.serializers import NotificationDispatchSerializer
from apps.notifications.models import NotificationChannel, NotificationDispatch

RECENT_LIMIT = 20
POLL_LIMIT = 50


class MyNotificationsView(APIView):
    """
    GET /api/v1/notifications/mine/ — o'z in-app bildirishnomalari, frontend
    tomonidan davriy so'rov (polling) uchun.

    `?since=<ISO vaqt>` berilsa — shu vaqtdan keyingi yangilarini (eskisidan
    yangisiga qarab) qaytaradi. Berilmasa — so'nggi bir nechtasini tarix
    sifatida (eskisidan yangisiga qarab) qaytaradi.
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(responses=NotificationDispatchSerializer(many=True))
    def get(self, request):
        base = NotificationDispatch.objects.filter(
            user=request.user, channel=NotificationChannel.IN_APP,
        )

        since = parse_datetime(request.query_params.get("since") or "")
        if since:
            rows = list(base.filter(created_at__gt=since).order_by("created_at")[:POLL_LIMIT])
        else:
            rows = list(base.order_by("-created_at")[:RECENT_LIMIT])[::-1]

        return Response(NotificationDispatchSerializer(rows, many=True).data)
