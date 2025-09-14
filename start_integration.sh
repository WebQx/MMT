#!/bin/bash

# MMT Django-OpenEMR Integration Quick Start Script
# This script sets up the complete environment with MariaDB, OpenEMR, and Django

set -e

echo "🚀 Starting MMT Django-OpenEMR Integration Setup..."

# Check if Docker and Docker Compose are installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

echo "✅ Docker and Docker Compose found"

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p mysql-config uploads logs

# Start the services
echo "🔧 Starting services with Docker Compose..."
docker-compose up -d

echo "⏳ Waiting for services to start..."
sleep 30

# Check service health
echo "🔍 Checking service health..."
docker-compose ps

# Wait for MariaDB to be ready
echo "⏳ Waiting for MariaDB to be ready..."
until docker-compose exec -T mariadb mariadb-admin ping -h localhost -u root -proot --silent; do
    echo "Waiting for MariaDB..."
    sleep 5
done
echo "✅ MariaDB is ready"

# Wait for OpenEMR to be ready
echo "⏳ Waiting for OpenEMR to be ready..."
until curl -f http://localhost:8080 &> /dev/null; do
    echo "Waiting for OpenEMR..."
    sleep 10
done
echo "✅ OpenEMR is ready"

# Setup Django backend
echo "🔧 Setting up Django backend..."
docker-compose exec -T django-backend python manage.py setup_openemr

echo "🎉 Setup completed successfully!"
echo ""
echo "=== Access Information ==="
echo "OpenEMR Web Interface: http://localhost:8080"
echo "  Username: admin"
echo "  Password: pass"
echo ""
echo "Django API: http://localhost:8001/api/"
echo "Django Admin: http://localhost:8001/admin/"
echo "  Username: admin"
echo "  Password: admin123"
echo ""
echo "Flutter Web App: http://localhost:3000"
echo ""
echo "MariaDB Database: localhost:3306"
echo "  Database: openemr"
echo "  Username: openemr"
echo "  Password: openemr"
echo ""
echo "=== API Endpoints ==="
echo "Health Check: http://localhost:8001/api/health/"
echo "Authentication: http://localhost:8001/api/auth/login/"
echo "Patients: http://localhost:8001/api/patients/"
echo "Encounters: http://localhost:8001/api/encounters/"
echo "Transcriptions: http://localhost:8001/api/transcriptions/"
echo ""
echo "=== Next Steps ==="
echo "1. Access OpenEMR at http://localhost:8080 and complete setup"
echo "2. Create some test patients and encounters"
echo "3. Test the Django API at http://localhost:8001/api/"
echo "4. Use the Flutter app at http://localhost:3000 for transcription"
echo ""
echo "For troubleshooting, check: docker-compose logs [service-name]"
echo "For detailed documentation, see: DJANGO_OPENEMR_INTEGRATION.md"