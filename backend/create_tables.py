import env_setup
import sys
from sqlalchemy import create_engine
from app.db.base import Base
from app.models.user import User  # Import all models here
from app.core.config import settings
from app.core.security import get_password_hash

# Set environment variables if needed
env_setup.set_envs()

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
