from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker

# Create engine
engine = create_engine("sqlite:///app.db", connect_args={"check_same_thread": False})

# Create session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()

# Get inspector
inspector = inspect(engine)

# Print all tables
print("Tables in the database:")
for table_name in inspector.get_table_names():
    print(f"- {table_name}")
    
    # Print columns for each table
    print("  Columns:")
    for column in inspector.get_columns(table_name):
        print(f"    - {column['name']} ({column['type']}), nullable: {column['nullable']}")
    
    print()

# Close session
db.close()
