# MMT Django-OpenEMR Integration

This integration provides a Django REST API backend that connects to OpenEMR's MariaDB database, enabling seamless authentication and medical data management.

## Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Flutter Web   │    │  Django REST    │    │    MariaDB      │
│      App        │◄──►│      API        │◄──►│   Database      │
│                 │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │                        ▲
                                │                        │
                                ▼                        │
                       ┌─────────────────┐               │
                       │     OpenEMR     │───────────────┘
                       │    PHP App      │
                       └─────────────────┘
```

## Key Features

### 🔐 Authentication Integration
- **PHP Password Compatibility**: Supports bcrypt, MD5, and SHA1 password verification
- **Session Bridging**: Can authenticate using OpenEMR PHP sessions
- **Guest Access**: Fallback guest authentication for demo purposes
- **Django User Creation**: Automatically creates Django users from OpenEMR data

### 📊 Database Integration
- **Shared Database**: Uses the same MariaDB database as OpenEMR
- **Non-destructive**: Django models marked as `managed=False` don't interfere with OpenEMR tables
- **Custom Tables**: Adds MMT-specific tables for transcription data
- **Foreign Key Relationships**: Links transcriptions to OpenEMR patients and encounters

### 🚀 RESTful API
- **Patient Management**: CRUD operations for patient data
- **Encounter Tracking**: Manage clinical encounters
- **Transcription Workflow**: Complete transcription lifecycle management
- **OpenEMR Integration**: Seamless data exchange with OpenEMR

## Quick Start

### 1. Start the Services

```bash
# Start all services with Docker Compose
docker-compose up -d

# Check service health
docker-compose ps
```

### 2. Initialize the Database

```bash
# Run the setup command to initialize Django tables
docker-compose exec django-backend python manage.py setup_openemr

# Check database connectivity only
docker-compose exec django-backend python manage.py setup_openemr --check-only
```

### 3. Access the Services

- **OpenEMR**: http://localhost:8080
  - Username: `admin`
  - Password: `pass`

- **Django API**: http://localhost:8001/api/
  - Admin: http://localhost:8001/admin/
  - Username: `admin`
  - Password: `admin123`

- **Flutter App**: http://localhost:3000

## API Endpoints

### Authentication
```http
POST /api/auth/login/          # Login with OpenEMR credentials
POST /api/auth/logout/         # Logout
GET  /api/auth/user/           # Get current user info
```

### Patient Management
```http
GET    /api/patients/          # List patients
GET    /api/patients/{id}/     # Get patient details
POST   /api/patients/          # Create patient (if allowed)
PUT    /api/patients/{id}/     # Update patient
DELETE /api/patients/{id}/     # Delete patient (if allowed)
```

### Encounters
```http
GET    /api/encounters/        # List encounters
GET    /api/encounters/{id}/   # Get encounter details
POST   /api/encounters/        # Create encounter
```

### Transcriptions
```http
GET    /api/transcriptions/              # List transcriptions
GET    /api/transcriptions/{id}/         # Get transcription with segments
POST   /api/transcriptions/              # Create transcription
PUT    /api/transcriptions/{id}/         # Update transcription
POST   /api/transcriptions/{id}/approve/ # Approve transcription
POST   /api/transcriptions/{id}/reject/  # Reject transcription
POST   /api/transcriptions/{id}/integrate_with_openemr/ # Integrate with OpenEMR
```

### OpenEMR Integration
```http
GET /api/openemr/facilities/   # Get OpenEMR facilities
GET /api/openemr/providers/    # Get OpenEMR providers/users
```

### Health Check
```http
GET /api/health/               # Service health status
```

## Database Schema

### OpenEMR Tables (Read/Write)
- `users` - OpenEMR user accounts
- `patient_data` - Patient information
- `form_encounter` - Clinical encounters
- `sessions` - PHP session data

### Custom MMT Tables
- `mmt_transcriptions` - Audio transcription metadata
- `mmt_transcription_segments` - Individual transcription segments

## Authentication Flow

### 1. Direct Login
```python
# Client sends credentials to Django
POST /api/auth/login/
{
    "username": "doctor1",
    "password": "password123"
}

# Django validates against OpenEMR users table
# Returns Django session + user info
```

### 2. OpenEMR Session Bridge
```python
# Client has OpenEMR session cookie
# Django middleware checks OpenEMR sessions table
# Automatically authenticates user if valid session exists
```

### 3. Guest Access
```python
# For demo/testing purposes
POST /api/auth/login/
{
    "username": "guest",
    "password": "guest"
}
```

## Configuration

### Environment Variables

#### Django Backend (`docker-compose.yml`)
```yaml
environment:
  DB_NAME: openemr                    # Database name
  DB_USER: openemr                    # Database user
  DB_PASSWORD: openemr                # Database password
  DB_HOST: mariadb                    # Database host
  DB_PORT: 3306                       # Database port
  DJANGO_SECRET_KEY: "your-secret"    # Django secret key
  DJANGO_DEBUG: "False"               # Debug mode
  OPENEMR_BASE_URL: "http://openemr"  # OpenEMR URL
  ALLOWED_HOSTS: "localhost,127.0.0.1" # Allowed hosts
```

#### MariaDB
```yaml
environment:
  MARIADB_ROOT_PASSWORD: root
  MARIADB_USER: openemr
  MARIADB_PASSWORD: openemr
  MARIADB_DATABASE: openemr
```

## Development

### Local Development Setup

1. **Install Dependencies**
```bash
cd medtranscribe_backend
pip install -r requirements.txt
```

2. **Configure Database**
```bash
# Make sure MariaDB is running
docker-compose up -d mariadb

# Set environment variables
export DB_HOST=localhost
export DB_PORT=3306
export DB_NAME=openemr
export DB_USER=openemr
export DB_PASSWORD=openemr
```

3. **Run Migrations**
```bash
python manage.py migrate
```

4. **Start Development Server**
```bash
python manage.py runserver 8001
```

### Testing Authentication

```bash
# Test login endpoint
curl -X POST http://localhost:8001/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "pass"}'

# Test with guest credentials
curl -X POST http://localhost:8001/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "guest", "password": "guest"}'
```

## Security Considerations

### Password Handling
- Supports modern bcrypt hashes (OpenEMR 6.0+)
- Backward compatibility with legacy MD5/SHA1 hashes
- Never stores plaintext passwords

### Database Security
- Uses read-only access to OpenEMR tables where possible
- Custom tables isolated with `mmt_` prefix
- Proper foreign key constraints

### API Security
- Django CSRF protection
- Session-based authentication
- Permission-based access control
- Input validation and sanitization

## Troubleshooting

### Common Issues

1. **Database Connection Failed**
   ```bash
   # Check MariaDB is running
   docker-compose ps mariadb
   
   # Check logs
   docker-compose logs mariadb
   ```

2. **OpenEMR Tables Not Found**
   ```bash
   # Make sure OpenEMR initialization completed
   docker-compose logs openemr
   
   # Check OpenEMR web interface
   curl http://localhost:8080
   ```

3. **Authentication Issues**
   ```bash
   # Check user exists in OpenEMR
   docker-compose exec mariadb mysql -u root -proot openemr -e "SELECT username, active FROM users;"
   
   # Test login endpoint
   curl -X POST http://localhost:8001/api/auth/login/ \
     -H "Content-Type: application/json" \
     -d '{"username": "admin", "password": "pass"}'
   ```

4. **Permission Denied**
   ```bash
   # Check Django user permissions
   docker-compose exec django-backend python manage.py shell -c "
   from django.contrib.auth.models import User
   print(User.objects.all())
   "
   ```

### Logs

```bash
# Django backend logs
docker-compose logs django-backend

# OpenEMR logs
docker-compose logs openemr

# MariaDB logs
docker-compose logs mariadb

# All services
docker-compose logs -f
```

## Production Deployment

### Security Checklist
- [ ] Change default passwords
- [ ] Set strong `DJANGO_SECRET_KEY`
- [ ] Set `DJANGO_DEBUG=False`
- [ ] Configure proper `ALLOWED_HOSTS`
- [ ] Use HTTPS with SSL certificates
- [ ] Implement backup strategy
- [ ] Monitor logs for security events

### Performance Optimization
- [ ] Configure MariaDB memory settings
- [ ] Set up database connection pooling
- [ ] Enable Django caching
- [ ] Use reverse proxy (nginx)
- [ ] Monitor resource usage

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## License

This project is licensed under the same license as the main MMT project.