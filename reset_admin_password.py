#!/usr/bin/env python3
"""
Quick script to reset admin password to a default value.
Usage: python reset_admin_password.py
"""

from app import app, db, User
from werkzeug.security import generate_password_hash

def reset_admin_password():
    """Reset admin password to 'admin123'"""
    with app.app_context():
        # Find admin user
        admin = User.query.filter_by(username='admin').first()
        
        if not admin:
            print("❌ Error: Admin user not found!")
            return False
        
        # Set default password
        default_password = "admin123"
        
        try:
            admin.password_hash = generate_password_hash(default_password)
            db.session.commit()
            print("✅ Admin password reset successfully!")
            print(f"🔑 New admin password: {default_password}")
            print("⚠️  Please change this password after logging in!")
            return True
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error resetting password: {e}")
            return False

if __name__ == "__main__":
    print("🔧 Admin Password Reset Tool")
    print("=" * 40)
    print("⚠️  This will reset admin password to 'admin123'")
    
    confirm = input("Continue? (y/N): ").lower().strip()
    if confirm in ['y', 'yes']:
        success = reset_admin_password()
        if success:
            print("\n✅ Password reset completed!")
            print("🔐 Login with username: admin, password: admin123")
        else:
            print("\n❌ Password reset failed!")
    else:
        print("❌ Operation cancelled.")
