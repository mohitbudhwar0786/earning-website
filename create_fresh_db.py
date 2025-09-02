#!/usr/bin/env python3
"""
Standalone database creation script to create the correct schema with UPI columns.
This script doesn't import from app.py to avoid any potential caching issues.
"""

import sqlite3
import os
from werkzeug.security import generate_password_hash
import random
import string
from datetime import datetime

def generate_referral_code():
    """Generate a unique 7-digit referral code"""
    return ''.join(random.choices(string.digits, k=7))

def create_database():
    """Create database with correct schema including UPI columns"""
    db_file = 'earning_website.db'
    
    # Remove existing file
    if os.path.exists(db_file):
        os.remove(db_file)
        print(f"Removed existing database file: {db_file}")
    
    # Connect and create schema
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    
    try:
        # Create User table
        cursor.execute("""
        CREATE TABLE user (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username VARCHAR(80) UNIQUE NOT NULL,
            email VARCHAR(120) UNIQUE NOT NULL,
            password_hash VARCHAR(120) NOT NULL,
            referral_code VARCHAR(7) UNIQUE NOT NULL,
            referred_by VARCHAR(7),
            total_investment FLOAT DEFAULT 0,
            total_earnings FLOAT DEFAULT 0,
            referral_earnings FLOAT DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # Create Investment table
        cursor.execute("""
        CREATE TABLE investment (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            amount FLOAT NOT NULL,
            daily_return FLOAT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            is_active BOOLEAN DEFAULT 1,
            FOREIGN KEY(user_id) REFERENCES user(id)
        )
        """)
        
        # Create DailyEarning table
        cursor.execute("""
        CREATE TABLE daily_earning (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            amount FLOAT NOT NULL,
            earning_type VARCHAR(20) NOT NULL,
            date DATE DEFAULT CURRENT_DATE,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES user(id)
        )
        """)
        
        # Create Referral table
        cursor.execute("""
        CREATE TABLE referral (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            referrer_id INTEGER NOT NULL,
            referred_user_id INTEGER NOT NULL,
            referral_code VARCHAR(7) NOT NULL,
            bonus_earned FLOAT DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(referrer_id) REFERENCES user(id)
        )
        """)
        
        # Create Wallet table
        cursor.execute("""
        CREATE TABLE wallet (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            balance FLOAT DEFAULT 0,
            total_earned FLOAT DEFAULT 0,
            total_withdrawn FLOAT DEFAULT 0,
            last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES user(id)
        )
        """)
        
        # Create Withdrawal table WITH UPI COLUMNS
        cursor.execute("""
        CREATE TABLE withdrawal (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            amount FLOAT NOT NULL,
            status VARCHAR(20) DEFAULT 'pending',
            bank_details TEXT,
            upi_id VARCHAR(100),
            upi_name VARCHAR(100),
            requested_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            processed_at DATETIME,
            processing_time INTEGER DEFAULT 24,
            payment_method VARCHAR(20),
            payment_reference VARCHAR(100),
            payment_time_hours INTEGER,
            payment_time_minutes INTEGER,
            FOREIGN KEY(user_id) REFERENCES user(id)
        )
        """)
        
        # Create ChatMessage table
        cursor.execute("""
        CREATE TABLE chat_message (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            message TEXT NOT NULL,
            is_admin_reply BOOLEAN DEFAULT 0,
            is_read BOOLEAN DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES user(id)
        )
        """)
        
        # Create PaymentConfig table
        cursor.execute("""
        CREATE TABLE payment_config (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            admin_name VARCHAR(100) DEFAULT 'EarnDaily Admin',
            upi_id VARCHAR(100) DEFAULT 'admin@paytm',
            qr_code_path VARCHAR(200),
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # Create PaymentConfirmation table
        cursor.execute("""
        CREATE TABLE payment_confirmation (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            withdrawal_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            payment_reference VARCHAR(100) NOT NULL,
            payment_time_hours INTEGER NOT NULL,
            payment_time_minutes INTEGER NOT NULL,
            payment_method VARCHAR(20) NOT NULL,
            confirmed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            expires_at DATETIME NOT NULL,
            is_verified BOOLEAN DEFAULT 0,
            FOREIGN KEY(withdrawal_id) REFERENCES withdrawal(id),
            FOREIGN KEY(user_id) REFERENCES user(id)
        )
        """)
        
        # Create PendingInvestment table
        cursor.execute("""
        CREATE TABLE pending_investment (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            amount FLOAT NOT NULL,
            daily_return FLOAT NOT NULL,
            status VARCHAR(20) DEFAULT 'pending_payment',
            payment_method VARCHAR(20),
            payment_reference VARCHAR(100),
            payment_time_hours INTEGER,
            payment_time_minutes INTEGER,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            expires_at DATETIME,
            confirmed_at DATETIME,
            FOREIGN KEY(user_id) REFERENCES user(id)
        )
        """)
        
        # Create PasswordReset table
        cursor.execute("""
        CREATE TABLE password_reset (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            reset_token VARCHAR(100) UNIQUE NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            expires_at DATETIME NOT NULL,
            is_used BOOLEAN DEFAULT 0,
            FOREIGN KEY(user_id) REFERENCES user(id)
        )
        """)
        
        # Insert admin user
        admin_password = generate_password_hash('admin123')
        admin_code = generate_referral_code()
        cursor.execute("""
        INSERT INTO user (username, email, password_hash, referral_code, created_at)
        VALUES (?, ?, ?, ?, ?)
        """, ('admin', 'admin@example.com', admin_password, admin_code, datetime.utcnow()))
        
        # Commit all changes
        conn.commit()
        print("✅ All tables created successfully!")
        
        # Verify withdrawal table has UPI columns
        cursor.execute("PRAGMA table_info(withdrawal)")
        columns = cursor.fetchall()
        
        print("\nWithdrawal table columns:")
        for col in columns:
            print(f"  - {col[1]}: {col[2]}")
        
        upi_columns = [col[1] for col in columns if 'upi' in col[1].lower()]
        if upi_columns:
            print(f"\n✅ UPI columns found: {upi_columns}")
            print("Database schema is correct!")
        else:
            print("\n❌ UPI columns missing!")
        
        print("\nAdmin user created:")
        print("Username: admin")
        print("Password: admin123")
        
    except sqlite3.Error as e:
        print(f"SQLite error: {e}")
        conn.rollback()
    
    finally:
        conn.close()

if __name__ == '__main__':
    create_database()
