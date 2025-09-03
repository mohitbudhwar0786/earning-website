from flask import Flask, request, jsonify, redirect, url_for, flash, session
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import random
import string
import os
import re

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-change-this')

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# In-memory storage
users_data = {}
investments_data = {}
referrals_data = {}

# Auto-increment IDs
current_user_id = 1
current_investment_id = 1
current_referral_id = 1

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

# Initialize with admin and sample users
def init_data():
    global current_user_id, current_referral_id
    if not users_data:
        # Create admin
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

        # Create sample users
        sample_users = [
            {'mobile_number': '9876543210', 'email': 'user1@test.com', 'password': 'test123'},
            {'mobile_number': '9876543211', 'email': 'user2@test.com', 'password': 'test123'}
        ]
        
        for sample in sample_users:
            user_data = {
                'id': current_user_id,
                'username': f"user_{sample['mobile_number']}",
                'mobile_number': sample['mobile_number'],
                'email': sample['email'],
                'password_hash': generate_password_hash(sample['password']),
                'referral_code': generate_referral_code(),
                'referred_by': '0000000',
                'total_investment': 0,
                'total_earnings': 0,
                'referral_earnings': 0,
                'created_at': datetime.utcnow()
            }
            users_data[current_user_id] = user_data
            
            # Create referral record
            referrals_data[current_referral_id] = {
                'id': current_referral_id,
                'referrer_id': 1,  # Admin ID
                'referred_user_id': user_data['id'],
                'referral_code': '0000000',
                'created_at': datetime.utcnow()
            }
            current_referral_id += 1
            current_user_id += 1

# Initialize data
init_data()

# HTML Templates as strings
LOGIN_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>EarnDaily - Login</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: Arial, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
               margin: 0; padding: 20px; min-height: 100vh; }
        .container { max-width: 400px; margin: 50px auto; background: white; padding: 30px; border-radius: 15px; 
                     box-shadow: 0 10px 30px rgba(0,0,0,0.3); }
        .form-group { margin: 20px 0; }
        label { display: block; margin-bottom: 5px; font-weight: bold; color: #333; }
        input { width: 100%; padding: 12px; border: 2px solid #ddd; border-radius: 8px; font-size: 16px; 
                box-sizing: border-box; }
        input:focus { outline: none; border-color: #667eea; }
        .btn { background: #667eea; color: white; padding: 15px; border: none; border-radius: 8px; 
               font-size: 16px; cursor: pointer; width: 100%; font-weight: bold; }
        .btn:hover { background: #5a67d8; }
        .flash { background: #f8d7da; color: #721c24; padding: 10px; border-radius: 5px; margin: 10px 0; }
        .title { text-align: center; color: #333; margin-bottom: 30px; }
        .links { text-align: center; margin-top: 20px; }
        .links a { color: #667eea; text-decoration: none; }
        .test-info { background: #d1ecf1; color: #0c5460; padding: 15px; border-radius: 8px; margin: 20px 0; }
    </style>
</head>
<body>
    <div class="container">
        <h2 class="title">🚀 EarnDaily Login</h2>
        
        <div class="test-info">
            <strong>Test Logins:</strong><br>
            Admin: admin / admin123<br>
            User: 9876543210 / test123<br>
            User: 9876543211 / test123
        </div>
        
        {flash_messages}
        
        <form method="POST">
            <div class="form-group">
                <label>Mobile Number or Username:</label>
                <input type="text" name="mobile_number" placeholder="Enter 10-digit mobile or 'admin'" required>
            </div>
            <div class="form-group">
                <label>Password:</label>
                <input type="password" name="password" placeholder="Enter password" required>
            </div>
            <button type="submit" class="btn">Login</button>
        </form>
        
        <div class="links">
            <a href="/register">New User? Register Here</a><br>
            <a href="/">← Back to Home</a>
        </div>
    </div>
</body>
</html>
"""

DASHBOARD_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Dashboard - EarnDaily</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: Arial, sans-serif; background: #f5f5f5; margin: 0; padding: 20px; }
        .container { max-width: 1200px; margin: 0 auto; }
        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; 
                  padding: 20px; border-radius: 15px; text-align: center; margin-bottom: 20px; }
        .stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin: 20px 0; }
        .stat-card { background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); 
                     text-align: center; }
        .stat-number { font-size: 2em; font-weight: bold; color: #4CAF50; }
        .nav { background: white; padding: 15px; border-radius: 10px; margin-bottom: 20px; text-align: center; }
        .nav a { display: inline-block; margin: 5px 10px; padding: 10px 20px; background: #667eea; 
                 color: white; text-decoration: none; border-radius: 5px; }
        .nav a:hover { background: #5a67d8; }
        .flash { background: #d4edda; color: #155724; padding: 15px; border-radius: 8px; margin: 20px 0; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Welcome {username}!</h1>
            <p>Mobile: {mobile_number} | Referral Code: {referral_code}</p>
        </div>
        
        <div class="nav">
            <a href="/invest">💰 Invest</a>
            <a href="/profile">👤 Profile</a>
            <a href="/wallet">💼 Wallet</a>
            <a href="/earnings">📊 Earnings</a>
            <a href="/referral">👥 Refer & Earn</a>
            {admin_link}
            <a href="/logout">🚪 Logout</a>
        </div>
        
        {flash_messages}
        
        <div class="stats">
            <div class="stat-card">
                <div class="stat-number">₹{total_investment}</div>
                <div>Total Investment</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">₹{daily_earning}</div>
                <div>Daily Earning</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{referral_count}</div>
                <div>Referrals</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">₹{referral_bonus}</div>
                <div>Referral Bonus</div>
            </div>
        </div>
        
        <div style="background: white; padding: 20px; border-radius: 10px; margin-top: 20px;">
            <h3>Investment Plans</h3>
            <p>• ₹500 - Daily Return: ₹30 | Referral Bonus: ₹10</p>
            <p>• ₹1000 - Daily Return: ₹70 | Referral Bonus: ₹25</p>
            <p>• ₹2000 - Daily Return: ₹150 | Referral Bonus: ₹60</p>
        </div>
    </div>
</body>
</html>
"""

@app.route('/health')
def health_check():
    return {'status': 'healthy', 'timestamp': datetime.utcnow().isoformat(), 'users': len(users_data)}

@app.route('/')
def home():
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>EarnDaily - Investment Platform</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body {{ font-family: Arial, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                   margin: 0; padding: 20px; min-height: 100vh; color: white; }}
            .container {{ max-width: 800px; margin: 50px auto; text-align: center; }}
            .card {{ background: rgba(255,255,255,0.1); padding: 40px; border-radius: 20px; 
                     backdrop-filter: blur(10px); }}
            .btn {{ display: inline-block; padding: 15px 30px; background: #4CAF50; color: white; 
                    text-decoration: none; border-radius: 25px; margin: 10px; font-weight: bold; }}
            .btn:hover {{ background: #45a049; }}
            .stats {{ display: flex; justify-content: space-around; margin: 30px 0; }}
            .stat {{ text-align: center; }}
            .stat-number {{ font-size: 2.5em; font-weight: bold; color: #4CAF50; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="card">
                <h1>🚀 EarnDaily</h1>
                <p>Your Trusted Investment Platform</p>
                
                <div class="stats">
                    <div class="stat">
                        <div class="stat-number">{len(users_data)}</div>
                        <div>Users</div>
                    </div>
                    <div class="stat">
                        <div class="stat-number">₹2000</div>
                        <div>Max Investment</div>
                    </div>
                    <div class="stat">
                        <div class="stat-number">24/7</div>
                        <div>Support</div>
                    </div>
                </div>
                
                <div>
                    <a href="/login" class="btn">🔑 Login</a>
                    <a href="/register" class="btn">📝 Register</a>
                    <a href="/health" class="btn">🏥 Health</a>
                </div>
                
                <p style="margin-top: 40px; font-size: 0.9em; opacity: 0.8;">
                    <strong>Test Logins:</strong><br>
                    Admin: admin/admin123 | User: 9876543210/test123
                </p>
            </div>
        </div>
    </body>
    </html>
    """
    return html

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        login_input = request.form['mobile_number'].strip()
        password = request.form['password']
        
        user_data = None
        
        # Check if input is admin username
        if login_input == 'admin':
            user_data = next((user for user in users_data.values() 
                            if user['username'] == login_input), None)
        else:
            # Validate mobile number format
            if not re.match(r'^[0-9]{10}$', login_input):
                flash_msg = '<div class="flash">Please enter a valid 10-digit mobile number or admin username</div>'
                return LOGIN_TEMPLATE.format(flash_messages=flash_msg)
            
            # Find user by mobile number
            user_data = next((user for user in users_data.values() 
                            if user['mobile_number'] == login_input), None)
        
        if user_data and check_password_hash(user_data['password_hash'], password):
            user = User(user_data)
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            if login_input == 'admin':
                flash_msg = '<div class="flash">Invalid admin credentials</div>'
            else:
                flash_msg = '<div class="flash">Invalid mobile number or password</div>'
            return LOGIN_TEMPLATE.format(flash_messages=flash_msg)
    
    return LOGIN_TEMPLATE.format(flash_messages='')

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
    
    # Get referral count
    referral_count = len([ref for ref in referrals_data.values() 
                         if ref['referrer_id'] == current_user.id])
    
    # Calculate referral bonus
    referral_bonus = 0
    for referral in referrals_data.values():
        if referral['referrer_id'] == current_user.id:
            referred_investments = [inv for inv in investments_data.values() 
                                  if inv['user_id'] == referral['referred_user_id'] and inv['is_active']]
            for inv in referred_investments:
                referral_bonus += calculate_referral_bonus(inv['amount'])
    
    # Check if user is admin
    admin_link = '<a href="/admin">⚙️ Admin Panel</a>' if current_user.username == 'admin' else ''
    
    return DASHBOARD_TEMPLATE.format(
        username=current_user.username,
        mobile_number=current_user.mobile_number,
        referral_code=current_user.referral_code,
        total_investment=current_user.total_investment,
        daily_earning=int(total_daily_earning),
        referral_count=referral_count,
        referral_bonus=int(referral_bonus),
        admin_link=admin_link,
        flash_messages=''
    )

@app.route('/register')
def register():
    return "Registration page - Coming soon! Use test accounts for now."

@app.route('/invest')
@login_required
def invest():
    return "Investment page - Coming soon!"

@app.route('/profile')
@login_required
def profile():
    return f"Profile for {current_user.username} ({current_user.mobile_number})"

@app.route('/wallet')
@login_required
def wallet():
    return "Wallet page - Coming soon!"

@app.route('/earnings')
@login_required
def earnings():
    return "Earnings page - Coming soon!"

@app.route('/referral')
@login_required
def referral():
    return f"Your referral code: {current_user.referral_code}"

@app.route('/admin')
@login_required
def admin():
    if current_user.username != 'admin':
        return "Access denied. Admin only."
    
    html = f"""
    <h1>Admin Panel</h1>
    <p>Total Users: {len(users_data)}</p>
    <p>Total Investments: ₹{sum(inv['amount'] for inv in investments_data.values())}</p>
    <h3>All Users:</h3>
    <ul>
    """
    
    for user in users_data.values():
        html += f"<li>{user['username']} ({user['mobile_number']}) - Investment: ₹{user['total_investment']}</li>"
    
    html += "</ul><a href='/dashboard'>Back to Dashboard</a>"
    return html

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)
