#!/usr/bin/env python3
"""
Debug script to check exactly which database file SQLAlchemy is connecting to
"""

import os
from app import app, db

def debug_database_path():
    """Check the exact database path SQLAlchemy is using"""
    with app.app_context():
        # Get the database URL
        db_url = app.config['SQLALCHEMY_DATABASE_URI']
        print(f"SQLAlchemy Database URL: {db_url}")
        
        # Extract the actual file path
        if db_url.startswith('sqlite:///'):
            db_path = db_url[10:]  # Remove 'sqlite:///'
            print(f"Database file path: {db_path}")
            
            # Check if it's a relative path
            if not os.path.isabs(db_path):
                full_path = os.path.abspath(db_path)
                print(f"Absolute path: {full_path}")
                
                # Check if this file exists
                if os.path.exists(full_path):
                    print(f"✅ Database file exists: {full_path}")
                    print(f"File size: {os.path.getsize(full_path)} bytes")
                    print(f"Last modified: {os.path.getmtime(full_path)}")
                else:
                    print(f"❌ Database file does not exist: {full_path}")
            
        # Get the current working directory
        print(f"Current working directory: {os.getcwd()}")
        
        # List all .db files in current directory
        db_files = [f for f in os.listdir('.') if f.endswith('.db')]
        print(f"Database files in current directory: {db_files}")
        
        # Check if SQLAlchemy engine can connect
        try:
            result = db.session.execute(db.text("SELECT name FROM sqlite_master WHERE type='table' AND name='withdrawal'"))
            tables = result.fetchall()
            if tables:
                print("✅ SQLAlchemy can see the withdrawal table")
            else:
                print("❌ SQLAlchemy cannot see the withdrawal table")
                
            # Try to get the schema SQLAlchemy sees
            result = db.session.execute(db.text("PRAGMA table_info(withdrawal)"))
            columns = result.fetchall()
            print("Columns SQLAlchemy sees:")
            for col in columns:
                print(f"  - {col[1]}: {col[2]}")
                
            upi_columns = [col[1] for col in columns if 'upi' in col[1].lower()]
            if upi_columns:
                print(f"✅ SQLAlchemy sees UPI columns: {upi_columns}")
            else:
                print("❌ SQLAlchemy does not see UPI columns")
                
        except Exception as e:
            print(f"❌ Error connecting to database: {e}")

if __name__ == '__main__':
    debug_database_path()
