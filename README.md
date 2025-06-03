# Gemini Clone Backend - Production Deployment Guide

## Overview

This is a production-ready FastAPI backend for the Gemini Clone application with PostgreSQL database, comprehensive authentication, rate limiting, monitoring, and logging capabilities.

## Features

- **Database**: PostgreSQL with connection pooling and migrations
- **Authentication**: JWT-based with email verification via OTP
- **Rate Limiting**: In-memory rate limiting with automatic cleanup
- **Caching**: In-memory caching for session management and OTP tracking
- **Logging**: Structured logging with JSON format for production
- **Monitoring**: Health checks and metrics endpoints
- **Security**: Production-ready security middleware and validation
- **File Upload**: Secure file upload with validation
- **Admin Panel**: Admin routes for user management and statistics

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend       │    │   Database      │
│   (React)       │◄──►│   (FastAPI)     │◄──►│   (PostgreSQL)  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │   File Storage  │
                       │   (Local/S3)    │
                       └─────────────────┘
```

## Prerequisites

- Python 3.11+
- PostgreSQL 12+
- Node.js 18+ (for frontend)
- Git

## Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd Gemini-backend
```

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Database Setup

#### Install PostgreSQL
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install postgresql postgresql-contrib

# macOS
brew install postgresql

# Windows
# Download from https://www.postgresql.org/download/windows/
```

#### Create Database
```bash
sudo -u postgres psql
CREATE DATABASE gemini_clone_production;
CREATE USER gemini_user WITH PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE gemini_clone_production TO gemini_user;
\q
```

### 5. Environment Configuration

```bash
# Copy production environment template
cp env_production.txt .env

# Edit .env with your actual values
nano .env
```

#### Required Environment Variables

```env
# Database
POSTGRES_USER=gemini_user
POSTGRES_PASSWORD=your_secure_password
POSTGRES_DB=gemini_clone_production
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

# Security
SECRET_KEY=your_super_secure_secret_key_minimum_32_characters_long
ADMIN_EMAIL=admin@yourdomain.com
ADMIN_PASSWORD=your_secure_admin_password

# Google Gemini API
GOOGLE_API_KEY=your_google_gemini_api_key

# Email (Gmail SMTP)
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_gmail_app_password
FROM_EMAIL=noreply@yourdomain.com
```

### 6. Database Migration

```bash
# Initialize Alembic (if not already done)
alembic revision --autogenerate -m "Initial migration"

# Run migrations
alembic upgrade head
```

### 7. Create Required Directories

```bash
mkdir -p logs uploads
```

## Running the Application

### Development Mode

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Production Mode

```bash
# Using Gunicorn (recommended)
gunicorn --config gunicorn.conf.py main:app

# Or using Uvicorn directly
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

## API Documentation

Once running, access the API documentation at:
- Swagger UI: `http://localhost:8000/docs` (development only)
- ReDoc: `http://localhost:8000/redoc` (development only)

## Health Checks

### Endpoints

- **General Health**: `GET /health`
- **Database Health**: `GET /health/database`
- **Metrics**: `GET /metrics` (development only)

### Example Health Check Response

```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T12:00:00.000Z",
  "version": "1.0.0",
  "environment": "production",
  "services": {
    "database": {
      "status": "healthy",
      "response_time_ms": 5.2
    },
    "rate_limiting": {
      "status": "healthy",
      "stats": {
        "total_identifiers": 10,
        "total_requests": 150
      }
    },
    "cache": {
      "status": "healthy",
      "stats": {
        "total_keys": 25,
        "expired_keys": 2
      }
    }
  }
}
```

## Authentication Flow

### 1. User Registration

```bash
# Send OTP
POST /auth/send-otp
{
  "email": "user@example.com",
  "purpose": "email_verification"
}

# Verify OTP and Register
POST /auth/register
{
  "email": "user@example.com",
  "otp_code": "123456",
  "user_data": {
    "email": "user@example.com",
    "username": "username",
    "password": "secure_password",
    "full_name": "Full Name"
  }
}
```

### 2. User Login

```bash
POST /auth/login
{
  "email": "user@example.com",
  "password": "secure_password"
}
```

## Rate Limiting

The application includes in-memory rate limiting:

- **Default Limit**: 100 requests per hour per IP
- **Configurable**: Via environment variables
- **Automatic Cleanup**: Expired entries are cleaned up every 5 minutes
- **Fail-Safe**: Fails open if rate limiting service encounters errors

### Rate Limit Headers

```
X-Request-ID: uuid
X-Process-Time: 123.45
Retry-After: 3600 (when rate limited)
```

## Logging

### Log Levels

- **Development**: Colored console output
- **Production**: JSON structured logs with file rotation

### Log Files (Production)

- `logs/app.log` - Application logs (10MB rotation, 5 backups)
- `logs/error.log` - Error logs only
- `logs/access.log` - Gunicorn access logs
- `logs/gunicorn.pid` - Process ID file

### Log Format (JSON)

```json
{
  "timestamp": "2024-01-01T12:00:00.000Z",
  "level": "INFO",
  "logger": "main",
  "message": "Application startup completed",
  "module": "main",
  "function": "lifespan",
  "line": 45
}
```

## Security Features

### 1. Authentication & Authorization

- JWT tokens with configurable expiration
- Email verification via OTP
- Admin role-based access control
- Password hashing with bcrypt

### 2. Input Validation

- Pydantic models for request validation
- File upload validation (type, size)
- SQL injection prevention via SQLAlchemy ORM

### 3. Security Headers

- CORS configuration
- Trusted host middleware (production)
- Gzip compression
- Request ID tracking

### 4. Rate Limiting

- IP-based rate limiting
- OTP resend rate limiting
- Configurable limits and windows

## Monitoring & Observability

### 1. Health Checks

- Database connectivity
- Service status
- Response time monitoring

### 2. Metrics

- Database connection pool stats
- Rate limiting statistics
- Cache performance metrics

### 3. Logging

- Structured JSON logs
- Request/response logging
- Error tracking with context
- Security event logging

## Database Schema

### Core Tables

- **users**: User accounts and authentication
- **chats**: Chat sessions
- **messages**: Chat messages with AI responses
- **file_uploads**: Uploaded file metadata
- **otp_verifications**: Email verification OTPs
- **user_sessions**: Session tracking

### Relationships

```sql
users (1) ──── (many) chats
chats (1) ──── (many) messages
users (1) ──── (many) messages
users (1) ──── (many) file_uploads
users (1) ──── (many) otp_verifications
```

## File Upload

### Supported Formats

- JPEG, PNG, GIF, WebP images
- Maximum size: 10MB (configurable)
- Secure filename generation
- File type validation

### Upload Process

```bash
POST /upload
Content-Type: multipart/form-data

# Response
{
  "id": 1,
  "filename": "uuid-generated-name.jpg",
  "original_filename": "user-file.jpg",
  "url": "/uploads/uuid-generated-name.jpg",
  "file_size": 1024000,
  "content_type": "image/jpeg"
}
```

## Admin Features

### Admin Routes

- `GET /admin/stats` - Dashboard statistics
- `GET /admin/users` - User management with pagination
- `PUT /admin/users/{id}` - Update user
- `DELETE /admin/users/{id}` - Soft delete user

### Admin Statistics

```json
{
  "total_users": 1000,
  "total_chats": 5000,
  "total_messages": 25000,
  "active_users_today": 50,
  "new_users_this_week": 25
}
```

## Deployment Options

### 1. Traditional Server

```bash
# Install dependencies
pip install -r requirements.txt

# Run with Gunicorn
gunicorn --config gunicorn.conf.py main:app
```

### 2. Docker (Future Enhancement)

```dockerfile
# Multi-stage build for optimized image
FROM python:3.11-slim as production
# ... (Docker configuration would go here)
```

### 3. Cloud Platforms

- **AWS**: EC2 + RDS + S3
- **Google Cloud**: Compute Engine + Cloud SQL + Cloud Storage
- **Azure**: App Service + PostgreSQL + Blob Storage
- **DigitalOcean**: Droplets + Managed Database

## Performance Optimization

### 1. Database

- Connection pooling (20 connections, 30 overflow)
- Query optimization with indexes
- Connection timeout and retry logic

### 2. Application

- Async/await for I/O operations
- In-memory caching for frequently accessed data
- Gzip compression for responses

### 3. Monitoring

- Response time tracking
- Database query performance
- Memory usage monitoring

## Troubleshooting

### Common Issues

1. **Database Connection Failed**
   ```bash
   # Check PostgreSQL status
   sudo systemctl status postgresql
   
   # Check connection
   psql -h localhost -U gemini_user -d gemini_clone_production
   ```

2. **Email Not Sending**
   ```bash
   # Verify Gmail app password
   # Check SMTP settings in .env
   # Review email service logs
   ```

3. **Rate Limiting Issues**
   ```bash
   # Check rate limit stats
   curl http://localhost:8000/metrics
   
   # Clear rate limits (restart application)
   ```

### Log Analysis

```bash
# View recent logs
tail -f logs/app.log

# Search for errors
grep "ERROR" logs/app.log

# Monitor requests
tail -f logs/access.log
```

## Backup & Recovery

### Database Backup

```bash
# Create backup
pg_dump -h localhost -U gemini_user gemini_clone_production > backup.sql

# Restore backup
psql -h localhost -U gemini_user gemini_clone_production < backup.sql
```

### File Backup

```bash
# Backup uploads
tar -czf uploads_backup.tar.gz uploads/

# Backup logs
tar -czf logs_backup.tar.gz logs/
```

## Security Checklist

- [ ] Change default passwords
- [ ] Use strong JWT secret key
- [ ] Enable HTTPS in production
- [ ] Configure firewall rules
- [ ] Set up SSL certificates
- [ ] Regular security updates
- [ ] Monitor access logs
- [ ] Implement backup strategy
- [ ] Configure rate limiting
- [ ] Enable audit logging

## Support

For issues and questions:

1. Check the logs: `logs/app.log` and `logs/error.log`
2. Verify configuration: `.env` file settings
3. Test health endpoints: `/health` and `/health/database`
4. Review this documentation

## License

[Your License Here]

---

**Note**: This is a production-ready setup without Redis dependency. All caching and rate limiting is handled in-memory, which means these features will reset on application restart. For high-availability production environments, consider implementing external rate limiting via reverse proxy (nginx, Cloudflare) or load balancer. 