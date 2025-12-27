"""
Management command to create a manager user.
Usage: python manage.py create_manager
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from maintenance.models import UserProfile


class Command(BaseCommand):
    help = 'Create a manager user for GearGuard'

    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            type=str,
            help='Username for the manager',
            default='manager'
        )
        parser.add_argument(
            '--email',
            type=str,
            help='Email for the manager',
            default='manager@gearguard.com'
        )
        parser.add_argument(
            '--password',
            type=str,
            help='Password for the manager (if not provided, will prompt)',
            default=None
        )

    def handle(self, *args, **options):
        username = options['username']
        email = options['email']
        password = options['password']

        # Check if user already exists
        if User.objects.filter(username=username).exists():
            self.stdout.write(
                self.style.WARNING(f'User "{username}" already exists.')
            )
            user = User.objects.get(username=username)
            
            # Update profile to Manager if not already
            profile, created = UserProfile.objects.get_or_create(user=user)
            if profile.role != 'Manager':
                profile.role = 'Manager'
                profile.save()
                self.stdout.write(
                    self.style.SUCCESS(f'Updated user "{username}" role to Manager.')
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS(f'User "{username}" is already a Manager.')
                )
            
            # Reset password if provided
            if password:
                user.set_password(password)
                user.save()
                self.stdout.write(
                    self.style.SUCCESS(f'Password updated for user "{username}".')
                )
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'\nLogin credentials:\n'
                    f'Username: {username}\n'
                    f'Password: {"(use the password you set)" if password else "(existing password)"}'
                )
            )
            return

        # Create new user
        if not password:
            from getpass import getpass
            password = getpass('Enter password for manager: ')
            password_confirm = getpass('Confirm password: ')
            if password != password_confirm:
                self.stdout.write(self.style.ERROR('Passwords do not match!'))
                return

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )
        
        # Create or update profile with Manager role
        profile, created = UserProfile.objects.get_or_create(
            user=user,
            defaults={'role': 'Manager'}
        )
        if not created:
            profile.role = 'Manager'
            profile.save()

        self.stdout.write(
            self.style.SUCCESS(
                f'\nSuccessfully created manager user!\n\n'
                f'Login credentials:\n'
                f'Username: {username}\n'
                f'Password: {"(the password you entered)" if not options["password"] else password}\n\n'
                f'You can now login at: http://localhost:8000/accounts/login/'
            )
        )

