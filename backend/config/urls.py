from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView

urlpatterns = [
    path("admin/", admin.site.urls),
    # TZ 5.6 — API hujjati
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/schema/swagger-ui/", SpectacularSwaggerView.as_view(url_name="schema")),
    path("api/schema/redoc/", SpectacularRedocView.as_view(url_name="schema")),
    # TZ 5.6 — Endpoint guruhlari, barchasi /api/v1/ ostida (D-09)
    path("api/v1/auth/", include("apps.accounts.api.auth_urls")),
    path("api/v1/me/", include("apps.accounts.api.me_urls")),
    path("api/v1/catalog/", include("apps.catalog.api.urls")),
    path("api/v1/courses/", include("apps.courses.api.urls")),
    path("api/v1/courses/", include("apps.communication.api.urls")),  # N-01: dars ostida izoh/Q&A
    path("api/v1/groups/", include("apps.groups.api.urls")),
    path("api/v1/manager/", include("apps.groups.api.manager_urls")),
    path("api/v1/mentor/", include("apps.groups.api.mentor_urls")),
    path("api/v1/learn/", include("apps.enrollment.api.urls")),
    path("api/v1/assessments/", include("apps.assessments.api.urls")),
    path("api/v1/assignments/", include("apps.assignments.api.urls")),
    path("api/v1/certificates/", include("apps.certificates.api.urls")),
    path("api/v1/notifications/", include("apps.notifications.api.urls")),
    path("api/v1/payments/", include("apps.payments.api.urls")),
    path("api/v1/teacher/", include("apps.courses.api.teacher_urls")),
    path("api/v1/admin/", include("apps.audit.api.urls")),
    path("verify/", include("apps.certificates.api.verify_urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
