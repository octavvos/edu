"""
So'rov konteksti (actor, IP, user-agent) ni thread-local'da saqlaydi,
shunda services.py qatlami (masalan AuditLog yozuvchi kod) request
obyektini har joyga uzatib yurmasdan "kim qildi"ni bilishi mumkin.

A-10: barcha kirish urinishlari IP va User-Agent bilan logga yoziladi.
"""

import threading

_local = threading.local()


def get_current_actor():
    return getattr(_local, "user", None)


def get_current_ip():
    return getattr(_local, "ip", None)


def get_current_user_agent():
    return getattr(_local, "user_agent", None)


def _client_ip(request) -> str:
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "")


class RequestContextMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        _local.user = getattr(request, "user", None)
        _local.ip = _client_ip(request)
        _local.user_agent = request.META.get("HTTP_USER_AGENT", "")
        try:
            response = self.get_response(request)
        finally:
            _local.user = None
            _local.ip = None
            _local.user_agent = None
        return response
