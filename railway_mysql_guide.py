#!/usr/bin/env python3
"""
Railway MySQL Setup and Testing Guide

This script helps diagnose and fix MySQL configuration issues on Railway.
"""

def check_railway_project_status():
    """Instructions for checking Railway project status"""
    print("=== STEP 1: Check Railway Project Status ===")
    print()
    print("1. Go to your Railway project dashboard:")
    print("   https://railway.app/project/49749dfc-af4f-44b4-be7f-9f6411aee691")
    print()
    print("2. Check if you see TWO services:")
    print("   ✅ Backend Service (your application)")
    print("   ✅ MySQL Service (database)")
    print()
    print("3. If you only see the Backend service:")
    print("   - Click 'New Service' or '+' button")
    print("   - Select 'Database' → 'MySQL'")
    print("   - Railway will create the MySQL service")
    print()

def check_mysql_service_variables():
    """Instructions for checking MySQL service variables"""
    print("=== STEP 2: Verify MySQL Environment Variables ===")
    print()
    print("1. In Railway dashboard, click on your MySQL service")
    print("2. Go to 'Variables' tab")
    print("3. You should see these variables provided by MySQL service:")
    print("   - MYSQLHOST")
    print("   - MYSQLPORT")
    print("   - MYSQLUSER") 
    print("   - MYSQLPASSWORD")
    print("   - MYSQLDATABASE")
    print()
    print("4. Click on your Backend service")
    print("5. Go to 'Variables' tab")
    print("6. These MySQL variables should be automatically available")
    print()

def check_railway_deployment():
    """Instructions for checking deployment logs"""
    print("=== STEP 3: Check Deployment Logs ===")
    print()
    print("1. In your Backend service, go to 'Deployments' tab")
    print("2. Click on the latest deployment")
    print("3. Look for these log messages:")
    print()
    print("✅ EXPECTED (MySQL working):")
    print("   'Starting MMT Backend on Railway... (MySQL configured)'")
    print("   'MySQL database detected from Railway'")
    print("   'Database configured: [user]@[host]:3306/[database]'")
    print()
    print("❌ PROBLEM (MySQL not configured):")
    print("   'No MySQL detected - check if Railway MySQL addon is installed'")
    print("   'SQLite backend is not permitted in production'")
    print()

def create_test_script():
    """Create a test script for Railway deployment"""
    print("=== STEP 4: Test Script for Railway ===")
    print()
    print("If your local environment doesn't have MySQL vars (normal for dev),")
    print("you can simulate Railway environment by setting them manually:")
    print()
    
    test_script = """
# Test script - save as test_railway_env.py
import os

# Simulate Railway MySQL environment variables
os.environ['MYSQLHOST'] = 'containers-us-west-123.railway.app'
os.environ['MYSQLPORT'] = '3306' 
os.environ['MYSQLUSER'] = 'root'
os.environ['MYSQLPASSWORD'] = 'test_password'
os.environ['MYSQLDATABASE'] = 'railway'

# Now run your database test
import simple_db_test
simple_db_test.main()
"""
    
    with open('/workspaces/MMT/test_railway_env.py', 'w') as f:
        f.write(test_script.strip())
    
    print("Created test_railway_env.py - run it to simulate Railway environment")
    print()

def show_troubleshooting_steps():
    """Show common troubleshooting steps"""
    print("=== TROUBLESHOOTING ===")
    print()
    print("ISSUE: 'No MySQL detected' in logs")
    print("SOLUTION: Add MySQL service to Railway project")
    print()
    print("ISSUE: MySQL service exists but variables not available to backend")
    print("SOLUTION: Redeploy backend service after adding MySQL")
    print()
    print("ISSUE: Backend still uses SQLite in production")
    print("SOLUTION: Check that run.py is setting environment variables correctly")
    print()
    print("ISSUE: Connection refused / can't connect to MySQL")
    print("SOLUTION: Wait 30-60 seconds after MySQL service creation for it to be ready")
    print()

def main():
    print("🚂 Railway MySQL Configuration Troubleshooting Guide")
    print("=" * 60)
    print()
    
    check_railway_project_status()
    print()
    check_mysql_service_variables()
    print()
    check_railway_deployment()
    print()
    create_test_script()
    print()
    show_troubleshooting_steps()
    
    print("=" * 60)
    print("💡 TIP: The most common issue is forgetting to add the MySQL service!")
    print("   Go to Railway dashboard and make sure you have BOTH services.")

if __name__ == '__main__':
    main()