"""
RFC 7807 (Problem Details) xato formati — TZ 5.6:
    {"type", "title", "status", "detail", "errors": []}
"""

from rest_framework.views import exception_handler as drf_exception_handler


class DomainError(Exception):
    """services.py qatlamida ko'tariladigan biznes-logika xatosi."""

    def __init__(self, detail: str, code: str = "domain_error", status_code: int = 400):
        self.detail = detail
        self.code = code
        self.status_code = status_code
        super().__init__(detail)


def _flatten_errors(detail, field=None):
    errors = []
    if isinstance(detail, dict):
        for key, value in detail.items():
            errors.extend(_flatten_errors(value, field=key))
    elif isinstance(detail, list):
        for item in detail:
            errors.extend(_flatten_errors(item, field=field))
    else:
        errors.append({"field": field, "message": str(detail)})
    return errors


def rfc7807_exception_handler(exc, context):
    response = drf_exception_handler(exc, context)
    if response is None:
        return None

    title = getattr(exc, "default_detail", exc.__class__.__name__)
    problem = {
        "type": f"https://api.edu-platform.local/errors/{exc.__class__.__name__.lower()}",
        "title": str(title) if not isinstance(title, (list, dict)) else exc.__class__.__name__,
        "status": response.status_code,
        "detail": response.data if isinstance(response.data, str) else "",
        "errors": _flatten_errors(response.data),
    }
    response.data = problem
    return response
