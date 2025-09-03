from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import random
import string
import os
import json

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-change-this')

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# In-memory storage (data will be lost on restart)
users_data = {}
investments_data = {}
referrals_data = {}
wallets_data = {}
withdrawals_data = {}
daily_earnings_data = {}
pending_investments_data = {}

# Auto-increment IDs
current_user_id = 1
current_investment_id = 1
current_referral_id = 1
current_withdrawal_id = 1
current_daily_earning_id = 1
current_pending_investment_id = 1

# Simple User class for Flask-Login
class User(UserMixin):
    def __init__(self, user_data):
        self.id = user_data['id']
        self.username = user_data['username']
        self.mobile_number = user_data['mobile_number']
        self.email = user_data['email']
        self.password_hash = user_data['password_hash']
        self.referral_code = user_data['referral_code']
        self.referred_by = user_data.get('referred_by')
        self.total_investment = user_data.get('total_investment', 0)
        self.total_earnings = user_data.get('total_earnings', 0)
        self.referral_earnings = user_data.get('referral_earnings', 0)
        self.created_at = user_data.get('created_at', datetime.utcnow())

@login_manager.user_loader
def load_user(user_id):
    user_data = users_data.get(int(user_id))
    if user_data:
        return User(user_data)
    return None

def generate_referral_code():
    """Generate a unique 7-digit referral code"""
    while True:
        code = ''.join(random.choices(string.digits, k=7))
        # Check if code exists in any user
        exists = any(user['referral_code'] == code for user in users_data.values())
        if not exists:
            return code

def calculate_daily_return(amount):
    """Calculate daily return based on investment amount"""
    if amount >= 2000:
        return amount * 0.075
    elif amount >= 1000:
        return 70
    elif amount >= 500:
        return 30
    else:
        return 0

def calculate_referral_bonus(investment_amount):
    """Calculate referral bonus based on investment amount"""
    if investment_amount >= 2000:
        return investment_amount * 0.03
    elif investment_amount >= 1000:
        return 25
    elif investment_amount >= 500:
        return 10
    else:
        return 0

# Initialize with admin user
def init_data():
    global current_user_id
    if not users_data:
        admin_data = {
            'id': current_user_id,
            'username': 'admin',
            'mobile_number': '9999999999',
            'email': 'admin@earndaily.com',
            'password_hash': generate_password_hash('admin123'),
            'referral_code': '0000000',
            'total_investment': 0,
            'total_earnings': 0,
            'referral_earnings': 0,
            'created_at': datetime.utcnow()
        }
        users_data[current_user_id] = admin_data
        current_user_id += 1
        print("Admin user created - username: admin, password: admin123")

# Initialize data on startup
init_data()

# Routes
@app.route('/health')
def health_check():
    """Health check endpoint for Railway"""
    return {'status': 'healthy', 'timestamp': datetime.utcnow().isoformat(), 'users': len(users_data)}

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    global current_user_id
    if request.method == 'POST':
        mobile_number = request.form['mobile_number']
        email = request.form['email']
        password = request.form['password']
        referral_code_used = request.form.get('referral_code', '')
        
        # Validate mobile number format
        import re
        if not re.match(r'^[0-9]{10}$', mobile_number):
            flash('Please enter a valid 10-digit mobile number')
            return render_template('register.html')
        
        # Check if user already exists
        mobile_exists = any(user['mobile_number'] == mobile_number for user in users_data.values())
        email_exists = any(user['email'] == email for user in users_data.values())
        
        if mobile_exists:
            flash('Mobile number already registered')
            return render_template('register.html')
        
        if email_exists:
            flash('Email already exists')
            return render_template('register.html')
        
        # Validate referral code if provided
        referrer = None
        if referral_code_used:
            referrer_data = next((user for user in users_data.values() 
                                if user['referral_code'] == referral_code_used), None)
            if not referrer_data:
                flash('Invalid referral code')
                return render_template('register.html')
            referrer = referrer_data
        
        # Create new user
        user_data = {
            'id': current_user_id,
            'username': f"user_{mobile_number}",
            'mobile_number': mobile_number,
            'email': email,
            'password_hash': generate_password_hash(password),
            'referral_code': generate_referral_code(),
            'referred_by': referral_code_used if referrer else None,
            'total_investment': 0,
            'total_earnings': 0,
            'referral_earnings': 0,
            'created_at': datetime.utcnow()
        }
        
        users_data[current_user_id] = user_data
        current_user_id += 1
        
        # Create referral record if user was referred
        if referrer:
            global current_referral_id
            referrals_data[current_referral_id] = {
                'id': current_referral_id,
                'referrer_id': referrer['id'],
                'referred_user_id': user_data['id'],
                'referral_code': referral_code_used,
                'created_at': datetime.utcnow()
            }
            current_referral_id += 1
        
        flash('Registration successful! Please login.')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        login_input = request.form['mobile_number']
        password = request.form['password']
        
        user_data = None
        
        # Check if input is admin username
        if login_input == 'admin':
            user_data = next((user for user in users_data.values() 
                            if user['username'] == login_input), None)
        else:
            # Validate mobile number format for regular users
            import re
            if not re.match(r'^[0-9]{10}$', login_input):
                flash('Please enter a valid 10-digit mobile number or admin username')
                return render_template('login.html')
            
            # Try to find user by mobile number
            user_data = next((user for user in users_data.values() 
                            if user['mobile_number'] == login_input), None)
        
        if user_data and check_password_hash(user_data['password_hash'], password):
            user = User(user_data)
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            if login_input == 'admin':
                flash('Invalid admin credentials')
            else:
                flash('Invalid mobile number or password')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/dashboard')
@login_required
def dashboard():
    # Get user investments
    user_investments = [inv for inv in investments_data.values() 
                       if inv['user_id'] == current_user.id and inv['is_active']]
    total_daily_earning = sum([calculate_daily_return(inv['amount']) for inv in user_investments])
    
    # Get referral count and bonus
    user_referrals = [ref for ref in referrals_data.values() 
                     if ref['referrer_id'] == current_user.id]
    referral_count = len(user_referrals)
    
    # Calculate referral bonus from referred users' investments
    referral_bonus = 0
    for referral in user_referrals:
        referred_investments = [inv for inv in investments_data.values() 
                              if inv['user_id'] == referral['referred_user_id'] and inv['is_active']]
        for inv in referred_investments:
            referral_bonus += calculate_referral_bonus(inv['amount'])
    
    return render_template('dashboard.html', 
                         user=current_user,
                         investments=user_investments,
                         total_daily_earning=total_daily_earning,
                         referral_count=referral_count,
                         referral_bonus=referral_bonus)

@app.route('/invest', methods=['GET', 'POST'])
@login_required
def invest():
    # Set maximum investment limit per user
    MAX_INVESTMENT_LIMIT = 2000
    
    if request.method == 'POST':
        amount = float(request.form['amount'])
        current_total = current_user.total_investment
        
        if amount < 500:
            flash('Minimum investment amount is ₹500.')
            remaining_capacity = MAX_INVESTMENT_LIMIT - current_total
            return render_template('invest.html', 
                                 current_investment=current_total,
                                 remaining_capacity=max(0, remaining_capacity),
                                 max_investment_limit=MAX_INVESTMENT_LIMIT,
                                 user=current_user)
        
        # Check if investment would exceed limit
        if current_total + amount > MAX_INVESTMENT_LIMIT:
            remaining = MAX_INVESTMENT_LIMIT - current_total
            if remaining <= 0:
                flash(f'Investment limit reached! You have invested the maximum of ₹{MAX_INVESTMENT_LIMIT}. Earn more through referrals!')
            else:
                flash(f'Investment amount exceeds limit. You can invest up to ₹{remaining} more. Total limit: ₹{MAX_INVESTMENT_LIMIT}.')
            remaining_capacity = max(0, remaining)
            return render_template('invest.html', 
                                 current_investment=current_total,
                                 remaining_capacity=remaining_capacity,
                                 max_investment_limit=MAX_INVESTMENT_LIMIT,
                                 user=current_user)
        
        daily_return = calculate_daily_return(amount)
        
        # Create investment directly (simplified for no-database version)
        global current_investment_id
        investment_data = {
            'id': current_investment_id,
            'user_id': current_user.id,
            'amount': amount,
            'daily_return': daily_return,
            'created_at': datetime.utcnow(),
            'is_active': True
        }
        
        investments_data[current_investment_id] = investment_data
        current_investment_id += 1
        
        # Update user's total investment
        users_data[current_user.id]['total_investment'] += amount
        
        # Initialize wallet if doesn't exist
        if current_user.id not in wallets_data:
            wallets_data[current_user.id] = {
                'user_id': current_user.id,
                'balance': 0,
                'total_earned': 0,
                'total_withdrawn': 0
            }
        
        flash(f'Investment of ₹{amount} activated successfully! Daily return: ₹{daily_return}')
        return redirect(url_for('dashboard'))
    
    # Calculate current investment status for GET request
    current_total = current_user.total_investment
    remaining_capacity = MAX_INVESTMENT_LIMIT - current_total
    
    return render_template('invest.html', 
                         current_investment=current_total,
                         remaining_capacity=max(0, remaining_capacity),
                         max_investment_limit=MAX_INVESTMENT_LIMIT,
                         user=current_user)

@app.route('/profile')
@login_required
def profile():
    # Get user referrals with user data
    user_referrals = []
    for referral in referrals_data.values():
        if referral['referrer_id'] == current_user.id:
            referred_user = users_data.get(referral['referred_user_id'])
            if referred_user:
                user_referrals.append((referral, referred_user))
    
    return render_template('profile.html', user=current_user, referrals=user_referrals)

@app.route('/referral')
@login_required
def referral_share():
    """Dedicated referral sharing page"""
    referral_count = len([ref for ref in referrals_data.values() 
                         if ref['referrer_id'] == current_user.id])
    
    # Calculate potential earnings
    potential_earnings = {
        500: 10,
        1000: 25, 
        2000: 60
    }
    
    return render_template('referral.html', 
                         user=current_user, 
                         referral_count=referral_count,
                         potential_earnings=potential_earnings)

@app.route('/earnings')
@login_required
def earnings():
    user_earnings = [earning for earning in daily_earnings_data.values() 
                    if earning['user_id'] == current_user.id]
    # Sort by date descending
    user_earnings.sort(key=lambda x: x['created_at'], reverse=True)
    return render_template('earnings.html', earnings=user_earnings)

@app.route('/wallet')
@login_required
def wallet():
    # Get or create user wallet
    if current_user.id not in wallets_data:
        wallets_data[current_user.id] = {
            'user_id': current_user.id,
            'balance': 0,
            'total_earned': 0,
            'total_withdrawn': 0
        }
    
    wallet_data = wallets_data[current_user.id]
    
    # Get withdrawal history
    user_withdrawals = [w for w in withdrawals_data.values() 
                       if w['user_id'] == current_user.id]
    user_withdrawals.sort(key=lambda x: x['requested_at'], reverse=True)
    
    # Calculate today's earnings (simplified)
    today_total = 0
    
    return render_template('wallet.html', 
                         wallet=wallet_data, 
                         withdrawals=user_withdrawals, 
                         today_earnings=today_total, 
                         user=current_user)

@app.route('/admin')
@login_required
def admin_panel():
    # Check if user is admin
    if current_user.username != 'admin':
        flash('Access denied. Admin privileges required.')
        return redirect(url_for('dashboard'))
    
    # Get basic statistics
    total_users = len(users_data)
    total_investments = sum(inv['amount'] for inv in investments_data.values())
    total_referrals = len(referrals_data)
    
    # Calculate daily payouts
    daily_payouts = sum(calculate_daily_return(inv['amount']) 
                       for inv in investments_data.values() if inv['is_active'])
    
    # Get recent users
    recent_users = sorted(users_data.values(), 
                         key=lambda x: x['created_at'], reverse=True)[:10]
    
    # Get top investors
    top_investors = sorted(users_data.values(), 
                          key=lambda x: x['total_investment'], reverse=True)[:5]
    
    for user in top_investors:
        user_investments = [inv for inv in investments_data.values() 
                          if inv['user_id'] == user['id'] and inv['is_active']]
        user['daily_earning'] = sum(calculate_daily_return(inv['amount']) 
                                  for inv in user_investments)
    
    # Get top referrers
    top_referrers = sorted(users_data.values(), 
                          key=lambda x: x['referral_earnings'], reverse=True)[:5]
    
    for user in top_referrers:
        user['referral_count'] = len([ref for ref in referrals_data.values() 
                                    if ref['referrer_id'] == user['id']])
    
    # Get withdrawal statistics
    total_withdrawals = sum(w['amount'] for w in withdrawals_data.values() 
                           if w['status'] == 'completed')
    pending_withdrawals = len([w for w in withdrawals_data.values() 
                              if w['status'] == 'pending'])
    
    return render_template('admin.html',
                         total_users=total_users,
                         total_investments=total_investments,
                         daily_payouts=daily_payouts,
                         total_referrals=total_referrals,
                         total_withdrawals=total_withdrawals,
                         pending_withdrawals=pending_withdrawals,
                         recent_users=recent_users,
                         top_investors=top_investors,
                         top_referrers=top_referrers)

if __name__ == '__main__':
    # For Railway deployment, use PORT environment variable
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') != 'production'
    app.run(debug=debug, host='0.0.0.0', port=port)
