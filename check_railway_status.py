#!/usr/bin/env python3
"""
Railway Deployment Status Checker

This script helps you verify what's happening with your Railway deployment
and provides specific steps to check the MySQL service status.
"""

def check_deployment_status():
    """Instructions for checking current Railway deployment status"""
    print("🚂 Railway Deployment Status Check")
    print("=" * 50)
    print()
    print("Since your last deployment was 2 hours ago with the updated code,")
    print("let's check what's happening on Railway:")
    print()
    
    print("=== STEP 1: Check Current Deployment Logs ===")
    print("1. Go to: https://railway.app/project/49749dfc-af4f-44b4-be7f-9f6411aee691")
    print("2. Click on your Backend service")
    print("3. Go to 'Deployments' tab")
    print("4. Click on the latest deployment (from 2 hours ago)")
    print("5. Check the deployment logs for these messages:")
    print()
    
    print("✅ IF MYSQL IS WORKING, you should see:")
    print("   'Starting MMT Backend on Railway... (MySQL configured)'")
    print("   'MySQL database detected from Railway'")
    print("   'Database configured: [user]@[host]:3306/[database]'")
    print("   'config/validated prod=True'")
    print("   '[INFO] Database connected successfully'")
    print()
    
    print("❌ IF MYSQL IS MISSING, you should see:")
    print("   'No MySQL detected - check if Railway MySQL addon is installed'")
    print("   'Visit: https://railway.app/project/49749dfc-af4f-44b4-be7f-9f6411aee691'")
    print("   'Add a MySQL database service to fix this issue'")
    print()
    
    print("🔥 IF DEPLOYMENT FAILED, you might see:")
    print("   'SQLite backend is not permitted in production'")
    print("   'Health check failed'")
    print("   'Application not found'")
    print()

def check_services_status():
    """Instructions for checking Railway services"""
    print("=== STEP 2: Check Railway Services ===")
    print("1. In your Railway project dashboard, look at the services list")
    print("2. Count how many services you see:")
    print()
    print("✅ CORRECT SETUP (2 services):")
    print("   - Backend Service (your application)")
    print("   - MySQL Service (database)")
    print()
    print("❌ MISSING MYSQL (1 service only):")
    print("   - Backend Service (your application)")
    print("   - [Missing] MySQL Service")
    print()
    print("If you only see 1 service, that's the problem!")
    print()

def check_environment_variables():
    """Instructions for checking environment variables"""
    print("=== STEP 3: Check Environment Variables ===")
    print("1. Click on your Backend service")
    print("2. Go to 'Variables' tab")
    print("3. Look for these MySQL variables:")
    print("   - MYSQLHOST")
    print("   - MYSQLPORT") 
    print("   - MYSQLUSER")
    print("   - MYSQLPASSWORD")
    print("   - MYSQLDATABASE")
    print()
    print("✅ If you see these variables: MySQL service is working")
    print("❌ If you don't see these: MySQL service is not added")
    print()

def show_next_steps():
    """Show what to do based on different scenarios"""
    print("=== NEXT STEPS BASED ON WHAT YOU FIND ===")
    print()
    
    print("SCENARIO A: MySQL service exists, variables present, but deployment fails")
    print("→ MySQL is configured but there might be a connection issue")
    print("→ Check if MySQL service is actually running (green status)")
    print("→ Try redeploying the backend service")
    print()
    
    print("SCENARIO B: No MySQL service visible in project")
    print("→ Add MySQL service: Click 'New Service' → 'Database' → 'MySQL'")
    print("→ Wait for MySQL to finish setting up (1-2 minutes)")
    print("→ Redeploy backend service")
    print()
    
    print("SCENARIO C: MySQL service exists but no environment variables")
    print("→ MySQL service might be in failed state")
    print("→ Try deleting and recreating the MySQL service")
    print("→ Or check MySQL service logs for errors")
    print()
    
    print("SCENARIO D: Everything looks correct but still not working")
    print("→ MySQL service might be in a different region/zone")
    print("→ Check MySQL service connection details")
    print("→ Verify network connectivity between services")
    print()

def show_quick_verification():
    """Show how to quickly verify the issue"""
    print("=== QUICK VERIFICATION ===")
    print()
    print("🔍 Fastest way to check:")
    print("1. Look at your Railway project dashboard")
    print("2. Count the services - should be 2 (Backend + MySQL)")
    print("3. If only 1 service: Add MySQL")
    print("4. If 2 services: Check latest deployment logs")
    print()
    print("💡 Most likely scenario:")
    print("Since you're getting SQLite instead of MySQL, the MySQL")
    print("service probably hasn't been added to your Railway project yet.")
    print()

def main():
    check_deployment_status()
    print()
    check_services_status()
    print()
    check_environment_variables()
    print()
    show_next_steps()
    print()
    show_quick_verification()
    
    print("=" * 50)
    print("📋 SUMMARY: Check your Railway dashboard and report back:")
    print("   1. How many services do you see?")
    print("   2. What do the latest deployment logs show?")
    print("   3. Are MySQL environment variables present?")

if __name__ == '__main__':
    main()