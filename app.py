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

app = Flask(__name__)

# Production-ready configuration
import os
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-change-this')

# Database configuration for deployment
database_url = os.environ.get('DATABASE_URL')
if database_url:
    # Fix PostgreSQL URL format for newer SQLAlchemy
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://')
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
else:
    # Fallback to SQLite for testing
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
    username = db.Column(db.String(80), unique=True, nullable=False)  # Keep for backward compatibility
    mobile_number = db.Column(db.String(15), unique=True, nullable=True)  # New mobile number field
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    referral_code = db.Column(db.String(7), unique=True, nullable=False)
    referred_by = db.Column(db.String(7), nullable=True)
    total_investment = db.Column(db.Float, default=0)
    total_earnings = db.Column(db.Float, default=0)
    referral_earnings = db.Column(db.Float, default=0)
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
    bank_details = db.Column(db.Text, nullable=True)  # Legacy field, keep for backward compatibility
    upi_id = db.Column(db.String(100), nullable=True)  # New UPI ID field
    upi_name = db.Column(db.String(100), nullable=True)  # New UPI account holder name field
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
        # For amounts >= 2000, calculate proportionally (7.5% daily return)
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
        # For amounts >= 2000, calculate proportionally (3% of investment amount)
        return investment_amount * 0.03
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
        email = request.form['email']
        password = request.form['password']
        referral_code_used = request.form.get('referral_code', '')
        
        # Check if user already exists
        if User.query.filter_by(username=username).first():
            flash('Username already exists')
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
        username = request.form['username']
        password = request.form['password']
        
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password')
    
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
        if not user:
            flash('User not found. Please try again or contact support.')
            return redirect(url_for('login'))
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
    if request.method == 'POST':
        amount = float(request.form['amount'])
        
        if amount < 500:
            flash('Minimum investment amount is ₹500.')
            current_total = current_user.total_investment
            remaining = max(0, 2000 - current_total)
            return render_template('invest.html', 
                                 current_investment=current_total, 
                                 remaining_capacity=remaining,
                                 max_investment_limit=2000,
                                 user=current_user)
        
        if current_user.total_investment + amount > 2000:
            flash('Investment limit exceeded. Maximum total investment is ₹2,000 per user.')
            current_total = current_user.total_investment
            remaining = max(0, 2000 - current_total)
            return render_template('invest.html', 
                                 current_investment=current_total, 
                                 remaining_capacity=remaining,
                                 max_investment_limit=2000,
                                 user=current_user)
        
        daily_return = calculate_daily_return(amount)
        
        # Create pending investment instead of direct investment
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
    
    # Calculate current investment status for GET request
    current_total = current_user.total_investment
    remaining = max(0, 2000 - current_total)
    
    return render_template('invest.html', 
                         current_investment=current_total, 
                         remaining_capacity=remaining,
                         max_investment_limit=2000,
                         user=current_user)

@app.route('/profile')
@login_required
def profile():
    try:
        referrals = db.session.query(Referral, User).join(User, Referral.referred_user_id == User.id).filter(Referral.referrer_id == current_user.id).all()
        # Filter out any None results from the join
        referrals = [(ref, user) for ref, user in referrals if ref is not None and user is not None]
    except Exception as e:
        print(f"Database error in profile route: {e}")
        referrals = []
        flash("Error loading referral data. Please try again.")
    
    return render_template('profile.html', user=current_user, referrals=referrals)

@app.route('/referral')
@login_required
def referral_share():
    """Dedicated referral sharing page"""
    referrals = Referral.query.filter_by(referrer_id=current_user.id).all()
    referral_count = len(referrals)
    
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
    earnings = DailyEarning.query.filter_by(user_id=current_user.id).order_by(DailyEarning.date.desc()).all()
    return render_template('earnings.html', earnings=earnings)

@app.route('/admin')
@login_required
def admin_panel():
    # Check if user is admin (you can customize this logic)
    if current_user.username != 'admin':
        flash('Access denied. Admin privileges required.')
        return redirect(url_for('dashboard'))
    
    try:
        # Get basic statistics
        total_users = User.query.count()
        total_investments = db.session.query(db.func.sum(Investment.amount)).scalar() or 0
        total_referrals = Referral.query.count()
        
        # Calculate daily payouts
        daily_payouts = 0
        try:
            active_investments = Investment.query.filter_by(is_active=True).all()
            for inv in active_investments:
                daily_payouts += calculate_daily_return(inv.amount)
        except Exception as investment_error:
            print(f"Error calculating daily payouts: {investment_error}")
            daily_payouts = 0
        
        # Get recent users
        recent_users = User.query.order_by(User.created_at.desc()).limit(10).all()
        
        # Get top investors with error handling
        top_investors = []
        try:
            top_investors = User.query.order_by(User.total_investment.desc()).limit(5).all()
            for user in top_investors:
                try:
                    user.daily_earning = sum([calculate_daily_return(inv.amount) for inv in user.investments if inv.is_active])
                except Exception as earning_error:
                    print(f"Error calculating daily earning for user {user.id}: {earning_error}")
                    user.daily_earning = 0
        except Exception as top_investors_error:
            print(f"Error getting top investors: {top_investors_error}")
            top_investors = []
        
        # Get top referrers with error handling
        top_referrers = []
        try:
            top_referrers = User.query.order_by(User.referral_earnings.desc()).limit(5).all()
            for user in top_referrers:
                try:
                    user.referral_count = Referral.query.filter_by(referrer_id=user.id).count()
                except Exception as referral_error:
                    print(f"Error calculating referral count for user {user.id}: {referral_error}")
                    user.referral_count = 0
        except Exception as top_referrers_error:
            print(f"Error getting top referrers: {top_referrers_error}")
            top_referrers = []
        
        # Get withdrawal statistics with error handling
        total_withdrawals = 0
        pending_withdrawals = 0
        try:
            total_withdrawals = db.session.query(db.func.sum(Withdrawal.amount)).filter(
                Withdrawal.status == 'completed'
            ).scalar() or 0
            pending_withdrawals = Withdrawal.query.filter_by(status='pending').count()
        except Exception as withdrawal_stats_error:
            print(f"Error getting withdrawal statistics: {withdrawal_stats_error}")
            total_withdrawals = 0
            pending_withdrawals = 0
        
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
                             
    except Exception as e:
        print(f"Database error in admin panel: {e}")
        flash("Database error occurred. Some statistics may not be available.")
        # Return minimal admin panel with safe defaults
        return render_template('admin.html',
                             total_users=0,
                             total_investments=0,
                             daily_payouts=0,
                             total_referrals=0,
                             total_withdrawals=0,
                             pending_withdrawals=0,
                             recent_users=[],
                             top_investors=[],
                             top_referrers=[])

@app.route('/admin/process-earnings', methods=['POST'])
@login_required
def admin_process_earnings():
    if current_user.username != 'admin':
        return jsonify({'error': 'Access denied'}), 403
    
    try:
        process_daily_earnings()
        return jsonify({'message': 'Daily earnings processed successfully!'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/wallet')
@login_required
def wallet():
    # Get or create user wallet
    wallet = Wallet.query.filter_by(user_id=current_user.id).first()
    if not wallet:
        wallet = Wallet(user_id=current_user.id)
        db.session.add(wallet)
        db.session.commit()
    
    # Get withdrawal history with error handling for schema mismatch
    withdrawals = []
    try:
        withdrawals = Withdrawal.query.filter_by(user_id=current_user.id).order_by(Withdrawal.requested_at.desc()).all()
    except Exception as e:
        # Handle case where database schema doesn't match model
        print(f"Database schema mismatch: {e}")
        flash("Database needs to be updated. Please restart the application to update the schema.")
        withdrawals = []
    
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
        upi_id = request.form['upi_id']
        upi_name = request.form['upi_name']
        
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
        
        # Validate UPI ID format (basic validation)
        if not upi_id or '@' not in upi_id:
            flash('Please enter a valid UPI ID.')
            return redirect(url_for('withdraw'))
        
        if not upi_name or len(upi_name.strip()) < 2:
            flash('Please enter a valid name for the UPI account.')
            return redirect(url_for('withdraw'))
        
        # Create withdrawal request with UPI details
        try:
            withdrawal = Withdrawal(
                user_id=current_user.id,
                amount=amount,
                upi_id=upi_id.strip(),
                upi_name=upi_name.strip(),
                status='pending'
            )
            
            # Deduct from wallet balance
            wallet.balance -= amount
            
            db.session.add(withdrawal)
            db.session.commit()
        except Exception as e:
            print(f"Database schema mismatch in withdraw: {e}")
            flash("Database schema error. Please restart the application to update the schema.")
            return redirect(url_for('wallet'))
        
        flash(f'Withdrawal request of ₹{amount} to UPI ID {upi_id} submitted successfully! Processing time: 24 hours.')
        return redirect(url_for('wallet'))
    
    return render_template('withdraw.html')

@app.route('/chat/send', methods=['POST'])
@login_required
def send_chat_message():
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'error': 'Invalid JSON data'})
        
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
    if not data:
        return jsonify({'success': False, 'error': 'Invalid JSON data'})
        
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
    
    try:
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
        withdrawals = []
        try:
            withdrawals_query = db.session.query(Withdrawal, User).join(User)
            if user_id_filter:
                selected_user = User.query.get(user_id_filter)
                withdrawals_query = withdrawals_query.filter(User.id == user_id_filter)
            withdrawals_raw = withdrawals_query.order_by(Withdrawal.requested_at.desc()).all()
            
            # Filter out any None results and ensure bank_details has a safe value
            withdrawals = []
            for withdrawal, user in withdrawals_raw:
                if withdrawal is not None and user is not None:
                    # Ensure bank_details is not None to prevent subscriptable errors
                    if withdrawal.bank_details is None:
                        withdrawal.bank_details = "Not provided"
                    withdrawals.append((withdrawal, user))
                    
        except Exception as e:
            print(f"Database schema mismatch in admin payments: {e}")
            flash("Database schema error. Please restart the application to update the schema.")
            withdrawals = []
        
        # Get pending investments awaiting confirmation - filter by user if specified
        pending_investments = []
        try:
            pending_investments_query = db.session.query(PendingInvestment, User).join(User).filter(
                PendingInvestment.status == 'awaiting_confirmation'
            )
            if user_id_filter:
                pending_investments_query = pending_investments_query.filter(User.id == user_id_filter)
            pending_investments_raw = pending_investments_query.order_by(PendingInvestment.confirmed_at.desc()).all()
            
            # Filter out any None results
            pending_investments = [(inv, user) for inv, user in pending_investments_raw 
                                 if inv is not None and user is not None]
        except Exception as e:
            print(f"Database error loading pending investments: {e}")
            pending_investments = []
        
        return render_template('admin_payments.html', 
                             withdrawals=withdrawals, 
                             pending_investments=pending_investments, 
                             config=config,
                             selected_user=selected_user)
                             
    except Exception as e:
        print(f"Database error in admin payments route: {e}")
        flash("Database error occurred. Please try again or restart the application.")
        return redirect(url_for('admin_panel'))

@app.route('/admin/investments/approve/<int:investment_id>', methods=['POST'])
@login_required
def admin_approve_investment(investment_id):
    if current_user.username != 'admin':
        return jsonify({'error': 'Access denied'}), 403
    
    try:
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
        if not user:
            return jsonify({'success': False, 'error': 'User not found'})
            
        user.total_investment += pending_investment.amount
        
        # Update pending investment status
        pending_investment.status = 'confirmed'
        
        db.session.add(investment)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Investment approved and activated!'})
        
    except Exception as e:
        db.session.rollback()
        print(f"Database error in investment approval: {e}")
        return jsonify({'success': False, 'error': 'Database error occurred. Please try again or restart the application.'})

@app.route('/admin/investments/reject/<int:investment_id>', methods=['POST'])
@login_required
def admin_reject_investment(investment_id):
    if current_user.username != 'admin':
        return jsonify({'error': 'Access denied'}), 403
    
    try:
        pending_investment = PendingInvestment.query.get_or_404(investment_id)
        
        if pending_investment.status != 'awaiting_confirmation':
            return jsonify({'success': False, 'error': 'Investment not in awaiting confirmation status'})
        
        # Update status to rejected
        pending_investment.status = 'rejected'
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Investment rejected.'})
        
    except Exception as e:
        db.session.rollback()
        print(f"Database error in investment rejection: {e}")
        return jsonify({'success': False, 'error': 'Database error occurred. Please try again or restart the application.'})

@app.route('/admin/users')
@login_required
def admin_users():
    if current_user.username != 'admin':
        flash('Access denied. Admin privileges required.')
        return redirect(url_for('dashboard'))
    
    try:
        # Get all users with their statistics
        users = User.query.order_by(User.created_at.desc()).all()
        
        for user in users:
            try:
                # Calculate user statistics
                user.total_investments_count = Investment.query.filter_by(user_id=user.id, is_active=True).count()
                user.current_daily_earning = sum([calculate_daily_return(inv.amount) for inv in user.investments if inv.is_active])
                user.referral_count = Referral.query.filter_by(referrer_id=user.id).count()
                
                # Get wallet with error handling
                try:
                    user.wallet = Wallet.query.filter_by(user_id=user.id).first()
                    if not user.wallet:
                        # Create a temporary wallet object for display (don't save to DB)
                        class TempWallet:
                            def __init__(self):
                                self.balance = 0
                                self.total_earned = 0
                                self.total_withdrawn = 0
                        user.wallet = TempWallet()
                except Exception as wallet_error:
                    print(f"Wallet query error for user {user.id}: {wallet_error}")
                    # Create a temporary wallet object for display
                    class TempWallet:
                        def __init__(self):
                            self.balance = 0
                            self.total_earned = 0
                            self.total_withdrawn = 0
                    user.wallet = TempWallet()
                
                # Try to get withdrawal count (might fail due to schema mismatch)
                try:
                    user.withdrawal_count = Withdrawal.query.filter_by(user_id=user.id).count()
                    user.pending_withdrawals = Withdrawal.query.filter_by(user_id=user.id, status='pending').count()
                except Exception as withdrawal_error:
                    print(f"Withdrawal query error for user {user.id}: {withdrawal_error}")
                    user.withdrawal_count = 0
                    user.pending_withdrawals = 0
                    
            except Exception as user_stats_error:
                print(f"Error calculating stats for user {user.id}: {user_stats_error}")
                # Set safe defaults
                user.total_investments_count = 0
                user.current_daily_earning = 0
                user.referral_count = 0
                # Create a temporary wallet object for display
                class TempWallet:
                    def __init__(self):
                        self.balance = 0
                        self.total_earned = 0
                        self.total_withdrawn = 0
                user.wallet = TempWallet()
                user.withdrawal_count = 0
                user.pending_withdrawals = 0
        
        return render_template('admin_users.html', users=users)
        
    except Exception as e:
        print(f"Database error in admin users: {e}")
        flash("Database error occurred. Please restart the application to update the schema.")
        return redirect(url_for('admin_panel'))

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
        
        # Delete withdrawals (with error handling for schema mismatch)
        try:
            Withdrawal.query.filter_by(user_id=user_id).delete()
        except Exception as withdrawal_error:
            print(f"Schema error deleting withdrawals for user {user_id}: {withdrawal_error}")
            # Continue with user deletion even if withdrawal deletion fails
        
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
        print(f"Database error in user deletion: {e}")
        if 'withdrawal' in str(e).lower():
            return jsonify({'success': False, 'error': 'Database schema error with withdrawals. Please restart the application to update the schema.'})
        else:
            return jsonify({'success': False, 'error': f'Failed to delete user: {str(e)}'})

@app.route('/admin/payments/update', methods=['POST'])
@login_required
def admin_update_payment():
    if current_user.username != 'admin':
        return jsonify({'error': 'Access denied'}), 403
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'Invalid JSON data'})
            
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
        
    except Exception as e:
        db.session.rollback()
        print(f"Database error in admin payment update: {e}")
        return jsonify({'success': False, 'error': 'Database error occurred. Please restart the application to update the schema.'})

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
    try:
        withdrawal = Withdrawal.query.filter_by(id=withdrawal_id, user_id=current_user.id).first_or_404()
    except Exception as e:
        print(f"Database schema mismatch in confirm_payment: {e}")
        flash("Database schema needs to be updated. Please restart the application.")
        return redirect(url_for('wallet'))
    
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

def process_daily_earnings():
    """Process daily earnings for all users"""
    with app.app_context():
        today = datetime.utcnow().date()
        
        # Check if today's earnings have already been processed
        if DailyEarning.query.filter_by(date=today).first():
            return
        
        users = User.query.all()
        
        for user in users:
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
            
            # Update user's total earnings
            user.total_earnings += total_daily_earning
            user.referral_earnings += total_referral_earning
            
            # Update wallet balance
            wallet = Wallet.query.filter_by(user_id=user.id).first()
            if not wallet:
                wallet = Wallet(user_id=user.id)
                db.session.add(wallet)
            
            daily_total = total_daily_earning + total_referral_earning
            wallet.balance += daily_total
            wallet.total_earned += daily_total
            wallet.last_updated = datetime.utcnow()
        
        db.session.commit()

# Initialize database and scheduler
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

if __name__ == '__main__':
    # For Railway deployment, use PORT environment variable
    port = int(os.environ.get('PORT', 8080))
    debug = os.environ.get('FLASK_ENV') != 'production'
    app.run(debug=debug, host='0.0.0.0', port=port)
