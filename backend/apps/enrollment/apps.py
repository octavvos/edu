from django.apps import AppConfig


class EnrollmentConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.enrollment"
    label = "enrollment"

    def ready(self):
        from apps.enrollment import handlers  # noqa: F401
