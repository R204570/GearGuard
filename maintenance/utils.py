"""
Utility functions for role-based authentication.
"""
from django.shortcuts import redirect
from django.urls import reverse_lazy


def get_role_redirect_url(role):
    """
    Get redirect URL based on user role.
    
    Args:
        role: User role string ('Admin', 'Manager', 'Technician', 'User')
    
    Returns:
        URL string for redirect
    """
    role_redirects = {
        'Admin': '/admin/dashboard/',
        'Manager': '/manager/dashboard/',
        'Technician': '/technician/dashboard/',
        'User': '/user/dashboard/',
    }
    
    return role_redirects.get(role, '/manager/dashboard/')


def get_user_role(user):
    """
    Get user role from profile.
    
    Args:
        user: Django User instance
    
    Returns:
        Role string or None if profile doesn't exist
    """
    try:
        return user.profile.role
    except AttributeError:
        return None


def has_role(user, *roles):
    """
    Check if user has any of the specified roles.
    
    Args:
        user: Django User instance
        *roles: Variable number of role strings to check
    
    Returns:
        True if user has any of the specified roles, False otherwise
    """
    user_role = get_user_role(user)
    return user_role in roles

