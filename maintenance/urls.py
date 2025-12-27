from django.urls import path
from django.views.generic import RedirectView
from . import views

app_name = 'maintenance'

urlpatterns = [
    path('', RedirectView.as_view(url='/manager/dashboard/', permanent=False), name='home'),
    path('accounts/login/', views.CustomLoginView.as_view(), name='login'),
    path('accounts/logout/', views.logout_view, name='logout'),
    path('accounts/signup/', views.SignupView.as_view(), name='signup'),
    path('accounts/signup/success/', views.SignupSuccessView.as_view(), name='signup_success'),
    path('admin/registrations/', views.UserRegistrationListView.as_view(), name='user_registrations'),
    path('admin/registrations/<int:pk>/approve/', views.approve_registration, name='approve_registration'),
    path('admin/registrations/<int:pk>/reject/', views.reject_registration, name='reject_registration'),
    path('api/equipment/<int:pk>/data/', views.get_equipment_data, name='get_equipment_data'),
    # Manager URLs
    path('manager/dashboard/', views.ManagerDashboardView.as_view(), name='manager_dashboard'),
    path('manager/requests/', views.MaintenanceRequestListView.as_view(), name='request_list'),
    path('manager/requests/<int:pk>/update/', views.MaintenanceRequestUpdateView.as_view(), name='request_update'),
    path('manager/preventive/', views.PreventiveMaintenanceCreateView.as_view(), name='preventive_maintenance'),
    path('manager/calendar/', views.PreventiveMaintenanceCalendarView.as_view(), name='preventive_calendar'),
    path('manager/kanban/', views.KanbanBoardView.as_view(), name='kanban_board'),
    path('manager/reports/', views.ReportsDashboardView.as_view(), name='reports_dashboard'),
    path('manager/technician-reports/', views.ManagerTechnicianReportsView.as_view(), name='manager_technician_reports'),
    path('manager/requests/<int:pk>/update-stage/', views.update_request_stage, name='update_request_stage'),
    # Admin URLs
    path('admin/dashboard/', views.AdminDashboardView.as_view(), name='admin_dashboard'),
    path('admin/equipment/', views.EquipmentManagementView.as_view(), name='admin_equipment'),
    path('admin/teams/', views.TeamManagementView.as_view(), name='admin_teams'),
    path('admin/teams/create/', views.TeamCreateView.as_view(), name='admin_team_create'),
    path('admin/reports/', views.ReportsView.as_view(), name='admin_reports'),
    path('admin/manager-hours/', views.AdminManagerHoursView.as_view(), name='admin_manager_hours'),
    # Equipment CRUD URLs
    path('equipment/', views.EquipmentListView.as_view(), name='equipment_list'),
    path('equipment/create/', views.EquipmentCreateView.as_view(), name='equipment_create'),
    path('equipment/<int:pk>/update/', views.EquipmentUpdateView.as_view(), name='equipment_update'),
    path('equipment/<int:pk>/delete/', views.EquipmentDeleteView.as_view(), name='equipment_delete'),
    # Technician URLs
    path('technician/dashboard/', views.TechnicianDashboardView.as_view(), name='technician_dashboard'),
    path('technician/requests/<int:pk>/', views.TechnicianRequestDetailView.as_view(), name='technician_request_detail'),
    path('technician/requests/<int:pk>/start-task/', views.start_task, name='start_task'),
    path('technician/requests/<int:pk>/end-task/', views.end_task, name='end_task'),
    path('technician/reports/', views.TechnicianReportsView.as_view(), name='technician_reports'),
    # User URLs
    path('user/dashboard/', views.UserDashboardView.as_view(), name='user_dashboard'),
    path('user/requests/create/', views.UserCreateRequestView.as_view(), name='user_create_request'),
    path('user/requests/<int:pk>/', views.UserRequestDetailView.as_view(), name='user_request_detail'),
]

