"""Manager paneli: /api/v1/manager/"""

from django.urls import path

from apps.groups.api import views

urlpatterns = [
    path("groups/", views.ManagerGroupListCreateView.as_view(), name="manager-groups"),
    path("groups/<uuid:group_id>/schedule/", views.ManagerGroupScheduleView.as_view(),
         name="manager-group-schedule"),
    path("groups/<uuid:group_id>/mentor/", views.ManagerAssignMentorView.as_view(),
         name="manager-group-mentor"),
]
