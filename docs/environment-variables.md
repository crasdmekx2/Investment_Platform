# Environment Variables

This document describes all environment variables used by the Investment Platform application.

## Database Configuration

### DB_HOST
- **Description:** Database server hostname
- **Default:** `localhost`
- **Example:** `postgres.example.com`
- **Required:** No

### DB_PORT
- **Description:** Database server port
- **Default:** `5432`
- **Example:** `5432`
- **Required:** No

### DB_NAME
- **Description:** Database name
- **Default:** `investment_platform`
- **Example:** `investment_platform`
- **Required:** No

### DB_USER
- **Description:** Database username
- **Default:** `postgres`
- **Example:** `db_user`
- **Required:** No

### DB_PASSWORD
- **Description:** Database password
- **Default:** `postgres`
- **Example:** `secure_password_123`
- **Required:** No (but should be set in production)

## CORS Configuration

### CORS_ORIGINS
- **Description:** Comma-separated list of allowed CORS origins
- **Default:** Empty (no CORS allowed - fail-safe for production)
- **Example:** `http://localhost:3000,https://example.com`
- **Required:** No (but must be set to enable CORS)
- **Security Note:** In production, always specify exact origins. Never use `*` in production.

**Usage:**
```bash
# Development - allow localhost
export CORS_ORIGINS="http://localhost:3000,http://localhost:5173"

# Production - allow specific domains
export CORS_ORIGINS="https://app.example.com,https://admin.example.com"
```

## Scheduler Configuration

### ENABLE_EMBEDDED_SCHEDULER
- **Description:** Enable embedded scheduler in API server
- **Default:** `true`
- **Values:** `true` or `false`
- **Required:** No
- **Note:** Set to `false` if running scheduler as a separate service

## Example Configuration Files

### Development (.env.development)
```bash
DB_HOST=localhost
DB_PORT=5432
DB_NAME=investment_platform_dev
DB_USER=postgres
DB_PASSWORD=postgres
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
ENABLE_EMBEDDED_SCHEDULER=true
```

### Production (.env.production)
```bash
DB_HOST=postgres.production.example.com
DB_PORT=5432
DB_NAME=investment_platform
DB_USER=prod_user
DB_PASSWORD=<secure_password_from_secrets_manager>
CORS_ORIGINS=https://app.example.com
ENABLE_EMBEDDED_SCHEDULER=true
```

## Security Best Practices

1. **Never commit `.env` files** to version control
2. **Use secrets management** (AWS Secrets Manager, HashiCorp Vault, etc.) in production
3. **Set CORS_ORIGINS** explicitly in production - never use `*`
4. **Use strong database passwords** in production
5. **Rotate credentials** regularly
6. **Use different credentials** for development, staging, and production

## Loading Environment Variables

The application loads environment variables using Python's `os.getenv()` function. Variables can be set:

1. **System environment variables**
2. **`.env` file** (if using python-dotenv)
3. **Docker environment variables**
4. **Kubernetes secrets/config maps**

## Validation

Environment variables are validated at application startup. Invalid values will cause the application to fail to start with clear error messages.

