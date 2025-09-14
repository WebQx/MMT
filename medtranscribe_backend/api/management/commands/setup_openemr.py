"""
Django management command to setup OpenEMR integration.
This command initializes the database and creates necessary tables.
"""

from django.core.management.base import BaseCommand
from django.db import connection
from django.conf import settings
import os


class Command(BaseCommand):
    help = 'Setup OpenEMR integration and database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--check-only',
            action='store_true',
            help='Only check database connectivity, don\'t create tables',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting OpenEMR integration setup...'))
        
        # Check database connectivity
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                self.stdout.write(self.style.SUCCESS('✓ Database connection successful'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Database connection failed: {e}'))
            return
        
        if options['check_only']:
            self.stdout.write(self.style.SUCCESS('Database check completed.'))
            return
        
        # Check if OpenEMR tables exist
        openemr_tables = ['users', 'patient_data', 'form_encounter', 'sessions']
        existing_tables = []
        
        with connection.cursor() as cursor:
            cursor.execute("SHOW TABLES")
            all_tables = [table[0] for table in cursor.fetchall()]
            
            for table in openemr_tables:
                if table in all_tables:
                    existing_tables.append(table)
                    self.stdout.write(f'✓ OpenEMR table "{table}" found')
                else:
                    self.stdout.write(self.style.WARNING(f'⚠ OpenEMR table "{table}" not found'))
        
        if len(existing_tables) < len(openemr_tables):
            self.stdout.write(self.style.WARNING(
                'Some OpenEMR tables are missing. Make sure OpenEMR is properly installed and initialized.'
            ))
        
        # Run Django migrations for custom tables
        self.stdout.write('Running Django migrations for custom MMT tables...')
        from django.core.management import call_command
        
        try:
            call_command('migrate', verbosity=1)
            self.stdout.write(self.style.SUCCESS('✓ Django migrations completed'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Migration failed: {e}'))
            return
        
        # Check if custom tables were created
        custom_tables = ['mmt_transcriptions', 'mmt_transcription_segments']
        with connection.cursor() as cursor:
            cursor.execute("SHOW TABLES")
            all_tables = [table[0] for table in cursor.fetchall()]
            
            for table in custom_tables:
                if table in all_tables:
                    self.stdout.write(f'✓ Custom table "{table}" created')
                else:
                    self.stdout.write(self.style.ERROR(f'✗ Custom table "{table}" not created'))
        
        # Create superuser if it doesn't exist
        from django.contrib.auth.models import User
        if not User.objects.filter(username='admin').exists():
            self.stdout.write('Creating Django admin user...')
            try:
                User.objects.create_superuser(
                    username='admin',
                    email='admin@example.com',
                    password='admin123'
                )
                self.stdout.write(self.style.SUCCESS('✓ Admin user created (username: admin, password: admin123)'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'✗ Failed to create admin user: {e}'))
        else:
            self.stdout.write('✓ Admin user already exists')
        
        # Summary
        self.stdout.write(self.style.SUCCESS('\n=== Setup Summary ==='))
        self.stdout.write(f'Database: {settings.DATABASES["default"]["NAME"]}')
        self.stdout.write(f'Host: {settings.DATABASES["default"]["HOST"]}')
        self.stdout.write(f'OpenEMR tables found: {len(existing_tables)}/{len(openemr_tables)}')
        self.stdout.write('Django admin: /admin/')
        self.stdout.write('API endpoints: /api/')
        self.stdout.write('Health check: /api/health/')
        self.stdout.write(self.style.SUCCESS('\nSetup completed successfully!'))