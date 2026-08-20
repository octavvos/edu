from django.urls import path

from apps.assessments.api import views

urlpatterns = [
    path("mine/", views.MyQuizzesView.as_view(), name="my-quizzes"),
    path("quizzes/<uuid:lesson_id>/start/", views.QuizStartView.as_view(), name="quiz-start"),
    path("attempts/", views.AttemptListView.as_view(), name="attempt-list"),
    path("attempts/<uuid:attempt_id>/answer/", views.QuizAnswerView.as_view(), name="quiz-answer"),
    path("attempts/<uuid:attempt_id>/submit/", views.QuizSubmitView.as_view(), name="quiz-submit"),
]
