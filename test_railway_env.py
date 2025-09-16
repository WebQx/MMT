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