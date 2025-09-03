#!/usr/bin/env python3

"""
Test script to verify that daily earnings duplicate prevention is working
This will test the fixed process_daily_earnings function
"""

from app import app, db, User, Investment, DailyEarning, Wallet, process_daily_earnings
from datetime import datetime

def test_daily_earnings_fix():
    print("🔧 Testing Daily Earnings Duplicate Prevention Fix")
    print("=" * 60)
    
    with app.app_context():
        today = datetime.utcnow().date()
        
        # Get users with investments
        users_with_investments = []
        for user in User.query.all():
            investments = Investment.query.filter_by(user_id=user.id, is_active=True).all()
            if investments:
                users_with_investments.append((user, investments))
        
        print(f"📊 Found {len(users_with_investments)} users with active investments")
        
        # Check current state BEFORE processing
        print("\n🔍 BEFORE Processing:")
        for user, investments in users_with_investments:
            existing_earnings = DailyEarning.query.filter_by(user_id=user.id, date=today).all()
            wallet = Wallet.query.filter_by(user_id=user.id).first()
            
            print(f"   User: {user.username}")
            print(f"     Investments: {len(investments)} (₹{sum(inv.amount for inv in investments)})")
            print(f"     Today's earnings records: {len(existing_earnings)}")
            wallet_balance = wallet.balance if wallet else 0
            print(f"     Wallet balance: ₹{wallet_balance:.2f}")
            print(f"     Total earnings: ₹{user.total_earnings:.2f}")
            print("")
        
        # First run (should process normally)
        print("🚀 FIRST RUN - Normal Processing:")
        processed_count_1 = process_daily_earnings(force=False)
        print(f"   Processed {processed_count_1} users")
        
        # Check state AFTER first run
        print("\n📈 AFTER First Run:")
        for user, investments in users_with_investments:
            # Refresh user from database
            user = User.query.get(user.id)
            earnings_today = DailyEarning.query.filter_by(user_id=user.id, date=today).all()
            wallet = Wallet.query.filter_by(user_id=user.id).first()
            
            print(f"   User: {user.username}")
            print(f"     Today's earnings records: {len(earnings_today)}")
            wallet_balance = wallet.balance if wallet else 0
            print(f"     Wallet balance: ₹{wallet_balance:.2f}")
            print(f"     Total earnings: ₹{user.total_earnings:.2f}")
            print("")
        
        # Second run WITHOUT force (should skip already processed users)
        print("🔄 SECOND RUN - Should Skip Already Processed:")
        processed_count_2 = process_daily_earnings(force=False)
        print(f"   Processed {processed_count_2} users (should be 0)")
        
        # Check state AFTER second run (should be unchanged)
        print("\n📊 AFTER Second Run (Should be UNCHANGED):")
        for user, investments in users_with_investments:
            # Refresh user from database
            user = User.query.get(user.id)
            earnings_today = DailyEarning.query.filter_by(user_id=user.id, date=today).all()
            wallet = Wallet.query.filter_by(user_id=user.id).first()
            
            print(f"   User: {user.username}")
            print(f"     Today's earnings records: {len(earnings_today)}")
            wallet_balance = wallet.balance if wallet else 0
            print(f"     Wallet balance: ₹{wallet_balance:.2f}")
            print(f"     Total earnings: ₹{user.total_earnings:.2f}")
            print("")
        
        # Third run WITH force (should reprocess but delete old records first)
        print("💪 THIRD RUN - Force Reprocess (Delete old, create new):")
        processed_count_3 = process_daily_earnings(force=True)
        print(f"   Processed {processed_count_3} users")
        
        # Final check
        print("\n🏁 FINAL STATE:")
        for user, investments in users_with_investments:
            # Refresh user from database
            user = User.query.get(user.id)
            earnings_today = DailyEarning.query.filter_by(user_id=user.id, date=today).all()
            wallet = Wallet.query.filter_by(user_id=user.id).first()
            
            print(f"   User: {user.username}")
            print(f"     Today's earnings records: {len(earnings_today)}")
            wallet_balance = wallet.balance if wallet else 0
            print(f"     Wallet balance: ₹{wallet_balance:.2f}")
            print(f"     Total earnings: ₹{user.total_earnings:.2f}")
            print("")
        
        # Summary
        print("📋 TEST RESULTS:")
        print(f"   ✅ First run processed: {processed_count_1} users")
        print(f"   ✅ Second run processed: {processed_count_2} users (should be 0)")
        print(f"   ✅ Third run processed: {processed_count_3} users")
        
        if processed_count_2 == 0:
            print("   🎉 SUCCESS: Duplicate prevention is working!")
            print("   👍 Users are not processed multiple times for the same day")
        else:
            print("   ❌ ISSUE: Duplicate prevention failed!")
            print("   ❓ Users were processed again when they shouldn't have been")

if __name__ == "__main__":
    test_daily_earnings_fix()
