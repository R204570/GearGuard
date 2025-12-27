"""
Example views demonstrating role-based decorators.
This file shows how to use decorators to protect function-based views.
"""
from django.shortcuts import render
from django.http import HttpResponse
from .decorators import (
    role_required, admin_required, manager_required,
    technician_required, user_required, admin_or_manager_required
)


# Example 1: Single role required
@admin_required
def admin_only_view(request):
    """Only Admin can access this view."""
    return HttpResponse("This is an admin-only page.")


# Example 2: Multiple roles allowed
@role_required('Admin', 'Manager')
def admin_or_manager_view(request):
    """Admin or Manager can access this view."""
    return HttpResponse("This page is accessible to Admin and Manager.")


# Example 3: Using the convenience decorator
@admin_or_manager_required
def reports_view(request):
    """Admin or Manager can access reports."""
    return render(request, 'maintenance/reports.html')


# Example 4: Technician only
@technician_required
def technician_work_view(request):
    """Only Technician can access this view."""
    return HttpResponse("Technician work area.")


# Example 5: User only
@user_required
def user_dashboard_view(request):
    """Only User role can access this view."""
    return render(request, 'maintenance/user_dashboard.html')


# Example 6: Custom role combination
@role_required('Admin', 'Manager', 'Technician')
def staff_view(request):
    """Admin, Manager, or Technician can access."""
    return HttpResponse("Staff area - no regular users allowed.")

