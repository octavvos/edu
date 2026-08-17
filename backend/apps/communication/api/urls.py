from django.urls import path

from apps.communication.api import views

urlpatterns = [
    path("lessons/<uuid:lesson_id>/comments/", views.LessonCommentsView.as_view(), name="lesson-comments"),
    path("comments/<uuid:comment_id>/helpful/", views.CommentVoteHelpfulView.as_view(), name="comment-helpful"),
]
