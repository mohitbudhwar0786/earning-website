# 📋 Complete Installation Guide - EarnDaily Website

## Step 1: Install Python

### Windows Installation:
1. **Download Python**:
   - Go to https://www.python.org/downloads/
   - Download Python 3.9 or higher for Windows
   - Choose the Windows installer (64-bit recommended)

2. **Install Python**:
   - Run the downloaded installer
   - ⚠️ **IMPORTANT**: Check "Add Python to PATH" during installation
   - Choose "Install Now"
   - Wait for installation to complete

3. **Verify Installation**:
   - Open Command Prompt (cmd) or PowerShell
   - Type: `python --version`
   - You should see something like "Python 3.9.x"

## Step 2: Set Up the Website

### Option A: Automatic Setup (Easiest)
1. **Navigate to the project folder**:
   - Open the `earning-website` folder
   - Double-click `start.bat`
   - The script will automatically install everything and start the website

### Option B: Manual Setup
1. **Open Command Prompt in project folder**:
   - Hold Shift + Right-click in the `earning-website` folder
   - Select "Open PowerShell window here" or "Open command window here"

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up Database**:
   ```bash
   python setup.py
   ```

4. **Start the Website**:
   ```bash
   python app.py
   ```

## Step 3: Access Your Website

1. **Open your web browser**
2. **Go to**: http://localhost:5000
3. **You should see the EarnDaily homepage!**

## 🎯 First Steps After Installation

### 1. Login as Admin
- **Username**: `admin`
- **Password**: `admin123`
- This gives you access to the admin panel

### 2. Test User Registration
- Create a new account
- Use the admin's referral code (found in admin profile)
- Test the referral system

### 3. Make Test Investment
- Choose an investment plan
- See how daily earnings are calculated
- Check the dashboard updates

### 4. Test Referral System
- Share your referral code
- Register another user with your code
- See how referral bonuses work

## 🔧 Configuration

### Change Investment Plans:
Edit `app.py` and modify the `calculate_daily_return()` function:

```python
def calculate_daily_return(amount):
    if amount >= 2000:
        return 150  # Change this for ₹2000 plan
    elif amount >= 1000:
        return 70   # Change this for ₹1000 plan
    elif amount >= 500:
        return 30   # Change this for ₹500 plan
```

### Change Referral Bonus Rate:
Edit the `calculate_referral_bonus()` function:

```python
def calculate_referral_bonus(investment_amount):
    daily_return = calculate_daily_return(investment_amount)
    return daily_return * 0.1  # Change 0.1 to your desired rate
```

### Change Website Colors/Design:
Edit the CSS in `templates/base.html`

## 📁 Project Structure

```
earning-website/
├── app.py                 # Main application
├── setup.py              # Database setup
├── config.py             # Configuration settings
├── requirements.txt      # Python dependencies
├── start.bat            # Windows startup script
├── README.md            # Detailed documentation
├── QUICKSTART.md        # Quick start guide
├── INSTALLATION.md      # This file
└── templates/           # HTML templates
    ├── base.html        # Base template
    ├── index.html       # Home page
    ├── register.html    # Registration
    ├── login.html       # Login page
    ├── dashboard.html   # User dashboard
    ├── invest.html      # Investment page
    ├── profile.html     # User profile
    ├── earnings.html    # Earnings history
    └── admin.html       # Admin panel
```

## 🆘 Troubleshooting

### Python Installation Issues:
1. **Make sure Python is in PATH**
2. **Try `py` instead of `python`**
3. **Restart Command Prompt after Python installation**

### Module Installation Issues:
```bash
# Try these commands if pip install fails:
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### Port Issues:
If port 5000 is in use, edit `app.py` and change:
```python
app.run(debug=True, host='0.0.0.0', port=5001)  # Change port here
```

### Database Issues:
If you encounter database errors:
1. Delete the `earning_website.db` file
2. Run `python setup.py` again

## 🎉 Success!

Once everything is installed and running:
- Your website will be at http://localhost:5000
- You can access the admin panel with admin/admin123
- Users can register, invest, and start earning
- The referral system will track bonuses automatically
- Daily earnings are processed automatically at midnight

## 📧 Need Help?

If you need assistance:
1. Check error messages in the command prompt
2. Verify Python and pip are working
3. Make sure all files are in the correct location
4. Try running each setup step manually

**Your earning website is ready to go! 🚀**
