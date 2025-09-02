#!/usr/bin/env python3
"""
Simple script to change admin password - works in PowerShell
Usage: python simple_password_change.py
"""

from app import app, db, User
from werkzeug.security import generate_password_hash

def change_admin_password():
    """Change the admin user password with visible input"""
    with app.app_context():
        # Find admin user
        admin = User.query.filter_by(username='admin').first()
        
        if not admin:
            print("❌ Error: Admin user not found!")
            return False
        
        print(f"📧 Current admin email: {admin.email}")
        print("🔐 Changing password for admin user...")
        print("⚠️  Note: Password will be visible on screen")
        
        # Get new password with visible input
        while True:
            new_password = input("Enter new admin password (6+ characters): ").strip()
            if len(new_password) < 6:
                print("❌ Password must be at least 6 characters long!")
                continue
            
            confirm_password = input("Confirm new password: ").strip()
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
            print("🔐 Login credentials:")
            print(f"   Username: admin")
            print(f"   Password: {new_password}")
            return True
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error updating password: {e}")
            return False

if __name__ == "__main__":
    print("🔧 Simple Admin Password Change Tool")
    print("=" * 50)
    
    success = change_admin_password()
    
    if success:
        print("\n✅ Password change completed!")
    else:
        print("\n❌ Password change failed!")
