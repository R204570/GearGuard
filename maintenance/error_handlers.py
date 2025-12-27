"""
Custom error handlers for GearGuard application.
"""
from django.shortcuts import render


def handler404(request, exception):
    """Custom 404 error handler."""
    context = {
        'user': request.user if hasattr(request, 'user') else None,
    }
    return render(request, '404.html', context, status=404)


def handler500(request):
    """Custom 500 error handler."""
    return render(request, '500.html', status=500)


def handler403(request, exception):
    """Custom 403 error handler."""
    return render(request, '403.html', status=403)


def handler400(request, exception):
    """Custom 400 error handler."""
    return render(request, '400.html', status=400)

