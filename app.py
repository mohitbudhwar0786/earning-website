from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta
import random
import string
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Configuration with environment variables
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'fallback-secret-key-change-this-in-production')

# Database configuration - use PostgreSQL for production, SQLite for development
if os.environ.get('RAILWAY_ENVIRONMENT') or os.environ.get('DATABASE_URL'):
    # Production configuration (Railway)
    database_url = os.environ.get('DATABASE_URL')
    if database_url and database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
else:
    # Development configuration
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///earning_website.db'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Create upload directory if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Database Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    mobile_number = db.Column(db.String(15), unique=True, nullable=True)  # Added mobile number field
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    referral_code = db.Column(db.String(7), unique=True, nullable=False)
    referred_by = db.Column(db.String(7), nullable=True)
    total_investment = db.Column(db.Float, default=0)
    total_earnings = db.Column(db.Float, default=0)
    referral_earnings = db.Column(db.Float, default=0)
    is_admin = db.Column(db.Boolean, default=False)  # Added admin flag
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    investments = db.relationship('Investment', backref='user', lazy=True)
    daily_earnings = db.relationship('DailyEarning', backref='user', lazy=True)
    referrals = db.relationship('Referral', backref='referrer', lazy=True)

class Investment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    daily_return = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)

class DailyEarning(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    earning_type = db.Column(db.String(20), nullable=False)  # 'investment' or 'referral'
    date = db.Column(db.Date, default=datetime.utcnow().date)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Referral(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    referrer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    referred_user_id = db.Column(db.Integer, nullable=False)
    referral_code = db.Column(db.String(7), nullable=False)
    bonus_earned = db.Column(db.Float, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Wallet(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    balance = db.Column(db.Float, default=0)
    total_earned = db.Column(db.Float, default=0)
    total_withdrawn = db.Column(db.Float, default=0)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)

class Withdrawal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, processing, completed, cancelled
    bank_details = db.Column(db.Text, nullable=True)
    requested_at = db.Column(db.DateTime, default=datetime.utcnow)
    processed_at = db.Column(db.DateTime, nullable=True)
    processing_time = db.Column(db.Integer, default=24)  # hours
    payment_method = db.Column(db.String(20), nullable=True)  # 'upi' or 'qr'
    payment_reference = db.Column(db.String(100), nullable=True)
    payment_time_hours = db.Column(db.Integer, nullable=True)
    payment_time_minutes = db.Column(db.Integer, nullable=True)

class ChatMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    is_admin_reply = db.Column(db.Boolean, default=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class PaymentConfig(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    admin_name = db.Column(db.String(100), default='EarnDaily Admin')
    upi_id = db.Column(db.String(100), default='admin@paytm')
    qr_code_path = db.Column(db.String(200), nullable=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)

class PaymentConfirmation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    withdrawal_id = db.Column(db.Integer, db.ForeignKey('withdrawal.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    payment_reference = db.Column(db.String(100), nullable=False)
    payment_time_hours = db.Column(db.Integer, nullable=False)
    payment_time_minutes = db.Column(db.Integer, nullable=False)
    payment_method = db.Column(db.String(20), nullable=False)  # 'upi' or 'qr'
    confirmed_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)
    is_verified = db.Column(db.Boolean, default=False)

class PendingInvestment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    daily_return = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='pending_payment')  # pending_payment, awaiting_confirmation, confirmed, expired
    payment_method = db.Column(db.String(20), nullable=True)  # 'upi' or 'qr'
    payment_reference = db.Column(db.String(100), nullable=True)
    payment_time_hours = db.Column(db.Integer, nullable=True)
    payment_time_minutes = db.Column(db.Integer, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=True)
    confirmed_at = db.Column(db.DateTime, nullable=True)

class PasswordReset(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    reset_token = db.Column(db.String(100), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)
    is_used = db.Column(db.Boolean, default=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def generate_referral_code():
    """Generate a unique 7-digit referral code"""
    while True:
        code = ''.join(random.choices(string.digits, k=7))
        if not User.query.filter_by(referral_code=code).first():
            return code

def calculate_daily_return(amount):
    """Calculate daily return based on investment amount"""
    if amount >= 2000:
        return 150
    elif amount >= 1000:
        return 70
    elif amount >= 500:
        return 30
    else:
        return 0

def calculate_referral_bonus(investment_amount):
    """Calculate referral bonus based on investment amount"""
    if investment_amount >= 2000:
        return 60
    elif investment_amount >= 1000:
        return 25
    elif investment_amount >= 500:
        return 10
    else:
        return 0

def get_referral_income_info():
    """Get referral income information for display"""
    return {
        500: 10,
        1000: 25,
        2000: 60
    }

def generate_reset_token():
    """Generate a unique reset token"""
    while True:
        token = ''.join(random.choices(string.ascii_letters + string.digits, k=32))
        if not PasswordReset.query.filter_by(reset_token=token).first():
            return token

# Routes
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
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
        if User.query.filter_by(username=username).first():
            flash('Username already exists')
            return render_template('register.html')
        
        if User.query.filter_by(mobile_number=mobile_number).first():
            flash('Mobile number already exists')
            return render_template('register.html')
        
        if User.query.filter_by(email=email).first():
            flash('Email already exists')
            return render_template('register.html')
        
        # Validate referral code if provided
        referrer = None
        if referral_code_used:
            referrer = User.query.filter_by(referral_code=referral_code_used).first()
            if not referrer:
                flash('Invalid referral code')
                return render_template('register.html')
        
        # Create new user
        user = User(
            username=username,
            mobile_number=mobile_number,
            email=email,
            password_hash=generate_password_hash(password),
            referral_code=generate_referral_code(),
            referred_by=referral_code_used if referrer else None
        )
        
        db.session.add(user)
        db.session.commit()
        
        # Create referral record if user was referred
        if referrer:
            referral = Referral(
                referrer_id=referrer.id,
                referred_user_id=user.id,
                referral_code=referral_code_used
            )
            db.session.add(referral)
            db.session.commit()
        
        flash('Registration successful! Please login.')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        login_input = request.form['username']  # This field can be username OR mobile number
        password = request.form['password']
        
        user = None
        
        # Check if login input is 'admin' (special admin login)
        if login_input == 'admin':
            user = User.query.filter_by(username='admin').first()
        else:
            # For regular users, only allow login with mobile number
            # Check if it's a valid 10-digit mobile number
            import re
            if re.match(r'^[0-9]{10}$', login_input):
                user = User.query.filter_by(mobile_number=login_input).first()
            else:
                # Invalid input - not admin and not a valid mobile number
                user = None
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            if login_input == 'admin':
                flash('Invalid admin credentials')
            elif re.match(r'^[0-9]{10}$', login_input):
                flash('Invalid mobile number or password')
            else:
                flash('Please enter a valid 10-digit mobile number or "admin" for admin login')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email']
        
        user = User.query.filter_by(email=email).first()
        
        if user:
            # Generate reset token
            reset_token = generate_reset_token()
            
            # Create password reset record
            password_reset = PasswordReset(
                user_id=user.id,
                reset_token=reset_token,
                expires_at=datetime.utcnow() + timedelta(hours=24)
            )
            
            db.session.add(password_reset)
            db.session.commit()
            
            # In a real application, you would send an email here
            # For this demo, we'll just show the reset link
            reset_link = url_for('reset_password', token=reset_token, _external=True)
            flash(f'Password reset link: {reset_link}')
        else:
            # Don't reveal if email exists or not for security
            flash('If an account with that email exists, a password reset link has been sent.')
        
        return redirect(url_for('login'))
    
    return render_template('forgot_password.html')

@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    # Find valid, unused reset token
    password_reset = PasswordReset.query.filter_by(
        reset_token=token,
        is_used=False
    ).filter(
        PasswordReset.expires_at > datetime.utcnow()
    ).first()
    
    if not password_reset:
        flash('Invalid or expired reset token.')
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        new_password = request.form['password']
        confirm_password = request.form['confirm_password']
        
        if new_password != confirm_password:
            flash('Passwords do not match.')
            return render_template('reset_password.html', token=token)
        
        if len(new_password) < 6:
            flash('Password must be at least 6 characters long.')
            return render_template('reset_password.html', token=token)
        
        # Update user password
        user = User.query.get(password_reset.user_id)
        user.password_hash = generate_password_hash(new_password)
        
        # Mark reset token as used
        password_reset.is_used = True
        
        db.session.commit()
        
        flash('Password reset successful! Please login with your new password.')
        return redirect(url_for('login'))
    
    return render_template('reset_password.html', token=token)

@app.route('/dashboard')
@login_required
def dashboard():
    user_investments = Investment.query.filter_by(user_id=current_user.id, is_active=True).all()
    total_daily_earning = sum([calculate_daily_return(inv.amount) for inv in user_investments])
    
    # Get referral count and bonus
    referrals = Referral.query.filter_by(referrer_id=current_user.id).all()
    referral_count = len(referrals)
    
    # Calculate referral bonus from referred users' investments
    referral_bonus = 0
    for referral in referrals:
        referred_user = User.query.get(referral.referred_user_id)
        if referred_user:
            user_investments_referred = Investment.query.filter_by(user_id=referred_user.id, is_active=True).all()
            for inv in user_investments_referred:
                referral_bonus += calculate_referral_bonus(inv.amount)
    
    return render_template('dashboard.html', 
                         user=current_user,
                         investments=user_investments,
                         total_daily_earning=total_daily_earning,
                         referral_count=referral_count,
                         referral_bonus=referral_bonus)

@app.route('/invest', methods=['GET', 'POST'])
@login_required
def invest():
    # Check user's total investment amount
    total_investment = current_user.total_investment or 0
    
    # Check if user has reached the ₹2000 investment limit
    has_reached_limit = total_investment >= 2000
    
    # Calculate referral earnings info for display
    referral_count = Referral.query.filter_by(referrer_id=current_user.id).count()
    referral_bonus = 0
    referrals = Referral.query.filter_by(referrer_id=current_user.id).all()
    for referral in referrals:
        referred_user = User.query.get(referral.referred_user_id)
        if referred_user:
            user_investments_referred = Investment.query.filter_by(user_id=referred_user.id, is_active=True).all()
            for inv in user_investments_referred:
                referral_bonus += calculate_referral_bonus(inv.amount)
    
    # Check if user already has an investment (active or pending)
    existing_investment = Investment.query.filter_by(user_id=current_user.id, is_active=True).first()
    pending_investment_check = PendingInvestment.query.filter_by(
        user_id=current_user.id
    ).filter(
        PendingInvestment.status.in_(['pending_payment', 'awaiting_confirmation'])
    ).first()
    
    if existing_investment or pending_investment_check:
        if has_reached_limit:
            # User has reached ₹2000 limit - show referral message instead
            return render_template('invest.html', 
                                 has_reached_limit=True,
                                 total_investment=total_investment,
                                 referral_count=referral_count,
                                 referral_bonus=referral_bonus,
                                 user=current_user)
        else:
            flash('You already have an active investment. You can only make one investment per account.')
            return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        # Check if trying to invest when limit is reached
        if has_reached_limit:
            flash('🎯 Investment limit reached! Focus on earning more through referrals instead.')
            return render_template('invest.html', 
                                 has_reached_limit=True,
                                 total_investment=total_investment,
                                 referral_count=referral_count,
                                 referral_bonus=referral_bonus,
                                 user=current_user)
        
        amount = float(request.form['amount'])
        
        if amount not in [500, 1000, 2000]:
            flash('Invalid investment amount. Choose from 500, 1000, or 2000.')
            return render_template('invest.html',
                                 has_reached_limit=has_reached_limit,
                                 total_investment=total_investment,
                                 referral_count=referral_count,
                                 referral_bonus=referral_bonus,
                                 user=current_user)
        
        # Check if new investment would exceed ₹2000 limit
        if total_investment + amount > 2000:
            flash('🚫 This investment would exceed the ₹2000 limit. Please choose a smaller amount or focus on referral earnings.')
            return render_template('invest.html',
                                 has_reached_limit=False,
                                 total_investment=total_investment,
                                 referral_count=referral_count,
                                 referral_bonus=referral_bonus,
                                 user=current_user)
        
        daily_return = calculate_daily_return(amount)
        
        # Create pending investment
        pending_investment = PendingInvestment(
            user_id=current_user.id,
            amount=amount,
            daily_return=daily_return,
            status='pending_payment',
            expires_at=datetime.utcnow() + timedelta(hours=24)
        )
        
        db.session.add(pending_investment)
        db.session.commit()
        
        # Redirect to payment confirmation
        return redirect(url_for('confirm_investment_payment', investment_id=pending_investment.id))
    
    return render_template('invest.html',
                         has_reached_limit=has_reached_limit,
                         total_investment=total_investment,
                         referral_count=referral_count,
                         referral_bonus=referral_bonus,
                         user=current_user)

@app.route('/profile')
@login_required
def profile():
    referrals = db.session.query(Referral, User).join(User, Referral.referred_user_id == User.id).filter(Referral.referrer_id == current_user.id).all()
    return render_template('profile.html', user=current_user, referrals=referrals)

@app.route('/earnings')
@login_required
def earnings():
    earnings = DailyEarning.query.filter_by(user_id=current_user.id).order_by(DailyEarning.date.desc()).all()
    return render_template('earnings.html', earnings=earnings)

@app.route('/admin')
@login_required
def admin_panel():
    # Check if user is admin (you can customize this logic)
    if current_user.username != 'admin':
        flash('Access denied. Admin privileges required.')
        return redirect(url_for('dashboard'))
    
    # Get statistics
    total_users = User.query.count()
    total_investments = db.session.query(db.func.sum(Investment.amount)).scalar() or 0
    total_referrals = Referral.query.count()
    
    # Calculate daily payouts
    daily_payouts = 0
    active_investments = Investment.query.filter_by(is_active=True).all()
    for inv in active_investments:
        daily_payouts += calculate_daily_return(inv.amount)
    
    # Get recent users
    recent_users = User.query.order_by(User.created_at.desc()).limit(10).all()
    
    # Get top investors
    top_investors = User.query.order_by(User.total_investment.desc()).limit(5).all()
    for user in top_investors:
        user.daily_earning = sum([calculate_daily_return(inv.amount) for inv in user.investments if inv.is_active])
    
    # Get top referrers
    top_referrers = User.query.order_by(User.referral_earnings.desc()).limit(5).all()
    for user in top_referrers:
        user.referral_count = Referral.query.filter_by(referrer_id=user.id).count()
    
    return render_template('admin.html',
                         total_users=total_users,
                         total_investments=total_investments,
                         daily_payouts=daily_payouts,
                         total_referrals=total_referrals,
                         recent_users=recent_users,
                         top_investors=top_investors,
                         top_referrers=top_referrers)

@app.route('/admin/process-earnings', methods=['POST'])
@login_required
def admin_process_earnings():
    if current_user.username != 'admin':
        return jsonify({'error': 'Access denied'}), 403
    
    try:
        processed_count = process_daily_earnings(force=True)
        
        # Get updated statistics
        today = datetime.utcnow().date()
        total_users = User.query.count()
        active_investments = Investment.query.filter_by(is_active=True).count()
        today_earnings = DailyEarning.query.filter_by(date=today).count()
        
        message = f'Daily earnings processed successfully! Processed {processed_count} users out of {total_users}. Total active investments: {active_investments}. Earnings records for today: {today_earnings}.'
        return jsonify({'message': message})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/admin/debug-earnings')
@login_required
def debug_earnings():
    if current_user.username != 'admin':
        return jsonify({'error': 'Access denied'}), 403
    
    today = datetime.utcnow().date()
    
    # Get debug info
    users = User.query.all()
    active_investments = Investment.query.filter_by(is_active=True).all()
    today_earnings = DailyEarning.query.filter_by(date=today).all()
    
    debug_info = {
        'total_users': len(users),
        'active_investments': len(active_investments),
        'today_earnings_count': len(today_earnings),
        'investment_details': [],
        'earnings_details': []
    }
    
    for inv in active_investments:
        user = User.query.get(inv.user_id)
        debug_info['investment_details'].append({
            'user': user.username if user else 'Unknown',
            'amount': inv.amount,
            'daily_return': calculate_daily_return(inv.amount)
        })
    
    for earning in today_earnings:
        user = User.query.get(earning.user_id)
        debug_info['earnings_details'].append({
            'user': user.username if user else 'Unknown',
            'amount': earning.amount,
            'type': earning.earning_type,
            'date': earning.date.isoformat()
        })
    
    return jsonify(debug_info)

@app.route('/wallet')
@login_required
def wallet():
    # Get or create user wallet
    wallet = Wallet.query.filter_by(user_id=current_user.id).first()
    if not wallet:
        wallet = Wallet(user_id=current_user.id)
        db.session.add(wallet)
        db.session.commit()
    
    # Get withdrawal history
    withdrawals = Withdrawal.query.filter_by(user_id=current_user.id).order_by(Withdrawal.requested_at.desc()).all()
    
    # Calculate today's earnings
    today = datetime.utcnow().date()
    today_earnings = DailyEarning.query.filter_by(user_id=current_user.id, date=today).all()
    today_total = sum([earning.amount for earning in today_earnings])
    
    return render_template('wallet.html', 
                         wallet=wallet, 
                         withdrawals=withdrawals, 
                         today_earnings=today_total, 
                         user=current_user)

@app.route('/withdraw', methods=['GET', 'POST'])
@login_required
def withdraw():
    if request.method == 'POST':
        amount = float(request.form['amount'])
        bank_details = request.form['bank_details']
        
        # Get user wallet
        wallet = Wallet.query.filter_by(user_id=current_user.id).first()
        if not wallet:
            flash('Wallet not found. Please contact support.')
            return redirect(url_for('wallet'))
        
        if amount > wallet.balance:
            flash('Insufficient balance for withdrawal.')
            return redirect(url_for('wallet'))
        
        if amount < 100:
            flash('Minimum withdrawal amount is ₹100.')
            return redirect(url_for('wallet'))
        
        # Create withdrawal request
        withdrawal = Withdrawal(
            user_id=current_user.id,
            amount=amount,
            bank_details=bank_details,
            status='pending'
        )
        
        # Deduct from wallet balance
        wallet.balance -= amount
        
        db.session.add(withdrawal)
        db.session.commit()
        
        flash(f'Withdrawal request of ₹{amount} submitted successfully! Processing time: 24 hours.')
        return redirect(url_for('wallet'))
    
    return render_template('withdraw.html')

@app.route('/chat/send', methods=['POST'])
@login_required
def send_chat_message():
    data = request.get_json()
    message = data.get('message', '').strip()
    
    if not message:
        return jsonify({'success': False, 'error': 'Message cannot be empty'})
    
    # Save message to database
    chat_message = ChatMessage(
        user_id=current_user.id,
        message=message,
        is_admin_reply=False
    )
    
    db.session.add(chat_message)
    db.session.commit()
    
    return jsonify({'success': True})

@app.route('/chat/messages')
@login_required
def get_chat_messages():
    messages = ChatMessage.query.filter_by(user_id=current_user.id).order_by(ChatMessage.created_at.asc()).all()
    
    message_data = []
    for msg in messages:
        message_data.append({
            'message': msg.message,
            'is_admin_reply': msg.is_admin_reply,
            'created_at': msg.created_at.isoformat()
        })
    
    return jsonify({'messages': message_data})

@app.route('/admin/chat')
@login_required
def admin_chat():
    if current_user.username != 'admin':
        flash('Access denied. Admin privileges required.')
        return redirect(url_for('dashboard'))
    
    # Check if filtering by specific user
    user_id_filter = request.args.get('user_id')
    selected_user = None
    
    if user_id_filter:
        # Get specific user and redirect to chat with them
        selected_user = User.query.get(user_id_filter)
        if selected_user:
            # Create a chat message if none exists to ensure user appears in chat list
            existing_message = ChatMessage.query.filter_by(user_id=selected_user.id).first()
            if not existing_message:
                # Create an initial system message
                initial_message = ChatMessage(
                    user_id=selected_user.id,
                    message="Chat initiated by admin",
                    is_admin_reply=True,
                    is_read=True
                )
                db.session.add(initial_message)
                db.session.commit()
    
    # Get all users who have sent messages or have been contacted by admin
    users_with_messages = db.session.query(User).join(ChatMessage).filter(ChatMessage.user_id == User.id).distinct().all()
    
    # Get unread message count for each user
    for user in users_with_messages:
        user.unread_count = ChatMessage.query.filter_by(user_id=user.id, is_read=False, is_admin_reply=False).count()
        user.last_message = ChatMessage.query.filter_by(user_id=user.id).order_by(ChatMessage.created_at.desc()).first()
    
    return render_template('admin_chat.html', users=users_with_messages, selected_user=selected_user)

@app.route('/admin/chat/<int:user_id>')
@login_required
def admin_chat_user(user_id):
    if current_user.username != 'admin':
        return jsonify({'error': 'Access denied'}), 403
    
    user = User.query.get_or_404(user_id)
    messages = ChatMessage.query.filter_by(user_id=user_id).order_by(ChatMessage.created_at.asc()).all()
    
    # Mark user messages as read
    ChatMessage.query.filter_by(user_id=user_id, is_read=False, is_admin_reply=False).update({'is_read': True})
    db.session.commit()
    
    message_data = []
    for msg in messages:
        message_data.append({
            'id': msg.id,
            'message': msg.message,
            'is_admin_reply': msg.is_admin_reply,
            'created_at': msg.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'is_read': msg.is_read
        })
    
    return jsonify({'user': user.username, 'messages': message_data})

@app.route('/admin/chat/reply', methods=['POST'])
@login_required
def admin_chat_reply():
    if current_user.username != 'admin':
        return jsonify({'error': 'Access denied'}), 403
    
    data = request.get_json()
    user_id = data.get('user_id')
    message = data.get('message', '').strip()
    
    if not message or not user_id:
        return jsonify({'success': False, 'error': 'Invalid data'})
    
    # Save admin reply
    chat_message = ChatMessage(
        user_id=user_id,
        message=message,
        is_admin_reply=True,
        is_read=True
    )
    
    db.session.add(chat_message)
    db.session.commit()
    
    return jsonify({'success': True})

@app.route('/admin/payments')
@login_required
def admin_payments():
    if current_user.username != 'admin':
        flash('Access denied. Admin privileges required.')
        return redirect(url_for('dashboard'))
    
    # Check if filtering by specific user
    user_id_filter = request.args.get('user_id')
    selected_user = None
    
    # Get payment config
    config = PaymentConfig.query.first()
    if not config:
        config = PaymentConfig()
        db.session.add(config)
        db.session.commit()
    
    # Get withdrawal requests - filter by user if specified
    withdrawals_query = db.session.query(Withdrawal, User).join(User)
    if user_id_filter:
        selected_user = User.query.get(user_id_filter)
        withdrawals_query = withdrawals_query.filter(User.id == user_id_filter)
    withdrawals = withdrawals_query.order_by(Withdrawal.requested_at.desc()).all()
    
    # Get pending investments awaiting confirmation - filter by user if specified
    pending_investments_query = db.session.query(PendingInvestment, User).join(User).filter(
        PendingInvestment.status == 'awaiting_confirmation'
    )
    if user_id_filter:
        pending_investments_query = pending_investments_query.filter(User.id == user_id_filter)
    pending_investments = pending_investments_query.order_by(PendingInvestment.confirmed_at.desc()).all()
    
    return render_template('admin_payments.html', 
                         withdrawals=withdrawals, 
                         pending_investments=pending_investments, 
                         config=config,
                         selected_user=selected_user)

@app.route('/admin/investments/approve/<int:investment_id>', methods=['POST'])
@login_required
def admin_approve_investment(investment_id):
    if current_user.username != 'admin':
        return jsonify({'error': 'Access denied'}), 403
    
    pending_investment = PendingInvestment.query.get_or_404(investment_id)
    
    if pending_investment.status != 'awaiting_confirmation':
        return jsonify({'success': False, 'error': 'Investment not in awaiting confirmation status'})
    
    # Create actual investment
    investment = Investment(
        user_id=pending_investment.user_id,
        amount=pending_investment.amount,
        daily_return=pending_investment.daily_return
    )
    
    # Update user's total investment
    user = User.query.get(pending_investment.user_id)
    user.total_investment += pending_investment.amount
    
    # Update pending investment status
    pending_investment.status = 'confirmed'
    
    db.session.add(investment)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Investment approved and activated!'})

@app.route('/admin/investments/reject/<int:investment_id>', methods=['POST'])
@login_required
def admin_reject_investment(investment_id):
    if current_user.username != 'admin':
        return jsonify({'error': 'Access denied'}), 403
    
    pending_investment = PendingInvestment.query.get_or_404(investment_id)
    
    if pending_investment.status != 'awaiting_confirmation':
        return jsonify({'success': False, 'error': 'Investment not in awaiting confirmation status'})
    
    # Update status to rejected
    pending_investment.status = 'rejected'
    
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Investment rejected.'})

@app.route('/admin/users')
@login_required
def admin_users():
    if current_user.username != 'admin':
        flash('Access denied. Admin privileges required.')
        return redirect(url_for('dashboard'))
    
    # Get all users with their statistics
    users = User.query.order_by(User.created_at.desc()).all()
    
    for user in users:
        # Calculate user statistics
        user.total_investments_count = Investment.query.filter_by(user_id=user.id, is_active=True).count()
        user.current_daily_earning = sum([calculate_daily_return(inv.amount) for inv in user.investments if inv.is_active])
        user.referral_count = Referral.query.filter_by(referrer_id=user.id).count()
        user.wallet = Wallet.query.filter_by(user_id=user.id).first()
        if not user.wallet:
            user.wallet = Wallet(user_id=user.id, balance=0, total_earned=0, total_withdrawn=0)
    
    return render_template('admin_users.html', users=users)

@app.route('/admin/users/delete/<int:user_id>', methods=['POST'])
@login_required
def admin_delete_user(user_id):
    if current_user.username != 'admin':
        return jsonify({'error': 'Access denied'}), 403
    
    if user_id == current_user.id:
        return jsonify({'success': False, 'error': 'Cannot delete your own admin account'})
    
    user = User.query.get_or_404(user_id)
    
    try:
        # Delete related records first (foreign key constraints)
        # Delete chat messages
        ChatMessage.query.filter_by(user_id=user_id).delete()
        
        # Delete daily earnings
        DailyEarning.query.filter_by(user_id=user_id).delete()
        
        # Delete investments
        Investment.query.filter_by(user_id=user_id).delete()
        
        # Delete pending investments
        PendingInvestment.query.filter_by(user_id=user_id).delete()
        
        # Delete withdrawals
        Withdrawal.query.filter_by(user_id=user_id).delete()
        
        # Delete payment confirmations
        PaymentConfirmation.query.filter_by(user_id=user_id).delete()
        
        # Delete wallet
        Wallet.query.filter_by(user_id=user_id).delete()
        
        # Delete referrals where this user is the referrer
        Referral.query.filter_by(referrer_id=user_id).delete()
        
        # Delete referrals where this user was referred
        Referral.query.filter_by(referred_user_id=user_id).delete()
        
        # Finally delete the user
        db.session.delete(user)
        db.session.commit()
        
        return jsonify({'success': True, 'message': f'User {user.username} deleted successfully'})
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': f'Failed to delete user: {str(e)}'})

@app.route('/admin/payments/update', methods=['POST'])
@login_required
def admin_update_payment():
    if current_user.username != 'admin':
        return jsonify({'error': 'Access denied'}), 403
    
    data = request.get_json()
    withdrawal_id = data.get('withdrawal_id')
    status = data.get('status')
    payment_method = data.get('payment_method')
    payment_reference = data.get('payment_reference')
    payment_hours = data.get('payment_hours')
    payment_minutes = data.get('payment_minutes')
    
    if not withdrawal_id or not status:
        return jsonify({'success': False, 'error': 'Missing required data'})
    
    withdrawal = Withdrawal.query.get_or_404(withdrawal_id)
    
    # Update withdrawal status and payment details
    withdrawal.status = status
    if payment_method:
        withdrawal.payment_method = payment_method
    if payment_reference:
        withdrawal.payment_reference = payment_reference
    if payment_hours is not None:
        withdrawal.payment_time_hours = payment_hours
    if payment_minutes is not None:
        withdrawal.payment_time_minutes = payment_minutes
    
    if status in ['completed', 'processing']:
        withdrawal.processed_at = datetime.utcnow()
        
        # Update user wallet if completed
        if status == 'completed':
            wallet = Wallet.query.filter_by(user_id=withdrawal.user_id).first()
            if wallet:
                wallet.total_withdrawn += withdrawal.amount
    
    elif status == 'cancelled':
        # Refund amount to wallet if cancelled
        wallet = Wallet.query.filter_by(user_id=withdrawal.user_id).first()
        if wallet:
            wallet.balance += withdrawal.amount
    
    db.session.commit()
    
    return jsonify({'success': True, 'message': f'Payment status updated to {status}'})

@app.route('/admin/payment-settings', methods=['GET', 'POST'])
@login_required
def admin_payment_settings():
    if current_user.username != 'admin':
        flash('Access denied. Admin privileges required.')
        return redirect(url_for('dashboard'))
    
    # Get or create payment config
    config = PaymentConfig.query.first()
    if not config:
        config = PaymentConfig()
        db.session.add(config)
        db.session.commit()
    
    if request.method == 'POST':
        # Update payment settings
        config.admin_name = request.form.get('admin_name', config.admin_name)
        config.upi_id = request.form.get('upi_id', config.upi_id)
        
        # Handle QR code upload
        if 'qr_code' in request.files:
            file = request.files['qr_code']
            if file and file.filename != '' and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                # Add timestamp to avoid conflicts
                filename = f"qr_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{filename}"
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)
                config.qr_code_path = f"uploads/{filename}"
        
        config.updated_at = datetime.utcnow()
        db.session.commit()
        
        flash('Payment settings updated successfully!')
        return redirect(url_for('admin_payment_settings'))
    
    return render_template('admin_payment_settings.html', config=config)

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/invest/confirm/<int:investment_id>', methods=['GET', 'POST'])
@login_required
def confirm_investment_payment(investment_id):
    pending_investment = PendingInvestment.query.filter_by(id=investment_id, user_id=current_user.id).first_or_404()
    
    if pending_investment.status not in ['pending_payment']:
        flash('This investment cannot be processed.')
        return redirect(url_for('dashboard'))
    
    # Check if expired
    if pending_investment.expires_at and datetime.utcnow() > pending_investment.expires_at:
        pending_investment.status = 'expired'
        db.session.commit()
        flash('Investment request expired. Please try again.')
        return redirect(url_for('invest'))
    
    # Get payment config
    config = PaymentConfig.query.first()
    if not config:
        config = PaymentConfig()
        db.session.add(config)
        db.session.commit()
    
    if request.method == 'POST':
        payment_method = request.form.get('payment_method')
        payment_reference = request.form.get('payment_reference')
        payment_hours = int(request.form.get('payment_hours', 0))
        payment_minutes = int(request.form.get('payment_minutes', 0))
        
        if not payment_method or not payment_reference:
            flash('Please fill all required fields.')
            return render_template('confirm_investment_payment.html', pending_investment=pending_investment, config=config)
        
        # Update pending investment with payment info
        pending_investment.payment_method = payment_method
        pending_investment.payment_reference = payment_reference
        pending_investment.payment_time_hours = payment_hours
        pending_investment.payment_time_minutes = payment_minutes
        pending_investment.status = 'awaiting_confirmation'
        pending_investment.confirmed_at = datetime.utcnow()
        
        db.session.commit()
        
        flash('Investment payment submitted! Admin will verify and activate your investment within 24 hours.')
        return redirect(url_for('dashboard'))
    
    return render_template('confirm_investment_payment.html', pending_investment=pending_investment, config=config)

@app.route('/withdraw/confirm/<int:withdrawal_id>', methods=['GET', 'POST'])
@login_required
def confirm_payment(withdrawal_id):
    withdrawal = Withdrawal.query.filter_by(id=withdrawal_id, user_id=current_user.id).first_or_404()
    
    if withdrawal.status != 'pending':
        flash('This withdrawal request cannot be confirmed.')
        return redirect(url_for('wallet'))
    
    # Get payment config
    config = PaymentConfig.query.first()
    if not config:
        config = PaymentConfig()
        db.session.add(config)
        db.session.commit()
    
    if request.method == 'POST':
        payment_method = request.form.get('payment_method')
        payment_reference = request.form.get('payment_reference')
        payment_hours = int(request.form.get('payment_hours', 0))
        payment_minutes = int(request.form.get('payment_minutes', 0))
        
        if not payment_method or not payment_reference:
            flash('Please fill all required fields.')
            return render_template('confirm_payment.html', withdrawal=withdrawal, config=config)
        
        # Create payment confirmation
        confirmation = PaymentConfirmation(
            withdrawal_id=withdrawal.id,
            user_id=current_user.id,
            payment_reference=payment_reference,
            payment_time_hours=payment_hours,
            payment_time_minutes=payment_minutes,
            payment_method=payment_method,
            expires_at=datetime.utcnow() + timedelta(hours=24)
        )
        
        # Update withdrawal status
        withdrawal.status = 'awaiting_confirmation'
        
        db.session.add(confirmation)
        db.session.commit()
        
        flash('Payment confirmation submitted! Admin will verify within 24 hours.')
        return redirect(url_for('wallet'))
    
    return render_template('confirm_payment.html', withdrawal=withdrawal, config=config)

def process_daily_earnings(force=False):
    """Process daily earnings for all users"""
    with app.app_context():
        today = datetime.utcnow().date()
        
        users = User.query.all()
        processed_count = 0
        
        for user in users:
            # Check if this user's earnings have already been processed for today
            existing_earning = DailyEarning.query.filter_by(
                user_id=user.id, 
                date=today
            ).first()
            
            if existing_earning and not force:
                continue  # Skip this user as earnings already processed today
            
            # If forcing, delete existing earnings for today first
            if force and existing_earning:
                DailyEarning.query.filter_by(user_id=user.id, date=today).delete()
            
            # Calculate investment earnings
            investments = Investment.query.filter_by(user_id=user.id, is_active=True).all()
            total_daily_earning = 0
            
            for investment in investments:
                daily_return = calculate_daily_return(investment.amount)
                total_daily_earning += daily_return
                
                # Record daily earning
                earning = DailyEarning(
                    user_id=user.id,
                    amount=daily_return,
                    earning_type='investment',
                    date=today
                )
                db.session.add(earning)
            
            # Calculate referral earnings
            referrals = Referral.query.filter_by(referrer_id=user.id).all()
            total_referral_earning = 0
            
            for referral in referrals:
                referred_user = User.query.get(referral.referred_user_id)
                if referred_user:
                    referred_investments = Investment.query.filter_by(user_id=referred_user.id, is_active=True).all()
                    for inv in referred_investments:
                        bonus = calculate_referral_bonus(inv.amount)
                        total_referral_earning += bonus
            
            if total_referral_earning > 0:
                referral_earning = DailyEarning(
                    user_id=user.id,
                    amount=total_referral_earning,
                    earning_type='referral',
                    date=today
                )
                db.session.add(referral_earning)
            
            # Only update totals if there are actual earnings and not already processed
            daily_total = total_daily_earning + total_referral_earning
            if daily_total > 0:  # Only process users who actually have earnings
                if not existing_earning or force:
                    # Update user's total earnings only if not already added
                    user.total_earnings += total_daily_earning
                    user.referral_earnings += total_referral_earning
                    
                    # Update wallet balance
                    wallet = Wallet.query.filter_by(user_id=user.id).first()
                    if not wallet:
                        wallet = Wallet(user_id=user.id)
                        db.session.add(wallet)
                    
                    wallet.balance += daily_total
                    wallet.total_earned += daily_total
                    wallet.last_updated = datetime.utcnow()
                    
                    processed_count += 1
        
        db.session.commit()
        return processed_count

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        
        # Set up scheduler for daily earnings
        scheduler = BackgroundScheduler()
        scheduler.add_job(
            func=process_daily_earnings,
            trigger="cron",
            hour=0,
            minute=0,
            id='daily_earnings'
        )
        scheduler.start()
    
    # Use debug mode based on environment
    debug_mode = os.environ.get('FLASK_ENV', 'production') == 'development'
    port = int(os.environ.get('PORT', 5000))
    
    app.run(debug=debug_mode, host='0.0.0.0', port=port)
