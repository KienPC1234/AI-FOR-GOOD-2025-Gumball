import os
import uvicorn
from sqlalchemy import create_engine, inspect
from app.db.base import Base
from app.models.user import User  # Import all models here

# Set environment variables
os.environ["DATABASE_URL"] = "sqlite:///./app.db"
os.environ["SECRET_KEY"] = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
os.environ["ALGORITHM"] = "HS256"
os.environ["ACCESS_TOKEN_EXPIRE_MINUTES"] = "30"
os.environ["MAILJET_API_KEY"] = "4a36f7c82249e428aee78dec0498c82f"
os.environ["MAILJET_SECRET_KEY"] = "bc6dd8da3d0da5299bc76c2949f021e6"
os.environ["MAILJET_SENDER_EMAIL"] = "anhnguyenhoangnhatvn@gmail.com"
os.environ["MAILJET_SENDER_NAME"] = "Anh Nguyen"
os.environ["BACKEND_CORS_ORIGINS"] = '["http://localhost:8000", "http://localhost:3000"]'
os.environ["PROJECT_NAME"] = "FastAPI Backend"

# Create engine
engine = create_engine("sqlite:///./app.db", connect_args={"check_same_thread": False})

# Check if tables exist
inspector = inspect(engine)
if "user" not in inspector.get_table_names():
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully!")
else:
    print("Database tables already exist.")

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
