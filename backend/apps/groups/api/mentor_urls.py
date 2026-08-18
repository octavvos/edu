"""Mentor paneli: /api/v1/mentor/"""

from django.urls import path

from apps.assessments.api import mentor_views as quiz_views
from apps.assignments.api import views as assignment_views
from apps.courses.api import mentor_views as content_views
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
    # Kurs kontenti: modul/dars/material (apps.courses)
    path("courses/", content_views.MentorCourseListView.as_view(), name="mentor-courses"),
    path("courses/<uuid:course_id>/modules/", content_views.MentorModuleCreateView.as_view(),
         name="mentor-course-modules"),
    path("modules/<uuid:module_id>/lessons/", content_views.MentorLessonCreateView.as_view(),
         name="mentor-module-lessons"),
    path("lessons/<uuid:lesson_id>/material/", content_views.MentorMaterialUploadView.as_view(),
         name="mentor-lesson-material"),
    # Testlar (apps.assessments)
    path("lessons/<uuid:lesson_id>/quiz/", quiz_views.MentorQuizCreateView.as_view(),
         name="mentor-lesson-quiz"),
    path("quizzes/<uuid:quiz_id>/", quiz_views.MentorQuizDetailView.as_view(), name="mentor-quiz-detail"),
    path("quizzes/<uuid:quiz_id>/questions/", quiz_views.MentorQuestionListCreateView.as_view(),
         name="mentor-quiz-questions"),
    path("questions/<uuid:question_id>/", quiz_views.MentorQuestionDetailView.as_view(),
         name="mentor-question-detail"),
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
