# Railway MySQL Setup Guide

## Steps to Add MySQL to Your Railway Project

### 1. Via Railway Dashboard (Recommended)
1. Go to your Railway project: https://railway.app/project/49749dfc-af4f-44b4-be7f-9f6411aee691
2. Click "New Service" or the "+" button
3. Select "Database" 
4. Choose "MySQL"
5. Railway will automatically create the MySQL instance and provide environment variables

### 2. Via Railway CLI (Alternative)
```bash
railway login
railway add --database mysql
```

## Environment Variables Provided by Railway

When you add MySQL, Railway automatically provides these environment variables:
- `MYSQLHOST` - MySQL server hostname
- `MYSQLPORT` - MySQL server port (usually 3306)
- `MYSQLUSER` - MySQL username
- `MYSQLPASSWORD` - MySQL password  
- `MYSQLDATABASE` - MySQL database name

## Updated Configuration

Your `railway.toml` is already configured to use these variables:

```toml
TRANSCRIPTS_DB_HOST = "${{MYSQLHOST}}"
TRANSCRIPTS_DB_PORT = "${{MYSQLPORT}}"
TRANSCRIPTS_DB_USER = "${{MYSQLUSER}}"
TRANSCRIPTS_DB_PASSWORD = "${{MYSQLPASSWORD}}"
TRANSCRIPTS_DB_NAME = "${{MYSQLDATABASE}}"
```

## Database Migration

After MySQL is set up, you may need to run database migrations:

```bash
# Railway will automatically create tables on first run
# Or you can run migrations manually if needed
railway run alembic upgrade head
```

## Next Steps

1. **Add MySQL service** via Railway dashboard
2. **Redeploy your backend** - Railway will automatically inject the MySQL environment variables
3. **Test the deployment** - The backend should now start successfully with MySQL

## Expected Startup Logs

After MySQL is configured, you should see:
```
Starting MMT Backend on Railway...
  PORT: 8080
  WORKERS: 2
  ENV: prod
  DEMO_MODE: false
config/validated prod=True
[INFO] Database connected successfully
[INFO] Starting application...
```

Instead of the previous SQLite error.