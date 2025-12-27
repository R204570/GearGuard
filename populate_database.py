"""
Automated script to populate PostgreSQL database with comprehensive dummy data
for GearGuard Maintenance Management System.

This script creates:
- Users with different roles (Admin, Manager, Technician, User)
- Maintenance Teams
- Team Members (assigning technicians to teams)
- Equipment with full details
- Maintenance Requests (Corrective and Preventive) in various stages

Usage:
    python populate_database.py

Requirements:
    - Django project must be set up
    - Database migrations must be applied
    - PostgreSQL database must be running and accessible
"""

import os
import sys
import django
from datetime import datetime, timedelta
from decimal import Decimal

# Setup Django environment (minimal setup to access settings)
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gearguard.settings')


def create_database_if_not_exists():
    """Create the database if it doesn't exist."""
    try:
        import psycopg2
        from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
        
        # Setup Django to access settings
        django.setup()
        from django.conf import settings
        
        db_config = settings.DATABASES['default']
        db_name = db_config['NAME']
        db_user = db_config['USER']
        db_password = db_config['PASSWORD']
        db_host = db_config['HOST']
        db_port = db_config['PORT']
        
        print("\n" + "="*60)
        print("Checking Database...")
        print("="*60)
        
        # Connect to PostgreSQL server (using default 'postgres' database)
        try:
            conn = psycopg2.connect(
                dbname="postgres",
                user=db_user,
                password=db_password,
                host=db_host,
                port=db_port,
            )
            
            conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            cursor = conn.cursor()
            
            # Check if database exists
            cursor.execute(
                "SELECT 1 FROM pg_database WHERE datname = %s",
                (db_name,)
            )
            
            if cursor.fetchone() is None:
                # Database doesn't exist, create it
                cursor.execute(f'CREATE DATABASE "{db_name}"')
                print(f"✓ Database '{db_name}' created successfully")
                print(f"  ⚠ Note: New database created. Make sure to run migrations:")
                print(f"      python manage.py migrate")
            else:
                print(f"✓ Database '{db_name}' already exists")
            
            cursor.close()
            conn.close()
            
        except psycopg2.OperationalError as e:
            print(f"✗ Error connecting to PostgreSQL: {str(e)}")
            print(f"  Please ensure PostgreSQL is running and credentials are correct.")
            print(f"  Host: {db_host}, Port: {db_port}, User: {db_user}")
            sys.exit(1)
            
    except ImportError:
        print("⚠ Warning: psycopg2 not available. Skipping database creation check.")
        print("  Please ensure the database 'gearguard' exists before running migrations.")
        django.setup()  # Setup Django even if psycopg2 is not available
    except Exception as e:
        print(f"⚠ Warning: Could not check/create database: {str(e)}")
        print("  Please ensure the database 'gearguard' exists before running migrations.")
        if not django.apps.apps.ready:
            django.setup()  # Setup Django anyway


# Check and create database if needed
create_database_if_not_exists()

# Ensure Django is fully setup
if not django.apps.apps.ready:
    django.setup()

from django.contrib.auth.models import User
from django.utils import timezone
from maintenance.models import (
    UserProfile, MaintenanceTeam, TeamMember, Equipment, MaintenanceRequest
)


def create_users():
    """Create users with different roles."""
    print("\n" + "="*60)
    print("Creating Users...")
    print("="*60)
    
    users_data = [
        # Admins
        {'username': 'admin', 'email': 'admin@gearguard.com', 'first_name': 'System', 'last_name': 'Administrator', 'role': 'Admin', 'password': 'admin123'},
        {'username': 'admin2', 'email': 'admin2@gearguard.com', 'first_name': 'John', 'last_name': 'Admin', 'role': 'Admin', 'password': 'admin123'},
        
        # Managers
        {'username': 'manager1', 'email': 'manager1@gearguard.com', 'first_name': 'Sarah', 'last_name': 'Johnson', 'role': 'Manager', 'password': 'manager123'},
        {'username': 'manager2', 'email': 'manager2@gearguard.com', 'first_name': 'Michael', 'last_name': 'Chen', 'role': 'Manager', 'password': 'manager123'},
        
        # Technicians
        {'username': 'tech1', 'email': 'tech1@gearguard.com', 'first_name': 'David', 'last_name': 'Williams', 'role': 'Technician', 'password': 'tech123'},
        {'username': 'tech2', 'email': 'tech2@gearguard.com', 'first_name': 'Emily', 'last_name': 'Brown', 'role': 'Technician', 'password': 'tech123'},
        {'username': 'tech3', 'email': 'tech3@gearguard.com', 'first_name': 'James', 'last_name': 'Davis', 'role': 'Technician', 'password': 'tech123'},
        {'username': 'tech4', 'email': 'tech4@gearguard.com', 'first_name': 'Lisa', 'last_name': 'Miller', 'role': 'Technician', 'password': 'tech123'},
        {'username': 'tech5', 'email': 'tech5@gearguard.com', 'first_name': 'Robert', 'last_name': 'Wilson', 'role': 'Technician', 'password': 'tech123'},
        
        # Regular Users
        {'username': 'user1', 'email': 'user1@gearguard.com', 'first_name': 'Alice', 'last_name': 'Smith', 'role': 'User', 'password': 'user123'},
        {'username': 'user2', 'email': 'user2@gearguard.com', 'first_name': 'Bob', 'last_name': 'Jones', 'role': 'User', 'password': 'user123'},
        {'username': 'user3', 'email': 'user3@gearguard.com', 'first_name': 'Carol', 'last_name': 'Taylor', 'role': 'User', 'password': 'user123'},
        {'username': 'user4', 'email': 'user4@gearguard.com', 'first_name': 'Daniel', 'last_name': 'Anderson', 'role': 'User', 'password': 'user123'},
        {'username': 'user5', 'email': 'user5@gearguard.com', 'first_name': 'Emma', 'last_name': 'Martinez', 'role': 'User', 'password': 'user123'},
    ]
    
    created_users = []
    for user_data in users_data:
        user, created = User.objects.get_or_create(
            username=user_data['username'],
            defaults={
                'email': user_data['email'],
                'first_name': user_data['first_name'],
                'last_name': user_data['last_name'],
            }
        )
        
        if created:
            user.set_password(user_data['password'])
            user.save()
            print(f"✓ Created user: {user_data['username']} ({user_data['role']})")
        else:
            print(f"⚠ User already exists: {user_data['username']}")
        
        # Create or update profile
        profile, profile_created = UserProfile.objects.get_or_create(
            user=user,
            defaults={'role': user_data['role']}
        )
        
        if not profile_created and profile.role != user_data['role']:
            profile.role = user_data['role']
            profile.save()
            print(f"  Updated role to: {user_data['role']}")
        
        created_users.append(user)
    
    return created_users


def create_teams():
    """Create maintenance teams."""
    print("\n" + "="*60)
    print("Creating Maintenance Teams...")
    print("="*60)
    
    teams_data = [
        {
            'team_name': 'Mechanics Team',
            'description': 'Handles mechanical equipment repairs, maintenance, and servicing. Specializes in machinery, vehicles, and mechanical systems.'
        },
        {
            'team_name': 'Electrical Team',
            'description': 'Electrical systems maintenance, wiring, panels, and electrical equipment repairs.'
        },
        {
            'team_name': 'IT Support Team',
            'description': 'Computer hardware, software support, network equipment, and IT infrastructure maintenance.'
        },
        {
            'team_name': 'HVAC Team',
            'description': 'Heating, ventilation, and air conditioning systems maintenance and repairs.'
        },
        {
            'team_name': 'Facilities Team',
            'description': 'General building maintenance, facilities management, and infrastructure upkeep.'
        },
        {
            'team_name': 'Plumbing Team',
            'description': 'Water systems, plumbing, and drainage maintenance and repairs.'
        },
    ]
    
    teams = {}
    for team_data in teams_data:
        team, created = MaintenanceTeam.objects.get_or_create(
            team_name=team_data['team_name'],
            defaults={'description': team_data['description']}
        )
        
        if created:
            print(f"✓ Created team: {team.team_name}")
        else:
            print(f"⚠ Team already exists: {team.team_name}")
        
        teams[team_data['team_name']] = team
    
    return teams


def assign_team_members(teams, users):
    """Assign technicians to teams."""
    print("\n" + "="*60)
    print("Assigning Team Members...")
    print("="*60)
    
    technicians = [u for u in users if u.profile.role == 'Technician']
    
    assignments = [
        (technicians[0] if len(technicians) > 0 else None, 'Mechanics Team', 'Lead Technician'),
        (technicians[1] if len(technicians) > 1 else None, 'Mechanics Team', 'Technician'),
        (technicians[2] if len(technicians) > 2 else None, 'Electrical Team', 'Lead Technician'),
        (technicians[3] if len(technicians) > 3 else None, 'Electrical Team', 'Technician'),
        (technicians[0] if len(technicians) > 0 else None, 'IT Support Team', 'Lead Technician'),
        (technicians[1] if len(technicians) > 1 else None, 'IT Support Team', 'Technician'),
        (technicians[4] if len(technicians) > 4 else None, 'IT Support Team', 'Technician'),
        (technicians[2] if len(technicians) > 2 else None, 'HVAC Team', 'Technician'),
        (technicians[3] if len(technicians) > 3 else None, 'Facilities Team', 'Technician'),
        (technicians[4] if len(technicians) > 4 else None, 'Plumbing Team', 'Technician'),
    ]
    
    for tech, team_name, role in assignments:
        if tech and team_name in teams:
            team = teams[team_name]
            member, created = TeamMember.objects.get_or_create(
                user=tech,
                team=team,
                defaults={'role_in_team': role}
            )
            
            if created:
                print(f"✓ Assigned {tech.get_full_name()} to {team.team_name} as {role}")
            else:
                print(f"⚠ {tech.get_full_name()} already in {team.team_name}")


def create_equipment(teams, users):
    """Create equipment with full details."""
    print("\n" + "="*60)
    print("Creating Equipment...")
    print("="*60)
    
    technicians = [u for u in users if u.profile.role == 'Technician']
    regular_users = [u for u in users if u.profile.role == 'User']
    
    equipment_data = [
        {
            'equipment_name': 'CNC Milling Machine Model X-5000',
            'serial_number': 'CNC-2023-001',
            'category': 'Machinery',
            'department': 'Production',
            'maintenance_team': teams['Mechanics Team'],
            'location': 'Factory Floor A - Bay 3',
            'purchase_date': datetime(2023, 1, 15).date(),
            'warranty_expiry': datetime(2026, 1, 15).date(),
            'maintenance_interval_days': 90,
            'specifications': 'High-precision CNC milling machine with 5-axis capability. Maximum workpiece size: 500x300x200mm. Spindle speed: 12,000 RPM.',
        },
        {
            'equipment_name': 'Dell XPS 15 Laptop',
            'serial_number': 'DELL-LT-5001',
            'category': 'Computer',
            'department': 'IT',
            'maintenance_team': teams['IT Support Team'],
            'location': 'Office 204 - Desk 12',
            'purchase_date': datetime(2023, 6, 20).date(),
            'warranty_expiry': datetime(2026, 6, 20).date(),
            'maintenance_interval_days': 180,
            'specifications': 'Dell XPS 15, Intel i7, 16GB RAM, 512GB SSD, 15.6" 4K Display',
        },
        {
            'equipment_name': 'HP Industrial Laser Printer',
            'serial_number': 'HP-IP-9000',
            'category': 'Printer',
            'department': 'Administration',
            'maintenance_team': teams['IT Support Team'],
            'location': 'Print Room - Main Office',
            'purchase_date': datetime(2022, 3, 10).date(),
            'warranty_expiry': datetime(2025, 3, 10).date(),
            'maintenance_interval_days': 30,
            'specifications': 'HP LaserJet Enterprise, 50ppm, Duplex printing, Network capable',
        },
        {
            'equipment_name': 'Toyota Forklift 3000kg',
            'serial_number': 'FORK-TY-3000',
            'category': 'Vehicle',
            'department': 'Warehouse',
            'maintenance_team': teams['Mechanics Team'],
            'location': 'Warehouse B - Loading Bay',
            'purchase_date': datetime(2021, 11, 5).date(),
            'warranty_expiry': datetime(2024, 11, 5).date(),
            'maintenance_interval_days': 60,
            'specifications': 'Toyota 8FBE30 Electric Forklift, 3000kg capacity, 48V battery system',
        },
        {
            'equipment_name': 'Industrial Air Compressor 450CFM',
            'serial_number': 'AC-COMP-450',
            'category': 'Machinery',
            'department': 'Production',
            'maintenance_team': teams['Mechanics Team'],
            'location': 'Factory Floor B - Compressor Room',
            'purchase_date': datetime(2022, 8, 12).date(),
            'warranty_expiry': datetime(2025, 8, 12).date(),
            'maintenance_interval_days': 30,
            'specifications': 'Rotary screw air compressor, 450 CFM, 150 PSI, 50HP motor',
        },
        {
            'equipment_name': 'Conference Room PC System',
            'serial_number': 'HP-PC-CR01',
            'category': 'Computer',
            'department': 'Administration',
            'maintenance_team': teams['IT Support Team'],
            'location': 'Conference Room 1',
            'purchase_date': datetime(2023, 9, 1).date(),
            'warranty_expiry': datetime(2026, 9, 1).date(),
            'maintenance_interval_days': 90,
            'specifications': 'HP ProDesk 600 G6, Intel i5, 8GB RAM, 256GB SSD, Windows 11 Pro',
        },
        {
            'equipment_name': 'HVAC Unit Main Building',
            'serial_number': 'HVAC-MB-001',
            'category': 'HVAC',
            'department': 'Facilities',
            'maintenance_team': teams['HVAC Team'],
            'location': 'Roof - Main Building',
            'purchase_date': datetime(2020, 5, 20).date(),
            'warranty_expiry': datetime(2025, 5, 20).date(),
            'maintenance_interval_days': 30,
            'specifications': 'Central HVAC system, 50-ton capacity, Variable speed compressor, Smart controls',
        },
        {
            'equipment_name': 'Water Pump System 200GPM',
            'serial_number': 'WP-SYS-200',
            'category': 'Plumbing',
            'department': 'Facilities',
            'maintenance_team': teams['Plumbing Team'],
            'location': 'Basement - Pump Room',
            'purchase_date': datetime(2021, 3, 15).date(),
            'warranty_expiry': datetime(2026, 3, 15).date(),
            'maintenance_interval_days': 60,
            'specifications': 'Centrifugal water pump system, 200 GPM capacity, 100 PSI, Stainless steel construction',
        },
        {
            'equipment_name': 'Main Electrical Panel 400A',
            'serial_number': 'ELEC-PNL-001',
            'category': 'Electrical',
            'department': 'Facilities',
            'maintenance_team': teams['Electrical Team'],
            'location': 'Electrical Room - Ground Floor',
            'purchase_date': datetime(2019, 7, 10).date(),
            'warranty_expiry': datetime(2024, 7, 10).date(),
            'maintenance_interval_days': 180,
            'specifications': 'Main electrical distribution panel, 400A service, 3-phase, 208V/120V',
        },
        {
            'equipment_name': 'Backup Generator 500kW',
            'serial_number': 'GEN-500-001',
            'category': 'Electrical',
            'department': 'Facilities',
            'maintenance_team': teams['Electrical Team'],
            'location': 'Generator Room - Exterior',
            'purchase_date': datetime(2022, 1, 30).date(),
            'warranty_expiry': datetime(2027, 1, 30).date(),
            'maintenance_interval_days': 30,
            'specifications': 'Diesel backup generator, 500kW capacity, Automatic transfer switch, Weatherproof enclosure',
        },
        {
            'equipment_name': 'MIG Welding Machine 150A',
            'serial_number': 'WELD-MIG-150',
            'category': 'Machinery',
            'department': 'Production',
            'maintenance_team': teams['Mechanics Team'],
            'location': 'Workshop A - Welding Station',
            'purchase_date': datetime(2023, 4, 12).date(),
            'warranty_expiry': datetime(2026, 4, 12).date(),
            'maintenance_interval_days': 60,
            'specifications': 'MIG welding machine, 150A output, Gas/No-gas capable, Digital display',
        },
        {
            'equipment_name': 'Server Rack Unit 1',
            'serial_number': 'SRV-RACK-001',
            'category': 'Computer',
            'department': 'IT',
            'maintenance_team': teams['IT Support Team'],
            'location': 'Server Room - Rack 1',
            'purchase_date': datetime(2022, 11, 8).date(),
            'warranty_expiry': datetime(2025, 11, 8).date(),
            'maintenance_interval_days': 90,
            'specifications': '42U Server Rack, Network switches, UPS system, Cooling fans',
        },
        {
            'equipment_name': 'Elevator Car 1',
            'serial_number': 'ELEV-C1-001',
            'category': 'Facilities',
            'department': 'Facilities',
            'maintenance_team': teams['Facilities Team'],
            'location': 'Main Building - Elevator Shaft 1',
            'purchase_date': datetime(2020, 9, 15).date(),
            'warranty_expiry': datetime(2025, 9, 15).date(),
            'maintenance_interval_days': 30,
            'specifications': 'Passenger elevator, 2000kg capacity, 8 floors, Modern control system',
        },
        {
            'equipment_name': 'Fire Suppression System',
            'serial_number': 'FIRE-SYS-001',
            'category': 'Safety',
            'department': 'Facilities',
            'maintenance_team': teams['Facilities Team'],
            'location': 'Throughout Building',
            'purchase_date': datetime(2021, 2, 20).date(),
            'warranty_expiry': datetime(2026, 2, 20).date(),
            'maintenance_interval_days': 90,
            'specifications': 'Sprinkler fire suppression system, Smoke detectors, Alarm system, Central monitoring',
        },
        {
            'equipment_name': 'Ultimaker 3D Printer',
            'serial_number': '3D-ULT-001',
            'category': 'Printer',
            'department': 'R&D',
            'maintenance_team': teams['IT Support Team'],
            'location': 'R&D Lab - Prototyping Area',
            'purchase_date': datetime(2023, 8, 25).date(),
            'warranty_expiry': datetime(2026, 8, 25).date(),
            'maintenance_interval_days': 60,
            'specifications': 'Ultimaker S5 3D Printer, Dual extrusion, Build volume 330x240x300mm, PLA/ABS compatible',
        },
    ]
    
    created_equipment = []
    for i, eq_data in enumerate(equipment_data):
        # Assign default technician from team
        team_members = TeamMember.objects.filter(team=eq_data['maintenance_team'])
        default_tech = team_members.first().user if team_members.exists() else (technicians[0] if technicians else None)
        
        # Assign to user (if available)
        assigned_user = regular_users[i % len(regular_users)] if regular_users else None
        
        equipment, created = Equipment.objects.get_or_create(
            serial_number=eq_data['serial_number'],
            defaults={
                'equipment_name': eq_data['equipment_name'],
                'category': eq_data['category'],
                'department': eq_data['department'],
                'maintenance_team': eq_data['maintenance_team'],
                'location': eq_data['location'],
                'purchase_date': eq_data['purchase_date'],
                'warranty_expiry': eq_data['warranty_expiry'],
                'maintenance_interval_days': eq_data['maintenance_interval_days'],
                'specifications': eq_data['specifications'],
                'default_technician': default_tech,
                'assigned_to_user': assigned_user,
            }
        )
        
        if created:
            print(f"✓ Created equipment: {equipment.equipment_name}")
            created_equipment.append(equipment)
        else:
            print(f"⚠ Equipment already exists: {equipment.equipment_name}")
            created_equipment.append(equipment)
    
    return created_equipment


def create_maintenance_requests(equipment_list, users):
    """Create maintenance requests in various stages."""
    print("\n" + "="*60)
    print("Creating Maintenance Requests...")
    print("="*60)
    
    managers = [u for u in users if u.profile.role == 'Manager']
    regular_users = [u for u in users if u.profile.role == 'User']
    technicians = [u for u in users if u.profile.role == 'Technician']
    
    now = timezone.now()
    
    requests_data = [
        # Corrective - New
        {
            'subject': 'CNC Machine Oil Leak',
            'description': 'Hydraulic oil leak detected from CNC machine. Oil pooling on floor. Immediate attention required to prevent damage.',
            'request_type': 'Corrective',
            'stage': 'New',
            'priority': 'High',
            'equipment': next((e for e in equipment_list if 'CNC' in e.equipment_name), None),
            'created_by': regular_users[0] if regular_users else managers[0] if managers else users[0],
            'scheduled_date': now.date(),
        },
        {
            'subject': 'Printer Paper Jam - Multiple Attempts Failed',
            'description': 'Industrial printer keeps jamming. Multiple attempts to clear have failed. Paper path may be obstructed.',
            'request_type': 'Corrective',
            'stage': 'New',
            'priority': 'Medium',
            'equipment': next((e for e in equipment_list if 'Printer' in e.equipment_name and '3D' not in e.equipment_name), None),
            'created_by': regular_users[1] if len(regular_users) > 1 else regular_users[0] if regular_users else users[0],
            'scheduled_date': now.date() + timedelta(days=1),
        },
        {
            'subject': 'Forklift Battery Failure - Critical',
            'description': 'Forklift battery not holding charge. Equipment unusable for warehouse operations. Affecting daily operations.',
            'request_type': 'Corrective',
            'stage': 'New',
            'priority': 'Critical',
            'equipment': next((e for e in equipment_list if 'Forklift' in e.equipment_name), None),
            'created_by': managers[0] if managers else users[0],
            'scheduled_date': now.date() - timedelta(days=2),
        },
        
        # Corrective - In Progress
        {
            'subject': 'Server Rack Cooling System Failure',
            'description': 'Server room temperature rising. Cooling system needs immediate inspection. Risk of equipment overheating.',
            'request_type': 'Corrective',
            'stage': 'In Progress',
            'priority': 'High',
            'equipment': next((e for e in equipment_list if 'Server' in e.equipment_name), None),
            'created_by': managers[0] if managers else users[0],
            'assigned_technician': technicians[2] if len(technicians) > 2 else technicians[0] if technicians else None,
            'scheduled_date': now.date() - timedelta(days=1),
            'actual_start_time': now - timedelta(hours=2),
            'technician_notes': 'Inspected cooling fans. One fan not working. Replacement part ordered. Temporary fan installed.',
        },
        {
            'subject': 'Welding Machine Overheating Issue',
            'description': 'Machine shuts down after 30 minutes of use due to overheating. Thermal protection activating.',
            'request_type': 'Corrective',
            'stage': 'In Progress',
            'priority': 'Medium',
            'equipment': next((e for e in equipment_list if 'Welding' in e.equipment_name), None),
            'created_by': regular_users[0] if regular_users else users[0],
            'assigned_technician': technicians[0] if technicians else None,
            'scheduled_date': now.date(),
            'actual_start_time': now - timedelta(hours=5),
            'technician_notes': 'Cleaned air filters and ventilation system. Checking thermal sensors and cooling system.',
        },
        
        # Corrective - Repaired
        {
            'subject': 'Air Compressor Pressure Drop',
            'description': 'Compressor not maintaining required pressure levels. Production line affected.',
            'request_type': 'Corrective',
            'stage': 'Repaired',
            'priority': 'Medium',
            'equipment': next((e for e in equipment_list if 'Compressor' in e.equipment_name), None),
            'created_by': managers[0] if managers else users[0],
            'assigned_technician': technicians[0] if technicians else None,
            'scheduled_date': now.date() - timedelta(days=5),
            'completed_date': now.date() - timedelta(days=3),
            'actual_start_time': now - timedelta(days=5, hours=2),
            'actual_end_time': now - timedelta(days=3, hours=4),
            'duration_hours': Decimal('18.5'),
            'technician_notes': 'Replaced pressure regulator valve. System tested and working properly. All pressure levels normal.',
            'resolution_summary': 'Pressure regulator valve was faulty. Replaced with new part. System now maintaining optimal pressure. Production line operational.',
        },
        {
            'subject': 'Laptop Screen Flickering Issue',
            'description': 'Dell XPS laptop screen flickers intermittently. Affecting user productivity and causing eye strain.',
            'request_type': 'Corrective',
            'stage': 'Repaired',
            'priority': 'Low',
            'equipment': next((e for e in equipment_list if 'Laptop' in e.equipment_name), None),
            'created_by': regular_users[0] if regular_users else users[0],
            'assigned_technician': technicians[2] if len(technicians) > 2 else technicians[0] if technicians else None,
            'scheduled_date': now.date() - timedelta(days=7),
            'completed_date': now.date() - timedelta(days=6),
            'actual_start_time': now - timedelta(days=7, hours=1),
            'actual_end_time': now - timedelta(days=6, hours=3),
            'duration_hours': Decimal('2.0'),
            'technician_notes': 'Updated display drivers and BIOS. Issue resolved. No hardware replacement needed.',
            'resolution_summary': 'Display driver update fixed the flickering issue. System tested for 24 hours with no recurrence.',
        },
        
        # Preventive - New
        {
            'subject': 'Quarterly CNC Machine Service',
            'description': 'Scheduled quarterly maintenance for CNC machine. Includes lubrication, calibration, and comprehensive inspection.',
            'request_type': 'Preventive',
            'stage': 'New',
            'priority': 'Low',
            'equipment': next((e for e in equipment_list if 'CNC' in e.equipment_name), None),
            'created_by': managers[0] if managers else users[0],
            'scheduled_date': now.date() + timedelta(days=7),
            'estimated_duration_hours': Decimal('4.0'),
        },
        {
            'subject': 'Monthly HVAC System Inspection',
            'description': 'Regular monthly inspection of HVAC unit. Check filters, refrigerant levels, and system performance.',
            'request_type': 'Preventive',
            'stage': 'New',
            'priority': 'Low',
            'equipment': next((e for e in equipment_list if 'HVAC' in e.equipment_name), None),
            'created_by': managers[0] if managers else users[0],
            'scheduled_date': now.date() + timedelta(days=3),
            'estimated_duration_hours': Decimal('2.0'),
        },
        {
            'subject': 'Annual Electrical Panel Inspection',
            'description': 'Annual safety inspection of main electrical panel. Check connections, breakers, and safety systems.',
            'request_type': 'Preventive',
            'stage': 'New',
            'priority': 'Medium',
            'equipment': next((e for e in equipment_list if 'Electrical' in e.equipment_name), None),
            'created_by': managers[0] if managers else users[0],
            'scheduled_date': now.date() + timedelta(days=14),
            'estimated_duration_hours': Decimal('6.0'),
        },
        
        # Preventive - In Progress
        {
            'subject': 'Weekly Generator Test Run',
            'description': 'Weekly backup generator test run. Verify automatic transfer switch and load capacity.',
            'request_type': 'Preventive',
            'stage': 'In Progress',
            'priority': 'Medium',
            'equipment': next((e for e in equipment_list if 'Generator' in e.equipment_name), None),
            'created_by': managers[0] if managers else users[0],
            'assigned_technician': technicians[3] if len(technicians) > 3 else technicians[0] if technicians else None,
            'scheduled_date': now.date(),
            'actual_start_time': now - timedelta(hours=1),
            'technician_notes': 'Generator test in progress. All systems functioning normally so far. Load test scheduled next.',
            'estimated_duration_hours': Decimal('1.5'),
        },
        
        # Preventive - Repaired
        {
            'subject': 'Monthly Air Compressor Service',
            'description': 'Regular monthly inspection and service of air compressor system.',
            'request_type': 'Preventive',
            'stage': 'Repaired',
            'priority': 'Low',
            'equipment': next((e for e in equipment_list if 'Compressor' in e.equipment_name), None),
            'created_by': managers[0] if managers else users[0],
            'assigned_technician': technicians[0] if technicians else None,
            'scheduled_date': now.date() - timedelta(days=30),
            'completed_date': now.date() - timedelta(days=30),
            'actual_start_time': now - timedelta(days=30, hours=2),
            'actual_end_time': now - timedelta(days=30, hours=4),
            'duration_hours': Decimal('2.0'),
            'technician_notes': 'Completed monthly service. Replaced air filter and checked oil levels. All systems operational.',
            'resolution_summary': 'Monthly service completed successfully. All components in good condition. Next service scheduled.',
            'estimated_duration_hours': Decimal('2.0'),
        },
    ]
    
    created_requests = []
    for req_data in requests_data:
        # Skip if equipment doesn't exist
        if not req_data.get('equipment'):
            continue
        
        # Auto-assign maintenance team from equipment
        req_data['maintenance_team'] = req_data['equipment'].maintenance_team
        
        # Create the request
        try:
            request_obj = MaintenanceRequest.objects.create(**req_data)
            created_requests.append(request_obj)
            print(f"✓ Created request: {request_obj.subject} ({request_obj.stage})")
        except Exception as e:
            print(f"✗ Error creating request '{req_data['subject']}': {str(e)}")
    
    return created_requests


def main():
    """Main function to populate database."""
    print("\n" + "="*70)
    print("GearGuard Database Population Script")
    print("="*70)
    print("\nThis script will populate your database with comprehensive dummy data.")
    print("This includes users, teams, equipment, and maintenance requests.\n")
    
    try:
        # Create users
        users = create_users()
        
        # Create teams
        teams = create_teams()
        
        # Assign team members
        assign_team_members(teams, users)
        
        # Create equipment
        equipment_list = create_equipment(teams, users)
        
        # Create maintenance requests
        requests = create_maintenance_requests(equipment_list, users)
        
        # Summary
        print("\n" + "="*70)
        print("POPULATION COMPLETE!")
        print("="*70)
        print(f"\nSummary:")
        print(f"  ✓ Users created: {User.objects.count()}")
        print(f"  ✓ Teams created: {MaintenanceTeam.objects.count()}")
        print(f"  ✓ Team members: {TeamMember.objects.count()}")
        print(f"  ✓ Equipment created: {Equipment.objects.count()}")
        print(f"  ✓ Maintenance requests: {MaintenanceRequest.objects.count()}")
        print("\n" + "="*70)
        print("\nDefault Login Credentials:")
        print("  Admin:    admin / admin123")
        print("  Manager:  manager1 / manager123")
        print("  Technician: tech1 / tech123")
        print("  User:     user1 / user123")
        print("\n" + "="*70)
        print("\n✓ Database populated successfully!")
        print("="*70 + "\n")
        
    except Exception as e:
        print(f"\n✗ Error during population: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()

