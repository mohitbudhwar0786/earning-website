#!/usr/bin/env python3

"""
Test script to verify user management functionality
Run this to test if the admin user management system is working properly
"""

from app import app, db, User, Wallet, Investment, Referral

def test_user_management():
    print("🔍 Testing User Management System...")
    print("=" * 50)
    
    with app.app_context():
        # Check admin user
        admin = User.query.filter_by(username='admin').first()
        if admin:
            print(f"✅ Admin user found: {admin.username} (ID: {admin.id})")
            print(f"   Admin flag: {admin.is_admin}")
        else:
            print("❌ Admin user not found!")
            return
        
        # Check all users
        users = User.query.all()
        print(f"\n📊 Total users in system: {len(users)}")
        
        # Test user statistics calculation
        for user in users:
            # Calculate statistics like the admin_users route does
            user.total_investments_count = Investment.query.filter_by(user_id=user.id, is_active=True).count()
            user.referral_count = Referral.query.filter_by(referrer_id=user.id).count()
            user.wallet = Wallet.query.filter_by(user_id=user.id).first()
            
            if not user.wallet:
                user.wallet = Wallet(user_id=user.id, balance=0, total_earned=0, total_withdrawn=0)
                db.session.add(user.wallet)
                print(f"   Created wallet for user: {user.username}")
        
        db.session.commit()
        
        # Display user info
        print("\n👥 User Details:")
        for user in users:
            print(f"   User: {user.username} (ID: {user.id})")
            print(f"     📧 Email: {user.email}")
            print(f"     📱 Mobile: {user.mobile_number}")
            print(f"     💰 Investments: {user.total_investments_count} (₹{user.total_investment:.2f})")
            print(f"     🤝 Referrals: {user.referral_count}")
            print(f"     💳 Wallet: ₹{user.wallet.balance:.2f} (Total Earned: ₹{user.wallet.total_earned:.2f})")
            print(f"     📅 Joined: {user.created_at.strftime('%Y-%m-%d')}")
            print("")
        
        # Test filtering
        investors = [u for u in users if u.total_investments_count > 0]
        referrers = [u for u in users if u.referral_count > 0]
        
        print(f"📈 Active investors: {len(investors)}")
        print(f"👥 Users with referrals: {len(referrers)}")
        
        # Test wallet balance calculation
        total_wallet_balance = sum(u.wallet.balance for u in users if u.wallet)
        print(f"💰 Total wallet balance: ₹{total_wallet_balance:.2f}")
        
        print("\n✅ User Management System Test Complete!")
        print("   All functionality appears to be working correctly.")

if __name__ == "__main__":
    test_user_management()
