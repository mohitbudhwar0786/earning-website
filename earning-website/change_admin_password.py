#!/usr/bin/env python3
"""
Script to change the admin password for the earning website.
Usage: python change_admin_password.py
"""

from app import app, db, User
from werkzeug.security import generate_password_hash
import getpass

def change_admin_password():
    """Change the admin user password"""
    with app.app_context():
        # Find admin user
        admin = User.query.filter_by(username='admin').first()
        
        if not admin:
            print("❌ Error: Admin user not found!")
            return False
        
        print(f"📧 Current admin email: {admin.email}")
        print("🔐 Changing password for admin user...")
        
        # Get new password
        while True:
            new_password = getpass.getpass("Enter new admin password: ")
            if len(new_password) < 6:
                print("❌ Password must be at least 6 characters long!")
                continue
            
            confirm_password = getpass.getpass("Confirm new password: ")
            if new_password != confirm_password:
                print("❌ Passwords do not match!")
                continue
            
            break
        
        # Update password
        try:
            admin.password_hash = generate_password_hash(new_password)
            db.session.commit()
            print("✅ Admin password changed successfully!")
            print("🔑 You can now login with the new password.")
            return True
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error updating password: {e}")
            return False

if __name__ == "__main__":
    print("🔧 Admin Password Change Tool")
    print("=" * 40)
    
    success = change_admin_password()
    
    if success:
        print("\n✅ Password change completed!")
    else:
        print("\n❌ Password change failed!")
