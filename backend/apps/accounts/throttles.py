from rest_framework.throttling import SimpleRateThrottle


class OTPRequestThrottle(SimpleRateThrottle):
    """A-04: 1 raqamga soatiga maksimal 3 ta SMS."""

    scope = "otp"

    def get_cache_key(self, request, view):
        phone = request.data.get("phone", "") if hasattr(request, "data") else ""
        ident = phone or self.get_ident(request)
        return self.cache_format % {"scope": self.scope, "ident": ident}
