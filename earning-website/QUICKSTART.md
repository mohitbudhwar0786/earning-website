# 🚀 Quick Start Guide - EarnDaily Website

## Installation (Windows)

### Option 1: Easy Setup (Recommended)
1. **Double-click `start.bat`** - This will automatically:
   - Check Python installation
   - Install all dependencies
   - Set up the database
   - Start the website

### Option 2: Manual Setup
1. **Install Python** (if not already installed):
   - Download from https://python.org
   - Make sure to add Python to PATH

2. **Install Dependencies**:
   ```
   pip install -r requirements.txt
   ```

3. **Set up Database**:
   ```
   python setup.py
   ```

4. **Start the Website**:
   ```
   python app.py
   ```

## 🌐 Access the Website

Once running, open your browser and go to:
**http://localhost:5000**

## 🔑 Test Accounts

### Admin Account:
- **Username**: `admin`
- **Password**: `admin123`
- **Features**: Access to admin panel, user management

### Sample Users:
- **Username**: `john_doe` | **Password**: `password123`
- **Username**: `jane_smith` | **Password**: `password123`  
- **Username**: `mike_wilson` | **Password**: `password123`

## 💰 How to Test the System

### 1. Register New User
- Go to `/register`
- Use referral code from admin: Check admin profile for their 7-digit code
- Complete registration

### 2. Make Investment
- Login to dashboard
- Click "Invest Now"
- Choose from ₹500, ₹1000, or ₹2000 plans
- Confirm investment

### 3. Check Earnings
- Daily earnings are processed automatically at midnight
- For testing, use admin panel to manually process earnings
- View earnings in "Earnings" section

### 4. Test Referral System
- Copy your 7-digit referral code from dashboard
- Register a new user with your referral code
- When the new user invests, you'll earn 10% bonus

## 📊 Investment Plans

| Amount | Daily Return | Return Rate |
|--------|--------------|-------------|
| ₹500   | ₹30         | 6%          |
| ₹1000  | ₹70         | 7%          |
| ₹2000  | ₹150        | 7.5%        |

## 👥 Referral System

- **Bonus Rate**: 10% of referrals' daily earnings
- **Example**: If your referral earns ₹70/day, you earn ₹7/day bonus
- **Tracking**: View all referrals in your profile
- **Code**: Unique 7-digit code for each user

## 🛠️ Admin Features

### Access Admin Panel:
1. Login as admin user
2. Click "Admin" in navigation
3. View platform statistics
4. Manage users and earnings

### Admin Functions:
- **Process Earnings**: Manually trigger daily earnings calculation
- **View Statistics**: Total users, investments, payouts
- **User Management**: View recent users and top performers
- **Data Export**: Download user and earnings data

## 📱 Website Features

### For Users:
- ✅ User registration with referral support
- ✅ Secure login/logout
- ✅ Investment management
- ✅ Real-time earnings tracking
- ✅ Referral code sharing
- ✅ Earnings history
- ✅ Profile management

### For Admins:
- ✅ Admin dashboard
- ✅ User statistics
- ✅ Manual earnings processing
- ✅ Top performers tracking
- ✅ Platform analytics

## 🔧 Customization

### Change Investment Plans:
Edit `calculate_daily_return()` function in `app.py`

### Change Referral Rate:
Edit `calculate_referral_bonus()` function in `app.py`

### Styling:
Modify CSS in `templates/base.html`

## 🆘 Troubleshooting

### Common Issues:

1. **"Python not found"**
   - Install Python 3.7+ and add to PATH

2. **"Port 5000 in use"**
   - Change port in `app.py`: `app.run(port=5001)`

3. **"Module not found"**
   - Run: `pip install -r requirements.txt`

4. **Database errors**
   - Delete `earning_website.db` and run `python setup.py`

## 📞 Support

If you encounter any issues:
1. Check the console for error messages
2. Verify all dependencies are installed
3. Ensure Python 3.7+ is installed
4. Check that port 5000 is available

## 🚀 Ready to Go!

Your earning website is now ready! Users can:
- Register and get unique referral codes
- Make investments and earn daily returns
- Refer friends and earn bonuses
- Track all earnings and referrals

**Happy earning! 💰**
