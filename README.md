# EarnDaily - Membership Investment Platform

A comprehensive membership-based earning website where users can invest money and earn daily returns, plus additional income through referrals.

## Features

### 💰 Investment Plans
- **₹500 Plan**: Earn ₹30 daily (6% daily return)
- **₹1000 Plan**: Earn ₹70 daily (7% daily return) 
- **₹2000 Plan**: Earn ₹150 daily (7.5% daily return)

### 👥 Referral System
- Each user gets a unique 7-digit referral code
- Earn 10% bonus from referrals' daily earnings
- Track all your referrals and their performance
- Multi-level referral tracking

### 📊 User Dashboard
- Real-time earnings tracking
- Investment portfolio overview
- Referral management
- Earnings history
- Profile management

### 🔐 Security Features
- Secure user authentication
- Password hashing
- Session management
- Input validation

## Installation

### Prerequisites
- Python 3.7 or higher
- pip (Python package installer)

### Step 1: Install Python Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Set up Database
```bash
python setup.py
```

### Step 3: Run the Application
```bash
python app.py
```

The website will be available at: http://localhost:5000

## Default Login Credentials

After running the setup script, you can use these sample accounts:

- **Admin Account**: 
  - Username: `admin`
  - Password: `admin123`

- **Sample Users**:
  - Username: `john_doe`, Password: `password123`
  - Username: `jane_smith`, Password: `password123`
  - Username: `mike_wilson`, Password: `password123`

## How It Works

### For Users:
1. **Register**: Create account with optional referral code
2. **Invest**: Choose from ₹500, ₹1000, or ₹2000 plans
3. **Earn**: Receive daily returns automatically
4. **Refer**: Share your 7-digit code to earn bonuses

### For Referrers:
- Earn 10% of daily earnings from each person you refer
- Higher referral earnings when your referrals choose higher investment plans
- Track all referrals and their performance in your dashboard

### Investment Returns:
- **₹500 investment** → ₹30/day
- **₹1000 investment** → ₹70/day  
- **₹2000 investment** → ₹150/day

### Referral Bonuses:
- **₹500 referral** → ₹3/day bonus for referrer
- **₹1000 referral** → ₹7/day bonus for referrer
- **₹2000 referral** → ₹15/day bonus for referrer

## File Structure

```
earning-website/
├── app.py              # Main Flask application
├── setup.py            # Database setup script
├── requirements.txt    # Python dependencies
├── templates/          # HTML templates
│   ├── base.html      # Base template
│   ├── index.html     # Home page
│   ├── register.html  # Registration page
│   ├── login.html     # Login page
│   ├── dashboard.html # User dashboard
│   ├── invest.html    # Investment page
│   ├── profile.html   # User profile
│   └── earnings.html  # Earnings history
└── earning_website.db # SQLite database (created after setup)
```

## Database Schema

### Users Table
- User ID, username, email, password
- Unique 7-digit referral code
- Investment and earnings tracking
- Referral relationships

### Investments Table
- Investment amount and daily returns
- User associations
- Investment dates and status

### Daily Earnings Table
- Daily earning records
- Investment and referral earnings tracking
- Date-wise earning history

### Referrals Table
- Referrer and referred user relationships
- Bonus tracking
- Referral performance metrics

## API Endpoints

- `GET /` - Home page
- `GET/POST /register` - User registration
- `GET/POST /login` - User login
- `GET /logout` - User logout
- `GET /dashboard` - User dashboard
- `GET/POST /invest` - Investment management
- `GET /profile` - User profile and referrals
- `GET /earnings` - Earnings history

## Automated Features

### Daily Earnings Processing
- Runs automatically at midnight every day
- Calculates investment returns for all users
- Processes referral bonuses
- Updates user earning totals

### Security
- Password hashing with Werkzeug
- Session management with Flask-Login
- Input validation and sanitization
- SQL injection prevention

## Customization

### Changing Investment Plans
Edit the `calculate_daily_return()` function in `app.py`:

```python
def calculate_daily_return(amount):
    if amount >= 2000:
        return 150  # Change this value
    elif amount >= 1000:
        return 70   # Change this value
    elif amount >= 500:
        return 30   # Change this value
    else:
        return 0
```

### Changing Referral Bonus Rate
Edit the `calculate_referral_bonus()` function in `app.py`:

```python
def calculate_referral_bonus(investment_amount):
    daily_return = calculate_daily_return(investment_amount)
    return daily_return * 0.1  # Change 0.1 to desired percentage
```

## Production Deployment

### Environment Variables
Create a `.env` file with:
```
SECRET_KEY=your-super-secret-key-here
DATABASE_URL=your-database-url
FLASK_ENV=production
```

### Security Considerations
1. Change the SECRET_KEY in production
2. Use a proper database (PostgreSQL/MySQL) instead of SQLite
3. Set up HTTPS/SSL certificates
4. Configure proper logging
5. Set up backup systems
6. Implement rate limiting
7. Add email verification for registration

## Support

For issues or questions, please check:
1. Make sure all dependencies are installed
2. Verify Python version (3.7+)
3. Check that the database was created successfully
4. Ensure port 5000 is available

## License

This project is for educational purposes. Please ensure compliance with local financial regulations before deploying in production.
