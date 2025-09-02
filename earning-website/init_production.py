#!/usr/bin/env python3
"""
Initialize production database and create admin user
Run this ONCE after deploying to production
"""

from app import app, db, User
from werkzeug.security import generate_password_hash
import os

def init_production_db():
    """Initialize production database and create admin user"""
    with app.app_context():
        print("🚀 Initializing production database...")
        
        # Create all database tables
        db.create_all()
        print("✅ Database tables created")
        
        # Check if admin user exists
        admin = User.query.filter_by(username='admin').first()
        
        if not admin:
            print("👤 Creating admin user...")
            # Create admin user with default password
            admin = User(
                username='admin',
                email='admin@yourdomain.com',  # Change this to your email
                password_hash=generate_password_hash('admin123'),  # Change this password
                referral_code='1000000',  # Special admin referral code
                total_investment=0,
                total_earnings=0,
                referral_earnings=0
            )
            
            db.session.add(admin)
            db.session.commit()
            
            print("✅ Admin user created successfully!")
            print("🔐 Default admin credentials:")
            print("   Username: admin")
            print("   Password: admin123")
            print("   Email: admin@yourdomain.com")
            print("⚠️  IMPORTANT: Change these credentials immediately!")
        else:
            print("👤 Admin user already exists")
            print(f"   Username: {admin.username}")
            print(f"   Email: {admin.email}")
        
        print("🎉 Production initialization completed!")

if __name__ == "__main__":
    print("🏭 Production Database Initialization")
    print("=" * 50)
    
    # Check if we're in production environment
    if os.environ.get('DATABASE_URL'):
        print("🌐 Production environment detected")
    else:
        print("💻 Local environment detected")
    
    confirm = input("Continue with initialization? (y/N): ").lower().strip()
    if confirm in ['y', 'yes']:
        init_production_db()
    else:
        print("❌ Initialization cancelled")
