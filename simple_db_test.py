#!/usr/bin/env python3
"""
Simple test to check database URL generation without Settings class
"""
import os

def test_database_url_simple():
    """Test the database URL logic directly without importing persistence module"""
    print("=== Simple Database URL Test ===")
    
    print("\n1. Current Environment Variables:")
    mysql_vars = ['MYSQLHOST', 'MYSQLPORT', 'MYSQLUSER', 'MYSQLPASSWORD', 'MYSQLDATABASE']
    app_vars = ['TRANSCRIPTS_DB_HOST', 'TRANSCRIPTS_DB_PORT', 'TRANSCRIPTS_DB_USER', 'TRANSCRIPTS_DB_PASSWORD', 'TRANSCRIPTS_DB_NAME']
    
    print("   Railway MySQL vars:")
    for var in mysql_vars:
        value = os.environ.get(var, "Not set")
        print(f"     {var}: {value}")
    
    print("   App DB vars:")
    for var in app_vars:
        value = os.environ.get(var, "Not set")
        print(f"     {var}: {value}")
    
    print("\n2. Simulating _database_url() function:")
    host = os.environ.get("TRANSCRIPTS_DB_HOST")
    if host:
        user = os.environ.get("TRANSCRIPTS_DB_USER", "openemr")
        password = os.environ.get("TRANSCRIPTS_DB_PASSWORD", "openemr")
        db = os.environ.get("TRANSCRIPTS_DB_NAME", "openemr")
        port = os.environ.get("TRANSCRIPTS_DB_PORT", "3306")
        db_url = f"mysql+pymysql://{user}:{password}@{host}:{port}/{db}?charset=utf8mb4"
        print(f"   ✅ Would use MySQL: {db_url}")
        return "mysql"
    else:
        db_url = "sqlite:///transcripts.db"
        print(f"   ❌ Using SQLite: {db_url}")
        return "sqlite"

def simulate_run_py_env_mapping():
    """Simulate the environment variable mapping from run.py"""
    print("\n3. Simulating run.py environment mapping:")
    
    if os.environ.get('MYSQLHOST'):
        print("   ✅ MYSQLHOST found - mapping Railway vars to app vars")
        os.environ['TRANSCRIPTS_DB_HOST'] = os.environ['MYSQLHOST']
        os.environ['TRANSCRIPTS_DB_PORT'] = os.environ.get('MYSQLPORT', '3306')
        os.environ['TRANSCRIPTS_DB_USER'] = os.environ['MYSQLUSER']
        os.environ['TRANSCRIPTS_DB_PASSWORD'] = os.environ['MYSQLPASSWORD']
        os.environ['TRANSCRIPTS_DB_NAME'] = os.environ['MYSQLDATABASE']
        print(f"   Mapped TRANSCRIPTS_DB_HOST = {os.environ['TRANSCRIPTS_DB_HOST']}")
        return True
    else:
        print("   ❌ MYSQLHOST not found - no mapping performed")
        return False

def main():
    print("Testing Database Configuration (Simple)")
    
    # Test current state
    db_type1 = test_database_url_simple()
    
    # Simulate mapping if needed
    if db_type1 == "sqlite":
        mapped = simulate_run_py_env_mapping()
        if mapped:
            print("\n--- After environment mapping ---")
            db_type2 = test_database_url_simple()
        else:
            db_type2 = db_type1
    else:
        db_type2 = db_type1
    
    print("\n=== Conclusion ===")
    if db_type2 == "mysql":
        print("✅ MySQL configuration is working")
    else:
        print("❌ Still using SQLite")
        print("   Problem: Railway MySQL environment variables are not set")
        print("   Solution: Add MySQL service to Railway project")

if __name__ == '__main__':
    main()