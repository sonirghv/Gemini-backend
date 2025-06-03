# Environment Configuration Guide

This guide explains how to set up environment variables for the Gemini Clone Backend.

## Quick Setup

1. **Copy the example file:**
   ```bash
   cp env.example .env
   ```

2. **Edit the .env file with your actual values:**
   ```bash
   nano .env  # or use your preferred editor
   ```

3. **Ensure .env is in .gitignore** (it should be by default)

## Environment Variables Reference

### Core Settings

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `ENVIRONMENT` | Application environment | `development` | No |
| `DEBUG` | Enable debug mode | `false` | No |

### Database Configuration

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `DATABASE_URL` | Complete PostgreSQL connection string | Auto-generated | No* |
| `POSTGRES_USER` | PostgreSQL username | `postgres` | Yes |
| `POSTGRES_PASSWORD` | PostgreSQL password | `""` | Yes |
| `POSTGRES_DB` | Database name | `gemini_clone_db` | Yes |
| `POSTGRES_HOST` | Database host | `localhost` | Yes |
| `POSTGRES_PORT` | Database port | `5432` | No |

*If `DATABASE_URL` is provided, individual postgres settings are ignored.

### Database Pool Settings

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `DB_POOL_SIZE` | Connection pool size | `20` | No |
| `DB_MAX_OVERFLOW` | Max overflow connections | `30` | No |
| `DB_POOL_TIMEOUT` | Pool timeout in seconds | `30` | No |
| `DB_POOL_RECYCLE` | Connection recycle time | `3600` | No |

### Security & Authentication

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `SECRET_KEY` | JWT secret key | `your-super-secret-key...` | Yes |
| `ALGORITHM` | JWT algorithm | `HS256` | No |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token expiration | `720` | No |
| `REFRESH_TOKEN_EXPIRE_DAYS` | Refresh token expiration | `30` | No |

### Google Gemini API

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `GOOGLE_API_KEY` | Google Gemini API key | `""` | Yes |

### Admin Configuration

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `ADMIN_EMAIL` | Admin user email | `admin@example.com` | Yes |
| `ADMIN_PASSWORD` | Admin user password | `change-in-production` | Yes |

### Email Configuration (SMTP)

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `SMTP_SERVER` | SMTP server hostname | `smtp.gmail.com` | Yes |
| `SMTP_PORT` | SMTP server port | `587` | No |
| `SMTP_USERNAME` | SMTP username | `""` | Yes |
| `SMTP_PASSWORD` | SMTP password/app password | `""` | Yes |
| `FROM_EMAIL` | From email address | `""` | Yes |
| `FROM_NAME` | From name | `Gemini Clone` | No |
| `SMTP_USE_TLS` | Use TLS encryption | `true` | No |

### Application Settings

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `FRONTEND_URL` | Frontend application URL | `http://localhost:5173` | No |
| `APP_NAME` | Application name | `Gemini Clone API` | No |
| `VERSION` | Application version | `1.0.0` | No |
| `API_PREFIX` | API route prefix | `/api/v1` | No |

### CORS Configuration

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `ALLOWED_ORIGINS` | JSON array of allowed origins | `["http://localhost:3000", ...]` | No |

### File Upload

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `MAX_FILE_SIZE` | Maximum file size in bytes | `10485760` (10MB) | No |
| `UPLOAD_DIR` | Upload directory | `uploads` | No |
| `ALLOWED_FILE_TYPES` | JSON array of allowed MIME types | `["image/jpeg", ...]` | No |

### Rate Limiting

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `RATE_LIMIT_REQUESTS` | Max requests per window | `100` | No |
| `RATE_LIMIT_WINDOW` | Rate limit window in seconds | `3600` | No |

### Security Settings

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `PASSWORD_MIN_LENGTH` | Minimum password length | `8` | No |
| `MAX_LOGIN_ATTEMPTS` | Max failed login attempts | `5` | No |
| `LOCKOUT_DURATION_MINUTES` | Account lockout duration | `30` | No |

### OTP Settings

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `OTP_EXPIRE_MINUTES` | OTP expiration time | `10` | No |
| `OTP_MAX_ATTEMPTS` | Max OTP verification attempts | `3` | No |
| `OTP_RESEND_COOLDOWN_MINUTES` | OTP resend cooldown | `1` | No |

### Logging

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `LOG_LEVEL` | Logging level | `INFO` | No |
| `LOG_FORMAT` | Log format (json/text) | `json` | No |

### Health Check

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `HEALTH_CHECK_INTERVAL` | Health check interval | `30` | No |

## Environment-Specific Examples

### Development (.env)

```env
ENVIRONMENT=development
DEBUG=true
POSTGRES_PASSWORD=dev_password
GOOGLE_API_KEY=your_dev_api_key
ADMIN_EMAIL=admin@localhost
ADMIN_PASSWORD=admin123
SMTP_USERNAME=your_dev_email@gmail.com
SMTP_PASSWORD=your_app_password
FROM_EMAIL=dev@localhost
SECRET_KEY=dev-secret-key-not-for-production
```

### Production (.env)

```env
ENVIRONMENT=production
DEBUG=false
POSTGRES_PASSWORD=super_secure_production_password
GOOGLE_API_KEY=your_production_api_key
ADMIN_EMAIL=admin@yourdomain.com
ADMIN_PASSWORD=very_secure_admin_password
SMTP_USERNAME=noreply@yourdomain.com
SMTP_PASSWORD=production_app_password
FROM_EMAIL=noreply@yourdomain.com
SECRET_KEY=super-secure-production-key-minimum-32-characters
FRONTEND_URL=https://yourdomain.com
ALLOWED_ORIGINS=["https://yourdomain.com", "https://www.yourdomain.com"]
```

## Security Best Practices

### 1. Secret Key Generation

Generate a strong secret key:

```bash
# Python method
python -c "import secrets; print(secrets.token_urlsafe(32))"

# OpenSSL method
openssl rand -base64 32
```

### 2. Gmail SMTP Setup

For Gmail SMTP:

1. Enable 2-Factor Authentication
2. Generate an App Password:
   - Go to Google Account settings
   - Security → 2-Step Verification → App passwords
   - Generate password for "Mail"
   - Use this password in `SMTP_PASSWORD`

### 3. Database Security

- Use strong passwords
- Enable SSL/TLS for database connections
- Restrict database access by IP
- Regular security updates

### 4. Production Checklist

- [ ] Change all default passwords
- [ ] Use strong, unique secret keys
- [ ] Enable HTTPS
- [ ] Configure proper CORS origins
- [ ] Set up database backups
- [ ] Monitor logs and metrics
- [ ] Regular security audits

## Validation

The application validates critical settings on startup:

- **Production Environment**: Ensures no default values for sensitive settings
- **Database Connection**: Tests connectivity on startup
- **Required Fields**: Validates all required environment variables

## Troubleshooting

### Common Issues

1. **Database Connection Failed**
   ```
   Check POSTGRES_* variables
   Ensure PostgreSQL is running
   Verify network connectivity
   ```

2. **Email Not Sending**
   ```
   Verify SMTP_* settings
   Check Gmail app password
   Test SMTP connectivity
   ```

3. **JWT Token Issues**
   ```
   Ensure SECRET_KEY is set
   Check token expiration settings
   Verify algorithm setting
   ```

### Environment Loading

The application loads environment variables in this order:

1. System environment variables
2. `.env` file in the application root
3. Default values from `Settings` class

### Debugging Environment

To debug environment loading:

```python
from utils.config import settings
print(f"Environment: {settings.environment}")
print(f"Debug: {settings.debug}")
print(f"Database URL: {settings.database_url}")
# Don't print sensitive values in production!
```

## File Structure

```
Gemini-backend/
├── .env                 # Your actual environment file (not in git)
├── env.example          # Development example
├── env_production.txt   # Production example
└── utils/
    └── config.py        # Configuration class
```

## Support

If you encounter issues with environment configuration:

1. Check this documentation
2. Verify your `.env` file syntax
3. Test individual components (database, email, etc.)
4. Check application logs for validation errors
5. Ensure all required variables are set 