#!/usr/bin/env python3
"""
MySQL Service Diagnostic - Since MySQL service exists on Railway
"""

def check_mysql_service_details():
    """Instructions for checking MySQL service details"""
    print("🔍 MySQL Service Diagnostic")
    print("=" * 40)
    print()
    print("Since you can see the MySQL service on Railway, let's check why")
    print("your backend isn't connecting to it:")
    print()
    
    print("=== STEP 1: Check MySQL Service Health ===")
    print("1. In Railway dashboard, click on your MySQL service")
    print("2. Check the service status indicator:")
    print("   ✅ Green = Running and healthy")
    print("   🟡 Yellow = Starting up or unhealthy") 
    print("   🔴 Red = Failed or crashed")
    print()
    print("3. If not green, click on 'Deployments' tab in MySQL service")
    print("4. Check the MySQL service logs for any errors")
    print()

def check_environment_variables():
    """Check if environment variables are properly shared"""
    print("=== STEP 2: Check Environment Variables Sharing ===")
    print("1. Click on your Backend service")
    print("2. Go to 'Variables' tab")
    print("3. Look for these MySQL variables (they should be auto-provided):")
    print("   - MYSQLHOST")
    print("   - MYSQLPORT")
    print("   - MYSQLUSER") 
    print("   - MYSQLPASSWORD")
    print("   - MYSQLDATABASE")
    print()
    print("4. If these variables are MISSING:")
    print("   → Railway isn't sharing MySQL variables with your backend")
    print("   → This can happen if services are in different environments")
    print("   → Or if there's a Railway configuration issue")
    print()

def check_deployment_logs():
    """Check what the deployment logs show"""
    print("=== STEP 3: Check Latest Deployment Logs ===")
    print("1. Go to Backend service → Deployments tab")
    print("2. Click on the deployment from 2 hours ago")
    print("3. Look for these specific messages:")
    print()
    print("✅ SUCCESS - Should see:")
    print("   'MySQL database detected from Railway'")
    print("   'Database configured: [user]@[host]:3306/[database]'")
    print()
    print("❌ PROBLEM - Might see:")
    print("   'No MySQL detected - check if Railway MySQL addon is installed'")
    print("   'SQLite backend is not permitted in production'")
    print("   'Could not connect to MySQL'")
    print()

def show_troubleshooting_steps():
    """Show specific troubleshooting steps"""
    print("=== TROUBLESHOOTING STEPS ===")
    print()
    print("ISSUE A: MySQL variables missing from backend")
    print("SOLUTION:")
    print("  1. Delete and recreate the MySQL service")
    print("  2. Or check if MySQL service is in 'shared' mode")
    print("  3. Redeploy backend after MySQL is ready")
    print()
    
    print("ISSUE B: MySQL service shows red/failed status")
    print("SOLUTION:")
    print("  1. Check MySQL service logs for errors")
    print("  2. Try restarting the MySQL service")
    print("  3. If persistent, delete and recreate MySQL service")
    print()
    
    print("ISSUE C: Variables present but connection fails")
    print("SOLUTION:")
    print("  1. Check if MySQL service is fully initialized")
    print("  2. MySQL takes 1-2 minutes to be ready after creation")
    print("  3. Try redeploying backend service")
    print()
    
    print("ISSUE D: Logs show 'No MySQL detected'")
    print("SOLUTION:")
    print("  1. Environment variables aren't reaching the backend")
    print("  2. Check Railway project environment/workspace settings")
    print("  3. Ensure both services are in the same Railway project")
    print()

def show_immediate_actions():
    """Show what to check right now"""
    print("=== IMMEDIATE ACTIONS ===")
    print()
    print("🔍 Check these RIGHT NOW and report back:")
    print()
    print("1. MySQL Service Status:")
    print("   Click MySQL service → What color is the status indicator?")
    print()
    print("2. Backend Environment Variables:")
    print("   Backend service → Variables tab → Do you see MYSQLHOST?")
    print()
    print("3. Latest Deployment Logs:")
    print("   Backend service → Deployments → Latest logs → Search for 'MySQL'")
    print()
    print("4. MySQL Service Age:")
    print("   When was the MySQL service created? (check deployments)")
    print()

def main():
    check_mysql_service_details()
    print()
    check_environment_variables()
    print()
    check_deployment_logs()
    print()
    show_troubleshooting_steps()
    print()
    show_immediate_actions()
    
    print("=" * 40)
    print("📊 PLEASE REPORT:")
    print("1. MySQL service status color (green/yellow/red)")
    print("2. Whether MYSQLHOST variable exists in backend")
    print("3. What the latest deployment logs say about MySQL")

if __name__ == '__main__':
    main()