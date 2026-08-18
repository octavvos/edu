"""Ochiq + o'quvchi uchun guruh endpointlari: /api/v1/groups/"""

from django.urls import path

from apps.groups.api import views

urlpatterns = [
    # Ro'yxatdan o'tish formasi uchun (autentifikatsiyasiz)
    path("open/", views.OpenGroupListView.as_view(), name="groups-open"),
    # O'quvchining o'z guruhi
    path("my/", views.MyGroupView.as_view(), name="groups-my"),
    path("leaderboard/", views.MyLeaderboardView.as_view(), name="groups-leaderboard"),
]
