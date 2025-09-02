#!/usr/bin/env python3
"""
Setup script for EarnDaily Website
This script will help you set up the earning website with sample data
"""

import os
import sys
from app import app, db, User, Investment, DailyEarning, Referral
from werkzeug.security import generate_password_hash
import random
import string

def generate_referral_code():
    """Generate a unique 7-digit referral code"""
    while True:
        code = ''.join(random.choices(string.digits, k=7))
        if not User.query.filter_by(referral_code=code).first():
            return code

def setup_database():
    """Create database tables and add sample data"""
    print("Setting up database...")
    
    with app.app_context():
        # Create all tables
        db.create_all()
        
        # Check if admin user already exists
        admin_user = User.query.filter_by(username='admin').first()
        if not admin_user:
            # Create admin user
            admin = User(
                username='admin',
                email='admin@earndaily.com',
                password_hash=generate_password_hash('admin123'),
                referral_code=generate_referral_code()
            )
            db.session.add(admin)
            
            # Create sample users
            users_data = [
                {'username': 'john_doe', 'email': 'john@example.com', 'password': 'password123'},
                {'username': 'jane_smith', 'email': 'jane@example.com', 'password': 'password123'},
                {'username': 'mike_wilson', 'email': 'mike@example.com', 'password': 'password123'},
            ]
            
            created_users = []
            for user_data in users_data:
                user = User(
                    username=user_data['username'],
                    email=user_data['email'],
                    password_hash=generate_password_hash(user_data['password']),
                    referral_code=generate_referral_code()
                )
                db.session.add(user)
                created_users.append(user)
            
            db.session.commit()
            
            # Add sample investments
            for i, user in enumerate(created_users):
                amounts = [500, 1000, 2000]
                amount = amounts[i]
                daily_return = 30 if amount == 500 else 70 if amount == 1000 else 150
                
                investment = Investment(
                    user_id=user.id,
                    amount=amount,
                    daily_return=daily_return
                )
                user.total_investment = amount
                db.session.add(investment)
            
            # Add referral relationships
            referral1 = Referral(
                referrer_id=admin.id,
                referred_user_id=created_users[0].id,
                referral_code=admin.referral_code
            )
            created_users[0].referred_by = admin.referral_code
            
            referral2 = Referral(
                referrer_id=created_users[0].id,
                referred_user_id=created_users[1].id,
                referral_code=created_users[0].referral_code
            )
            created_users[1].referred_by = created_users[0].referral_code
            
            db.session.add(referral1)
            db.session.add(referral2)
            db.session.commit()
            
            print("Database setup completed!")
            print("\nSample Users Created:")
            print("Admin User: username='admin', password='admin123'")
            print("Sample User 1: username='john_doe', password='password123'")
            print("Sample User 2: username='jane_smith', password='password123'")
            print("Sample User 3: username='mike_wilson', password='password123'")
            print(f"\nAdmin Referral Code: {admin.referral_code}")
        else:
            print("Database already exists!")

if __name__ == '__main__':
    setup_database()
