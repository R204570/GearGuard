from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.utils import timezone


# Helper function to get user role
def get_user_role(user):
    """Get user role from profile."""
    try:
        return user.profile.role
    except AttributeError:
        return None


# Add role property to User model
def user_get_role(self):
    """Get user role from profile."""
    try:
        return self.profile.role
    except AttributeError:
        return None


# Monkey patch User model to add role property
User.add_to_class('get_role', user_get_role)


class MaintenanceTeam(models.Model):
    team_name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'maintenance_teams'
        ordering = ['team_name']

    def __str__(self):
        return self.team_name


class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('Admin', 'Admin'),
        ('Manager', 'Manager'),
        ('Technician', 'Technician'),
        ('User', 'User'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=50, choices=ROLE_CHOICES, default='User')
    avatar_url = models.URLField(max_length=500, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['user__username']

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} ({self.role})"


class TeamMember(models.Model):
    team = models.ForeignKey(MaintenanceTeam, on_delete=models.CASCADE, related_name='members')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='team_memberships')
    role_in_team = models.CharField(max_length=100, default='Member')
    joined_date = models.DateField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'team_members'
        unique_together = ['team', 'user']
        ordering = ['team', 'user']

    def __str__(self):
        return f"{self.user.username} - {self.team.team_name}"


class Equipment(models.Model):
    equipment_name = models.CharField(max_length=255)
    serial_number = models.CharField(max_length=100, unique=True)
    category = models.CharField(max_length=100)
    department = models.CharField(max_length=100, blank=True, null=True)
    
    assigned_to_user = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='assigned_equipment'
    )
    maintenance_team = models.ForeignKey(
        MaintenanceTeam, 
        on_delete=models.PROTECT, 
        related_name='equipment'
    )
    default_technician = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='default_equipment'
    )
    
    purchase_date = models.DateField(blank=True, null=True)
    warranty_expiry = models.DateField(blank=True, null=True)
    location = models.CharField(max_length=255, blank=True, null=True)
    specifications = models.TextField(blank=True, null=True)
    
    # Preventive maintenance interval (in days)
    maintenance_interval_days = models.IntegerField(
        blank=True, 
        null=True,
        help_text='Number of days between preventive maintenance cycles (e.g., 30 for monthly, 90 for quarterly)'
    )
    
    is_scrapped = models.BooleanField(default=False)
    scrap_date = models.DateField(blank=True, null=True)
    scrap_reason = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def get_next_maintenance_date(self):
        """Calculate next preventive maintenance date based on interval."""
        if not self.maintenance_interval_days:
            return None
        
        # Get the last completed preventive maintenance for this equipment
        last_preventive = MaintenanceRequest.objects.filter(
            equipment=self,
            request_type='Preventive',
            stage='Repaired'
        ).order_by('-completed_date', '-actual_end_time').first()
        
        if last_preventive and last_preventive.completed_date:
            from datetime import timedelta
            return last_preventive.completed_date + timedelta(days=self.maintenance_interval_days)
        
        # If no previous maintenance, calculate from purchase date or current date
        from django.utils import timezone
        from datetime import timedelta
        base_date = self.purchase_date if self.purchase_date else timezone.now().date()
        return base_date + timedelta(days=self.maintenance_interval_days)

    class Meta:
        db_table = 'equipment'
        ordering = ['equipment_name']

    def __str__(self):
        return f"{self.equipment_name} ({self.serial_number})"


class UserRegistration(models.Model):
    """Model for user registration requests awaiting admin approval."""
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
    ]
    
    ROLE_CHOICES = [
        ('User', 'User'),
        ('Technician', 'Technician'),
        ('Manager', 'Manager'),
    ]
    
    username = models.CharField(max_length=150, unique=True)
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    password = models.CharField(max_length=128)  # Will be hashed when creating user
    requested_role = models.CharField(max_length=50, choices=ROLE_CHOICES, default='User')
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='Pending')
    
    approved_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='approved_registrations'
    )
    approved_at = models.DateTimeField(blank=True, null=True)
    rejection_reason = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'user_registrations'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.username} - {self.status}"


class MaintenanceRequest(models.Model):
    REQUEST_TYPE_CHOICES = [
        ('Corrective', 'Corrective'),
        ('Preventive', 'Preventive'),
    ]

    STAGE_CHOICES = [
        ('New', 'New'),
        ('In Progress', 'In Progress'),
        ('Repaired', 'Repaired'),
        ('Scrap', 'Scrap'),
    ]

    PRIORITY_CHOICES = [
        ('Low', 'Low'),
        ('Medium', 'Medium'),
        ('High', 'High'),
        ('Critical', 'Critical'),
    ]

    subject = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    
    request_type = models.CharField(max_length=50, choices=REQUEST_TYPE_CHOICES)
    stage = models.CharField(max_length=50, choices=STAGE_CHOICES, default='New')
    priority = models.CharField(max_length=50, choices=PRIORITY_CHOICES, default='Medium')
    
    equipment = models.ForeignKey(
        Equipment, 
        on_delete=models.CASCADE, 
        related_name='maintenance_requests'
    )
    maintenance_team = models.ForeignKey(
        MaintenanceTeam, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='maintenance_requests'
    )
    assigned_technician = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='assigned_requests'
    )
    created_by = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='created_requests'
    )
    
    scheduled_date = models.DateField(blank=True, null=True)
    due_date = models.DateField(blank=True, null=True)
    completed_date = models.DateField(blank=True, null=True)
    
    # Estimated/Assigned duration for preventive maintenance (set when creating request)
    estimated_duration_hours = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        blank=True, 
        null=True,
        validators=[MinValueValidator(0)],
        help_text="Estimated duration in hours (typically set for preventive maintenance)"
    )
    # Actual duration (calculated when task is completed)
    duration_hours = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        blank=True, 
        null=True,
        validators=[MinValueValidator(0)]
    )
    actual_start_time = models.DateTimeField(blank=True, null=True)
    actual_end_time = models.DateTimeField(blank=True, null=True)
    
    is_overdue = models.BooleanField(default=False)
    
    technician_notes = models.TextField(blank=True, null=True)
    resolution_summary = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'maintenance_requests'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.subject} - {self.equipment.equipment_name}"

    def save(self, *args, **kwargs):
        # Auto-detect overdue status
        if self.scheduled_date and self.stage not in ['Repaired', 'Scrap']:
            self.is_overdue = self.scheduled_date < timezone.now().date()
        else:
            self.is_overdue = False
        
        # Scrap logic: If stage is Scrap, mark equipment as scrapped
        if self.stage == 'Scrap' and self.equipment:
            if not self.equipment.is_scrapped:
                self.equipment.is_scrapped = True
                self.equipment.scrap_date = timezone.now().date()
                if self.resolution_summary:
                    self.equipment.scrap_reason = self.resolution_summary
                self.equipment.save()
        
        super().save(*args, **kwargs)
