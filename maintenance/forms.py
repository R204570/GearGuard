from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from .models import MaintenanceRequest, Equipment, MaintenanceTeam, UserRegistration


class PreventiveMaintenanceForm(forms.ModelForm):
    """Form for creating preventive maintenance requests."""
    
    class Meta:
        model = MaintenanceRequest
        fields = ['subject', 'description', 'equipment', 'maintenance_team', 
                  'assigned_technician', 'scheduled_date', 'priority']
        widgets = {
            'subject': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter maintenance subject'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter maintenance description (optional)'
            }),
            'equipment': forms.Select(attrs={
                'class': 'form-control'
            }),
            'maintenance_team': forms.Select(attrs={
                'class': 'form-control'
            }),
            'assigned_technician': forms.Select(attrs={
                'class': 'form-control'
            }),
            'scheduled_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'priority': forms.Select(attrs={
                'class': 'form-control'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['equipment'].queryset = Equipment.objects.filter(is_scrapped=False)
        self.fields['maintenance_team'].queryset = MaintenanceTeam.objects.filter(is_active=True)
        
        # Add data attributes for auto-fill
        self.fields['equipment'].widget.attrs.update({
            'id': 'id_equipment',
            'data-autofill': 'true'
        })
        self.fields['maintenance_team'].widget.attrs.update({
            'id': 'id_maintenance_team'
        })
        
        # Filter technicians only
        technician_ids = User.objects.filter(
            profile__role='Technician'
        ).values_list('id', flat=True)
        self.fields['assigned_technician'].queryset = User.objects.filter(
            id__in=technician_ids
        )
        
        # Set default request type
        self.instance.request_type = 'Preventive'


class MaintenanceRequestUpdateForm(forms.ModelForm):
    """Form for updating maintenance request (assign technician, change status)."""
    
    class Meta:
        model = MaintenanceRequest
        fields = ['assigned_technician', 'stage', 'priority']
        widgets = {
            'assigned_technician': forms.Select(attrs={
                'class': 'form-control'
            }),
            'stage': forms.Select(attrs={
                'class': 'form-control'
            }),
            'priority': forms.Select(attrs={
                'class': 'form-control'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Filter technicians only
        technician_ids = User.objects.filter(
            profile__role='Technician'
        ).values_list('id', flat=True)
        self.fields['assigned_technician'].queryset = User.objects.filter(
            id__in=technician_ids
        )
        
        # Add empty option for technician
        self.fields['assigned_technician'].empty_label = "Unassigned"


class EquipmentForm(forms.ModelForm):
    """Form for creating and updating equipment."""
    
    class Meta:
        model = Equipment
        fields = [
            'equipment_name', 'serial_number', 'category', 'department', 
            'location', 'warranty_expiry', 'maintenance_team', 
            'default_technician', 'purchase_date', 'maintenance_interval_days', 'specifications'
        ]
        widgets = {
            'equipment_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter equipment name'
            }),
            'serial_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter serial number'
            }),
            'category': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Machinery, Computer, Vehicle'
            }),
            'department': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter department'
            }),
            'location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter location'
            }),
            'warranty_expiry': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'purchase_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'maintenance_interval_days': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'placeholder': 'e.g., 30 for monthly, 90 for quarterly'
            }),
            'maintenance_team': forms.Select(attrs={
                'class': 'form-control'
            }),
            'default_technician': forms.Select(attrs={
                'class': 'form-control'
            }),
            'specifications': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Enter equipment specifications (optional)'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['maintenance_team'].queryset = MaintenanceTeam.objects.filter(is_active=True)
        self.fields['maintenance_team'].empty_label = "Select maintenance team"
        
        # Filter technicians only
        technician_ids = User.objects.filter(
            profile__role='Technician'
        ).values_list('id', flat=True)
        self.fields['default_technician'].queryset = User.objects.filter(
            id__in=technician_ids
        )
        self.fields['default_technician'].empty_label = "No default technician"
        
        # Make required fields
        self.fields['equipment_name'].required = True
        self.fields['serial_number'].required = True
        self.fields['maintenance_team'].required = True


class UserBreakdownRequestForm(forms.ModelForm):
    """Form for users to create breakdown (corrective) maintenance requests."""
    
    class Meta:
        model = MaintenanceRequest
        fields = ['subject', 'description', 'equipment', 'priority']
        widgets = {
            'subject': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Brief description of the issue'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Describe the problem in detail...'
            }),
            'equipment': forms.Select(attrs={
                'class': 'form-control'
            }),
            'priority': forms.Select(attrs={
                'class': 'form-control'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only show active, non-scrapped equipment
        self.fields['equipment'].queryset = Equipment.objects.filter(
            is_scrapped=False
        ).order_by('equipment_name')
        
        # Add data attributes for auto-fill
        self.fields['equipment'].widget.attrs.update({
            'id': 'id_equipment',
            'data-autofill': 'true'
        })
        
        # Set default request type to Corrective (breakdown)
        self.instance.request_type = 'Corrective'
        self.instance.stage = 'New'

    def save(self, commit=True):
        instance = super().save(commit=False)
        # Auto-assign maintenance team from equipment
        if instance.equipment and instance.equipment.maintenance_team:
            instance.maintenance_team = instance.equipment.maintenance_team
        
        # Set request type
        instance.request_type = 'Corrective'
        instance.stage = 'New'
        
        if commit:
            instance.save()
        return instance


class TechnicianRequestUpdateForm(forms.ModelForm):
    """Form for technicians to update maintenance requests."""
    
    class Meta:
        model = MaintenanceRequest
        fields = ['stage', 'duration_hours', 'technician_notes', 'resolution_summary']
        widgets = {
            'stage': forms.Select(attrs={
                'class': 'form-control'
            }),
            'duration_hours': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': 'Enter duration in hours'
            }),
            'technician_notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Enter your notes about the maintenance work...'
            }),
            'resolution_summary': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Enter resolution summary (required when marking as Repaired)...'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Limit stage choices based on current stage
        current_stage = self.instance.stage if self.instance.pk else 'New'
        stage_choices = []
        
        if current_stage == 'New':
            stage_choices = [('New', 'New'), ('In Progress', 'In Progress')]
        elif current_stage == 'In Progress':
            stage_choices = [
                ('In Progress', 'In Progress'),
                ('Repaired', 'Repaired'),
                ('Scrap', 'Scrap')
            ]
        elif current_stage == 'Repaired':
            stage_choices = [('Repaired', 'Repaired')]
        elif current_stage == 'Scrap':
            stage_choices = [('Scrap', 'Scrap')]
        else:
            stage_choices = MaintenanceRequest.STAGE_CHOICES
        
        self.fields['stage'].choices = stage_choices
        
        # Hide duration_hours field if task is completed and duration was auto-calculated
        if self.instance.pk and self.instance.stage == 'Repaired' and self.instance.actual_start_time and self.instance.actual_end_time:
            # Duration was auto-calculated, so hide the field completely (it will be saved as hidden input)
            self.fields['duration_hours'].widget = forms.HiddenInput()
        elif self.instance.pk and self.instance.stage == 'In Progress':
            # Task is in progress, make it read-only with helpful message
            self.fields['duration_hours'].widget.attrs['readonly'] = True
            self.fields['duration_hours'].widget.attrs['style'] = 'background-color: #e9ecef; cursor: not-allowed;'
            self.fields['duration_hours'].help_text = 'Duration will be automatically calculated when you end the task using the "End Task" button.'

    def clean(self):
        cleaned_data = super().clean()
        stage = cleaned_data.get('stage')
        resolution_summary = cleaned_data.get('resolution_summary')
        
        # Require resolution summary when marking as Repaired
        if stage == 'Repaired' and not resolution_summary:
            raise forms.ValidationError({
                'resolution_summary': 'Resolution summary is required when marking request as Repaired.'
            })
        
        return cleaned_data


class TeamForm(forms.ModelForm):
    """Form for creating and updating maintenance teams."""
    
    class Meta:
        model = MaintenanceTeam
        fields = ['team_name', 'description', 'is_active']
        widgets = {
            'team_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter team name'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Enter team description (optional)'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make required fields
        self.fields['team_name'].required = True


class UserSignupForm(forms.ModelForm):
    """Form for user registration/signup."""
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter password'
        }),
        min_length=8,
        help_text='Password must be at least 8 characters long.'
    )
    password_confirm = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm password'
        }),
        label='Confirm Password'
    )
    requested_role = forms.ChoiceField(
        choices=[
            ('User', 'User'),
            ('Technician', 'Technician'),
            ('Manager', 'Manager'),
        ],
        widget=forms.Select(attrs={
            'class': 'form-control'
        }),
        initial='User',
        help_text='Select the role you are requesting. Admin will approve your request.'
    )
    
    class Meta:
        model = UserRegistration
        fields = ['username', 'email', 'first_name', 'last_name', 'password', 'requested_role']
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Choose a username',
                'autocomplete': 'username'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter your email',
                'autocomplete': 'email'
            }),
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'First name (optional)'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Last name (optional)'
            }),
        }
    
    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError('This username is already taken.')
        if UserRegistration.objects.filter(username=username, status='Pending').exists():
            raise forms.ValidationError('A registration request with this username is already pending.')
        return username
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('This email is already registered.')
        if UserRegistration.objects.filter(email=email, status='Pending').exists():
            raise forms.ValidationError('A registration request with this email is already pending.')
        return email
    
    def clean_password(self):
        password = self.cleaned_data.get('password')
        validate_password(password)
        return password
    
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')
        
        if password and password_confirm and password != password_confirm:
            raise forms.ValidationError({
                'password_confirm': 'Passwords do not match.'
            })
        
        return cleaned_data
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        # Store password as-is (will be hashed when creating user)
        instance.password = self.cleaned_data['password']
        instance.status = 'Pending'
        if commit:
            instance.save()
        return instance

