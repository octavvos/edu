"""Mentor paneli: /api/v1/mentor/"""

from django.urls import path

from apps.assignments.api import views as assignment_views
from apps.groups.api import views

urlpatterns = [
    # Uy vazifalari boshqaruvi (apps.assignments)
    path("submissions/", assignment_views.MentorQueueView.as_view(), name="mentor-submissions"),
    path("submissions/<uuid:submission_id>/status/", assignment_views.SubmissionStatusView.as_view(),
         name="mentor-submission-status"),
    path("submissions/<uuid:submission_id>/grade/", assignment_views.SubmissionGradeView.as_view(),
         name="mentor-submission-grade"),
    # O'quvchilar monitoringi
    path("students/", assignment_views.MentorStudentsView.as_view(), name="mentor-students"),
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
