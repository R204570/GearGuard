"""
Management command to add comprehensive sample data including teams, equipment, and maintenance requests.
Usage: python manage.py add_sample_data
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import datetime, timedelta
from maintenance.models import (
    MaintenanceTeam, Equipment, UserProfile, TeamMember, MaintenanceRequest
)


class Command(BaseCommand):
    help = 'Add sample maintenance teams and equipment to the database'

    def handle(self, *args, **options):
        self.stdout.write('Adding sample data...\n')

        # Create or get maintenance teams
        teams_data = [
            {
                'team_name': 'Mechanics',
                'description': 'Handles mechanical equipment repairs and maintenance'
            },
            {
                'team_name': 'Electricians',
                'description': 'Electrical systems and wiring maintenance'
            },
            {
                'team_name': 'IT Support',
                'description': 'Computer hardware and software support'
            },
            {
                'team_name': 'HVAC Team',
                'description': 'Heating, ventilation, and air conditioning'
            },
            {
                'team_name': 'Facilities',
                'description': 'General building and facility maintenance'
            },
            {
                'team_name': 'Plumbing',
                'description': 'Water systems and plumbing maintenance'
            },
        ]

        teams = {}
        for team_data in teams_data:
            team, created = MaintenanceTeam.objects.get_or_create(
                team_name=team_data['team_name'],
                defaults={'description': team_data['description']}
            )
            teams[team_data['team_name']] = team
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'Created team: {team.team_name}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'Team already exists: {team.team_name}')
                )

        # Get or create a default technician (use manager if exists, otherwise create one)
        try:
            default_tech = User.objects.filter(profile__role='Technician').first()
            if not default_tech:
                # Create a default technician user
                default_tech = User.objects.create_user(
                    username='tech1',
                    email='tech1@gearguard.com',
                    password='tech123'
                )
                UserProfile.objects.get_or_create(
                    user=default_tech,
                    defaults={'role': 'Technician'}
                )
                self.stdout.write(
                    self.style.SUCCESS('Created default technician user: tech1')
                )
        except Exception as e:
            self.stdout.write(
                self.style.WARNING(f'Could not get/create technician: {e}')
            )
            default_tech = None

        # Sample equipment data
        equipment_data = [
            {
                'equipment_name': 'CNC Machine 01',
                'serial_number': 'CNC-2023-001',
                'category': 'Machinery',
                'department': 'Production',
                'maintenance_team': teams['Mechanics'],
                'location': 'Factory Floor A',
                'purchase_date': '2023-01-15',
                'warranty_expiry': '2026-01-15',
            },
            {
                'equipment_name': 'Laptop Dell XPS 15',
                'serial_number': 'DELL-LT-5001',
                'category': 'Computer',
                'department': 'IT',
                'maintenance_team': teams['IT Support'],
                'location': 'Office 204',
                'purchase_date': '2023-06-20',
                'warranty_expiry': '2026-06-20',
            },
            {
                'equipment_name': 'Industrial Printer HP',
                'serial_number': 'HP-IP-9000',
                'category': 'Printer',
                'department': 'Administration',
                'maintenance_team': teams['IT Support'],
                'location': 'Print Room',
                'purchase_date': '2022-03-10',
                'warranty_expiry': '2025-03-10',
            },
            {
                'equipment_name': 'Forklift Toyota 3000',
                'serial_number': 'FORK-TY-3000',
                'category': 'Vehicle',
                'department': 'Warehouse',
                'maintenance_team': teams['Mechanics'],
                'location': 'Warehouse B',
                'purchase_date': '2021-11-05',
                'warranty_expiry': '2024-11-05',
            },
            {
                'equipment_name': 'Air Compressor Industrial',
                'serial_number': 'AC-COMP-450',
                'category': 'Machinery',
                'department': 'Production',
                'maintenance_team': teams['Mechanics'],
                'location': 'Factory Floor B',
                'purchase_date': '2022-08-12',
                'warranty_expiry': '2025-08-12',
            },
            {
                'equipment_name': 'Conference Room PC',
                'serial_number': 'HP-PC-CR01',
                'category': 'Computer',
                'department': 'Administration',
                'maintenance_team': teams['IT Support'],
                'location': 'Conference Room 1',
                'purchase_date': '2023-09-01',
                'warranty_expiry': '2026-09-01',
            },
            {
                'equipment_name': 'HVAC Unit Main Building',
                'serial_number': 'HVAC-MB-001',
                'category': 'HVAC',
                'department': 'Facilities',
                'maintenance_team': teams['HVAC Team'],
                'location': 'Roof - Main Building',
                'purchase_date': '2020-05-20',
                'warranty_expiry': '2025-05-20',
            },
            {
                'equipment_name': 'Water Pump System',
                'serial_number': 'WP-SYS-200',
                'category': 'Plumbing',
                'department': 'Facilities',
                'maintenance_team': teams['Plumbing'],
                'location': 'Basement',
                'purchase_date': '2021-03-15',
                'warranty_expiry': '2026-03-15',
            },
            {
                'equipment_name': 'Electrical Panel Main',
                'serial_number': 'ELEC-PNL-001',
                'category': 'Electrical',
                'department': 'Facilities',
                'maintenance_team': teams['Electricians'],
                'location': 'Electrical Room',
                'purchase_date': '2019-07-10',
                'warranty_expiry': '2024-07-10',
            },
            {
                'equipment_name': 'Generator Backup 500kW',
                'serial_number': 'GEN-500-001',
                'category': 'Electrical',
                'department': 'Facilities',
                'maintenance_team': teams['Electricians'],
                'location': 'Generator Room',
                'purchase_date': '2022-01-30',
                'warranty_expiry': '2027-01-30',
            },
            {
                'equipment_name': 'Welding Machine MIG',
                'serial_number': 'WELD-MIG-150',
                'category': 'Machinery',
                'department': 'Production',
                'maintenance_team': teams['Mechanics'],
                'location': 'Workshop A',
                'purchase_date': '2023-04-12',
                'warranty_expiry': '2026-04-12',
            },
            {
                'equipment_name': 'Server Rack Unit 1',
                'serial_number': 'SRV-RACK-001',
                'category': 'Computer',
                'department': 'IT',
                'maintenance_team': teams['IT Support'],
                'location': 'Server Room',
                'purchase_date': '2022-11-08',
                'warranty_expiry': '2025-11-08',
            },
            {
                'equipment_name': 'Elevator Car 1',
                'serial_number': 'ELEV-C1-001',
                'category': 'Facilities',
                'department': 'Facilities',
                'maintenance_team': teams['Facilities'],
                'location': 'Main Building',
                'purchase_date': '2020-09-15',
                'warranty_expiry': '2025-09-15',
            },
            {
                'equipment_name': 'Fire Suppression System',
                'serial_number': 'FIRE-SYS-001',
                'category': 'Safety',
                'department': 'Facilities',
                'maintenance_team': teams['Facilities'],
                'location': 'Throughout Building',
                'purchase_date': '2021-02-20',
                'warranty_expiry': '2026-02-20',
            },
            {
                'equipment_name': '3D Printer Ultimaker',
                'serial_number': '3D-ULT-001',
                'category': 'Printer',
                'department': 'R&D',
                'maintenance_team': teams['IT Support'],
                'location': 'R&D Lab',
                'purchase_date': '2023-08-25',
                'warranty_expiry': '2026-08-25',
            },
        ]

        created_count = 0
        existing_count = 0

        for eq_data in equipment_data:
            # Convert date strings to date objects
            from datetime import datetime
            purchase_date = datetime.strptime(eq_data['purchase_date'], '%Y-%m-%d').date() if eq_data.get('purchase_date') else None
            warranty_expiry = datetime.strptime(eq_data['warranty_expiry'], '%Y-%m-%d').date() if eq_data.get('warranty_expiry') else None

            equipment, created = Equipment.objects.get_or_create(
                serial_number=eq_data['serial_number'],
                defaults={
                    'equipment_name': eq_data['equipment_name'],
                    'category': eq_data['category'],
                    'department': eq_data.get('department', ''),
                    'maintenance_team': eq_data['maintenance_team'],
                    'location': eq_data.get('location', ''),
                    'purchase_date': purchase_date,
                    'warranty_expiry': warranty_expiry,
                    'default_technician': default_tech,
                }
            )
            
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Created equipment: {equipment.equipment_name}')
                )
            else:
                existing_count += 1
                self.stdout.write(
                    self.style.WARNING(f'Equipment already exists: {equipment.equipment_name}')
                )

        # Assign users to equipment (assigned_to_user field)
        self.stdout.write('\nAssigning users to equipment...\n')
        users = User.objects.filter(profile__role='User')[:5]
        equipment_list = Equipment.objects.all()[:len(users)]
        for i, equipment in enumerate(equipment_list):
            if i < len(users):
                equipment.assigned_to_user = users[i]
                equipment.save()
                self.stdout.write(
                    self.style.SUCCESS(f'Assigned {users[i].username} to {equipment.equipment_name}')
                )

        # Assign technicians to teams
        self.stdout.write('\nAssigning technicians to teams...\n')
        technicians = User.objects.filter(profile__role='Technician')
        team_assignments = [
            (technicians[0] if len(technicians) > 0 else None, teams['Mechanics'], 'Lead Technician'),
            (technicians[1] if len(technicians) > 1 else None, teams['Mechanics'], 'Technician'),
            (technicians[2] if len(technicians) > 2 else None, teams['IT Support'], 'Lead Technician'),
            (technicians[3] if len(technicians) > 3 else None, teams['Electricians'], 'Technician'),
            (technicians[0] if len(technicians) > 0 else None, teams['HVAC Team'], 'Technician'),
            (technicians[1] if len(technicians) > 1 else None, teams['Plumbing'], 'Technician'),
        ]
        
        for tech, team, role in team_assignments:
            if tech and team:
                team_member, created = TeamMember.objects.get_or_create(
                    user=tech,
                    team=team,
                    defaults={'role_in_team': role}
                )
                if created:
                    self.stdout.write(
                        self.style.SUCCESS(f'Assigned {tech.username} to {team.team_name} as {role}')
                    )

        # Update equipment with assigned technicians and specifications
        self.stdout.write('\nUpdating equipment with technicians and specifications...\n')
        equipment_list = Equipment.objects.all()
        for equipment in equipment_list:
            # Assign default technician from the equipment's team
            team_members = TeamMember.objects.filter(team=equipment.maintenance_team)
            if team_members.exists():
                equipment.default_technician = team_members.first().user
            # Add specifications
            equipment.specifications = f"""
Specifications for {equipment.equipment_name}:
- Model: {equipment.serial_number}
- Category: {equipment.category}
- Department: {equipment.department or 'N/A'}
- Location: {equipment.location or 'N/A'}
- Maintenance Team: {equipment.maintenance_team.team_name}
- Purchase Date: {equipment.purchase_date or 'N/A'}
- Warranty Expiry: {equipment.warranty_expiry or 'N/A'}
            """.strip()
            equipment.save()

        # Create maintenance requests with all fields populated
        self.stdout.write('\nCreating maintenance requests...\n')
        managers = User.objects.filter(profile__role='Manager')
        regular_users = User.objects.filter(profile__role='User')
        
        requests_data = [
            # Corrective Requests - New Stage
            {
                'subject': 'Oil Leak Detected',
                'description': 'CNC machine has oil leaking from the hydraulic system. Immediate attention required.',
                'request_type': 'Corrective',
                'stage': 'New',
                'priority': 'High',
                'equipment': Equipment.objects.filter(equipment_name__icontains='CNC').first(),
                'created_by': regular_users[0] if regular_users.exists() else managers[0] if managers.exists() else User.objects.first(),
                'scheduled_date': timezone.now().date(),
            },
            {
                'subject': 'Printer Paper Jam',
                'description': 'Industrial printer keeps jamming. Multiple attempts to clear have failed.',
                'request_type': 'Corrective',
                'stage': 'New',
                'priority': 'Medium',
                'equipment': Equipment.objects.filter(equipment_name__icontains='Printer').first(),
                'created_by': regular_users[1] if len(regular_users) > 1 else regular_users[0] if regular_users.exists() else User.objects.first(),
                'scheduled_date': timezone.now().date() + timedelta(days=1),
            },
            {
                'subject': 'Forklift Battery Failure',
                'description': 'Battery not holding charge. Equipment unusable for warehouse operations.',
                'request_type': 'Corrective',
                'stage': 'New',
                'priority': 'Critical',
                'equipment': Equipment.objects.filter(equipment_name__icontains='Forklift').first(),
                'created_by': managers[0] if managers.exists() else User.objects.first(),
                'scheduled_date': timezone.now().date() - timedelta(days=2),
            },
            # Corrective Requests - In Progress
            {
                'subject': 'Server Rack Cooling Issue',
                'description': 'Server room temperature rising. Cooling system needs inspection.',
                'request_type': 'Corrective',
                'stage': 'In Progress',
                'priority': 'High',
                'equipment': Equipment.objects.filter(equipment_name__icontains='Server').first(),
                'created_by': managers[0] if managers.exists() else User.objects.first(),
                'assigned_technician': technicians[2] if len(technicians) > 2 else technicians[0] if technicians.exists() else None,
                'scheduled_date': timezone.now().date() - timedelta(days=1),
                'actual_start_time': timezone.now() - timedelta(hours=2),
                'technician_notes': 'Inspected cooling fans. One fan not working. Replacement part ordered.',
            },
            {
                'subject': 'Welding Machine Overheating',
                'description': 'Machine shuts down after 30 minutes of use due to overheating.',
                'request_type': 'Corrective',
                'stage': 'In Progress',
                'priority': 'Medium',
                'equipment': Equipment.objects.filter(equipment_name__icontains='Welding').first(),
                'created_by': regular_users[0] if regular_users.exists() else User.objects.first(),
                'assigned_technician': technicians[0] if technicians.exists() else None,
                'scheduled_date': timezone.now().date(),
                'actual_start_time': timezone.now() - timedelta(hours=5),
                'technician_notes': 'Cleaned air filters. Checking thermal sensors.',
            },
            # Corrective Requests - Repaired
            {
                'subject': 'Air Compressor Pressure Drop',
                'description': 'Compressor not maintaining required pressure levels.',
                'request_type': 'Corrective',
                'stage': 'Repaired',
                'priority': 'Medium',
                'equipment': Equipment.objects.filter(equipment_name__icontains='Compressor').first(),
                'created_by': managers[0] if managers.exists() else User.objects.first(),
                'assigned_technician': technicians[0] if technicians.exists() else None,
                'scheduled_date': timezone.now().date() - timedelta(days=5),
                'completed_date': timezone.now().date() - timedelta(days=3),
                'actual_start_time': timezone.now() - timedelta(days=5, hours=2),
                'actual_end_time': timezone.now() - timedelta(days=3, hours=4),
                'duration_hours': 18.5,
                'technician_notes': 'Replaced pressure regulator valve. System tested and working properly.',
                'resolution_summary': 'Pressure regulator valve was faulty. Replaced with new part. System now maintaining optimal pressure.',
            },
            {
                'subject': 'Laptop Screen Flickering',
                'description': 'Dell XPS laptop screen flickers intermittently. Affecting productivity.',
                'request_type': 'Corrective',
                'stage': 'Repaired',
                'priority': 'Low',
                'equipment': Equipment.objects.filter(equipment_name__icontains='Laptop').first(),
                'created_by': regular_users[0] if regular_users.exists() else User.objects.first(),
                'assigned_technician': technicians[2] if len(technicians) > 2 else technicians[0] if technicians.exists() else None,
                'scheduled_date': timezone.now().date() - timedelta(days=7),
                'completed_date': timezone.now().date() - timedelta(days=6),
                'actual_start_time': timezone.now() - timedelta(days=7, hours=1),
                'actual_end_time': timezone.now() - timedelta(days=6, hours=3),
                'duration_hours': 2.0,
                'technician_notes': 'Updated display drivers. Issue resolved.',
                'resolution_summary': 'Display driver update fixed the flickering issue. No hardware replacement needed.',
            },
            # Preventive Requests - New
            {
                'subject': 'Quarterly CNC Machine Service',
                'description': 'Scheduled quarterly maintenance for CNC machine. Includes lubrication, calibration, and inspection.',
                'request_type': 'Preventive',
                'stage': 'New',
                'priority': 'Low',
                'equipment': Equipment.objects.filter(equipment_name__icontains='CNC').first(),
                'created_by': managers[0] if managers.exists() else User.objects.first(),
                'scheduled_date': timezone.now().date() + timedelta(days=7),
            },
            {
                'subject': 'Monthly HVAC System Inspection',
                'description': 'Regular monthly inspection of HVAC unit. Check filters, refrigerant levels, and system performance.',
                'request_type': 'Preventive',
                'stage': 'New',
                'priority': 'Low',
                'equipment': Equipment.objects.filter(equipment_name__icontains='HVAC').first(),
                'created_by': managers[0] if managers.exists() else User.objects.first(),
                'scheduled_date': timezone.now().date() + timedelta(days=3),
            },
            {
                'subject': 'Annual Electrical Panel Inspection',
                'description': 'Annual safety inspection of main electrical panel. Check connections, breakers, and safety systems.',
                'request_type': 'Preventive',
                'stage': 'New',
                'priority': 'Medium',
                'equipment': Equipment.objects.filter(equipment_name__icontains='Electrical').first(),
                'created_by': managers[0] if managers.exists() else User.objects.first(),
                'scheduled_date': timezone.now().date() + timedelta(days=14),
            },
            # Preventive Requests - In Progress
            {
                'subject': 'Weekly Generator Test',
                'description': 'Weekly backup generator test run. Verify automatic transfer switch and load capacity.',
                'request_type': 'Preventive',
                'stage': 'In Progress',
                'priority': 'Medium',
                'equipment': Equipment.objects.filter(equipment_name__icontains='Generator').first(),
                'created_by': managers[0] if managers.exists() else User.objects.first(),
                'assigned_technician': technicians[3] if len(technicians) > 3 else technicians[0] if technicians.exists() else None,
                'scheduled_date': timezone.now().date(),
                'actual_start_time': timezone.now() - timedelta(hours=1),
                'technician_notes': 'Generator test in progress. All systems functioning normally so far.',
            },
            # Preventive Requests - Repaired
            {
                'subject': 'Monthly Air Compressor Service',
                'description': 'Regular monthly inspection and service of air compressor system.',
                'request_type': 'Preventive',
                'stage': 'Repaired',
                'priority': 'Low',
                'equipment': Equipment.objects.filter(equipment_name__icontains='Compressor').first(),
                'created_by': managers[0] if managers.exists() else User.objects.first(),
                'assigned_technician': technicians[0] if technicians.exists() else None,
                'scheduled_date': timezone.now().date() - timedelta(days=30),
                'completed_date': timezone.now().date() - timedelta(days=30),
                'actual_start_time': timezone.now() - timedelta(days=30, hours=2),
                'actual_end_time': timezone.now() - timedelta(days=30, hours=4),
                'duration_hours': 2.0,
                'technician_notes': 'Completed monthly service. Replaced air filter and checked oil levels.',
                'resolution_summary': 'Monthly service completed successfully. All components in good condition.',
            },
        ]

        requests_created = 0
        for req_data in requests_data:
            # Skip if equipment doesn't exist
            if not req_data['equipment']:
                continue
            
            # Auto-assign maintenance team from equipment
            req_data['maintenance_team'] = req_data['equipment'].maintenance_team
            
            # Create the request
            request_obj = MaintenanceRequest.objects.create(**req_data)
            requests_created += 1
            self.stdout.write(
                self.style.SUCCESS(f'Created request: {request_obj.subject} ({request_obj.stage})')
            )

        self.stdout.write(
            self.style.SUCCESS(
                f'\n{"="*60}\n'
                f'Summary:\n'
                f'- Teams: {len(teams)} (all created/verified)\n'
                f'- Equipment: {created_count} created, {existing_count} already existed\n'
                f'- Users assigned to equipment: {min(len(users), len(equipment_list))}\n'
                f'- Team members assigned: {TeamMember.objects.count()}\n'
                f'- Maintenance requests created: {requests_created}\n'
                f'\nComprehensive sample data added successfully!'
                f'\n{"="*60}'
            )
        )

