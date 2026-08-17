from apps.audit.middleware import get_current_ip, get_current_user_agent
from apps.audit.models import AuditLog


def log_action(*, actor, action: str, obj, before: dict | None = None, after: dict | None = None):
    """Har qanday admin/moderatsiya amalidan keyin chaqiriladi (AD-08)."""
    return AuditLog.objects.create(
        actor=actor if actor and actor.is_authenticated else None,
        action=action,
        object_type=obj.__class__.__name__,
        object_id=str(obj.pk),
        before=before,
        after=after,
        ip_address=get_current_ip(),
        user_agent=get_current_user_agent() or "",
    )
