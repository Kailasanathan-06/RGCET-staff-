"""
Audit middleware — auto-captures IP and attaches profile to request.
This runs on every request so views don't need to look up the profile manually.
"""
from django.utils.functional import SimpleLazyObject


def get_client_ip(request):
    """Extract real IP even behind proxy/load balancer."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '')


class AuditMiddleware:
    """
    Attaches:
        request.client_ip    — real client IP address
        request.user_agent   — browser user agent
        request.profile      — StaffProfile (if authenticated, else None)

    Also logs LOGIN / LOGOUT via signal in accounts/signals.py (not here).
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Attach IP and user agent to every request
        request.client_ip = get_client_ip(request)
        request.user_agent = request.META.get('HTTP_USER_AGENT', '')[:500]

        # Attach profile lazily (avoids DB hit on anonymous requests)
        def get_profile():
            if request.user.is_authenticated and hasattr(request.user, 'profile'):
                return request.user.profile
            return None

        request.profile = SimpleLazyObject(get_profile)

        response = self.get_response(request)
        return response
