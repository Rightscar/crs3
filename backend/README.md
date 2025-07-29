# LiteraryAI Studio Backend API

This is the FastAPI backend for LiteraryAI Studio, providing REST APIs for document processing, character management, and real-time interactions.

## Phase 0 Implementation Status

This backend is part of Phase 0 (Technical Prerequisites) of the Multi-Character Ecosystem project. It provides:

- ✅ Separated backend API from monolithic Streamlit app
- ✅ RESTful API endpoints for all operations
- ✅ JWT-based authentication
- ✅ Async request handling
- ✅ Auto-generated API documentation
- 🚧 Database migrations (PostgreSQL, Neo4j, Pinecone)
- 🚧 WebSocket support for real-time updates
- 🚧 Background task processing (Celery)

## Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL 14+
- Redis 7+
- Neo4j 5+ (optional for now)

### Installation

1. Clone the repository and navigate to backend:
```bash
cd backend
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Copy environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. Run the development server:
```bash
uvicorn api.main:app --reload
```

The API will be available at `http://localhost:8000`

## API Documentation

Once the server is running, you can access:

- Interactive API docs (Swagger UI): `http://localhost:8000/api/v1/docs`
- Alternative API docs (ReDoc): `http://localhost:8000/api/v1/redoc`
- OpenAPI schema: `http://localhost:8000/api/v1/openapi.json`

## Authentication

The API uses JWT tokens for authentication. To get started:

1. Register a new user or use the test credentials:
   - Username: `testuser`
   - Password: `testpass123`

2. Login to get an access token:
```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=testuser&password=testpass123"
```

3. Use the token in subsequent requests:
```bash
curl -X GET "http://localhost:8000/api/v1/documents" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## Project Structure

```
backend/
├── api/
│   ├── main.py           # FastAPI application
│   ├── routers/          # API endpoints
│   │   ├── auth.py       # Authentication endpoints
│   │   ├── documents.py  # Document management
│   │   ├── characters.py # Character management
│   │   └── health.py     # Health checks
│   └── middleware/       # Custom middleware
├── core/
│   ├── config.py         # Configuration management
│   ├── database.py       # Database connections
│   └── security.py       # Security utilities
├── services/
│   ├── document_service.py  # Document processing logic
│   └── character_service.py # Character management logic
├── models/               # Database models
├── tests/               # Test suite
└── requirements.txt     # Python dependencies
```

## Available Endpoints

### Authentication
- `POST /api/v1/auth/login` - Login with username/password
- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/refresh` - Refresh access token
- `GET /api/v1/auth/me` - Get current user info

### Documents
- `POST /api/v1/documents/upload` - Upload a document
- `GET /api/v1/documents` - List documents
- `GET /api/v1/documents/{id}` - Get document details
- `GET /api/v1/documents/{id}/text` - Get document text
- `GET /api/v1/documents/{id}/analyze` - Analyze document
- `DELETE /api/v1/documents/{id}` - Delete document

### Characters
- `POST /api/v1/characters` - Create character
- `GET /api/v1/characters` - List characters
- `GET /api/v1/characters/{id}` - Get character details
- `PUT /api/v1/characters/{id}` - Update character
- `DELETE /api/v1/characters/{id}` - Delete character
- `POST /api/v1/characters/{id}/chat` - Chat with character

### Health
- `GET /health` - Basic health check
- `GET /health/detailed` - Detailed system status
- `GET /health/ready` - Kubernetes readiness probe
- `GET /health/live` - Kubernetes liveness probe

## Development

### Running Tests
```bash
pytest
```

### Code Coverage
```bash
pytest --cov=. --cov-report=html
```

### Linting
```bash
flake8 .
black .
isort .
```

## Docker

Build and run with Docker:

```bash
docker build -t literaryai-backend .
docker run -p 8000:8000 --env-file .env literaryai-backend
```

## Next Steps (Week 3-6 of Phase 0)

- [ ] Migrate from SQLite to PostgreSQL
- [ ] Set up Neo4j for relationship graphs
- [ ] Configure Pinecone for vector search
- [ ] Implement WebSocket support
- [ ] Add Redis caching
- [ ] Set up Celery for background tasks
- [ ] Create database models
- [ ] Write comprehensive tests

## Contributing

This is part of the Multi-Character Ecosystem project. Please refer to the main project documentation for contribution guidelines.

## License

[Your License Here]