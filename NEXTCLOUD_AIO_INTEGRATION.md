# Nextcloud AIO Integration Guide for Medical Transcriptions

This guide will help you set up Nextcloud AIO (All-in-One) as a secure storage backend for your Whisper-generated medical transcriptions, completely independent of OpenEMR.

## Overview

Your MMT application already has excellent Nextcloud integration built-in! The backend automatically:
- Stores transcription JSON metadata with full context
- Saves plain text transcripts for quick review
- Organizes files by date in a structured hierarchy
- Handles authentication and encryption securely
- Provides comprehensive error handling and monitoring

## Architecture

### Current Integration Flow
```
Audio Upload → Whisper Transcription → Database Storage → Nextcloud Backup
                                    ↘ Entity Extraction ↗
```

### Storage Structure in Nextcloud
```
/MedicalTranscripts/
├── 2025/
│   ├── 10/
│   │   ├── 02/
│   │   │   ├── 143520-123-patient_visit.json
│   │   │   ├── 143520-123-patient_visit.txt
│   │   │   ├── 150830-124-medical_consultation.json
│   │   │   └── 150830-124-medical_consultation.txt
```

## Setup Instructions

### 1. Deploy Nextcloud AIO

#### Option A: Docker Compose (Recommended for Development)
```yaml
# docker-compose.nextcloud.yml
version: '3.8'

services:
  nextcloud:
    image: nextcloud:latest
    ports:
      - "8080:80"
    environment:
      - MYSQL_HOST=db
      - MYSQL_DATABASE=nextcloud
      - MYSQL_USER=nextcloud
      - MYSQL_PASSWORD=secure_password_here
      - NEXTCLOUD_ADMIN_USER=admin
      - NEXTCLOUD_ADMIN_PASSWORD=admin_password_here
    volumes:
      - nextcloud_data:/var/www/html
      - nextcloud_apps:/var/www/html/custom_apps
      - nextcloud_config:/var/www/html/config
    depends_on:
      - db

  db:
    image: mysql:8.0
    environment:
      - MYSQL_ROOT_PASSWORD=root_password_here
      - MYSQL_DATABASE=nextcloud
      - MYSQL_USER=nextcloud
      - MYSQL_PASSWORD=secure_password_here
    volumes:
      - mysql_data:/var/lib/mysql

volumes:
  nextcloud_data:
  nextcloud_apps:
  nextcloud_config:
  mysql_data:
```

#### Option B: Nextcloud AIO (Production)
```bash
# Using the official Nextcloud AIO
docker run \
  --init \
  --sig-proxy=false \
  --name nextcloud-aio-mastercontainer \
  --restart always \
  --publish 80:80 \
  --publish 8080:8080 \
  --publish 8443:8443 \
  --volume nextcloud_aio_mastercontainer:/mnt/docker-aio-config \
  --volume /var/run/docker.sock:/var/run/docker.sock:ro \
  nextcloud/all-in-one:latest
```

#### Option C: Cloud Hosted Nextcloud
Use any Nextcloud hosting provider (recommended for production):
- Nextcloud.com (official hosting)
- Hetzner Storage Share
- Any cloud provider with Nextcloud

### 2. Configure Nextcloud for Medical Data

#### Create Dedicated User for MMT
1. Log in as admin to your Nextcloud instance
2. Go to **Users & Groups**
3. Create new user:
   - **Username**: `mmt-transcription`
   - **Password**: Generate strong password
   - **Groups**: Create "Medical" group
   - **Storage quota**: Set appropriate limit (e.g., 100GB)

#### Set Up App Password (Recommended)
1. Login as the `mmt-transcription` user
2. Go to **Settings > Security**
3. Generate an **App Password** for "MMT Backend"
4. Save this password - you'll use it instead of the user password

#### Enable Required Apps
Enable these apps for enhanced security:
- **End-to-End Encryption** (for client-side encryption)
- **Activity** (for audit trails)
- **Audit** (for detailed logging)
- **File Access Control** (for access restrictions)

### 3. Configure MMT Backend for Nextcloud

#### Environment Variables for Railway
Add these to your Railway backend service:

```bash
# Nextcloud Configuration
STORAGE_PROVIDER=nextcloud
NEXTCLOUD_BASE_URL=https://your-nextcloud-domain.com
NEXTCLOUD_USERNAME=mmt-transcription
NEXTCLOUD_PASSWORD=your_app_password_here
NEXTCLOUD_ROOT_PATH=MedicalTranscripts
NEXTCLOUD_TIMEOUT_SECONDS=30
NEXTCLOUD_VERIFY_TLS=true

# Optional: Enhanced security
ENABLE_FIELD_ENCRYPTION=true  # Encrypt sensitive data before upload
ADVANCED_PHI_MASKING=true     # Mask PHI in logs
```

#### Local Development (.env)
```bash
# For local testing
STORAGE_PROVIDER=nextcloud
NEXTCLOUD_BASE_URL=http://localhost:8080
NEXTCLOUD_USERNAME=admin
NEXTCLOUD_PASSWORD=admin_password_here
NEXTCLOUD_ROOT_PATH=DevTranscripts
NEXTCLOUD_VERIFY_TLS=false    # Only for local HTTP
```

### 4. Enhanced Security Configuration

#### Enable Encryption in MMT
The MMT backend supports field-level encryption before storing to Nextcloud:

```bash
# Add to Railway environment
ENABLE_FIELD_ENCRYPTION=true
ENCRYPTION_KEYS=key1:$(openssl rand -base64 32),key2:$(openssl rand -base64 32)
PRIMARY_ENCRYPTION_KEY_ID=key1
```

#### Nextcloud Security Settings
1. **Enable Two-Factor Authentication** for all users
2. **Set up SSL/TLS** with valid certificates
3. **Configure IP restrictions** if needed
4. **Enable audit logging** for compliance
5. **Set up regular backups** of Nextcloud data

### 5. Test the Integration

#### Backend Test Commands
```bash
# Test Nextcloud connectivity
curl -u "mmt-transcription:your_app_password" \
  "https://your-nextcloud-domain.com/remote.php/dav/files/mmt-transcription/"

# Test WebDAV upload
curl -u "mmt-transcription:your_app_password" \
  -X PUT \
  -H "Content-Type: text/plain" \
  -d "Test transcript content" \
  "https://your-nextcloud-domain.com/remote.php/dav/files/mmt-transcription/MedicalTranscripts/test.txt"
```

#### MMT Backend Test
```python
# Test the Nextcloud integration directly
from nextcloud_storage import store_transcript_payload

store_transcript_payload(
    record_id=999,
    filename="test_audio.wav",
    text="This is a test transcription for Nextcloud integration.",
    summary="Test summary",
    enrichment={"entities": ["test"]},
    metadata={"source": "test"}
)
```

### 6. Frontend Configuration

#### Add Nextcloud Settings to Frontend
Update the frontend to show Nextcloud integration status:

```dart
// In constants.dart, add:
static const String nextcloudStatusEndpoint = '/storage/status';

// In settings screen, add:
ListTile(
  leading: Icon(Icons.cloud),
  title: Text('Storage Provider'),
  subtitle: Text(appState.storageProvider ?? 'Database only'),
  trailing: Icon(
    appState.storageProvider == 'nextcloud' 
      ? Icons.cloud_done 
      : Icons.cloud_off
  ),
)
```

## Data Structure in Nextcloud

### JSON Metadata File Example
```json
{
  "record_id": 123,
  "filename": "patient_visit_20251002.wav",
  "text": "Patient presents with complaints of...",
  "summary": "Chief complaint: Headache. Assessment: Tension headache...",
  "enrichment": {
    "entities": {
      "symptoms": ["headache", "fatigue"],
      "medications": ["ibuprofen"],
      "procedures": []
    }
  },
  "metadata": {
    "source": "whisper_local",
    "model": "base",
    "confidence": 0.89,
    "duration_seconds": 180
  },
  "stored_at": "2025-10-02T14:35:20Z"
}
```

### Plain Text File Example
```
Patient presents with complaints of severe headaches over the past week. 
The headaches are described as throbbing and located primarily in the 
frontal region. Patient reports no associated nausea or visual changes.

Assessment: Tension headache likely related to stress.
Plan: Recommend ibuprofen 400mg as needed, stress management techniques.
```

## Advanced Features

### 1. Automated Backup and Sync
Nextcloud automatically provides:
- **Versioning**: Keep multiple versions of transcripts
- **Sync**: Real-time sync across devices
- **Sharing**: Secure sharing with healthcare teams
- **Mobile Access**: View transcripts on mobile devices

### 2. Compliance Features
- **Audit Trails**: Complete access logging
- **Retention Policies**: Automatic deletion after specified time
- **Access Controls**: Role-based permissions
- **Encryption**: End-to-end encryption support

### 3. Integration with Healthcare Systems
- **Calendar Integration**: Link transcripts to appointments
- **Contact Integration**: Associate with patient records
- **Talk Integration**: Secure communication about cases
- **Deck Integration**: Task management for follow-ups

## Monitoring and Maintenance

### Health Checks
The MMT backend includes metrics for Nextcloud:
- `nextcloud_upload_success_total`: Successful uploads
- `nextcloud_upload_failure_total`: Failed uploads with reasons

### Regular Maintenance
1. **Monitor Storage Usage**: Check Nextcloud storage quotas
2. **Review Access Logs**: Monitor for unauthorized access
3. **Update Credentials**: Rotate app passwords periodically
4. **Backup Verification**: Test backup restoration procedures
5. **Security Updates**: Keep Nextcloud updated

## Troubleshooting

### Common Issues

#### Connection Failures
```bash
# Check network connectivity
curl -I https://your-nextcloud-domain.com

# Test authentication
curl -u "username:password" \
  "https://your-nextcloud-domain.com/ocs/v1.php/cloud/capabilities"
```

#### Upload Failures
1. **Check disk space** on Nextcloud server
2. **Verify user permissions** for the upload path
3. **Check file size limits** in Nextcloud configuration
4. **Review Nextcloud logs** for detailed error messages

#### Performance Issues
1. **Increase timeout** values in MMT configuration
2. **Optimize Nextcloud** database and caching
3. **Use Redis** for Nextcloud caching
4. **Monitor network latency** between MMT and Nextcloud

### Log Analysis
```bash
# MMT Backend logs (look for nextcloud events)
grep "nextcloud" /var/log/mmt-backend.log

# Nextcloud logs
tail -f /var/www/html/data/nextcloud.log
```

## Security Best Practices

1. **Use HTTPS** for all Nextcloud communications
2. **Enable App Passwords** instead of main passwords
3. **Set up IP restrictions** if possible
4. **Enable Two-Factor Authentication** for all users
5. **Regular security audits** of access patterns
6. **Encrypt sensitive data** before upload to Nextcloud
7. **Use strong, unique passwords** for all accounts
8. **Regular backup testing** and disaster recovery drills

## Benefits of Nextcloud AIO Integration

### For Healthcare Providers
- ✅ **HIPAA Compliance**: With proper configuration
- ✅ **Data Sovereignty**: Full control over data location
- ✅ **Collaboration**: Secure sharing with healthcare teams
- ✅ **Mobile Access**: Access transcripts anywhere
- ✅ **Backup & Recovery**: Automated, reliable backups

### For IT Administrators
- ✅ **Self-Hosted**: No dependency on external services
- ✅ **Scalable**: Grows with your organization
- ✅ **Auditable**: Complete audit trails
- ✅ **Integrable**: Works with existing systems
- ✅ **Cost-Effective**: No per-user licensing fees

This integration provides a robust, secure, and compliant solution for storing medical transcriptions without relying on OpenEMR or external cloud services!