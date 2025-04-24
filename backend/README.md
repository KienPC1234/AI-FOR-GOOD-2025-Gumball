# FastAPI Backend

A professional FastAPI backend with SQLite, JWT authentication, and Mailjet email integration.

## Features

- FastAPI framework with automatic Swagger documentation
- SQLite database with SQLAlchemy ORM
- JWT authentication
- User registration and login
- Email notifications using Mailjet
- Comprehensive test suite
- Professional project structure

## Project Structure

```
backend/
├── app/                      # Application package
│   ├── api/                  # API endpoints
│   ├── core/                 # Core modules (config, security, email)
│   ├── db/                   # Database modules
│   ├── models/               # SQLAlchemy models
│   ├── schemas/              # Pydantic schemas
│   └── utils/                # Utility functions
├── tests/                    # Test suite
├── .env                      # Environment variables
├── .env.example             # Example environment variables
├── main.py                   # Entry point script
└── requirements.txt          # Project dependencies
```

## Getting Started

### Prerequisites

- Python 3.8+
- pip

### Installation

1. Clone the repository
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Configure environment variables:

```bash
cp .env.example .env
# Edit .env with your configuration
```

4. Run the application:

```bash
python main.py
```

5. Celery Setup

Install Redis and start the Redis server:

```bash
sudo apt install redis
redis-server
celery -A celery_app.celery_app worker --loglevel=info
```

### API Documentation

Once the application is running, you can access the Swagger documentation at:

```
http://localhost:8000/api/docs
```

## Testing

Run tests with pytest:

```bash
pytest
```

## API Endpoints

### Authentication

- `POST /api/auth/register` - Register a new user
- `POST /api/auth/login` - Login and get access token
- `POST /api/auth/test-token` - Test access token

### Users

- `GET /api/users/me` - Get current user
- `PUT /api/users/me` - Update current user
- `GET /api/users/{user_id}` - Get user by ID (admin only)
- `GET /api/users/` - Get all users (admin only)
