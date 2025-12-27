"""
Management command to create users with all roles.
Usage: python manage.py create_all_users
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from maintenance.models import UserProfile, MaintenanceTeam, TeamMember


class Command(BaseCommand):
    help = 'Create users with all roles (Admin, Manager, Technician, User)'

    def handle(self, *args, **options):
        self.stdout.write('Creating users with all roles...\n')

        # Users data with their roles
        users_data = [
            # Admins
            {'username': 'admin', 'email': 'admin@gearguard.com', 'password': 'admin123', 'role': 'Admin', 'first_name': 'John', 'last_name': 'Admin'},
            {'username': 'admin2', 'email': 'admin2@gearguard.com', 'password': 'admin123', 'role': 'Admin', 'first_name': 'Sarah', 'last_name': 'Administrator'},
            
            # Managers
            {'username': 'manager', 'email': 'manager@gearguard.com', 'password': 'manager123', 'role': 'Manager', 'first_name': 'Mike', 'last_name': 'Manager'},
            {'username': 'manager2', 'email': 'manager2@gearguard.com', 'password': 'manager123', 'role': 'Manager', 'first_name': 'Lisa', 'last_name': 'Supervisor'},
            
            # Technicians
            {'username': 'tech1', 'email': 'tech1@gearguard.com', 'password': 'tech123', 'role': 'Technician', 'first_name': 'David', 'last_name': 'Technician'},
            {'username': 'tech2', 'email': 'tech2@gearguard.com', 'password': 'tech123', 'role': 'Technician', 'first_name': 'Emma', 'last_name': 'Engineer'},
            {'username': 'tech3', 'email': 'tech3@gearguard.com', 'password': 'tech123', 'role': 'Technician', 'first_name': 'James', 'last_name': 'Repair'},
            {'username': 'tech4', 'email': 'tech4@gearguard.com', 'password': 'tech123', 'role': 'Technician', 'first_name': 'Maria', 'last_name': 'Specialist'},
            
            # Regular Users
            {'username': 'user1', 'email': 'user1@gearguard.com', 'password': 'user123', 'role': 'User', 'first_name': 'Bob', 'last_name': 'Employee'},
            {'username': 'user2', 'email': 'user2@gearguard.com', 'password': 'user123', 'role': 'User', 'first_name': 'Alice', 'last_name': 'Worker'},
            {'username': 'user3', 'email': 'user3@gearguard.com', 'password': 'user123', 'role': 'User', 'first_name': 'Charlie', 'last_name': 'Staff'},
            {'username': 'user4', 'email': 'user4@gearguard.com', 'password': 'user123', 'role': 'User', 'first_name': 'Diana', 'last_name': 'Member'},
        ]

        created_count = 0
        updated_count = 0
        skipped_count = 0

        for user_data in users_data:
            username = user_data['username']
            email = user_data['email']
            password = user_data['password']
            role = user_data['role']
            first_name = user_data.get('first_name', '')
            last_name = user_data.get('last_name', '')

            # Check if user already exists
            if User.objects.filter(username=username).exists():
                user = User.objects.get(username=username)
                self.stdout.write(
                    self.style.WARNING(f'User "{username}" already exists. Updating...')
                )
                
                # Update user info
                user.email = email
                user.first_name = first_name
                user.last_name = last_name
                user.set_password(password)
                user.save()
                
                # Update or create profile
                profile, created = UserProfile.objects.get_or_create(user=user)
                profile.role = role
                profile.save()
                
                updated_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'  Updated user "{username}" with role "{role}"')
                )
            else:
                # Create new user
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=password,
                    first_name=first_name,
                    last_name=last_name
                )
                
                # Create profile with role
                profile, created = UserProfile.objects.get_or_create(
                    user=user,
                    defaults={'role': role}
                )
                if not created:
                    profile.role = role
                    profile.save()
                
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Created user "{username}" with role "{role}"')
                )

        # Assign technicians to teams
        self.stdout.write('\nAssigning technicians to teams...\n')
        
        # Get teams
        try:
            mechanics_team = MaintenanceTeam.objects.get(team_name='Mechanics')
            it_team = MaintenanceTeam.objects.get(team_name='IT Support')
            electricians_team = MaintenanceTeam.objects.get(team_name='Electricians')
            hvac_team = MaintenanceTeam.objects.get(team_name='HVAC Team')
            
            # Get technicians
            tech1 = User.objects.get(username='tech1')
            tech2 = User.objects.get(username='tech2')
            tech3 = User.objects.get(username='tech3')
            tech4 = User.objects.get(username='tech4')
            
            # Assign technicians to teams
            team_assignments = [
                (tech1, mechanics_team, 'Lead Technician'),
                (tech2, mechanics_team, 'Technician'),
                (tech2, electricians_team, 'Technician'),
                (tech3, it_team, 'Lead Technician'),
                (tech4, hvac_team, 'Technician'),
            ]
            
            for user, team, role_in_team in team_assignments:
                team_member, created = TeamMember.objects.get_or_create(
                    user=user,
                    team=team,
                    defaults={'role_in_team': role_in_team}
                )
                if created:
                    self.stdout.write(
                        self.style.SUCCESS(f'  Assigned {user.username} to {team.team_name} as {role_in_team}')
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(f'  {user.username} already in {team.team_name}')
                    )
        except MaintenanceTeam.DoesNotExist:
            self.stdout.write(
                self.style.WARNING('  Teams not found. Run add_sample_data command first.')
            )
        except User.DoesNotExist:
            self.stdout.write(
                self.style.WARNING('  Some technicians not found. Skipping team assignments.')
            )

        # Summary
        self.stdout.write(
            self.style.SUCCESS(
                f'\n{"="*60}\n'
                f'Summary:\n'
                f'  - Created: {created_count} users\n'
                f'  - Updated: {updated_count} users\n'
                f'  - Total: {created_count + updated_count} users\n'
                f'{"="*60}\n'
                f'\nLogin Credentials:\n'
                f'  Admin: admin / admin123\n'
                f'  Manager: manager / manager123\n'
                f'  Technician: tech1 / tech123\n'
                f'  User: user1 / user123\n'
                f'\nAll users created successfully!'
            )
        )

