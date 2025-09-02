#!/usr/bin/env python3
"""
Database initialization script to create a fresh database with the correct schema.
This script will create all tables with the proper UPI columns.
"""

import os
import sys

def init_database():
    """Initialize a fresh database with all tables"""
    print("Creating fresh database...")
    
    # Remove existing database file if it exists
    db_file = 'earning_website.db'
    if os.path.exists(db_file):
        os.remove(db_file)
        print(f"Removed existing database file: {db_file}")
    
    # Import after removing DB file to avoid cached metadata
    from app import app, db, User, Withdrawal, generate_password_hash, generate_referral_code
    
    # Create all tables with correct schema
    with app.app_context():
        # Clear any cached metadata
        db.metadata.clear()
        
        # Force recreate all tables
        db.drop_all()
        db.create_all()
        print("Database tables created successfully!")
        
        # Create admin user
        try:
            admin_user = User(
                username='admin',
                email='admin@example.com',
                password_hash=generate_password_hash('admin123'),
                referral_code=generate_referral_code()
            )
            db.session.add(admin_user)
            db.session.commit()
            print("Admin user created successfully!")
            print("Username: admin")
            print("Password: admin123")
        except Exception as e:
            print(f"Admin user creation failed: {e}")
            db.session.rollback()
        
        # Verify the Withdrawal table has the correct columns
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        
        try:
            withdrawal_columns = inspector.get_columns('withdrawal')
            
            print("\nWithdrawal table columns:")
            for col in withdrawal_columns:
                print(f"  - {col['name']}: {col['type']}")
            
            # Check specifically for UPI columns
            upi_columns = [col['name'] for col in withdrawal_columns if 'upi' in col['name'].lower()]
            if upi_columns:
                print(f"\nUPI columns found: {upi_columns}")
                print("✅ Database schema is correct!")
                return True
            else:
                print("❌ UPI columns missing from schema!")
                return False
                
        except Exception as e:
            print(f"Error inspecting database: {e}")
            return False

if __name__ == '__main__':
    init_database()
