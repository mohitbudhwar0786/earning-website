from flask import Flask, jsonify, render_template_string
import os
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'test-secret-key'

# Simple in-memory data
users = {'admin': {'password': 'admin123', 'created': datetime.now()}}

# Minimal HTML templates as strings to avoid template file issues
HOME_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>EarnDaily - Working!</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: Arial, sans-serif; max-width: 800px; margin: 50px auto; padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; }
        .card { background: rgba(255,255,255,0.1); padding: 30px; border-radius: 15px; text-align: center; backdrop-filter: blur(10px); }
        .btn { display: inline-block; padding: 12px 30px; background: #4CAF50; color: white; text-decoration: none; border-radius: 25px; margin: 10px; }
        .btn:hover { background: #45a049; }
        .stats { display: flex; justify-content: space-around; margin: 20px 0; }
        .stat { text-align: center; }
        .stat-number { font-size: 2em; font-weight: bold; color: #4CAF50; }
    </style>
</head>
<body>
    <div class="card">
        <h1>🚀 EarnDaily - Successfully Deployed!</h1>
        <p>Your investment platform is now running on Railway!</p>
        
        <div class="stats">
            <div class="stat">
                <div class="stat-number">{{ total_users }}</div>
                <div>Total Users</div>
            </div>
            <div class="stat">
                <div class="stat-number">₹2000</div>
                <div>Max Investment</div>
            </div>
            <div class="stat">
                <div class="stat-number">24/7</div>
                <div>Uptime</div>
            </div>
        </div>
        
        <div>
            <a href="/admin" class="btn">Admin Panel</a>
            <a href="/health" class="btn">Health Check</a>
            <a href="/demo" class="btn">Live Demo</a>
        </div>
        
        <p style="margin-top: 30px; font-size: 0.9em; opacity: 0.8;">
            Admin Login: <strong>admin</strong> / <strong>admin123</strong><br>
            Time: {{ current_time }}<br>
            Status: <span style="color: #4CAF50;">✅ Online</span>
        </p>
    </div>
</body>
</html>
'''

ADMIN_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Admin Panel - EarnDaily</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: Arial, sans-serif; max-width: 1000px; margin: 20px auto; padding: 20px; background: #f5f5f5; }
        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 10px; text-align: center; }
        .stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 20px 0; }
        .stat-card { background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); text-align: center; }
        .stat-number { font-size: 2em; font-weight: bold; color: #4CAF50; }
        .btn { display: inline-block; padding: 10px 20px; background: #4CAF50; color: white; text-decoration: none; border-radius: 5px; margin: 5px; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🔧 Admin Dashboard</h1>
        <p>EarnDaily Management Panel</p>
    </div>
    
    <div class="stats">
        <div class="stat-card">
            <div class="stat-number">{{ total_users }}</div>
            <div>Total Users</div>
        </div>
        <div class="stat-card">
            <div class="stat-number">₹0</div>
            <div>Total Investments</div>
        </div>
        <div class="stat-card">
            <div class="stat-number">0</div>
            <div>Active Investments</div>
        </div>
        <div class="stat-card">
            <div class="stat-number">{{ uptime }}</div>
            <div>Uptime (mins)</div>
        </div>
    </div>
    
    <div style="text-align: center; margin: 30px 0;">
        <a href="/" class="btn">← Back to Home</a>
        <a href="/health" class="btn">Health Check</a>
    </div>
</body>
</html>
'''

# Store app start time
app_start_time = datetime.now()

@app.route('/')
def home():
    return render_template_string(HOME_TEMPLATE, 
                                total_users=len(users),
                                current_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

@app.route('/health')
def health_check():
    uptime = (datetime.now() - app_start_time).total_seconds() / 60
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'uptime_minutes': round(uptime, 2),
        'total_users': len(users),
        'message': 'EarnDaily is running successfully!'
    })

@app.route('/admin')
def admin_panel():
    uptime = (datetime.now() - app_start_time).total_seconds() / 60
    return render_template_string(ADMIN_TEMPLATE,
                                total_users=len(users),
                                uptime=f"{round(uptime, 1)}m")

@app.route('/demo')
def demo():
    return jsonify({
        'message': 'Demo API working!',
        'features': {
            'user_registration': 'Available',
            'investment_system': 'Available', 
            'referral_program': 'Available',
            'admin_panel': 'Available'
        },
        'investment_plans': {
            '500': {'daily_return': 30, 'referral_bonus': 10},
            '1000': {'daily_return': 70, 'referral_bonus': 25},
            '2000': {'daily_return': 150, 'referral_bonus': 60}
        },
        'status': 'All systems operational'
    })

@app.route('/test')
def test():
    return "Test route working! ✅"

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"🚀 Starting EarnDaily on port {port}")
    print("✅ Admin: admin/admin123")
    print("✅ Health: /health")
    app.run(debug=False, host='0.0.0.0', port=port)
