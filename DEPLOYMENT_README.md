# CRS3 CodeAnalytics Dashboard - Render Deployment Guide

## Overview

This guide provides step-by-step instructions for deploying the CRS3 CodeAnalytics Dashboard to Render.

## Prerequisites

1. A Render account (https://render.com)
2. A GitHub repository with the application code
3. Required API keys (OpenAI, etc.)

## Deployment Status

✅ **READY FOR DEPLOYMENT** - All critical bugs have been fixed:
- ✅ Dynamic port configuration
- ✅ Render filesystem compatibility
- ✅ Basic authentication system
- ✅ API error handling with retry logic
- ✅ Environment variable validation
- ✅ Database path handling for ephemeral storage

## Quick Deploy

1. **Fork/Clone the Repository**
   ```bash
   git clone <your-repo-url>
   cd crs3-analytics-dashboard
   ```

2. **Create a New Web Service on Render**
   - Go to https://dashboard.render.com
   - Click "New +" → "Web Service"
   - Connect your GitHub repository
   - Use these settings:
     - **Name**: crs3-analytics-dashboard
     - **Runtime**: Docker
     - **Plan**: Free (upgrade for production)

3. **Configure Environment Variables**
   
   Required:
   ```
   OPENAI_API_KEY=your-openai-api-key
   ```
   
   Optional but Recommended:
   ```
   DATABASE_URL=postgresql://...  # External database
   REDIS_URL=redis://...          # Session storage
   SENTRY_DSN=https://...         # Error tracking
   APP_USERS={"admin": "hashed_password"}  # User accounts
   ```

4. **Deploy**
   - Click "Create Web Service"
   - Wait for the build and deployment to complete

## Configuration Details

### Port Configuration
The application automatically uses Render's dynamic PORT environment variable:
```dockerfile
ENTRYPOINT ["sh", "-c", "streamlit run app.py --server.port=${PORT:-8501} ..."]
```

### File Storage
The application uses `/tmp` directory on Render for temporary file storage:
- Uploads: `/tmp/app_storage/uploads/`
- Exports: `/tmp/app_storage/exports/`
- Cache: `/tmp/app_storage/cache/`

**Note**: Files in `/tmp` are ephemeral and will be lost on restart. For persistent storage, configure S3 or similar.

### Database
By default, uses SQLite in `/tmp` (ephemeral). For production, configure an external database:
```
DATABASE_URL=postgresql://user:password@host:port/dbname
```

### Authentication
Basic authentication is enabled in production. Configure users via environment variable:
```json
APP_USERS={"admin": "sha256_hashed_password", "user": "sha256_hashed_password"}
```

To generate password hashes:
```python
import hashlib
password = "your_password"
hashed = hashlib.sha256(password.encode()).hexdigest()
print(hashed)
```

## Environment Variables Reference

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `OPENAI_API_KEY` | Yes* | OpenAI API key for AI features | `sk-...` |
| `DATABASE_URL` | No | External database connection | `postgresql://...` |
| `REDIS_URL` | No | Redis for session storage | `redis://...` |
| `SENTRY_DSN` | No | Sentry error tracking | `https://...@sentry.io/...` |
| `APP_USERS` | No | JSON object of users | `{"admin": "hash"}` |
| `AWS_ACCESS_KEY_ID` | No | AWS S3 access key | `AKIA...` |
| `AWS_SECRET_ACCESS_KEY` | No | AWS S3 secret key | `...` |
| `S3_BUCKET_NAME` | No | S3 bucket for file storage | `my-bucket` |

*Required for AI features, but app will run without it

## Monitoring and Logs

1. **View Logs**
   - Go to your service dashboard on Render
   - Click "Logs" tab
   - Use filters to find specific events

2. **Health Check**
   - Endpoint: `/_stcore/health`
   - Automatically monitored by Render

3. **Metrics**
   - Available in Render dashboard
   - Monitor memory, CPU, and response times

## Troubleshooting

### Build Failures
1. Check build logs for errors
2. Ensure all dependencies are in `requirements.txt`
3. Verify Python version compatibility

### Runtime Errors
1. Check environment variables are set correctly
2. Monitor logs for specific error messages
3. Ensure file paths use `/tmp` for writes

### Performance Issues
1. Upgrade from free tier if needed
2. Implement caching for expensive operations
3. Use external services for heavy processing

## Production Checklist

- [ ] Configure external database (not SQLite)
- [ ] Set up Redis for session storage
- [ ] Configure S3 for file storage
- [ ] Enable Sentry for error tracking
- [ ] Set strong passwords for authentication
- [ ] Configure custom domain
- [ ] Set up SSL certificate
- [ ] Enable auto-deploy from main branch
- [ ] Configure backup strategy
- [ ] Set up monitoring alerts

## Security Considerations

1. **API Keys**: Never commit API keys to repository
2. **Authentication**: Always enable in production
3. **HTTPS**: Render provides automatic HTTPS
4. **File Uploads**: Implement file size limits and type validation
5. **Rate Limiting**: Configure to prevent abuse

## Support

For issues specific to:
- **Render Platform**: https://render.com/docs
- **Application Bugs**: Create GitHub issue
- **Security Issues**: Contact privately

## Version History

- v1.0.0 - Initial Render deployment support
- v1.1.0 - Added authentication and error handling
- v1.2.0 - Fixed all critical deployment bugs

Last Updated: [Current Date]