from django.urls import path

from apps.assignments.api import views

urlpatterns = [
    path("<uuid:lesson_id>/submissions/", views.HomeworkSubmitView.as_view(), name="homework-submit"),
    path("mentor/queue/", views.MentorQueueView.as_view(), name="mentor-queue"),
    path("submissions/<uuid:submission_id>/grade/", views.SubmissionGradeView.as_view(), name="submission-grade"),
    path("courses/<uuid:course_id>/gradebook/", views.GradebookView.as_view(), name="gradebook"),
]
