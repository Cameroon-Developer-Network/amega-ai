#!/usr/bin/env python3

"""
Database initialization script for Amega AI.
This script creates the initial database schema and sets up any required tables.
"""

import os
import sys
from pathlib import Path

# Add the project root directory to the Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker

# Load environment variables
load_dotenv()

def init_database():
    """Initialize the database with required tables and initial data."""
    try:
        # Get database URL from environment variables
        db_url = os.getenv('DB_URL')
        if not db_url:
            print("Error: DB_URL environment variable not set")
            sys.exit(1)

        # Create database engine
        engine = create_engine(db_url)

        # Import models here to avoid circular imports
        from src.amega_ai.models import Base

        # Create all tables
        Base.metadata.create_all(engine)

        # Create session
        Session = sessionmaker(bind=engine)
        session = Session()

        # Add any initial data here if needed

        session.commit()
        print("Database initialized successfully!")

    except SQLAlchemyError as e:
        print(f"Error initializing database: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)
    finally:
        if 'session' in locals():
            session.close()

if __name__ == "__main__":
    print("Initializing database...")
    init_database() 
