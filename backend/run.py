#!/usr/bin/env python3
"""
Railway-compatible startup script for MMT Backend.
This provides an alternative to the bash start.sh script.
"""
import os
import subprocess
import sys

def main():
    # Set default port if not provided by Railway
    port = os.environ.get('PORT', '8000')
    
    # Set default workers if not provided (reduce for faster startup)
    workers = os.environ.get('WORKERS', '1')
    
    # Production environment configuration
    os.environ.setdefault('ENV', 'prod')
    os.environ.setdefault('ENVIRONMENT_NAME', 'production')
    os.environ.setdefault('DEMO_MODE', 'false')
    
    # Ensure required production secrets are set
    if not os.environ.get('INTERNAL_JWT_SECRET'):
        os.environ['INTERNAL_JWT_SECRET'] = 'railway_production_jwt_secret_32_chars_long_abcdef1234567890'
    
    # Set default configurations for Railway
    os.environ.setdefault('RABBITMQ_URL', 'amqp://guest:guest@localhost:5672/')
    os.environ.setdefault('ALLOW_GUEST_AUTH', 'true')
    
    # MySQL configuration for Railway
    # Railway provides MYSQLHOST, MYSQLPORT, etc. when MySQL addon is installed
    if os.environ.get('MYSQLHOST'):
        print("MySQL database detected from Railway")
        # Map Railway MySQL environment variables to app variables
        os.environ['TRANSCRIPTS_DB_HOST'] = os.environ['MYSQLHOST']
        os.environ['TRANSCRIPTS_DB_PORT'] = os.environ.get('MYSQLPORT', '3306')
        os.environ['TRANSCRIPTS_DB_USER'] = os.environ['MYSQLUSER']
        os.environ['TRANSCRIPTS_DB_PASSWORD'] = os.environ['MYSQLPASSWORD']
        os.environ['TRANSCRIPTS_DB_NAME'] = os.environ['MYSQLDATABASE']
        print(f"  Database configured: {os.environ['MYSQLUSER']}@{os.environ['MYSQLHOST']}:{os.environ.get('MYSQLPORT', '3306')}/{os.environ['MYSQLDATABASE']}")
    else:
        print("No MySQL detected - check if Railway MySQL addon is installed")
        print("Visit: https://railway.app/project/49749dfc-af4f-44b4-be7f-9f6411aee691")
        print("Add a MySQL database service to fix this issue")
    
    print(f"Starting MMT Backend on Railway...")
    print(f"  PORT: {port}")
    print(f"  WORKERS: {workers}")
    print(f"  ENV: {os.environ.get('ENV')}")
    print(f"  DEMO_MODE: {os.environ.get('DEMO_MODE')}")
    print(f"  INCLUDE_ML: {os.environ.get('INCLUDE_ML')}")
    print(f"  ENABLE_LOCAL_TRANSCRIPTION: {os.environ.get('ENABLE_LOCAL_TRANSCRIPTION')}")
    print(f"  MySQL Host: {os.environ.get('MYSQLHOST', 'Not configured')}")
    
    # Check if whisper is available
    try:
        import whisper
        print("  Whisper: Available")
    except ImportError:
        print("  Whisper: Not available (ML dependencies not installed)")
    
    # Give the MySQL service a moment to be fully ready
    if os.environ.get('MYSQLHOST'):
        print("Waiting for MySQL connection to stabilize...")
        import time
        time.sleep(2)  # Reduced from 5 to 2 seconds for faster startup
    
    print("Starting gunicorn server...")
    
    # Start the application with gunicorn (optimized for Railway)
    cmd = [
        'gunicorn',
        '-k', 'uvicorn.workers.UvicornWorker',
        '-w', workers,
        '-b', f'0.0.0.0:{port}',
        '--timeout', '60',
        '--max-requests', '1000',
        '--max-requests-jitter', '100',
        '--preload',
        '--access-logfile', '-',
        '--error-logfile', '-',
        '--log-level', 'info',
        'main:app'
    ]
    
    os.execvp('gunicorn', cmd)

if __name__ == '__main__':
    main()