from django.contrib import admin
from .models import (
    MaintenanceTeam, UserProfile, TeamMember, 
    Equipment, MaintenanceRequest, UserRegistration
)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'role', 'is_active', 'created_at']
    list_filter = ['role', 'is_active']
    search_fields = ['user__username', 'user__email', 'user__first_name', 'user__last_name']


@admin.register(MaintenanceTeam)
class MaintenanceTeamAdmin(admin.ModelAdmin):
    list_display = ['team_name', 'is_active', 'created_at']
    list_filter = ['is_active']
    search_fields = ['team_name', 'description']


@admin.register(TeamMember)
class TeamMemberAdmin(admin.ModelAdmin):
    list_display = ['user', 'team', 'role_in_team', 'joined_date']
    list_filter = ['team', 'role_in_team']
    search_fields = ['user__username', 'team__team_name']


@admin.register(Equipment)
class EquipmentAdmin(admin.ModelAdmin):
    list_display = ['equipment_name', 'serial_number', 'category', 'maintenance_team', 'is_scrapped']
    list_filter = ['category', 'department', 'is_scrapped', 'maintenance_team']
    search_fields = ['equipment_name', 'serial_number', 'category']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(MaintenanceRequest)
class MaintenanceRequestAdmin(admin.ModelAdmin):
    list_display = ['subject', 'equipment', 'request_type', 'stage', 'priority', 'scheduled_date', 'is_overdue']
    list_filter = ['request_type', 'stage', 'priority', 'is_overdue', 'maintenance_team']
    search_fields = ['subject', 'description', 'equipment__equipment_name']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'scheduled_date'


@admin.register(UserRegistration)
class UserRegistrationAdmin(admin.ModelAdmin):
    list_display = ['username', 'email', 'requested_role', 'status', 'created_at', 'approved_by']
    list_filter = ['status', 'requested_role', 'created_at']
    search_fields = ['username', 'email', 'first_name', 'last_name']
    readonly_fields = ['created_at', 'updated_at', 'approved_at']
    actions = ['approve_registrations', 'reject_registrations']
    
    def approve_registrations(self, request, queryset):
        from django.contrib.auth.models import User
        from .models import UserProfile
        from django.utils import timezone
        
        count = 0
        errors = []
        for registration in queryset.filter(status='Pending'):
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
                        profile.role = registration.requested_role
                        profile.save()
                    
                    # Update registration
                    registration.status = 'Approved'
                    registration.approved_by = request.user
                    registration.approved_at = timezone.now()
                    registration.save()
                    count += 1
                    continue
                
                # Check if email already exists
                if User.objects.filter(email=registration.email).exists():
                    errors.append(f'{registration.username}: Email already registered')
                    continue
                
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
                count += 1
            except Exception as e:
                errors.append(f'{registration.username}: {str(e)}')
        
        if errors:
            self.message_user(request, f'{count} registration(s) approved. Errors: {"; ".join(errors)}', level='warning')
        else:
            self.message_user(request, f'{count} registration(s) approved and users created.')
        
        self.message_user(request, f'{count} registration(s) approved and users created.')
    approve_registrations.short_description = "Approve selected registrations"
    
    def reject_registrations(self, request, queryset):
        count = queryset.filter(status='Pending').update(status='Rejected')
        self.message_user(request, f'{count} registration(s) rejected.')
    reject_registrations.short_description = "Reject selected registrations"
