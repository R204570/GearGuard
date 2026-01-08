from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied


class ManagerRequiredMixin(LoginRequiredMixin):
    """Mixin to ensure only users with Manager role can access the view."""
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        
        # Check if user has a profile with Manager role
        try:
            profile = request.user.profile
            if profile.role != 'Manager':
                raise PermissionDenied("Only managers or admin can access this page.")
        except AttributeError:
            raise PermissionDenied("User profile not found. Please contact administrator.")
        
        return super().dispatch(request, *args, **kwargs)


class AdminRequiredMixin(LoginRequiredMixin):
    """Mixin to ensure only users with Admin role can access the view."""
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        
        # Check if user has a profile with Admin role
        try:
            profile = request.user.profile
            if profile.role != 'Admin':
                raise PermissionDenied("Only administrators can access this page.")
        except AttributeError:
            raise PermissionDenied("User profile not found. Please contact administrator.")
        
        return super().dispatch(request, *args, **kwargs)


class TechnicianRequiredMixin(LoginRequiredMixin):
    """Mixin to ensure only users with Technician role can access the view."""
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        
        # Check if user has a profile with Technician role
        try:
            profile = request.user.profile
            if profile.role != 'Technician':
                raise PermissionDenied("Only technicians can access this page.")
        except AttributeError:
            raise PermissionDenied("User profile not found. Please contact administrator.")
        
        return super().dispatch(request, *args, **kwargs)


class UserRequiredMixin(LoginRequiredMixin):
    """Mixin to ensure only users with User role can access the view."""
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        
        # Check if user has a profile with User role
        try:
            profile = request.user.profile
            if profile.role != 'User':
                raise PermissionDenied("Only regular users can access this page.")
        except AttributeError:
            raise PermissionDenied("User profile not found. Please contact administrator.")
        
        return super().dispatch(request, *args, **kwargs)


class AdminOrManagerRequiredMixin(LoginRequiredMixin):
    """Mixin to ensure only users with Admin or Manager role can access the view."""
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        
        # Check if user has a profile with Admin or Manager role
        try:
            profile = request.user.profile
            if profile.role not in ['Admin', 'Manager']:
                raise PermissionDenied("Only administrators and managers can access this page.")
        except AttributeError:
            raise PermissionDenied("User profile not found. Please contact administrator.")
        
        return super().dispatch(request, *args, **kwargs)

