#!/usr/bin/env python3
"""
Manual DDL approach to force UPI columns creation
"""

import os
from sqlalchemy import text

def manual_ddl_fix():
    """Manually alter the withdrawal table to add UPI columns"""
    print("Applying manual DDL fix...")
    
    from app import app, db
    
    with app.app_context():
        # First, let's see what columns currently exist
        result = db.session.execute(text("PRAGMA table_info(withdrawal)"))
        current_columns = [row[1] for row in result.fetchall()]
        print(f"Current columns: {current_columns}")
        
        # Check if UPI columns already exist
        if 'upi_id' in current_columns and 'upi_name' in current_columns:
            print("✅ UPI columns already exist")
            return True
        
        # If UPI columns don't exist, add them manually
        try:
            if 'upi_id' not in current_columns:
                print("Adding upi_id column...")
                db.session.execute(text("ALTER TABLE withdrawal ADD COLUMN upi_id VARCHAR(100)"))
                
            if 'upi_name' not in current_columns:
                print("Adding upi_name column...")
                db.session.execute(text("ALTER TABLE withdrawal ADD COLUMN upi_name VARCHAR(100)"))
            
            db.session.commit()
            print("✅ UPI columns added successfully!")
            
            # Verify the columns were added
            result = db.session.execute(text("PRAGMA table_info(withdrawal)"))
            updated_columns = [row[1] for row in result.fetchall()]
            
            print(f"Updated columns: {updated_columns}")
            
            if 'upi_id' in updated_columns and 'upi_name' in updated_columns:
                print("✅ Verification successful - UPI columns are present")
                
                # Test that we can now create a withdrawal with UPI fields
                from app import User, Withdrawal
                
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
                    db.session.flush()  # Test without committing
                    print("✅ Can create Withdrawal with UPI fields!")
                    db.session.rollback()  # Clean up test
                
                return True
            else:
                print("❌ Verification failed - UPI columns not found after adding")
                return False
                
        except Exception as e:
            print(f"❌ Error adding UPI columns: {e}")
            db.session.rollback()
            return False

if __name__ == '__main__':
    success = manual_ddl_fix()
    if success:
        print("\n🎉 UPI columns successfully added to withdrawal table!")
        print("You can now start the Flask application.")
    else:
        print("\n❌ Failed to add UPI columns.")
