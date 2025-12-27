"""
Role-based decorators for protecting views.
"""
from functools import wraps
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied


def role_required(*allowed_roles):
    """
    Decorator to restrict access to views based on user role.
    
    Usage:
        @role_required('Admin', 'Manager')
        def my_view(request):
            ...
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('maintenance:login')
            
            # Get user role from profile
            try:
                user_role = request.user.profile.role
            except AttributeError:
                raise PermissionDenied("User profile not found. Please contact administrator.")
            
            # Check if user's role is in allowed roles
            if user_role not in allowed_roles:
                raise PermissionDenied(f"Access denied. Required roles: {', '.join(allowed_roles)}")
            
            return view_func(request, *args, **kwargs)
        return wrapped_view
    return decorator


def admin_required(view_func):
    """Decorator to restrict access to Admin role only."""
    return role_required('Admin')(view_func)


def manager_required(view_func):
    """Decorator to restrict access to Manager role only."""
    return role_required('Manager')(view_func)


def technician_required(view_func):
    """Decorator to restrict access to Technician role only."""
    return role_required('Technician')(view_func)


def user_required(view_func):
    """Decorator to restrict access to User role only."""
    return role_required('User')(view_func)


def admin_or_manager_required(view_func):
    """Decorator to restrict access to Admin or Manager roles."""
    return role_required('Admin', 'Manager')(view_func)

