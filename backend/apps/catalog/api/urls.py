from django.urls import path

from apps.catalog.api import views

urlpatterns = [
    path("categories/", views.CategoryListView.as_view(), name="catalog-categories"),
    path("courses/", views.CourseSearchView.as_view(), name="catalog-course-search"),
    path("courses/<uuid:course_id>/recommendations/", views.RecommendationsView.as_view(), name="catalog-recommendations"),
    path("courses/<uuid:course_id>/reviews/", views.CourseReviewListCreateView.as_view(), name="catalog-reviews"),
]
