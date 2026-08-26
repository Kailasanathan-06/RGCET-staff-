"""Project-level views (error handlers)."""
import traceback
from django.shortcuts import render


def error_500(request):
    """500 handler — logs the traceback and shows a helpful page."""
    try:
        tb = traceback.format_exc()
    except Exception:
        tb = 'No traceback available'
    return render(request, 'errors/500.html', {'traceback': tb}, status=500)
