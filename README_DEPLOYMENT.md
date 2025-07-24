# LiteraryAI Studio - Deployment Guide

## 🚨 Current Status: NOT PRODUCTION READY

The application is functional but requires additional work before production deployment. Use this guide for staging/testing deployments only.

## Prerequisites

- Python 3.9+
- PostgreSQL (for production) or SQLite (for testing)
- Redis (optional, for caching)
- 4GB+ RAM recommended
- 10GB+ disk space for file uploads

## Quick Start (Development)

1. **Clone the repository**
```bash
git clone <repository-url>
cd literaryai-studio
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

4. **Set up environment variables**
```bash
cp .env.example .env
# Edit .env with your values
```

5. **Initialize database**
```bash
cd character-creator
python -c "from core.database import DatabaseManager; db = DatabaseManager(); db.init_database()"
```

6. **Run the application**
```bash
streamlit run app/main.py
```

Default login:
- Username: `demo`
- Password: `demo123`

## Critical Issues Before Production

### 1. Authentication & Security
- [ ] Replace basic auth with proper authentication (OAuth, Auth0)
- [ ] Implement proper password hashing and storage
- [ ] Add CSRF protection
- [ ] Enable HTTPS only
- [ ] Implement rate limiting

### 2. Database
- [ ] Migrate from SQLite to PostgreSQL
- [ ] Add database migrations (Alembic)
- [ ] Implement connection pooling
- [ ] Add database backups
- [ ] Create indexes for performance

### 3. File Storage
- [ ] Move from local storage to S3/CloudStorage
- [ ] Implement virus scanning for uploads
- [ ] Add file type validation
- [ ] Implement automatic cleanup
- [ ] Add CDN for static files

### 4. API Integration
- [ ] Add OpenAI API key validation
- [ ] Implement API error handling
- [ ] Add retry logic
- [ ] Track API usage and costs
- [ ] Implement fallback models

### 5. Performance
- [ ] Add Redis caching
- [ ] Implement background job processing (Celery)
- [ ] Add request queuing
- [ ] Optimize database queries
- [ ] Implement pagination

### 6. Monitoring
- [ ] Set up error tracking (Sentry)
- [ ] Add application monitoring (DataDog/NewRelic)
- [ ] Implement logging aggregation
- [ ] Set up alerts
- [ ] Add health checks

## Staging Deployment (Docker)

1. **Build Docker image**
```bash
docker build -t literaryai-studio .
```

2. **Run with Docker Compose**
```bash
docker-compose up -d
```

3. **Access application**
```
http://localhost:8501
```

## Production Deployment (AWS/GCP)

### Using AWS Elastic Beanstalk

1. **Install EB CLI**
```bash
pip install awsebcli
```

2. **Initialize EB**
```bash
eb init -p python-3.9 literaryai-studio
```

3. **Create environment**
```bash
eb create production-env
```

4. **Deploy**
```bash
eb deploy
```

### Using Heroku

1. **Create Heroku app**
```bash
heroku create literaryai-studio
```

2. **Add PostgreSQL**
```bash
heroku addons:create heroku-postgresql:hobby-dev
```

3. **Set environment variables**
```bash
heroku config:set OPENAI_API_KEY=your-key
heroku config:set SECRET_KEY=your-secret-key
```

4. **Deploy**
```bash
git push heroku main
```

## Environment Variables

Required for production:

```bash
# API Keys
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=...

# Database
DATABASE_URL=postgresql://user:pass@host:port/dbname

# Security
SECRET_KEY=<generate-with-openssl-rand-hex-32>
SESSION_TIMEOUT=3600

# Application
APP_ENV=production
DEBUG=False
LOG_LEVEL=WARNING

# File Upload
UPLOAD_MAX_SIZE_MB=50
ALLOWED_EXTENSIONS=pdf,docx,txt,md,epub

# Redis (if using)
REDIS_URL=redis://localhost:6379/0
```

## Security Checklist

- [ ] Change default passwords
- [ ] Set strong SECRET_KEY
- [ ] Enable HTTPS
- [ ] Configure CORS properly
- [ ] Validate all user inputs
- [ ] Sanitize file uploads
- [ ] Implement rate limiting
- [ ] Add request logging
- [ ] Set up firewall rules
- [ ] Regular security updates

## Monitoring Setup

1. **Application Logs**
```bash
# View logs
tail -f logs/app.log
tail -f logs/error.log
```

2. **System Metrics**
- CPU usage < 80%
- Memory usage < 80%
- Disk space > 20%
- Response time < 2s

3. **Alerts**
- Set up alerts for errors
- Monitor API usage
- Track user signups
- Watch for suspicious activity

## Backup Strategy

1. **Database Backups**
```bash
# Daily backups
pg_dump $DATABASE_URL > backup_$(date +%Y%m%d).sql
```

2. **File Backups**
- Sync uploads to S3
- Keep 30-day retention
- Test restore process

## Scaling Considerations

1. **Horizontal Scaling**
- Use load balancer
- Share session state (Redis)
- Use external file storage
- Database read replicas

2. **Vertical Scaling**
- Start with 2 vCPUs, 4GB RAM
- Monitor and adjust
- Use auto-scaling groups

## Troubleshooting

### Common Issues

1. **"No module named 'character_creator'"**
   - Ensure you're in the correct directory
   - Check Python path

2. **"Database locked"**
   - SQLite limitation
   - Switch to PostgreSQL for production

3. **"Out of memory"**
   - Large file processing
   - Increase server RAM
   - Implement streaming

4. **"API rate limit"**
   - Implement caching
   - Use queue system
   - Upgrade API plan

## Support

For deployment issues:
1. Check logs first
2. Review this guide
3. Search existing issues
4. Create new issue with details

## Final Notes

**DO NOT DEPLOY TO PRODUCTION WITHOUT:**
1. Proper authentication
2. PostgreSQL database
3. S3 file storage
4. Error monitoring
5. Security review
6. Load testing
7. Backup system
8. SSL certificate

The application works well for testing but needs these improvements for production use.