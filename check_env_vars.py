#!/usr/bin/env python3
"""
Environment Variables and Deployment Logs Checker

Since MySQL is green/healthy, let's check why the backend isn't connecting.
"""

def check_environment_variables_detailed():
    """Detailed instructions for checking environment variables"""
    print("🔍 Environment Variables Check")
    print("=" * 40)
    print()
    print("✅ MySQL Service: GREEN (healthy)")
    print("📋 Next: Check if environment variables are being shared")
    print()
    
    print("=== CHECK BACKEND ENVIRONMENT VARIABLES ===")
    print("1. In Railway dashboard, click on your BACKEND service")
    print("2. Click on 'Variables' tab")
    print("3. Look for these MySQL variables:")
    print()
    print("   Expected MySQL variables:")
    print("   - MYSQLHOST (should be something like: containers-us-west-123.railway.app)")
    print("   - MYSQLPORT (should be: 3306)")
    print("   - MYSQLUSER (should be: root or mysql)")
    print("   - MYSQLPASSWORD (should be a long random string)")
    print("   - MYSQLDATABASE (should be: railway or similar)")
    print()
    print("4. REPORT BACK:")
    print("   ✅ 'I see all 5 MySQL variables' = GOOD")
    print("   ❌ 'I don't see MYSQLHOST' = PROBLEM")
    print("   ❌ 'I only see some variables' = PARTIAL PROBLEM")
    print()

def check_deployment_logs_detailed():
    """Detailed instructions for checking deployment logs"""
    print("=== CHECK DEPLOYMENT LOGS ===")
    print("1. In your BACKEND service, click 'Deployments' tab")
    print("2. Click on the deployment from 2 hours ago")
    print("3. Scroll through the logs and look for MySQL-related messages")
    print("4. Search for these exact phrases:")
    print()
    print("   🔍 Search for: 'MySQL database detected'")
    print("   🔍 Search for: 'No MySQL detected'")
    print("   🔍 Search for: 'Database configured:'")
    print("   🔍 Search for: 'Starting MMT Backend'")
    print()
    print("5. REPORT BACK the exact message you see:")
    print("   Example: 'MySQL database detected from Railway'")
    print("   Example: 'No MySQL detected - check if Railway MySQL addon is installed'")
    print()

def show_likely_scenarios():
    """Show the most likely scenarios based on MySQL being green"""
    print("=== LIKELY SCENARIOS (since MySQL is green) ===")
    print()
    print("SCENARIO 1: Environment variables missing")
    print("- MySQL is healthy but variables not shared with backend")
    print("- Common with newly created MySQL services")
    print("- Solution: Redeploy backend service")
    print()
    
    print("SCENARIO 2: Environment variables present but old deployment")
    print("- MySQL was added after the 2-hour deployment")
    print("- Backend deployment doesn't have the variables yet")
    print("- Solution: Trigger new deployment")
    print()
    
    print("SCENARIO 3: Variables present but connection timing issue")
    print("- MySQL takes time to fully initialize")
    print("- Backend tried to connect before MySQL was ready")
    print("- Solution: Redeploy backend (with 5-second delay in code)")
    print()

def show_quick_fixes():
    """Show quick fixes to try"""
    print("=== QUICK FIXES TO TRY ===")
    print()
    print("FIX 1: Force Backend Redeploy")
    print("1. Go to Backend service → Deployments")
    print("2. Click 'Redeploy' button on latest deployment")
    print("3. This will pick up any new MySQL environment variables")
    print()
    
    print("FIX 2: Check MySQL Creation Time")
    print("1. Click MySQL service → Deployments")
    print("2. When was MySQL service created?")
    print("3. If created AFTER your 2-hour backend deployment:")
    print("   → Backend doesn't know about MySQL yet")
    print("   → Redeploy backend to fix")
    print()
    
    print("FIX 3: Manual Environment Variable Check")
    print("1. If MYSQLHOST variables are missing from backend:")
    print("2. Try deleting and recreating MySQL service")
    print("3. Wait 2 minutes for MySQL to be ready")
    print("4. Redeploy backend service")
    print()

def main():
    check_environment_variables_detailed()
    print()
    check_deployment_logs_detailed() 
    print()
    show_likely_scenarios()
    print()
    show_quick_fixes()
    
    print("=" * 40)
    print("📊 PLEASE CHECK AND REPORT:")
    print("1. Do you see MYSQLHOST in backend variables? (YES/NO)")
    print("2. What does the deployment log say about MySQL?")
    print("3. When was the MySQL service created vs backend deployment?")

if __name__ == '__main__':
    main()