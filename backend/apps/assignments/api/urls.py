from django.urls import path

from apps.assignments.api import views

urlpatterns = [
    path("<uuid:lesson_id>/submissions/", views.HomeworkSubmitView.as_view(), name="homework-submit"),
    path("courses/<uuid:course_id>/gradebook/", views.GradebookView.as_view(), name="gradebook"),
    # Mentor endpointlari /api/v1/mentor/ ostida (apps.groups.api.mentor_urls) —
    # bitta panel, bitta manzil prefiksi.
]
