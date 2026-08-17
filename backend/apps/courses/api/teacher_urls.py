from django.urls import path
from rest_framework.routers import DefaultRouter

from apps.courses.api.teacher_views import ModerationViewSet, TeacherCourseViewSet
from apps.payouts.api.views import PayoutRequestListCreateView

router = DefaultRouter()
router.register("courses", TeacherCourseViewSet, basename="teacher-course")
router.register("moderation", ModerationViewSet, basename="course-moderation")

urlpatterns = [
    path("payouts/", PayoutRequestListCreateView.as_view(), name="teacher-payouts"),
    *router.urls,
]
