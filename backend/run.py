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
    
    # Set default workers if not provided
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
        # Railway MySQL environment variables are automatically available
        # The persistence.py will use them via TRANSCRIPTS_DB_* variables
    else:
        print("No MySQL detected - check if Railway MySQL addon is installed")
        print("Visit: https://railway.app/project/49749dfc-af4f-44b4-be7f-9f6411aee691")
        print("Add a MySQL database service to fix this issue")
    
    print(f"Starting MMT Backend on Railway... (MySQL configured)")
    print(f"  PORT: {port}")
    print(f"  WORKERS: {workers}")
    print(f"  ENV: {os.environ.get('ENV')}")
    print(f"  DEMO_MODE: {os.environ.get('DEMO_MODE')}")
    print(f"  MySQL Host: {os.environ.get('MYSQLHOST', 'Not configured')}")
    
    # Start the application with gunicorn
    cmd = [
        'gunicorn',
        '-k', 'uvicorn.workers.UvicornWorker',
        '-w', workers,
        '-b', f'0.0.0.0:{port}',
        '--timeout', '120',
        '--max-requests', '1000',
        '--max-requests-jitter', '100',
        '--preload',
        '--access-logfile', '-',
        '--error-logfile', '-',
        'main:app'
    ]
    
    os.execvp('gunicorn', cmd)

if __name__ == '__main__':
    main()