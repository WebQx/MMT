#!/usr/bin/env python3
"""
Test script to verify MySQL connectivity on Railway
"""
import os
import sys

def test_mysql_connection():
    """Test MySQL connection using Railway environment variables"""
    print("=== Railway MySQL Connection Test ===\n")
    
    # Check if Railway MySQL env vars are present
    mysql_vars = {
        'MYSQLHOST': os.environ.get('MYSQLHOST'),
        'MYSQLPORT': os.environ.get('MYSQLPORT'),
        'MYSQLUSER': os.environ.get('MYSQLUSER'),
        'MYSQLPASSWORD': os.environ.get('MYSQLPASSWORD'),
        'MYSQLDATABASE': os.environ.get('MYSQLDATABASE')
    }
    
    print("1. Environment Variables Check:")
    missing_vars = []
    for var, value in mysql_vars.items():
        if value:
            print(f"   ✅ {var}: {value}")
        else:
            print(f"   ❌ {var}: Not set")
            missing_vars.append(var)
    
    if missing_vars:
        print(f"\n❌ Missing MySQL environment variables: {', '.join(missing_vars)}")
        print("   This indicates that MySQL service is not properly configured on Railway")
        print("   Go to: https://railway.app/project/49749dfc-af4f-44b4-be7f-9f6411aee691")
        print("   Add a MySQL database service to fix this issue")
        return False
    
    print("\n2. Testing Database Connection:")
    try:
        import pymysql
        
        # Try to connect to MySQL
        connection = pymysql.connect(
            host=mysql_vars['MYSQLHOST'],
            port=int(mysql_vars['MYSQLPORT']),
            user=mysql_vars['MYSQLUSER'],
            password=mysql_vars['MYSQLPASSWORD'],
            database=mysql_vars['MYSQLDATABASE'],
            charset='utf8mb4'
        )
        
        print("   ✅ Successfully connected to MySQL")
        
        # Test basic query
        with connection.cursor() as cursor:
            cursor.execute("SELECT VERSION()")
            version = cursor.fetchone()
            print(f"   ✅ MySQL Version: {version[0]}")
            
            # Check if tables exist
            cursor.execute("SHOW TABLES")
            tables = cursor.fetchall()
            if tables:
                print(f"   ✅ Found {len(tables)} tables: {[t[0] for t in tables]}")
            else:
                print("   ⚠️  No tables found - database may need initialization")
        
        connection.close()
        return True
        
    except ImportError:
        print("   ❌ pymysql not installed - installing...")
        os.system("pip install pymysql")
        return test_mysql_connection()  # Retry after installation
        
    except Exception as e:
        print(f"   ❌ Failed to connect to MySQL: {e}")
        print(f"   Connection string attempted: mysql://{mysql_vars['MYSQLUSER']}:***@{mysql_vars['MYSQLHOST']}:{mysql_vars['MYSQLPORT']}/{mysql_vars['MYSQLDATABASE']}")
        return False

def test_app_db_config():
    """Test if the app's database configuration works"""
    print("\n3. Testing App Database Configuration:")
    try:
        # Add backend to path
        sys.path.insert(0, '/workspaces/MMT/backend')
        
        from persistence import _database_url, ENGINE
        
        db_url = _database_url()
        print(f"   Database URL: {db_url}")
        
        if db_url.startswith('sqlite'):
            print("   ❌ App is using SQLite (MySQL not configured)")
            return False
        elif db_url.startswith('mysql'):
            print("   ✅ App is configured to use MySQL")
            
            # Test SQLAlchemy connection
            connection = ENGINE.connect()
            result = connection.execute(ENGINE.dialect.name)
            print(f"   ✅ SQLAlchemy connection successful")
            connection.close()
            return True
        
    except Exception as e:
        print(f"   ❌ App database configuration error: {e}")
        return False

def main():
    print("Testing Railway MySQL Database Setup\n")
    
    mysql_ok = test_mysql_connection()
    app_ok = test_app_db_config()
    
    print("\n=== Summary ===")
    if mysql_ok and app_ok:
        print("✅ Railway MySQL setup is working correctly")
        print("   Your database should be accessible from the backend")
    elif mysql_ok and not app_ok:
        print("⚠️  MySQL is running but app configuration has issues")
        print("   Check TRANSCRIPTS_DB_* environment variable mapping")
    elif not mysql_ok:
        print("❌ MySQL service is not properly configured on Railway")
        print("   Add a MySQL database service to your Railway project")
    
    return mysql_ok and app_ok

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)