#!/usr/bin/env python3
"""
Debug script to check why MySQL is not being used instead of SQLite
"""
import os
import sys

def check_environment_variables():
    """Check all MySQL-related environment variables"""
    print("=== Environment Variables Check ===")
    
    # Railway MySQL variables
    railway_vars = ['MYSQLHOST', 'MYSQLPORT', 'MYSQLUSER', 'MYSQLPASSWORD', 'MYSQLDATABASE']
    app_vars = ['TRANSCRIPTS_DB_HOST', 'TRANSCRIPTS_DB_PORT', 'TRANSCRIPTS_DB_USER', 'TRANSCRIPTS_DB_PASSWORD', 'TRANSCRIPTS_DB_NAME']
    
    print("\n1. Railway MySQL Variables:")
    railway_configured = True
    for var in railway_vars:
        value = os.environ.get(var)
        if value:
            # Hide password for security
            display_value = value if var != 'MYSQLPASSWORD' else '*' * len(value)
            print(f"   ✅ {var}: {display_value}")
        else:
            print(f"   ❌ {var}: Not set")
            railway_configured = False
    
    print("\n2. App Database Variables:")
    app_configured = True
    for var in app_vars:
        value = os.environ.get(var)
        if value:
            display_value = value if var != 'TRANSCRIPTS_DB_PASSWORD' else '*' * len(value)
            print(f"   ✅ {var}: {display_value}")
        else:
            print(f"   ❌ {var}: Not set")
            if var == 'TRANSCRIPTS_DB_HOST':
                app_configured = False
    
    return railway_configured, app_configured

def test_database_url_generation():
    """Test the _database_url function to see what URL it generates"""
    print("\n=== Database URL Generation Test ===")
    
    # Add backend to Python path
    sys.path.insert(0, '/workspaces/MMT/backend')
    
    try:
        from persistence import _database_url
        
        db_url = _database_url()
        print(f"\nGenerated Database URL: {db_url}")
        
        if db_url.startswith('sqlite'):
            print("❌ Using SQLite - MySQL not detected")
            print("   This means TRANSCRIPTS_DB_HOST is not set")
        elif db_url.startswith('mysql'):
            print("✅ Using MySQL")
            # Parse the URL to show components
            import re
            match = re.match(r'mysql\+pymysql://([^:]+):([^@]+)@([^:]+):(\d+)/(.+)', db_url)
            if match:
                user, password, host, port, database = match.groups()
                print(f"   Host: {host}")
                print(f"   Port: {port}")
                print(f"   User: {user}")
                print(f"   Database: {database}")
        
        return db_url
        
    except Exception as e:
        print(f"❌ Error testing database URL: {e}")
        return None

def simulate_run_py_mapping():
    """Simulate what run.py does to map Railway vars to app vars"""
    print("\n=== Simulating run.py Environment Mapping ===")
    
    if os.environ.get('MYSQLHOST'):
        print("✅ MYSQLHOST detected - mapping variables...")
        
        # Show what run.py would set
        mappings = {
            'TRANSCRIPTS_DB_HOST': os.environ.get('MYSQLHOST'),
            'TRANSCRIPTS_DB_PORT': os.environ.get('MYSQLPORT', '3306'),
            'TRANSCRIPTS_DB_USER': os.environ.get('MYSQLUSER'),
            'TRANSCRIPTS_DB_PASSWORD': os.environ.get('MYSQLPASSWORD'),
            'TRANSCRIPTS_DB_NAME': os.environ.get('MYSQLDATABASE')
        }
        
        for app_var, value in mappings.items():
            if value:
                display_value = value if 'PASSWORD' not in app_var else '*' * len(value)
                print(f"   {app_var} = {display_value}")
                # Actually set it for testing
                os.environ[app_var] = value
            else:
                print(f"   ❌ {app_var} = None (source variable missing)")
    else:
        print("❌ MYSQLHOST not found - no mapping performed")

def main():
    print("Debugging MySQL vs SQLite Issue\n")
    
    # Check environment variables
    railway_ok, app_ok = check_environment_variables()
    
    # Simulate run.py mapping if Railway vars exist but app vars don't
    if railway_ok and not app_ok:
        simulate_run_py_mapping()
        print("\n--- After mapping ---")
        railway_ok, app_ok = check_environment_variables()
    
    # Test database URL generation
    db_url = test_database_url_generation()
    
    print("\n=== Analysis ===")
    if railway_ok and app_ok and db_url and db_url.startswith('mysql'):
        print("✅ Everything looks correct - MySQL should be used")
    elif railway_ok and not app_ok:
        print("⚠️  Railway MySQL vars exist but app vars not set")
        print("   Issue: Environment variable mapping in run.py not working")
    elif not railway_ok:
        print("❌ Railway MySQL variables not found")
        print("   Issue: MySQL service not properly configured on Railway")
    else:
        print("❓ Unexpected configuration state")
    
    print("\n=== Next Steps ===")
    if not railway_ok:
        print("1. Verify MySQL service is added to Railway project")
        print("2. Check Railway dashboard for MySQL service status")
    elif railway_ok and not app_ok:
        print("1. Check if run.py is actually being executed on Railway")
        print("2. Verify environment variable mapping logic in run.py")
    
    return railway_ok and app_ok

if __name__ == '__main__':
    main()