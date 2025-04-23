import os
import sys
from sqlalchemy import create_engine
from app.db.base import Base
from app.models.user import User  # Import all models here
from app.core.config import settings
from app.core.security import get_password_hash

# Set environment variables if needed
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
engine = create_engine(settings.DATABASE_URL, connect_args={"check_same_thread": False})

def init_db():
    # Create tables
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully!")

    # Create a session to add initial data if needed
    from sqlalchemy.orm import sessionmaker
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # Check if there's already a superuser
        from app.models.user import User
        user = db.query(User).filter(User.is_superuser == True).first()
        
        if not user:
            # Create a superuser
            admin_user = User(
                email="admin@example.com",
                hashed_password=get_password_hash("adminpassword"),
                is_active=True,
                is_superuser=True,
            )
            db.add(admin_user)
            db.commit()
            print("Admin user created successfully!")
    except Exception as e:
        print(f"Error creating admin user: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    init_db()
