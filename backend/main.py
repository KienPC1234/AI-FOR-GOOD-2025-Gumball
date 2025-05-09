import uvicorn
from sqlalchemy import create_engine, inspect

from app.db.base import Base
from app.models.user import User
from app.core.config import settings

# Create engine
engine = create_engine(settings.DATABASE_URL_ASYNC, connect_args={"check_same_thread": False})

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
