"""
Configuration settings for EarnDaily Website
Modify these values to customize the platform
"""

# Investment Plans Configuration
INVESTMENT_PLANS = {
    500: {
        'daily_return': 30,
        'name': 'Starter Plan',
        'description': 'Perfect for beginners',
        'features': ['6% Daily Return', 'Referral Bonus Eligible', 'Instant Activation']
    },
    1000: {
        'daily_return': 70,
        'name': 'Premium Plan', 
        'description': 'Best value for money',
        'features': ['7% Daily Return', 'Higher Referral Bonus', 'Priority Support']
    },
    2000: {
        'daily_return': 150,
        'name': 'VIP Plan',
        'description': 'Maximum earning potential',
        'features': ['7.5% Daily Return', 'Maximum Referral Bonus', 'VIP Support']
    }
}

# Referral System Configuration
REFERRAL_BONUS_RATE = 0.1  # 10% of referrals' daily earnings
REFERRAL_CODE_LENGTH = 7   # Length of referral codes

# Security Configuration
SECRET_KEY = 'your-secret-key-change-this-in-production'
PASSWORD_MIN_LENGTH = 6

# Database Configuration
DATABASE_URI = 'sqlite:///earning_website.db'

# Application Configuration
APP_NAME = 'EarnDaily'
APP_DESCRIPTION = 'Membership Investment Platform'
HOST = '0.0.0.0'
PORT = 5000
DEBUG = True

# Daily Processing Configuration
DAILY_PROCESSING_HOUR = 0   # Hour to process daily earnings (24-hour format)
DAILY_PROCESSING_MINUTE = 0 # Minute to process daily earnings

# Website Customization
COMPANY_INFO = {
    'name': 'EarnDaily',
    'tagline': 'Your Daily Earning Partner',
    'description': 'Join our exclusive membership platform and start earning daily returns on your investments!',
    'support_email': 'support@earndaily.com',
    'contact_phone': '+1-234-567-8900'
}

# Currency Settings
CURRENCY_SYMBOL = '₹'
CURRENCY_CODE = 'INR'

# Email Configuration (for future implementation)
EMAIL_CONFIG = {
    'smtp_server': 'smtp.gmail.com',
    'smtp_port': 587,
    'sender_email': 'noreply@earndaily.com',
    'sender_password': 'your-email-password'
}
