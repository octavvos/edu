from django.urls import path

from apps.courses.api import views

urlpatterns = [
    path("<slug:slug>/", views.CourseDetailView.as_view(), name="course-detail"),
    path("<slug:slug>/preview/", views.CoursePreviewView.as_view(), name="course-preview"),
    path("<slug:slug>/enroll/", views.CourseEnrollView.as_view(), name="course-enroll"),
]
