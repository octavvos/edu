from django.urls import path

from apps.enrollment.api import views

urlpatterns = [
    path("<uuid:enrollment_id>/lessons/<uuid:lesson_id>/", views.LessonLearnView.as_view(), name="learn-lesson"),
    path("<uuid:enrollment_id>/lessons/<uuid:lesson_id>/progress/", views.LessonProgressView.as_view(), name="learn-progress"),
    path("<uuid:enrollment_id>/lessons/<uuid:lesson_id>/playback-token/", views.PlaybackTokenView.as_view(), name="learn-playback-token"),
    path("<uuid:enrollment_id>/lessons/<uuid:lesson_id>/notes/", views.LessonNotesView.as_view(), name="learn-notes"),
]
