from django.views.generic import TemplateView, ListView, CreateView, UpdateView, DeleteView
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.auth.views import LoginView
from django.contrib.auth import logout
from django.contrib.auth.models import User
from django.db.models import Count, Q, Avg, Sum
from django.utils import timezone
from datetime import datetime, timedelta
from calendar import monthrange
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

from .models import MaintenanceRequest, Equipment, MaintenanceTeam, TeamMember, UserRegistration, UserProfile
from .forms import PreventiveMaintenanceForm, MaintenanceRequestUpdateForm, EquipmentForm, TechnicianRequestUpdateForm, UserBreakdownRequestForm, UserSignupForm, TeamForm
from .mixins import ManagerRequiredMixin, AdminRequiredMixin, TechnicianRequiredMixin, UserRequiredMixin, AdminOrManagerRequiredMixin


class CustomLoginView(LoginView):
    """Custom login view for GearGuard with role-based redirect."""
    template_name = 'maintenance/login.html'
    redirect_authenticated_user = True

    def get_success_url(self):
        """Redirect user based on their role after successful login."""
        user = self.request.user
        
        # Get user role from profile
        try:
            role = user.profile.role
        except AttributeError:
            # If no profile, redirect to login with error
            from django.contrib import messages
            messages.error(self.request, 'User profile not found. Please contact administrator.')
            return reverse_lazy('maintenance:login')
        
        # Role-based redirect URLs
        role_redirects = {
            'Admin': reverse_lazy('maintenance:admin_dashboard'),
            'Manager': reverse_lazy('maintenance:manager_dashboard'),
            'Technician': reverse_lazy('maintenance:technician_dashboard'),
            'User': reverse_lazy('maintenance:user_dashboard'),
        }
        
        # Redirect based on role, default to manager dashboard
        return role_redirects.get(role, reverse_lazy('maintenance:manager_dashboard'))


def logout_view(request):
    """Logout view."""
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('maintenance:login')


class SignupView(CreateView):
    """View for user registration/signup."""
    model = UserRegistration
    form_class = UserSignupForm
    template_name = 'maintenance/signup.html'
    success_url = reverse_lazy('maintenance:signup_success')
    
    def form_valid(self, form):
        messages.success(
            self.request,
            'Your registration request has been submitted successfully! '
            'An administrator will review your request and you will be notified once approved.'
        )
        return super().form_valid(form)


class SignupSuccessView(TemplateView):
    """View shown after successful signup."""
    template_name = 'maintenance/signup_success.html'


class UserRegistrationListView(AdminRequiredMixin, ListView):
    """Admin view to list and manage user registration requests."""
    model = UserRegistration
    template_name = 'maintenance/user_registrations.html'
    context_object_name = 'registrations'
    paginate_by = 20
    ordering = ['-created_at']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        status = self.request.GET.get('status', '')
        if status:
            queryset = queryset.filter(status=status)
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['pending_count'] = UserRegistration.objects.filter(status='Pending').count()
        context['current_status'] = self.request.GET.get('status', '')
        return context


@require_http_methods(["POST"])
def approve_registration(request, pk):
    """Approve a user registration and create the user."""
    if not request.user.is_authenticated or not hasattr(request.user, 'profile') or request.user.profile.role != 'Admin':
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    registration = get_object_or_404(UserRegistration, pk=pk, status='Pending')
    
    try:
        # Check if user already exists
        if User.objects.filter(username=registration.username).exists():
            user = User.objects.get(username=registration.username)
            # User already exists, just update the profile role
            profile, created = UserProfile.objects.get_or_create(
                user=user,
                defaults={'role': registration.requested_role}
            )
            if not created:
                # Profile already exists, just update the role
                profile.role = registration.requested_role
                profile.save()
            
            # Update registration
            registration.status = 'Approved'
            registration.approved_by = request.user
            registration.approved_at = timezone.now()
            registration.save()
            
            messages.success(request, f'User "{registration.username}" already exists. Profile role updated to {registration.requested_role}.')
            return JsonResponse({'success': True, 'message': 'User already exists. Profile role updated.'})
        
        # Check if email already exists
        if User.objects.filter(email=registration.email).exists():
            return JsonResponse({'error': f'Email "{registration.email}" is already registered to another user.'}, status=400)
        
        # Create new user (signal will automatically create UserProfile with default role='User')
        user = User.objects.create_user(
            username=registration.username,
            email=registration.email,
            password=registration.password,
            first_name=registration.first_name,
            last_name=registration.last_name
        )
        
        # Update the profile that was created by the signal with the requested role
        profile, created = UserProfile.objects.get_or_create(
            user=user,
            defaults={'role': registration.requested_role}
        )
        if not created:
            # Profile already exists (created by signal), just update the role
            profile.role = registration.requested_role
            profile.save()
        
        # Update registration
        registration.status = 'Approved'
        registration.approved_by = request.user
        registration.approved_at = timezone.now()
        registration.save()
        
        messages.success(request, f'User "{registration.username}" has been approved and created successfully.')
        return JsonResponse({'success': True, 'message': 'User approved and created successfully'})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@require_http_methods(["POST"])
def reject_registration(request, pk):
    """Reject a user registration."""
    if not request.user.is_authenticated or not hasattr(request.user, 'profile') or request.user.profile.role != 'Admin':
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    registration = get_object_or_404(UserRegistration, pk=pk, status='Pending')
    rejection_reason = request.POST.get('rejection_reason', '')
    
    registration.status = 'Rejected'
    registration.rejection_reason = rejection_reason
    registration.approved_by = request.user
    registration.approved_at = timezone.now()
    registration.save()
    
    messages.success(request, f'Registration request for "{registration.username}" has been rejected.')
    return JsonResponse({'success': True, 'message': 'Registration rejected'})


@require_http_methods(["GET"])
def get_equipment_data(request, pk):
    """Get equipment data for auto-fill functionality."""
    equipment = get_object_or_404(Equipment, pk=pk)
    next_maintenance_date = equipment.get_next_maintenance_date()
    return JsonResponse({
        'category': equipment.category,
        'maintenance_team_id': equipment.maintenance_team.id if equipment.maintenance_team else None,
        'maintenance_team_name': equipment.maintenance_team.team_name if equipment.maintenance_team else None,
        'default_technician_id': equipment.default_technician.id if equipment.default_technician else None,
        'maintenance_interval_days': equipment.maintenance_interval_days,
        'next_maintenance_date': next_maintenance_date.strftime('%Y-%m-%d') if next_maintenance_date else None,
    })


@require_http_methods(["POST"])
def start_task(request, pk):
    """Start a task - set stage to In Progress and record start time."""
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)
    
    request_obj = get_object_or_404(MaintenanceRequest, pk=pk)
    
    # Check if user is assigned technician or in the team
    user = request.user
    technician_teams = MaintenanceTeam.objects.filter(members__user=user).distinct()
    
    if request_obj.assigned_technician != user and request_obj.maintenance_team not in technician_teams:
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    # Start the task
    request_obj.stage = 'In Progress'
    request_obj.actual_start_time = timezone.now()
    if not request_obj.assigned_technician:
        request_obj.assigned_technician = user
    request_obj.save()
    
    return JsonResponse({
        'success': True,
        'message': 'Task started successfully',
        'start_time': request_obj.actual_start_time.isoformat()
    })


@require_http_methods(["POST"])
def end_task(request, pk):
    """End a task - calculate duration and mark as Repaired."""
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)
    
    request_obj = get_object_or_404(MaintenanceRequest, pk=pk)
    
    # Check if user is assigned technician
    if request_obj.assigned_technician != request.user:
        return JsonResponse({'error': 'Only assigned technician can end this task'}, status=403)
    
    # Check if task was started
    if not request_obj.actual_start_time:
        return JsonResponse({'error': 'Task must be started before it can be ended'}, status=400)
    
    # End the task and calculate duration
    request_obj.actual_end_time = timezone.now()
    time_diff = request_obj.actual_end_time - request_obj.actual_start_time
    duration_hours = time_diff.total_seconds() / 3600
    request_obj.duration_hours = round(duration_hours, 2)
    request_obj.stage = 'Repaired'
    request_obj.completed_date = timezone.now().date()
    request_obj.save()
    
    return JsonResponse({
        'success': True,
        'message': 'Task completed successfully',
        'duration_hours': request_obj.duration_hours,
        'end_time': request_obj.actual_end_time.isoformat()
    })


class TechnicianReportsView(TechnicianRequiredMixin, ListView):
    """View for technicians to see their past completed tasks/reports."""
    model = MaintenanceRequest
    template_name = 'maintenance/technician_reports.html'
    context_object_name = 'reports'
    paginate_by = 20
    
    def get_queryset(self):
        user = self.request.user
        return MaintenanceRequest.objects.filter(
            assigned_technician=user,
            stage='Repaired',
            duration_hours__isnull=False
        ).select_related(
            'equipment', 'maintenance_team', 'created_by'
        ).order_by('-completed_date', '-actual_end_time')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Statistics
        total_tasks = MaintenanceRequest.objects.filter(
            assigned_technician=user,
            stage='Repaired'
        ).count()
        
        total_hours = MaintenanceRequest.objects.filter(
            assigned_technician=user,
            duration_hours__isnull=False
        ).aggregate(total=Sum('duration_hours'))['total'] or 0
        
        avg_duration = MaintenanceRequest.objects.filter(
            assigned_technician=user,
            duration_hours__isnull=False
        ).aggregate(avg=Avg('duration_hours'))['avg'] or 0
        
        context.update({
            'total_tasks': total_tasks,
            'total_hours': round(total_hours, 2),
            'avg_duration': round(avg_duration, 2),
        })
        
        return context


class ManagerTechnicianReportsView(AdminOrManagerRequiredMixin, ListView):
    """View for managers and admins to see all technician reports."""
    model = MaintenanceRequest
    template_name = 'maintenance/manager_technician_reports.html'
    context_object_name = 'reports'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = MaintenanceRequest.objects.filter(
            stage='Repaired',
            duration_hours__isnull=False,
            assigned_technician__isnull=False
        ).select_related(
            'equipment', 'maintenance_team', 'assigned_technician', 'created_by'
        ).order_by('-completed_date', '-actual_end_time')
        
        # Filter by technician if provided
        technician_id = self.request.GET.get('technician')
        if technician_id:
            queryset = queryset.filter(assigned_technician_id=technician_id)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get all technicians who have completed tasks
        from django.contrib.auth.models import User
        technicians = User.objects.filter(
            profile__role='Technician',
            assigned_requests__stage='Repaired',
            assigned_requests__duration_hours__isnull=False
        ).distinct().annotate(
            total_tasks=Count('assigned_requests', filter=Q(assigned_requests__stage='Repaired')),
            total_hours=Sum('assigned_requests__duration_hours', filter=Q(assigned_requests__stage='Repaired'))
        )
        
        context['technicians'] = technicians
        context['selected_technician'] = self.request.GET.get('technician', '')
        
        return context


class AdminManagerHoursView(AdminRequiredMixin, TemplateView):
    """View for admin to see hours spent by managers on tasks."""
    template_name = 'maintenance/admin_manager_hours.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        from django.contrib.auth.models import User
        
        # Get managers and their task hours
        managers = User.objects.filter(
            profile__role='Manager'
        ).annotate(
            total_requests_created=Count('created_requests'),
            total_hours_managed=Sum('created_requests__duration_hours', filter=Q(created_requests__stage='Repaired')),
            completed_requests=Count('created_requests', filter=Q(created_requests__stage='Repaired'))
        ).order_by('-total_hours_managed')
        
        # Overall statistics
        total_manager_hours = MaintenanceRequest.objects.filter(
            created_by__profile__role='Manager',
            stage='Repaired',
            duration_hours__isnull=False
        ).aggregate(total=Sum('duration_hours'))['total'] or 0
        
        context.update({
            'managers': managers,
            'total_manager_hours': round(total_manager_hours, 2),
        })
        
        return context


class ManagerDashboardView(ManagerRequiredMixin, TemplateView):
    """Main dashboard view for managers with summary statistics."""
    template_name = 'maintenance/manager_dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Summary statistics
        total_equipment = Equipment.objects.filter(is_scrapped=False).count()
        open_requests = MaintenanceRequest.objects.exclude(
            stage__in=['Repaired', 'Scrap']
        ).count()
        overdue_requests = MaintenanceRequest.objects.filter(
            is_overdue=True
        ).exclude(stage__in=['Repaired', 'Scrap']).count()
        
        # Upcoming preventive maintenance (next 30 days)
        upcoming_date = timezone.now().date() + timedelta(days=30)
        upcoming_preventive = MaintenanceRequest.objects.filter(
            request_type='Preventive',
            scheduled_date__lte=upcoming_date,
            scheduled_date__gte=timezone.now().date()
        ).exclude(stage__in=['Repaired', 'Scrap']).count()
        
        context.update({
            'total_equipment': total_equipment,
            'open_requests': open_requests,
            'overdue_requests': overdue_requests,
            'upcoming_preventive': upcoming_preventive,
        })
        
        return context


class MaintenanceRequestListView(AdminOrManagerRequiredMixin, ListView):
    """List view for all maintenance requests with filtering."""
    model = MaintenanceRequest
    template_name = 'maintenance/request_list.html'
    context_object_name = 'requests'
    paginate_by = 20

    def get_queryset(self):
        queryset = MaintenanceRequest.objects.select_related(
            'equipment', 'maintenance_team', 'assigned_technician', 'created_by'
        ).order_by('-created_at')
        
        # Filter by status
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(stage=status)
        
        # Filter by team
        team_id = self.request.GET.get('team')
        if team_id:
            queryset = queryset.filter(maintenance_team_id=team_id)
        
        # Filter by equipment (for smart button)
        equipment_id = self.request.GET.get('equipment')
        if equipment_id:
            queryset = queryset.filter(equipment_id=equipment_id)
        
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['teams'] = MaintenanceTeam.objects.filter(is_active=True)
        context['status_choices'] = MaintenanceRequest.STAGE_CHOICES
        context['current_status'] = self.request.GET.get('status', '')
        context['current_team'] = self.request.GET.get('team', '')
        
        # Get equipment if filtering by equipment
        equipment_id = self.request.GET.get('equipment')
        if equipment_id:
            try:
                from .models import Equipment
                context['filtered_equipment'] = Equipment.objects.get(pk=equipment_id)
            except Equipment.DoesNotExist:
                pass
        
        return context


class MaintenanceRequestUpdateView(AdminOrManagerRequiredMixin, UpdateView):
    """View to update maintenance request (assign technician, change status)."""
    model = MaintenanceRequest
    form_class = MaintenanceRequestUpdateForm
    template_name = 'maintenance/request_update.html'
    success_url = reverse_lazy('maintenance:request_list')

    def form_valid(self, form):
        request_obj = form.instance
        
        # Auto-set completed_date and calculate duration when marked as Repaired or Scrap
        if request_obj.stage in ['Repaired', 'Scrap']:
            if not request_obj.completed_date:
                request_obj.completed_date = timezone.now().date()
            
            # Set actual_end_time if not already set
            if not request_obj.actual_end_time:
                request_obj.actual_end_time = timezone.now()
            
            # Auto-calculate duration if start time exists and duration not already calculated
            if request_obj.actual_start_time and not request_obj.duration_hours:
                time_diff = request_obj.actual_end_time - request_obj.actual_start_time
                duration_hours = time_diff.total_seconds() / 3600  # Convert to hours
                request_obj.duration_hours = round(duration_hours, 2)
        
        # Auto-set actual_start_time when moving to In Progress
        elif request_obj.stage == 'In Progress' and not request_obj.actual_start_time:
            request_obj.actual_start_time = timezone.now()
        
        messages.success(self.request, f'Maintenance request "{self.object.subject}" updated successfully.')
        return super().form_valid(form)


class PreventiveMaintenanceCreateView(AdminOrManagerRequiredMixin, CreateView):
    """View to create preventive maintenance requests."""
    model = MaintenanceRequest
    form_class = PreventiveMaintenanceForm
    template_name = 'maintenance/preventive_maintenance_form.html'
    success_url = reverse_lazy('maintenance:preventive_maintenance')

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        form.instance.request_type = 'Preventive'
        messages.success(self.request, 'Preventive maintenance request created successfully.')
        return super().form_valid(form)


class PreventiveMaintenanceCalendarView(AdminOrManagerRequiredMixin, TemplateView):
    """Calendar view for preventive maintenance requests."""
    template_name = 'maintenance/preventive_calendar.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get year and month from request or use current
        year = int(self.request.GET.get('year', timezone.now().year))
        month = int(self.request.GET.get('month', timezone.now().month))
        
        # Get all preventive maintenance for the month
        start_date = datetime(year, month, 1).date()
        _, last_day = monthrange(year, month)
        end_date = datetime(year, month, last_day).date()
        
        # Get explicitly scheduled preventive requests
        preventive_requests = MaintenanceRequest.objects.filter(
            request_type='Preventive',
            scheduled_date__gte=start_date,
            scheduled_date__lte=end_date
        ).exclude(stage__in=['Repaired', 'Scrap']).select_related(
            'equipment', 'maintenance_team', 'assigned_technician'
        ).order_by('scheduled_date')
        
        # Get equipment with maintenance intervals and calculate next maintenance dates
        equipment_with_intervals = Equipment.objects.filter(
            maintenance_interval_days__gt=0,
            is_scrapped=False
        ).select_related('maintenance_team', 'default_technician')
        
        # Create a dictionary to hold all maintenance items by date
        requests_by_date = {}
        
        # Add explicitly scheduled preventive requests
        for request in preventive_requests:
            date_key = request.scheduled_date.strftime('%Y-%m-%d')
            if date_key not in requests_by_date:
                requests_by_date[date_key] = []
            requests_by_date[date_key].append({
                'type': 'scheduled',
                'subject': request.subject,
                'equipment_name': request.equipment.equipment_name,
                'assigned_technician': request.assigned_technician,
                'pk': request.pk,
                'date': request.scheduled_date,
            })
        
        # Add recurring maintenance dates from equipment intervals
        for equipment in equipment_with_intervals:
            # Get the starting point for calculating recurring dates
            next_maintenance_date = equipment.get_next_maintenance_date()
            
            if next_maintenance_date and next_maintenance_date <= end_date:
                # Generate all recurring maintenance dates within the month
                current_date = next_maintenance_date
                interval_days = equipment.maintenance_interval_days
                
                # Continue generating dates while within the month
                while current_date <= end_date:
                    # Check if there's already a completed or scheduled request for this date
                    existing_request = MaintenanceRequest.objects.filter(
                        equipment=equipment,
                        request_type='Preventive',
                        scheduled_date=current_date
                    ).exclude(stage__in=['Scrap']).first()
                    
                    # Only add if no existing request on this date
                    if not existing_request:
                        date_key = current_date.strftime('%Y-%m-%d')
                        if date_key not in requests_by_date:
                            requests_by_date[date_key] = []
                        requests_by_date[date_key].append({
                            'type': 'interval',
                            'subject': f'Preventive Maintenance - {equipment.equipment_name}',
                            'equipment_name': equipment.equipment_name,
                            'assigned_technician': equipment.default_technician,
                            'pk': None,
                            'date': current_date,
                        })
                    
                    # Move to next occurrence
                    current_date += timedelta(days=interval_days)
        
        # Build calendar grid
        first_day = datetime(year, month, 1)
        first_weekday = first_day.weekday()  # 0 = Monday, 6 = Sunday
        calendar_days = []
        
        # Add empty cells for days before month starts
        for _ in range(first_weekday):
            calendar_days.append(None)
        
        # Add days of the month
        for day in range(1, last_day + 1):
            date_obj = datetime(year, month, day).date()
            date_key = date_obj.strftime('%Y-%m-%d')
            calendar_days.append({
                'date': date_obj,
                'day': day,
                'requests': requests_by_date.get(date_key, [])
            })
        
        # Calculate previous and next month
        if month == 1:
            prev_month = 12
            prev_year = year - 1
        else:
            prev_month = month - 1
            prev_year = year
        
        if month == 12:
            next_month = 1
            next_year = year + 1
        else:
            next_month = month + 1
            next_year = year
        
        context.update({
            'year': year,
            'month': month,
            'month_name': datetime(year, month, 1).strftime('%B'),
            'calendar_days': calendar_days,
            'prev_year': prev_year,
            'prev_month': prev_month,
            'next_year': next_year,
            'next_month': next_month,
            'today': timezone.now().date(),
        })
        
        return context


class AdminDashboardView(AdminRequiredMixin, TemplateView):
    """Admin dashboard view with system summary statistics."""
    template_name = 'maintenance/admin_dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Summary statistics
        total_equipment = Equipment.objects.count()
        total_requests = MaintenanceRequest.objects.count()
        active_teams = MaintenanceTeam.objects.filter(is_active=True).count()
        scrapped_equipment = Equipment.objects.filter(is_scrapped=True).count()
        
        # Additional statistics
        open_requests = MaintenanceRequest.objects.exclude(
            stage__in=['Repaired', 'Scrap']
        ).count()
        overdue_requests = MaintenanceRequest.objects.filter(
            is_overdue=True
        ).exclude(stage__in=['Repaired', 'Scrap']).count()
        total_users = User.objects.count()
        
        context.update({
            'total_equipment': total_equipment,
            'total_requests': total_requests,
            'active_teams': active_teams,
            'scrapped_equipment': scrapped_equipment,
            'open_requests': open_requests,
            'overdue_requests': overdue_requests,
            'total_users': total_users,
        })
        
        return context


class EquipmentManagementView(AdminOrManagerRequiredMixin, ListView):
    """Equipment management view for admins and managers."""
    model = Equipment
    template_name = 'maintenance/admin_equipment.html'
    context_object_name = 'equipment_list'
    paginate_by = 20
    ordering = ['equipment_name']

    def get_queryset(self):
        queryset = super().get_queryset().select_related(
            'maintenance_team', 'assigned_to_user', 'default_technician'
        )
        
        # Filter by category if provided
        category = self.request.GET.get('category')
        if category:
            queryset = queryset.filter(category=category)
        
        # Filter by scrapped status
        scrapped = self.request.GET.get('scrapped')
        if scrapped == 'true':
            queryset = queryset.filter(is_scrapped=True)
        elif scrapped == 'false':
            queryset = queryset.filter(is_scrapped=False)
        
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Get unique categories for filter
        context['categories'] = Equipment.objects.values_list(
            'category', flat=True
        ).distinct().order_by('category')
        context['current_category'] = self.request.GET.get('category', '')
        context['current_scrapped'] = self.request.GET.get('scrapped', '')
        return context


class TeamManagementView(AdminOrManagerRequiredMixin, ListView):
    """Team management view for admins and managers."""
    model = MaintenanceTeam
    template_name = 'maintenance/admin_teams.html'
    context_object_name = 'teams'
    paginate_by = 20
    ordering = ['team_name']

    def get_queryset(self):
        queryset = super().get_queryset().prefetch_related('members__user')
        
        # Filter by active status
        active = self.request.GET.get('active')
        if active == 'true':
            queryset = queryset.filter(is_active=True)
        elif active == 'false':
            queryset = queryset.filter(is_active=False)
        
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add member counts
        for team in context['teams']:
            team.member_count = team.members.count()
            team.equipment_count = team.equipment.count()
        context['current_active'] = self.request.GET.get('active', '')
        return context


class TeamCreateView(AdminOrManagerRequiredMixin, CreateView):
    """Create new maintenance team."""
    model = MaintenanceTeam
    form_class = TeamForm
    template_name = 'maintenance/team_form.html'
    success_url = reverse_lazy('maintenance:admin_teams')

    def form_valid(self, form):
        messages.success(self.request, f'Team "{form.instance.team_name}" created successfully.')
        return super().form_valid(form)


class TeamUpdateView(AdminOrManagerRequiredMixin, UpdateView):
    """Update existing maintenance team."""
    model = MaintenanceTeam
    form_class = TeamForm
    template_name = 'maintenance/team_form.html'
    success_url = reverse_lazy('maintenance:admin_teams')

    def form_valid(self, form):
        messages.success(self.request, f'Team "{form.instance.team_name}" updated successfully.')
        return super().form_valid(form)


class ReportsView(AdminRequiredMixin, TemplateView):
    """Admin view for system reports."""
    template_name = 'maintenance/admin_reports.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Equipment statistics
        equipment_by_category = Equipment.objects.values('category').annotate(
            count=Count('id')
        ).order_by('-count')
        
        equipment_by_team = MaintenanceTeam.objects.annotate(
            equipment_count=Count('equipment')
        ).order_by('-equipment_count')
        
        # Request statistics
        requests_by_status = MaintenanceRequest.objects.values('stage').annotate(
            count=Count('id')
        ).order_by('stage')
        
        requests_by_type = MaintenanceRequest.objects.values('request_type').annotate(
            count=Count('id')
        ).order_by('request_type')
        
        # Recent activity
        recent_requests = MaintenanceRequest.objects.select_related(
            'equipment', 'created_by'
        ).order_by('-created_at')[:10]
        
        context.update({
            'equipment_by_category': equipment_by_category,
            'equipment_by_team': equipment_by_team,
            'requests_by_status': requests_by_status,
            'requests_by_type': requests_by_type,
            'recent_requests': recent_requests,
        })
        
        return context


# Equipment CRUD Views
class EquipmentListView(AdminOrManagerRequiredMixin, ListView):
    """List view for all equipment with filtering."""
    model = Equipment
    template_name = 'maintenance/equipment_list.html'
    context_object_name = 'equipment_list'
    paginate_by = 20
    ordering = ['equipment_name']

    def get_queryset(self):
        queryset = super().get_queryset().select_related(
            'maintenance_team', 'default_technician'
        )
        
        # Filter by category if provided
        category = self.request.GET.get('category')
        if category:
            queryset = queryset.filter(category=category)
        
        # Filter by department if provided
        department = self.request.GET.get('department')
        if department:
            queryset = queryset.filter(department=department)
        
        # Filter by scrapped status
        scrapped = self.request.GET.get('scrapped')
        if scrapped == 'true':
            queryset = queryset.filter(is_scrapped=True)
        elif scrapped == 'false':
            queryset = queryset.filter(is_scrapped=False)
        
        # Search by name or serial number
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(equipment_name__icontains=search) |
                Q(serial_number__icontains=search)
            )
        
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Get unique categories and departments for filters
        context['categories'] = Equipment.objects.values_list(
            'category', flat=True
        ).distinct().order_by('category')
        context['departments'] = Equipment.objects.values_list(
            'department', flat=True
        ).distinct().exclude(department__isnull=True).exclude(department='').order_by('department')
        context['current_category'] = self.request.GET.get('category', '')
        
        # Add date context for next maintenance date calculations
        from datetime import timedelta
        context['today'] = timezone.now().date()
        context['next_week'] = timezone.now().date() + timedelta(days=7)
        context['current_department'] = self.request.GET.get('department', '')
        context['current_scrapped'] = self.request.GET.get('scrapped', '')
        context['current_search'] = self.request.GET.get('search', '')
        return context


class EquipmentCreateView(AdminOrManagerRequiredMixin, CreateView):
    """Create new equipment."""
    model = Equipment
    form_class = EquipmentForm
    template_name = 'maintenance/equipment_form.html'
    success_url = reverse_lazy('maintenance:equipment_list')

    def form_valid(self, form):
        messages.success(self.request, f'Equipment "{form.instance.equipment_name}" created successfully.')
        return super().form_valid(form)


class EquipmentUpdateView(AdminOrManagerRequiredMixin, UpdateView):
    """Update existing equipment."""
    model = Equipment
    form_class = EquipmentForm
    template_name = 'maintenance/equipment_form.html'
    success_url = reverse_lazy('maintenance:equipment_list')

    def form_valid(self, form):
        messages.success(self.request, f'Equipment "{form.instance.equipment_name}" updated successfully.')
        return super().form_valid(form)


class EquipmentDeleteView(AdminOrManagerRequiredMixin, DeleteView):
    """Delete equipment."""
    model = Equipment
    template_name = 'maintenance/equipment_confirm_delete.html'
    success_url = reverse_lazy('maintenance:equipment_list')

    def delete(self, request, *args, **kwargs):
        equipment = self.get_object()
        messages.success(self.request, f'Equipment "{equipment.equipment_name}" deleted successfully.')
        return super().delete(request, *args, **kwargs)


# Technician Views
class TechnicianDashboardView(TechnicianRequiredMixin, TemplateView):
    """Technician dashboard showing assigned maintenance requests."""
    template_name = 'maintenance/technician_dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Get technician's teams
        technician_teams = MaintenanceTeam.objects.filter(
            members__user=user
        ).distinct()
        
        # Get assigned requests (assigned to this technician)
        assigned_requests = MaintenanceRequest.objects.filter(
            assigned_technician=user
        ).select_related('equipment', 'maintenance_team', 'created_by').order_by('-created_at')
        
        # Get team requests (requests for technician's teams, not yet assigned)
        team_requests = MaintenanceRequest.objects.filter(
            maintenance_team__in=technician_teams,
            assigned_technician__isnull=True
        ).exclude(stage__in=['Repaired', 'Scrap']).select_related(
            'equipment', 'maintenance_team', 'created_by'
        ).order_by('-created_at')[:10]
        
        # Statistics
        new_requests = assigned_requests.filter(stage='New').count()
        in_progress = assigned_requests.filter(stage='In Progress').count()
        overdue = assigned_requests.filter(is_overdue=True).exclude(
            stage__in=['Repaired', 'Scrap']
        ).count()
        completed = assigned_requests.filter(stage='Repaired').count()
        
        # Calculate total hours spent
        total_hours = assigned_requests.filter(
            duration_hours__isnull=False
        ).aggregate(total=Sum('duration_hours'))['total'] or 0
        
        # Get completed requests with duration for reports
        completed_requests = assigned_requests.filter(
            stage='Repaired',
            duration_hours__isnull=False
        ).order_by('-completed_date', '-actual_end_time')
        
        context.update({
            'assigned_requests': assigned_requests[:20],  # Show latest 20
            'team_requests': team_requests,
            'new_requests': new_requests,
            'in_progress': in_progress,
            'overdue': overdue,
            'completed': completed,
            'total_assigned': assigned_requests.count(),
            'total_hours': round(total_hours, 2),
            'completed_requests': completed_requests[:10],  # Recent completed tasks
        })
        
        return context


class TechnicianRequestDetailView(TechnicianRequiredMixin, UpdateView):
    """Technician view to update maintenance request details."""
    model = MaintenanceRequest
    form_class = TechnicianRequestUpdateForm
    template_name = 'maintenance/request_detail.html'
    context_object_name = 'request'

    def get_queryset(self):
        user = self.request.user
        # Get technician's teams
        technician_teams = MaintenanceTeam.objects.filter(
            members__user=user
        ).distinct()
        
        # Only allow access to requests assigned to this technician or in their teams
        return MaintenanceRequest.objects.filter(
            Q(assigned_technician=user) | 
            Q(maintenance_team__in=technician_teams)
        ).select_related('equipment', 'maintenance_team', 'assigned_technician', 'created_by')

    def dispatch(self, request, *args, **kwargs):
        # Check if user has access to this request
        obj = self.get_object()
        user = request.user
        
        # Get technician's teams
        technician_teams = MaintenanceTeam.objects.filter(
            members__user=user
        ).distinct()
        
        # Check if request is assigned to this technician or in their team
        if obj.assigned_technician != user and obj.maintenance_team not in technician_teams:
            from django.core.exceptions import PermissionDenied
            raise PermissionDenied("You don't have access to this maintenance request.")
        
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        request_obj = form.instance
        
        # Auto-set completed_date when marked as Repaired
        if request_obj.stage == 'Repaired' and not request_obj.completed_date:
            request_obj.completed_date = timezone.now().date()
        
        # Auto-set actual_start_time when moving to In Progress
        if request_obj.stage == 'In Progress' and not request_obj.actual_start_time:
            request_obj.actual_start_time = timezone.now()
        
        # Auto-set actual_end_time and calculate duration when marked as Repaired or Scrap
        if request_obj.stage in ['Repaired', 'Scrap'] and not request_obj.actual_end_time:
            request_obj.actual_end_time = timezone.now()
            # Auto-calculate duration if start time exists
            if request_obj.actual_start_time:
                time_diff = request_obj.actual_end_time - request_obj.actual_start_time
                duration_hours = time_diff.total_seconds() / 3600  # Convert to hours
                request_obj.duration_hours = round(duration_hours, 2)
        
        # Ensure technician is assigned
        if not request_obj.assigned_technician:
            request_obj.assigned_technician = self.request.user
        
        messages.success(self.request, f'Maintenance request "{request_obj.subject}" updated successfully.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('maintenance:technician_dashboard')


# User Views
class UserDashboardView(UserRequiredMixin, TemplateView):
    """User dashboard showing their maintenance requests."""
    template_name = 'maintenance/user_dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Get all requests created by this user
        user_requests = MaintenanceRequest.objects.filter(
            created_by=user
        ).select_related(
            'equipment', 'maintenance_team', 'assigned_technician'
        ).order_by('-created_at')
        
        # Statistics
        new_requests = user_requests.filter(stage='New').count()
        in_progress = user_requests.filter(stage='In Progress').count()
        repaired = user_requests.filter(stage='Repaired').count()
        total_requests = user_requests.count()
        
        context.update({
            'user_requests': user_requests[:20],  # Show latest 20
            'new_requests': new_requests,
            'in_progress': in_progress,
            'repaired': repaired,
            'total_requests': total_requests,
        })
        
        return context


class UserCreateRequestView(UserRequiredMixin, CreateView):
    """View for users to create breakdown maintenance requests."""
    model = MaintenanceRequest
    form_class = UserBreakdownRequestForm
    template_name = 'maintenance/create_request.html'
    success_url = reverse_lazy('maintenance:user_dashboard')

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        form.instance.request_type = 'Corrective'
        form.instance.stage = 'New'
        
        # Auto-assign maintenance team from equipment
        if form.instance.equipment and form.instance.equipment.maintenance_team:
            form.instance.maintenance_team = form.instance.equipment.maintenance_team
        
        messages.success(
            self.request, 
            f'Maintenance request "{form.instance.subject}" created successfully. '
            f'It has been assigned to {form.instance.maintenance_team.team_name if form.instance.maintenance_team else "a maintenance team"}.'
        )
        return super().form_valid(form)


class UserRequestDetailView(UserRequiredMixin, TemplateView):
    """Read-only view for users to see their request details."""
    template_name = 'maintenance/user_request_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        request_id = self.kwargs.get('pk')
        
        # Only allow users to view their own requests
        request_obj = get_object_or_404(
            MaintenanceRequest,
            pk=request_id,
            created_by=user
        )
        
        context['request'] = request_obj
        return context


# Kanban Board View
class KanbanBoardView(AdminOrManagerRequiredMixin, TemplateView):
    """Kanban board view for maintenance requests with drag and drop."""
    template_name = 'maintenance/kanban_board.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get all requests grouped by stage
        stages = ['New', 'In Progress', 'Repaired', 'Scrap']
        requests_by_stage = {}
        
        for stage in stages:
            requests = MaintenanceRequest.objects.filter(
                stage=stage
            ).select_related(
                'equipment', 'maintenance_team', 'assigned_technician', 'created_by'
            ).order_by('-priority', '-created_at')
            requests_by_stage[stage] = requests
        
        context['requests_by_stage'] = requests_by_stage
        context['stages'] = stages
        return context


@require_http_methods(["POST"])
def update_request_stage(request, pk):
    """Update maintenance request stage via AJAX (for drag and drop)."""
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)
    
    request_obj = get_object_or_404(MaintenanceRequest, pk=pk)
    new_stage = request.POST.get('stage')
    
    if new_stage not in dict(MaintenanceRequest.STAGE_CHOICES):
        return JsonResponse({'error': 'Invalid stage'}, status=400)
    
    request_obj.stage = new_stage
    
    # Auto-set timestamps based on stage
    if new_stage == 'In Progress' and not request_obj.actual_start_time:
        request_obj.actual_start_time = timezone.now()
    elif new_stage in ['Repaired', 'Scrap']:
        # When moving to Repaired or Scrap, set end time and calculate duration
        if not request_obj.actual_end_time:
            request_obj.actual_end_time = timezone.now()
        
        # Calculate duration if start time exists
        if request_obj.actual_start_time and not request_obj.duration_hours:
            time_diff = request_obj.actual_end_time - request_obj.actual_start_time
            duration_hours = time_diff.total_seconds() / 3600  # Convert to hours
            request_obj.duration_hours = round(duration_hours, 2)
        
        # Set completed_date for both Repaired and Scrap
        if not request_obj.completed_date:
            request_obj.completed_date = timezone.now().date()
    
    request_obj.save()
    
    return JsonResponse({
        'success': True,
        'message': f'Request moved to {new_stage}',
        'stage': new_stage,
        'duration_hours': float(request_obj.duration_hours) if request_obj.duration_hours else None
    })


# Reports Dashboard
class ReportsDashboardView(AdminOrManagerRequiredMixin, TemplateView):
    """Reports dashboard accessible by Admin and Manager."""
    template_name = 'maintenance/reports.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Number of requests per team
        requests_per_team = MaintenanceTeam.objects.annotate(
            request_count=Count('maintenance_requests')
        ).filter(request_count__gt=0).order_by('-request_count')
        
        # Number of requests per equipment
        requests_per_equipment = Equipment.objects.annotate(
            request_count=Count('maintenance_requests')
        ).filter(request_count__gt=0).order_by('-request_count')[:20]  # Top 20
        
        # Average repair duration (only for repaired requests with duration)
        avg_repair_duration = MaintenanceRequest.objects.filter(
            stage='Repaired',
            duration_hours__isnull=False
        ).aggregate(
            avg_duration=Avg('duration_hours')
        )
        
        # Additional statistics
        total_requests = MaintenanceRequest.objects.count()
        repaired_requests = MaintenanceRequest.objects.filter(stage='Repaired').count()
        requests_with_duration = MaintenanceRequest.objects.filter(
            stage='Repaired',
            duration_hours__isnull=False
        ).count()
        
        # Requests per team with breakdown by status
        team_stats = []
        for team in requests_per_team:
            team_new = MaintenanceRequest.objects.filter(
                maintenance_team=team,
                stage='New'
            ).count()
            team_in_progress = MaintenanceRequest.objects.filter(
                maintenance_team=team,
                stage='In Progress'
            ).count()
            team_repaired = MaintenanceRequest.objects.filter(
                maintenance_team=team,
                stage='Repaired'
            ).count()
            
            team_stats.append({
                'team': team,
                'total': team.request_count,
                'new': team_new,
                'in_progress': team_in_progress,
                'repaired': team_repaired,
            })
        
        context.update({
            'requests_per_team': requests_per_team,
            'team_stats': team_stats,
            'requests_per_equipment': requests_per_equipment,
            'avg_repair_duration': avg_repair_duration['avg_duration'],
            'total_requests': total_requests,
            'repaired_requests': repaired_requests,
            'requests_with_duration': requests_with_duration,
        })
        
        return context
