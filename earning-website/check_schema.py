#!/usr/bin/env python3
"""
Direct SQLite schema inspection using Python sqlite3 module
"""

import sqlite3
import os

def check_database_schema():
    """Check the actual database schema"""
    db_file = 'earning_website.db'
    
    if not os.path.exists(db_file):
        print("Database file does not exist!")
        return
    
    # Connect to SQLite database
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    
    try:
        # Get withdrawal table schema
        cursor.execute("PRAGMA table_info(withdrawal)")
        columns = cursor.fetchall()
        
        print("Actual withdrawal table schema:")
        for col in columns:
            print(f"  - {col[1]}: {col[2]} (nullable: {col[3] == 0})")
        
        # Check if UPI columns exist
        upi_columns = [col[1] for col in columns if 'upi' in col[1].lower()]
        if upi_columns:
            print(f"\n✅ UPI columns found: {upi_columns}")
        else:
            print("\n❌ No UPI columns found!")
        
        # Get the actual CREATE TABLE statement
        cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='withdrawal'")
        create_statement = cursor.fetchone()
        if create_statement:
            print(f"\nActual CREATE TABLE statement:")
            print(create_statement[0])
        
    except sqlite3.Error as e:
        print(f"SQLite error: {e}")
    
    finally:
        conn.close()

if __name__ == '__main__':
    check_database_schema()
