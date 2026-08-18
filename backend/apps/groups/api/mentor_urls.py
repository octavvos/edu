"""Mentor paneli: /api/v1/mentor/"""

from django.urls import path

from apps.groups.api import views

urlpatterns = [
    path("groups/", views.MentorGroupListView.as_view(), name="mentor-groups"),
    path("groups/<uuid:group_id>/members/", views.MentorGroupMembersView.as_view(),
         name="mentor-group-members"),
    path("groups/<uuid:group_id>/students/<uuid:student_id>/remove/",
         views.MentorRemoveStudentView.as_view(), name="mentor-remove-student"),
    path("requests/", views.MentorJoinRequestListView.as_view(), name="mentor-requests"),
    path("requests/<uuid:request_id>/approve/", views.MentorApproveView.as_view(),
         name="mentor-approve"),
    path("requests/<uuid:request_id>/reject/", views.MentorRejectView.as_view(),
         name="mentor-reject"),
    path("transfer/", views.MentorTransferView.as_view(), name="mentor-transfer"),
]
