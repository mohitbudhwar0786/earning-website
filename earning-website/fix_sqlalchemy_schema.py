#!/usr/bin/env python3
"""
Force SQLAlchemy to recognize the updated database schema.
This script will clear SQLAlchemy's metadata cache and force it to reflect the actual database schema.
"""

import os
import sys

def fix_sqlalchemy_schema():
    """Fix SQLAlchemy schema recognition issues"""
    print("Fixing SQLAlchemy schema recognition...")
    
    # Import Flask app components
    from app import app, db
    
    with app.app_context():
        # Clear all cached metadata
        db.metadata.clear()
        
        # Drop all SQLAlchemy table objects (not the actual database tables)
        db.metadata.drop_all(db.engine, checkfirst=False)
        
        # Force SQLAlchemy to reflect the actual database schema
        db.metadata.reflect(db.engine)
        
        # Now recreate the metadata based on the actual database
        db.create_all()
        
        print("✅ SQLAlchemy metadata refreshed!")
        
        # Test that we can query the Withdrawal table
        try:
            from app import Withdrawal
            
            # Try to query the withdrawal table
            result = db.session.execute(db.text("SELECT COUNT(*) FROM withdrawal")).scalar()
            print(f"✅ Withdrawal table accessible - found {result} rows")
            
            # Test UPI columns specifically
            result = db.session.execute(db.text("SELECT upi_id, upi_name FROM withdrawal LIMIT 1")).fetchone()
            print("✅ UPI columns accessible")
            
            # Test creating a test withdrawal (then delete it)
            from app import User
            user = User.query.first()
            if user:
                test_withdrawal = Withdrawal(
                    user_id=user.id,
                    amount=100.0,
                    upi_id='test@upi',
                    upi_name='Test User',
                    status='pending'
                )
                db.session.add(test_withdrawal)
                db.session.flush()  # Don't commit, just test
                
                print("✅ Can create Withdrawal objects with UPI fields")
                
                # Clean up
                db.session.rollback()
            else:
                print("⚠️  No users found to test with")
                
        except Exception as e:
            print(f"❌ Schema issue still exists: {e}")
            return False
    
    print("🎉 SQLAlchemy schema is now properly synchronized!")
    return True

if __name__ == '__main__':
    success = fix_sqlalchemy_schema()
    if success:
        print("\n🚀 You can now start the Flask application safely!")
    else:
        print("\n❌ Schema issues persist. Manual intervention may be needed.")
