#!/usr/bin/env python3
"""
Force SQLAlchemy to use the correct model definitions by completely reloading the module
"""

import os
import sys

def force_correct_schema():
    """Force correct schema creation"""
    print("Forcing correct schema creation...")
    
    # Remove any cached modules
    modules_to_reload = [mod for mod in sys.modules.keys() if mod.startswith('app')]
    for mod in modules_to_reload:
        if mod in sys.modules:
            del sys.modules[mod]
    
    # Import fresh app module
    from app import app, db, User, Withdrawal, generate_password_hash, generate_referral_code
    
    with app.app_context():
        # Ensure the database file is completely gone
        db_file = 'earning_website.db'
        if os.path.exists(db_file):
            os.remove(db_file)
        
        # Print the Withdrawal model definition to verify it has UPI columns
        print("Withdrawal model columns:")
        for column_name in Withdrawal.__table__.columns.keys():
            column = Withdrawal.__table__.columns[column_name]
            print(f"  - {column_name}: {column.type}")
        
        # Check if UPI columns are in the model
        if 'upi_id' in Withdrawal.__table__.columns:
            print("✅ UPI columns found in Withdrawal model")
        else:
            print("❌ UPI columns missing from Withdrawal model!")
            return False
        
        # Create all tables from the current model definitions
        db.create_all()
        print("✅ Database created with SQLAlchemy models")
        
        # Verify the created schema matches our expectations
        result = db.session.execute(db.text("PRAGMA table_info(withdrawal)"))
        columns = result.fetchall()
        
        print("\nActual created schema:")
        for col in columns:
            print(f"  - {col[1]}: {col[2]}")
        
        # Check for UPI columns in created schema
        upi_columns = [col[1] for col in columns if 'upi' in col[1].lower()]
        if upi_columns:
            print(f"✅ UPI columns created: {upi_columns}")
            
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
                print("✅ Admin user created")
            except Exception as e:
                print(f"⚠️  Admin user creation: {e}")
                db.session.rollback()
            
            return True
        else:
            print("❌ UPI columns still missing after creation!")
            return False

if __name__ == '__main__':
    success = force_correct_schema()
    if success:
        print("\n🎉 Schema created successfully with UPI columns!")
    else:
        print("\n❌ Schema creation failed")
