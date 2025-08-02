# Fall In - University Dating App (FIXED VERSION)
# Complete Flask Application with Debug Routes

import os
import secrets
import uuid
import base64
from datetime import datetime, timedelta
from flask import Flask, render_template, render_template_string, request, redirect, url_for, flash, session, jsonify
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import random
import string
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-change-in-production'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Email Configuration
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS', 'True').lower() == 'true'
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')

# Supabase Configuration
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')

# Initialize Supabase client
if SUPABASE_URL and SUPABASE_KEY:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
else:
    supabase = None

# Check if email is configured
if app.config['MAIL_USERNAME'] and app.config['MAIL_PASSWORD']:
    EMAIL_ENABLED = True
else:
    EMAIL_ENABLED = False

# No longer need upload directory since we store images in database

# Database setup - Supabase is already configured via SQL schema
def init_db():
    pass

# Initialize database
init_db()

# Add sample data for testing
def add_sample_data():
    if not supabase:
        print("❌ Supabase not configured")
        return
    
    # Check if sample data already exists
    result = supabase.table('users').select('email').ilike('email', '%@example.com').execute()
    if len(result.data) > 0:
        return
    
    # Add sample users
    sample_users = [
        {'email': 'alice@example.com', 'name': 'Alice Johnson', 'age': 20, 'pronouns': 'she/her', 'department': 'Computer Science', 'year': 'Student', 'looking_for': 'dating', 'bio': 'Love coding and coffee! Looking for someone to explore with.', 'is_verified': True},
        {'email': 'bob@example.com', 'name': 'Bob Smith', 'age': 22, 'pronouns': 'he/him', 'department': 'Engineering', 'year': 'Student', 'looking_for': 'relationship', 'bio': 'Ready for something real. Into hiking and board games.', 'is_verified': True},
        {'email': 'carol@example.com', 'name': 'Carol Davis', 'age': 19, 'pronouns': 'she/her', 'department': 'Psychology', 'year': 'Student', 'looking_for': 'friendship', 'bio': 'Would love to meet people and maybe find something special.', 'is_verified': True},
        {'email': 'david@example.com', 'name': 'David Wilson', 'age': 21, 'pronouns': 'he/him', 'department': 'Business', 'year': 'Student', 'looking_for': 'dating', 'bio': 'Entrepreneur at heart. Love trying new restaurants and weekend adventures.', 'is_verified': True},
        {'email': 'emma@example.com', 'name': 'Emma Brown', 'age': 20, 'pronouns': 'she/her', 'department': 'Biology', 'year': 'Student', 'looking_for': 'relationship', 'bio': 'Pre-med student who needs someone to remind her to have fun!', 'is_verified': True},
    ]
    
    for user_data in sample_users:
        # Insert user
        result = supabase.table('users').insert(user_data).execute()
        user_id = result.data[0]['id'] if result.data else None
        
        if user_id:
            prompts = [
                {'user_id': user_id, 'prompt_question': 'What makes you laugh?', 'prompt_answer': f'{user_data["name"].split()[0]} has a great sense of humor!'},
                {'user_id': user_id, 'prompt_question': 'My ideal study buddy is...', 'prompt_answer': 'Someone who brings snacks and good vibes'},
                {'user_id': user_id, 'prompt_question': 'Best campus spot?', 'prompt_answer': 'The library rooftop at sunset'}
            ]
            
            for prompt in prompts:
                supabase.table('user_prompts').insert(prompt).execute()

# Helper functions
def get_db_connection():
    return supabase

def generate_otp():
    return ''.join(random.choices(string.digits, k=6))

def send_otp_email(email, otp):
    if not EMAIL_ENABLED:
        return True
    
    try:
        # Create message
        msg = MIMEMultipart()
        msg['From'] = app.config['MAIL_USERNAME']
        msg['To'] = email
        msg['Subject'] = 'Fall In - Your Verification Code'
        
        # Email body
        body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <div style="text-align: center; margin-bottom: 30px;">
                    <h1 style="color: #ec4899; margin: 0;">Fall In</h1>
                    <p style="color: #666; margin: 10px 0;">Where Hearts Meet</p>
                </div>
                
                <div style="background: #f9f9f9; padding: 30px; border-radius: 10px; text-align: center;">
                    <h2 style="color: #333; margin-bottom: 20px;">Your Verification Code</h2>
                    <div style="background: #ec4899; color: white; padding: 20px; border-radius: 8px; font-size: 24px; font-weight: bold; letter-spacing: 5px; margin: 20px 0;">
                        {otp}
                    </div>
                    <p style="color: #666; margin: 20px 0;">This code will expire in 10 minutes.</p>
                    <p style="color: #999; font-size: 14px;">If you didn't request this code, please ignore this email.</p>
                </div>
                
                <div style="text-align: center; margin-top: 30px; color: #999; font-size: 12px;">
                    <p>©  Fall In, Made with ❤️ for VIT.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        msg.attach(MIMEText(body, 'html'))
        
        # Create SMTP session
        server = smtplib.SMTP(app.config['MAIL_SERVER'], app.config['MAIL_PORT'])
        server.starttls()
        server.login(app.config['MAIL_USERNAME'], app.config['MAIL_PASSWORD'])
        
        # Send email
        text = msg.as_string()
        server.sendmail(app.config['MAIL_USERNAME'], email, text)
        server.quit()
        
        return True
        
    except Exception as e:
        return False

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'gif'}

def image_to_base64(image_file):
    """Convert uploaded image file to base64 string"""
    try:
        # Read the image file
        image_data = image_file.read()
        # Convert to base64
        base64_string = base64.b64encode(image_data).decode('utf-8')
        # Get file extension
        file_extension = image_file.filename.rsplit('.', 1)[1].lower() if '.' in image_file.filename else 'jpeg'
        # Return data URL format
        return f"data:image/{file_extension};base64,{base64_string}"
    except Exception as e:
        print(f"Error converting image to base64: {e}")
        return None

# Debug and Test Routes
@app.route('/debug')
def debug():
    """Debug page to check if everything is working"""
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Fall In - Debug</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    </head>
    <body class="bg-gray-100 p-8">
        <div class="max-w-md mx-auto bg-white rounded-xl p-6 shadow-lg">
            <h1 class="text-2xl font-bold text-red-500 mb-4">
                <i class="fas fa-heart"></i> Fall In Debug
            </h1>
            
            <div class="space-y-4">
                <div class="p-4 bg-green-50 rounded-lg">
                    <h3 class="font-semibold text-green-800">✅ Tailwind CSS Working</h3>
                    <p class="text-green-600">If you see green styling, Tailwind is loaded!</p>
                </div>
                
                <div class="p-4 bg-blue-50 rounded-lg">
                    <h3 class="font-semibold text-blue-800">🔧 Font Awesome Working</h3>
                    <p class="text-blue-600">Icons: <i class="fas fa-heart text-red-500"></i> <i class="fas fa-user"></i> <i class="fas fa-home"></i></p>
                </div>
                
                <div class="p-4 bg-purple-50 rounded-lg">
                    <h3 class="font-semibold text-purple-800">🗄️ Database Status</h3>
                    <p class="text-purple-600">Database initialized and ready!</p>
                </div>
                
                <div class="space-y-2">
                    <a href="{{ url_for('index') }}" class="block bg-red-500 text-white text-center py-3 rounded-lg hover:bg-red-600 transition-colors">
                        Go to Home Page
                    </a>
                    <a href="{{ url_for('test_data') }}" class="block bg-blue-500 text-white text-center py-3 rounded-lg hover:bg-blue-600 transition-colors">
                        Add Test Data
                    </a>
                    <a href="{{ url_for('quick_login') }}" class="block bg-green-500 text-white text-center py-3 rounded-lg hover:bg-green-600 transition-colors">
                        Quick Login (Skip OTP)
                    </a>
                </div>
            </div>
        </div>
    </body>
    </html>
    ''')

@app.route('/test-data')
def test_data():
    """Add sample data for testing"""
    add_sample_data()
    flash('✅ Sample data added! You can now test the app.', 'success')
    return redirect(url_for('debug'))





@app.route('/quick-login')
def quick_login():
    """Quick login for testing (skips OTP)"""
    user_result = supabase.table('users').select('*').eq('email', 'alice@example.com').execute()
    
    if user_result.data:
        user = user_result.data[0]
        session['user_id'] = user['id']
        flash('✅ Logged in as Alice for testing!', 'success')
        return redirect(url_for('dashboard'))
    else:
        flash('❌ No test user found. Add test data first.', 'error')
        return redirect(url_for('debug'))

# Main Routes
@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template_string('''
    {% extends "base.html" %}
    {% block content %}
    <div class="heart-bg min-h-screen flex flex-col">
        <div class="flex-1 flex flex-col justify-center items-center px-4 text-center">
            <div class="w-32 h-32 bg-gradient-to-br from-pink-300 to-red-400 rounded-3xl flex items-center justify-center mb-8 shadow-xl slide-up">
                <i class="fas fa-heart text-6xl text-white heartbeat"></i>
            </div>
            
            <h1 class="text-4xl font-bold text-gray-800 mb-4 slide-up">Fall In</h1>
            <p class="text-xl text-gray-600 mb-2 slide-up">Where Hearts Meet</p>
            <p class="text-gray-500 mb-12 max-w-sm slide-up">Connect with people around you. Find friends, study buddies, or something more special.</p>
            
            <div class="space-y-4 w-full max-w-xs slide-up">
                <a href="{{ url_for('signup') }}" class="block w-full btn-primary text-white py-4 rounded-xl font-semibold text-lg shadow-lg">
                    Get Started
                </a>
                <a href="{{ url_for('login') }}" class="block w-full border-2 border-red-500 text-red-500 py-4 rounded-xl font-semibold text-lg hover:bg-red-50 transition duration-300">
                    Sign In
                </a>
                <a href="{{ url_for('debug') }}" class="block w-full border border-gray-300 text-gray-600 py-2 rounded-lg text-sm hover:bg-gray-50 transition duration-300">
                    🔧 Debug Page
                </a>
            </div>
        </div>
    </div>
    {% endblock %}
    ''')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form['email'].lower().strip()
        
        # Check if user already exists
        existing_user_result = supabase.table('users').select('*').eq('email', email).execute()
        
        if existing_user_result.data:
            # If user exists, redirect them to login instead of showing error
            flash('Email already registered. Please sign in instead.', 'info')
            return redirect(url_for('login'))
        
        otp = generate_otp()
        otp_expires = datetime.now() + timedelta(minutes=10)
        
        # Insert new user
        try:
            supabase.table('users').insert({
                'email': email,
                'otp_code': otp,
                'otp_expires': otp_expires.isoformat()
            }).execute()
            
            send_otp_email(email, otp)
            session['signup_email'] = email
            flash('OTP sent to your email!', 'success')
            return redirect(url_for('verify_otp'))
        except Exception as e:
            flash('Error creating account. Please try again.', 'error')
            return redirect(url_for('signup'))
    
    return render_template_string('''
    {% extends "base.html" %}
    {% block content %}
    <div class="heart-bg min-h-screen flex items-center justify-center px-4">
        <div class="bg-white rounded-2xl p-8 w-full max-w-md shadow-xl slide-up">
            <div class="text-center mb-8">
                <div class="w-16 h-16 bg-gradient-to-br from-pink-200 to-red-200 rounded-2xl flex items-center justify-center mx-auto mb-4">
                    <i class="fas fa-heart text-3xl text-red-500"></i>
                </div>
                <h1 class="text-2xl font-bold text-gray-800">Join Fall In</h1>
                <p class="text-gray-600 mt-2">Enter your email to get started</p>
            </div>
            
            <form method="POST" class="space-y-6">
                <div>
                    <label class="block text-sm font-medium text-gray-700 mb-2">Email Address</label>
                    <input type="email" name="email" required 
                           class="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-red-500 focus:border-transparent"
                           placeholder="yourname@example.com">
                    <p class="text-xs text-gray-500 mt-1">We'll send a verification code to this email</p>
                </div>
                
                <button type="submit" 
                        class="w-full btn-primary text-white py-3 rounded-xl font-semibold">
                    Send Verification Code
                </button>
            </form>
            
            <div class="text-center mt-6">
                <p class="text-gray-600">Already have an account? 
                    <a href="{{ url_for('login') }}" class="text-red-500 font-semibold hover:underline">Sign In</a>
                </p>
                <p class="text-gray-500 text-xs mt-2">
                    For testing: <a href="{{ url_for('debug') }}" class="text-blue-500 hover:underline">Debug Page</a>
                </p>
            </div>
        </div>
    </div>
    {% endblock %}
    ''')

@app.route('/verify-otp', methods=['GET', 'POST'])
def verify_otp():
    if 'signup_email' not in session:
        return redirect(url_for('signup'))
    
    if request.method == 'POST':
        otp = request.form['otp']
        email = session['signup_email']
        
        # Find user with matching email, OTP, and non-expired OTP
        user_result = supabase.table('users').select('*').eq('email', email).eq('otp_code', otp).gt('otp_expires', datetime.now().isoformat()).execute()
        
        if user_result.data:
            user = user_result.data[0]
            # Update user to verified
            supabase.table('users').update({'is_verified': True}).eq('email', email).execute()
            
            session['user_id'] = user['id']
            session.pop('signup_email', None)
            flash('Email verified! Welcome to Fall In! 🎉', 'success')
            return redirect(url_for('create_profile'))
        else:
            flash('Invalid or expired OTP', 'error')
    
    return render_template_string('''
    {% extends "base.html" %}
    {% block content %}
    <div class="heart-bg min-h-screen flex items-center justify-center px-4">
        <div class="bg-white rounded-2xl p-8 w-full max-w-md shadow-xl slide-up">
            <div class="text-center mb-8">
                <div class="w-16 h-16 bg-pink-200 rounded-2xl flex items-center justify-center mx-auto mb-4">
                    <i class="fas fa-envelope text-3xl text-red-500"></i>
                </div>
                <h1 class="text-2xl font-bold text-gray-800">Check Your Email</h1>
                <p class="text-gray-600 mt-2">We sent a 6-digit code to {{ session.signup_email }}</p>
                <p class="text-xs text-blue-500 mt-2">Check the console/terminal for the OTP code</p>
            </div>
            
            <form method="POST" class="space-y-6">
                <div>
                    <label class="block text-sm font-medium text-gray-700 mb-2">Verification Code</label>
                    <input type="text" name="otp" required maxlength="6" 
                           class="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-red-500 focus:border-transparent text-center text-2xl font-mono"
                           placeholder="123456">
                </div>
                
                <button type="submit" 
                        class="w-full btn-primary text-white py-3 rounded-xl font-semibold">
                    Verify Email
                </button>
            </form>
            
            <div class="text-center mt-6">
                <p class="text-gray-600">Didn't receive the code? 
                    <a href="{{ url_for('signup') }}" class="text-red-500 font-semibold hover:underline">Try Again</a>
                </p>
            </div>
        </div>
    </div>
    {% endblock %}
    ''')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email'].lower().strip()
        
        # Find user by email
        user_result = supabase.table('users').select('*').eq('email', email).execute()
        
        if user_result.data:
            user = user_result.data[0]
            otp = generate_otp()
            otp_expires = datetime.now() + timedelta(minutes=10)
            
            # Update user with new OTP
            supabase.table('users').update({
                'otp_code': otp,
                'otp_expires': otp_expires.isoformat()
            }).eq('id', user['id']).execute()
            
            send_otp_email(email, otp)
            session['login_email'] = email
            flash('OTP sent to your email!', 'success')
            return redirect(url_for('verify_login_otp'))
        else:
            flash('Email not found. Please sign up first.', 'error')
    
    return render_template_string('''
    {% extends "base.html" %}
    {% block content %}
    <div class="heart-bg min-h-screen flex items-center justify-center px-4">
        <div class="bg-white rounded-2xl p-8 w-full max-w-md shadow-xl slide-up">
            <div class="text-center mb-8">
                <div class="w-16 h-16 bg-gradient-to-br from-pink-200 to-red-200 rounded-2xl flex items-center justify-center mx-auto mb-4">
                    <i class="fas fa-heart text-3xl text-red-500"></i>
                </div>
                <h1 class="text-2xl font-bold text-gray-800">Welcome Back</h1>
                <p class="text-gray-600 mt-2">Enter your email to sign in</p>
            </div>
            
            <form method="POST" class="space-y-6">
                <div>
                    <label class="block text-sm font-medium text-gray-700 mb-2">Email Address</label>
                    <input type="email" name="email" required 
                           class="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-red-500 focus:border-transparent"
                           placeholder="yourname@example.com">
                    <p class="text-xs text-gray-500 mt-1">We'll send a verification code to this email</p>
                </div>
                
                <button type="submit" 
                        class="w-full btn-primary text-white py-3 rounded-xl font-semibold">
                    Send Login Code
                </button>
            </form>
            
            <div class="text-center mt-6">
                <p class="text-gray-600">Don't have an account? 
                    <a href="{{ url_for('signup') }}" class="text-red-500 font-semibold hover:underline">Sign Up</a>
                </p>
            </div>
        </div>
    </div>
    {% endblock %}
    ''')

@app.route('/verify-login-otp', methods=['GET', 'POST'])
def verify_login_otp():
    if 'login_email' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        otp = request.form['otp']
        email = session['login_email']
        
        # Find user with matching email, OTP, and non-expired OTP
        user_result = supabase.table('users').select('*').eq('email', email).eq('otp_code', otp).gt('otp_expires', datetime.now().isoformat()).execute()
        
        if user_result.data:
            user = user_result.data[0]
            
            # Auto-verify user if they weren't verified before
            if not user['is_verified']:
                supabase.table('users').update({'is_verified': True}).eq('id', user['id']).execute()
            
            session['user_id'] = user['id']
            session.pop('login_email', None)
            flash('Welcome back! 👋', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid or expired OTP', 'error')
    
    return render_template_string('''
    {% extends "base.html" %}
    {% block content %}
    <div class="heart-bg min-h-screen flex items-center justify-center px-4">
        <div class="bg-white rounded-2xl p-8 w-full max-w-md shadow-xl slide-up">
            <div class="text-center mb-8">
                <div class="w-16 h-16 bg-pink-200 rounded-2xl flex items-center justify-center mx-auto mb-4">
                    <i class="fas fa-envelope text-3xl text-red-500"></i>
                </div>
                <h1 class="text-2xl font-bold text-gray-800">Enter Login Code</h1>
                <p class="text-gray-600 mt-2">We sent a code to {{ session.login_email }}</p>
                <p class="text-xs text-blue-500 mt-2">Check the console/terminal for the OTP code</p>
            </div>
            
            <form method="POST" class="space-y-6">
                <div>
                    <label class="block text-sm font-medium text-gray-700 mb-2">Login Code</label>
                    <input type="text" name="otp" required maxlength="6" 
                           class="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-red-500 focus:border-transparent text-center text-2xl font-mono"
                           placeholder="123456">
                </div>
                
                <button type="submit" 
                        class="w-full btn-primary text-white py-3 rounded-xl font-semibold">
                    Sign In
                </button>
            </form>
        </div>
    </div>
    {% endblock %}
    ''')

@app.route('/create-profile', methods=['GET', 'POST'])
def create_profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        name = request.form['name']
        age = request.form['age']
        pronouns = request.form['pronouns']
        department = request.form['department']
        year = request.form['year']
        looking_for = request.form['looking_for']
        bio = request.form['bio']
        
        # Handle file upload - convert to base64 and store in database
        profile_photo = None
        if 'profile_photo' in request.files:
            file = request.files['profile_photo']
            if file and allowed_file(file.filename):
                # Convert image to base64
                profile_photo = image_to_base64(file)
                if not profile_photo:
                    flash('Error processing image. Please try again.', 'error')
                    return redirect(url_for('create_profile'))
        
        # Update user profile
        supabase.table('users').update({
            'name': name,
            'age': age,
            'pronouns': pronouns,
            'department': department,
            'year': year,
            'looking_for': looking_for,
            'bio': bio,
            'profile_photo': profile_photo
        }).eq('id', session['user_id']).execute()
        
        # Handle prompts
        prompts = [
            ('What makes you laugh?', request.form.get('prompt1')),
            ('My ideal study buddy is...', request.form.get('prompt2')),
            ('Best campus spot?', request.form.get('prompt3'))
        ]
        
        for question, answer in prompts:
            if answer:
                supabase.table('user_prompts').insert({
                    'user_id': session['user_id'],
                    'prompt_question': question,
                    'prompt_answer': answer
                }).execute()
        
        flash('Profile created successfully! Time to start discovering! 🎉', 'success')
        return redirect(url_for('dashboard'))
    
    return render_template_string('''
    {% extends "base.html" %}
    {% block content %}
    <div class="bg-gray-50 min-h-screen py-8">
        <div class="max-w-md mx-auto px-4">
            <div class="text-center mb-8 slide-up">
                <h1 class="text-2xl font-bold text-gray-800">Create Your Profile</h1>
                <p class="text-gray-600 mt-2">Let others get to know the real you</p>
            </div>
            
            <form method="POST" enctype="multipart/form-data" class="space-y-6">
                <div class="bg-white rounded-xl p-6 shadow-sm slide-up">
                    <h3 class="font-semibold text-gray-800 mb-4">Profile Photo</h3>
                    <input type="file" name="profile_photo" accept="image/*" 
                           class="w-full px-4 py-3 border border-gray-300 rounded-xl">
                </div>
                
                <div class="bg-white rounded-xl p-6 shadow-sm space-y-4 slide-up">
                    <h3 class="font-semibold text-gray-800 mb-4">Basic Info</h3>
                    
                    <input type="text" name="name" required placeholder="Your Name"
                           class="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-red-500">
                    
                    <div class="grid grid-cols-2 gap-4">
                        <input type="number" name="age" required min="18" max="100" placeholder="Age"
                               class="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-red-500">
                        
                        <select name="pronouns" required 
                                class="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-red-500">
                            <option value="">Pronouns</option>
                            <option value="she/her">she/her</option>
                            <option value="he/him">he/him</option>
                            <option value="they/them">they/them</option>
                            <option value="other">other</option>
                        </select>
                    </div>
                    
                    <input type="text" name="department" required placeholder="Department (e.g., Computer Science)"
                           class="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-red-500">
                    
                    <select name="year" required 
                            class="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-red-500">
                        <option value="">Year</option>
                        <option value="Freshman">Freshman</option>
                        <option value="Sophomore">Sophomore</option>
                        <option value="Junior">Junior</option>
                        <option value="Senior">Senior</option>
                        <option value="Graduate">Graduate</option>
                        <option value="PhD">PhD</option>
                    </select>
                    
                    <select name="looking_for" required 
                            class="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-red-500">
                        <option value="">Looking for</option>
                        <option value="friendship">Friendship</option>
                        <option value="dating">Dating</option>
                        <option value="relationship">Relationship</option>
                        <option value="networking">Networking</option>
                    </select>
                </div>
                
                <div class="bg-white rounded-xl p-6 shadow-sm slide-up">
                    <h3 class="font-semibold text-gray-800 mb-4">About You</h3>
                    <textarea name="bio" rows="4" placeholder="Tell people about yourself..."
                              class="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-red-500"></textarea>
                </div>
                
                <div class="bg-white rounded-xl p-6 shadow-sm space-y-4 slide-up">
                    <h3 class="font-semibold text-gray-800 mb-4">Fun Prompts</h3>
                    
                    <input type="text" name="prompt1" placeholder="What makes you laugh?"
                           class="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-red-500">
                    
                    <input type="text" name="prompt2" placeholder="My ideal study buddy is..."
                           class="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-red-500">
                    
                    <input type="text" name="prompt3" placeholder="Best campus spot?"
                           class="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-red-500">
                </div>
                
                <button type="submit" 
                        class="w-full btn-primary text-white py-4 rounded-xl font-semibold shadow-lg slide-up">
                    Create Profile
                </button>
            </form>
        </div>
    </div>
    {% endblock %}
    ''')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # Get user data
    user_result = supabase.table('users').select('*').eq('id', session['user_id']).execute()
    if not user_result.data:
        return redirect(url_for('login'))
    
    user = user_result.data[0]
    
    if not user['name']:
        return redirect(url_for('create_profile'))
    
    # Get potential matches - users who haven't been liked by current user
    # and aren't already matched
    user_id = session['user_id']
    
    # Get users the current user has already liked
    liked_users_result = supabase.table('likes').select('liked_id').eq('liker_id', user_id).execute()
    liked_user_ids = [like['liked_id'] for like in liked_users_result.data]
    
    # Get users who have already matched with current user
    matches_result = supabase.table('matches').select('user1_id, user2_id').or_(f'user1_id.eq.{user_id},user2_id.eq.{user_id}').execute()
    matched_user_ids = []
    for match in matches_result.data:
        if match['user1_id'] == user_id:
            matched_user_ids.append(match['user2_id'])
        else:
            matched_user_ids.append(match['user1_id'])
    
    # Get potential matches
    excluded_ids = [user_id] + liked_user_ids + matched_user_ids
    potential_matches_result = supabase.table('users').select('*').neq('id', user_id).not_.in_('id', excluded_ids).not_.is_('name', 'null').limit(10).execute()
    
    # Get prompts for each potential match
    potential_matches = []
    for match in potential_matches_result.data:
        prompts_result = supabase.table('user_prompts').select('prompt_question, prompt_answer').eq('user_id', match['id']).execute()
        prompts_text = ' | '.join([f"{p['prompt_question']}: {p['prompt_answer']}" for p in prompts_result.data])
        match['prompts'] = prompts_text
        potential_matches.append(match)
    
    return render_template('dashboard.html', user=user, potential_matches=potential_matches)

@app.route('/like/<user_id>')
def like_user(user_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    liker_id = session['user_id']
    
    # Add like (Supabase will handle duplicates)
    try:
        supabase.table('likes').insert({'liker_id': liker_id, 'liked_id': user_id}).execute()
        
        # Get the liked user's info for notification
        liked_user_result = supabase.table('users').select('name').eq('id', user_id).execute()
        liked_user_name = liked_user_result.data[0]['name'] if liked_user_result.data else 'Someone'
        
        # Get the liker's info for the notification
        liker_result = supabase.table('users').select('name').eq('id', liker_id).execute()
        liker_name = liker_result.data[0]['name'] if liker_result.data else 'Someone'
        
        # Create notification for the liked user
        supabase.table('notifications').insert({
            'user_id': user_id,
            'from_user_id': liker_id,
            'type': 'like',
            'message': f'{liker_name} liked your profile! 💖'
        }).execute()
        
        flash(f'You liked {liked_user_name}! 💖', 'success')
        
    except Exception as e:
        # Like might already exist, that's okay
        pass
    
    # Check if it's a match
    existing_like_result = supabase.table('likes').select('*').eq('liker_id', user_id).eq('liked_id', liker_id).execute()
    
    if existing_like_result.data:
        # It's a match!
        user1_id = min(liker_id, user_id)
        user2_id = max(liker_id, user_id)
        
        try:
            supabase.table('matches').insert({'user1_id': user1_id, 'user2_id': user2_id}).execute()
            
            # Get both users' names for notifications
            user1_result = supabase.table('users').select('name').eq('id', user1_id).execute()
            user2_result = supabase.table('users').select('name').eq('id', user2_id).execute()
            
            user1_name = user1_result.data[0]['name'] if user1_result.data else 'Someone'
            user2_name = user2_result.data[0]['name'] if user2_result.data else 'Someone'
            
            # Create match notifications for both users
            supabase.table('notifications').insert([
                {
                    'user_id': user1_id,
                    'from_user_id': user2_id,
                    'type': 'match',
                    'message': f'It\'s a match with {user2_name}! 💖'
                },
                {
                    'user_id': user2_id,
                    'from_user_id': user1_id,
                    'type': 'match',
                    'message': f'It\'s a match with {user1_name}! 💖'
                }
            ]).execute()
            
            flash('It\'s a match! 💖', 'success')
        except Exception as e:
            # Match might already exist, that's okay
            pass
    
    return redirect(url_for('dashboard'))

@app.route('/pass/<user_id>')
def pass_user(user_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    return redirect(url_for('dashboard'))

@app.route('/matches')
def matches():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    
    # Get matches for the current user
    matches_result = supabase.table('matches').select('*').or_(f'user1_id.eq.{user_id},user2_id.eq.{user_id}').execute()
    
    user_matches = []
    for match in matches_result.data:
        # Determine the other user's ID
        other_user_id = match['user2_id'] if match['user1_id'] == user_id else match['user1_id']
        
        # Get the other user's details
        user_result = supabase.table('users').select('*').eq('id', other_user_id).execute()
        if user_result.data:
            user_data = user_result.data[0]
            user_data['matched_at'] = match['matched_at']
            user_data['match_id'] = other_user_id
            user_matches.append(user_data)
    
    # Sort by matched_at descending
    user_matches.sort(key=lambda x: x['matched_at'], reverse=True)
    return render_template_string('''
    {% extends "base.html" %}
    {% block content %}
    <div class="bg-gray-50 min-h-screen py-4">
        <div class="max-w-md mx-auto px-4">
            <div class="text-center mb-6 slide-up">
                <h1 class="text-2xl font-bold text-gray-800">Your Matches</h1>
                <p class="text-gray-600">{{ matches|length }} connection{{ 's' if matches|length != 1 else '' }}</p>
            </div>
            
            {% if matches %}
                <div class="space-y-4">
                    {% for match in matches %}
                    <div class="bg-white rounded-xl p-4 shadow-sm hover:shadow-md transition-all duration-300 slide-up">
                        <div class="flex items-center space-x-4">
                            <div class="w-16 h-16 bg-gradient-to-br from-pink-200 to-red-200 rounded-full flex items-center justify-center flex-shrink-0">
                                {% if match.profile_photo %}
                                    {% if match.profile_photo.startswith('data:image') %}
                                        <img src="{{ match.profile_photo }}" 
                                             alt="{{ match.name }}" class="w-16 h-16 object-cover rounded-full">
                                    {% else %}
                                        <img src="{{ url_for('static', filename='uploads/' + match.profile_photo) }}" 
                                             alt="{{ match.name }}" class="w-16 h-16 object-cover rounded-full">
                                    {% endif %}
                                {% else %}
                                    <i class="fas fa-user text-xl text-gray-400"></i>
                                {% endif %}
                            </div>
                            
                            <div class="flex-1 min-w-0">
                                <h3 class="font-semibold text-gray-800 truncate">{{ match.name }}</h3>
                                <p class="text-sm text-gray-600">{{ match.department }}</p>
                                <p class="text-xs text-gray-500">Matched {{ match.matched_at[:10] }}</p>
                            </div>
                            
                            <a href="{{ url_for('chat', user_id=match.match_id) }}" class="btn-primary text-white px-4 py-2 rounded-lg text-sm">
                                Chat
                            </a>
                        </div>
                    </div>
                    {% endfor %}
                </div>
            {% else %}
                <div class="text-center py-16 slide-up">
                    <div class="w-20 h-20 bg-pink-200 rounded-full flex items-center justify-center mx-auto mb-4">
                        <i class="fas fa-heart text-3xl text-red-500 heartbeat"></i>
                    </div>
                    <h3 class="text-xl font-bold text-gray-800 mb-2">No matches yet</h3>
                    <p class="text-gray-600 mb-6">Keep swiping to find your connections!</p>
                    <a href="{{ url_for('dashboard') }}" 
                       class="inline-block btn-primary text-white px-6 py-3 rounded-xl font-semibold">
                        Start Discovering
                    </a>
                </div>
            {% endif %}
        </div>
    </div>
    {% endblock %}
    ''', matches=user_matches)

@app.route('/profile')
def profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # Get user data
    user_result = supabase.table('users').select('*').eq('id', session['user_id']).execute()
    if not user_result.data:
        return redirect(url_for('login'))
    
    user = user_result.data[0]
    
    # Get user prompts
    prompts_result = supabase.table('user_prompts').select('*').eq('user_id', session['user_id']).execute()
    prompts = prompts_result.data
    
    return render_template_string('''
    {% extends "base.html" %}
    {% block content %}
    <div class="bg-gray-50 min-h-screen py-4">
        <div class="max-w-md mx-auto px-4">
            <div class="flex justify-between items-center mb-6 slide-up">
                <h1 class="text-2xl font-bold text-gray-800">Your Profile</h1>
                <a href="{{ url_for('logout') }}" class="text-red-500 hover:text-red-600">
                    <i class="fas fa-sign-out-alt text-xl"></i>
                </a>
            </div>
            
            <div class="bg-white rounded-2xl shadow-lg overflow-hidden mb-6 slide-up">
                <div class="h-64 bg-gradient-to-br from-pink-200 to-red-200 flex items-center justify-center">
                    {% if user.profile_photo %}
                        {% if user.profile_photo.startswith('data:image') %}
                            <img src="{{ user.profile_photo }}" 
                                 alt="{{ user.name }}" class="w-full h-full object-cover">
                        {% else %}
                            <img src="{{ url_for('static', filename='uploads/' + user.profile_photo) }}" 
                                 alt="{{ user.name }}" class="w-full h-full object-cover">
                        {% endif %}
                    {% else %}
                        <i class="fas fa-user text-6xl text-gray-400"></i>
                    {% endif %}
                </div>
                
                <div class="p-6">
                    <div class="mb-4">
                        <h3 class="text-xl font-bold text-gray-800">{{ user.name }}, {{ user.age }}</h3>
                        <p class="text-gray-600">{{ user.department }} • {{ user.year }}</p>
                        <p class="text-sm text-red-500 font-medium">{{ user.looking_for|title }}</p>
                    </div>
                    
                    {% if user.bio %}
                    <div class="mb-4">
                        <h4 class="font-semibold text-gray-800 mb-2">About Me</h4>
                        <p class="text-gray-700">{{ user.bio }}</p>
                    </div>
                    {% endif %}
                    
                    {% if prompts %}
                    <div class="mb-4">
                        <h4 class="font-semibold text-gray-800 mb-3">My Prompts</h4>
                        <div class="space-y-2">
                            {% for prompt in prompts %}
                            <div class="bg-gray-50 rounded-lg p-3">
                                <p class="text-sm font-medium text-gray-600">{{ prompt.prompt_question }}</p>
                                <p class="text-gray-800">{{ prompt.prompt_answer }}</p>
                            </div>
                            {% endfor %}
                        </div>
                    </div>
                    {% endif %}
                </div>
            </div>
            
            <div class="space-y-3 slide-up">
                <button class="w-full btn-primary text-white py-3 rounded-xl font-semibold">
                    Edit Profile
                </button>
                <a href="{{ url_for('dashboard') }}" class="block w-full bg-gray-200 text-gray-700 text-center py-3 rounded-xl font-semibold hover:bg-gray-300 transition-colors">
                    Back to Discover
                </a>
            </div>
        </div>
    </div>
    {% endblock %}
    ''', user=user, prompts=prompts)

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully', 'success')
    return redirect(url_for('index'))

# Chat and Notification Routes
@app.route('/notifications')
def notifications():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    
    # Get pending chat requests
    pending_requests_result = supabase.table('chat_requests').select('*, users!chat_requests_requester_id_fkey(*)').eq('receiver_id', user_id).eq('status', 'pending').order('created_at', desc=True).execute()
    
    # Process pending requests to get user data
    pending_requests = []
    for request in pending_requests_result.data:
        if 'users' in request:
            user_data = request['users']
            request_data = {
                'id': request['id'],
                'name': user_data['name'],
                'profile_photo': user_data['profile_photo'],
                'department': user_data['department'],
                'created_at': request['created_at']
            }
            pending_requests.append(request_data)
    
    # Get notifications
    notifications_result = supabase.table('notifications').select('*, users!notifications_from_user_id_fkey(*)').eq('user_id', user_id).order('created_at', desc=True).limit(10).execute()
    
    notifications = []
    for notification in notifications_result.data:
        if 'users' in notification:
            from_user = notification['users']
            notification_data = {
                'id': notification['id'],
                'type': notification['type'],
                'message': notification['message'],
                'from_user_id': notification['from_user_id'],
                'from_user_name': from_user['name'],
                'from_user_photo': from_user['profile_photo'],
                'from_user_department': from_user['department'],
                'created_at': notification['created_at'],
                'is_read': notification['is_read']
            }
            notifications.append(notification_data)
    
    # Get recent matches
    matches_result = supabase.table('matches').select('*').or_(f'user1_id.eq.{user_id},user2_id.eq.{user_id}').order('matched_at', desc=True).limit(5).execute()
    
    recent_matches = []
    for match in matches_result.data:
        other_user_id = match['user2_id'] if match['user1_id'] == user_id else match['user1_id']
        user_result = supabase.table('users').select('*').eq('id', other_user_id).execute()
        if user_result.data:
            user_data = user_result.data[0]
            match_data = {
                'id': match['id'],
                'other_user_id': other_user_id,
                'name': user_data['name'],
                'profile_photo': user_data['profile_photo'],
                'department': user_data['department'],
                'matched_at': match['matched_at']
            }
            recent_matches.append(match_data)
    
    return render_template_string('''
    {% extends "base.html" %}
    {% block content %}
    <div class="bg-gray-50 min-h-screen py-4">
        <div class="max-w-md mx-auto px-4">
            <div class="text-center mb-6 slide-up">
                <h1 class="text-2xl font-bold text-gray-800">Notifications</h1>
                <p class="text-gray-600">{{ notifications|length }} new notifications</p>
            </div>
            
            {% if notifications %}
            <div class="space-y-4 mb-8">
                <h2 class="font-semibold text-gray-800 mb-3">Recent Activity</h2>
                {% for notification in notifications %}
                <div class="bg-white rounded-xl p-4 shadow-sm hover:shadow-md transition-all duration-300 slide-up {% if not notification.is_read %}border-l-4 border-red-500{% endif %}">
                    <div class="flex items-center space-x-4">
                        <div class="w-12 h-12 bg-gradient-to-br from-pink-200 to-red-200 rounded-full flex items-center justify-center flex-shrink-0">
                            {% if notification.from_user_photo %}
                                {% if notification.from_user_photo.startswith('data:image') %}
                                    <img src="{{ notification.from_user_photo }}" 
                                         alt="{{ notification.from_user_name }}" class="w-12 h-12 object-cover rounded-full">
                                {% else %}
                                    <img src="{{ url_for('static', filename='uploads/' + notification.from_user_photo) }}" 
                                         alt="{{ notification.from_user_name }}" class="w-12 h-12 object-cover rounded-full">
                                {% endif %}
                            {% else %}
                                <i class="fas fa-user text-xl text-gray-400"></i>
                            {% endif %}
                        </div>
                        
                        <div class="flex-1 min-w-0">
                            <h3 class="font-semibold text-gray-800 truncate">{{ notification.from_user_name }}</h3>
                            <p class="text-sm text-gray-600">{{ notification.message }}</p>
                            <p class="text-xs text-gray-500">{{ notification.created_at[:10] }}</p>
                        </div>
                        
                        {% if notification.type == 'match' %}
                        <span class="bg-red-500 text-white px-2 py-1 rounded-full text-xs">
                            Match! 💖
                        </span>
                        {% elif notification.type == 'like' %}
                        <div class="flex space-x-2">
                            <span class="bg-pink-500 text-white px-2 py-1 rounded-full text-xs">
                                Like 💖
                            </span>
                            <a href="{{ url_for('accept_like_and_chat', user_id=notification.from_user_id) }}" 
                               class="bg-green-500 text-white px-3 py-1 rounded-lg text-xs hover:bg-green-600 transition-colors">
                                Accept
                            </a>
                        </div>
                        {% elif notification.type == 'chat_request' %}
                        <div class="flex space-x-2">
                            <span class="bg-blue-500 text-white px-2 py-1 rounded-full text-xs">
                                Chat Request 💬
                            </span>
                            <a href="{{ url_for('accept_chat_and_start_chat', user_id=notification.from_user_id) }}" 
                               class="bg-green-500 text-white px-3 py-1 rounded-lg text-xs hover:bg-green-600 transition-colors">
                                Accept
                            </a>
                        </div>
                        {% elif notification.type == 'chat_accepted' %}
                        <div class="flex space-x-2">
                            <span class="bg-green-500 text-white px-2 py-1 rounded-full text-xs">
                                Chat Accepted 💬
                            </span>
                            <a href="{{ url_for('chat', user_id=notification.from_user_id) }}" 
                               class="bg-blue-500 text-white px-3 py-1 rounded-lg text-xs hover:bg-blue-600 transition-colors">
                                Chat Now
                            </a>
                        </div>
                        {% endif %}
                    </div>
                </div>
                {% endfor %}
            </div>
            {% endif %}
            
            {% if pending_requests %}
            <div class="space-y-4 mb-8">
                <h2 class="font-semibold text-gray-800 mb-3">Chat Requests</h2>
                {% for request in pending_requests %}
                <div class="bg-white rounded-xl p-4 shadow-sm hover:shadow-md transition-all duration-300 slide-up">
                    <div class="flex items-center space-x-4">
                        <div class="w-12 h-12 bg-gradient-to-br from-pink-200 to-red-200 rounded-full flex items-center justify-center flex-shrink-0">
                            {% if request.profile_photo %}
                                {% if request.profile_photo.startswith('data:image') %}
                                    <img src="{{ request.profile_photo }}" 
                                         alt="{{ request.name }}" class="w-12 h-12 object-cover rounded-full">
                                {% else %}
                                    <img src="{{ url_for('static', filename='uploads/' + request.profile_photo) }}" 
                                         alt="{{ request.name }}" class="w-12 h-12 object-cover rounded-full">
                                {% endif %}
                            {% else %}
                                <i class="fas fa-user text-xl text-gray-400"></i>
                            {% endif %}
                        </div>
                        
                        <div class="flex-1 min-w-0">
                            <h3 class="font-semibold text-gray-800 truncate">{{ request.name }}</h3>
                            <p class="text-sm text-gray-600">{{ request.department }}</p>
                            <p class="text-xs text-gray-500">{{ request.created_at[:10] }}</p>
                        </div>
                        
                        <div class="flex space-x-2">
                            <a href="{{ url_for('accept_chat_request', request_id=request.id) }}" 
                               class="bg-green-500 text-white px-3 py-1 rounded-lg text-sm hover:bg-green-600 transition-colors">
                                Accept
                            </a>
                            <a href="{{ url_for('reject_chat_request', request_id=request.id) }}" 
                               class="bg-red-500 text-white px-3 py-1 rounded-lg text-sm hover:bg-red-600 transition-colors">
                                Reject
                            </a>
                        </div>
                    </div>
                </div>
                {% endfor %}
            </div>
            {% endif %}
            
            {% if recent_matches %}
            <div class="space-y-4">
                <h2 class="font-semibold text-gray-800 mb-3">Recent Matches</h2>
                {% for match in recent_matches %}
                <div class="bg-white rounded-xl p-4 shadow-sm hover:shadow-md transition-all duration-300 slide-up">
                    <div class="flex items-center space-x-4">
                        <div class="w-12 h-12 bg-gradient-to-br from-pink-200 to-red-200 rounded-full flex items-center justify-center flex-shrink-0">
                            {% if match.profile_photo %}
                                {% if match.profile_photo.startswith('data:image') %}
                                    <img src="{{ match.profile_photo }}" 
                                         alt="{{ match.name }}" class="w-12 h-12 object-cover rounded-full">
                                {% else %}
                                    <img src="{{ url_for('static', filename='uploads/' + match.profile_photo) }}" 
                                         alt="{{ match.name }}" class="w-12 h-12 object-cover rounded-full">
                                {% endif %}
                            {% else %}
                                <i class="fas fa-user text-xl text-gray-400"></i>
                            {% endif %}
                        </div>
                        
                        <div class="flex-1 min-w-0">
                            <h3 class="font-semibold text-gray-800 truncate">{{ match.name }}</h3>
                            <p class="text-sm text-gray-600">{{ match.department }}</p>
                            <p class="text-xs text-gray-500">Matched {{ match.matched_at[:10] }}</p>
                        </div>
                        
                        <a href="{{ url_for('chat', user_id=match.other_user_id) }}" 
                           class="bg-blue-500 text-white px-3 py-1 rounded-lg text-sm hover:bg-blue-600 transition-colors">
                            Chat
                        </a>
                    </div>
                </div>
                {% endfor %}
            </div>
            {% endif %}
            
            {% if not notifications and not pending_requests and not recent_matches %}
            <div class="text-center py-16 slide-up">
                <div class="w-20 h-20 bg-pink-200 rounded-full flex items-center justify-center mx-auto mb-4">
                    <i class="fas fa-bell text-3xl text-red-500"></i>
                </div>
                <h3 class="text-xl font-bold text-gray-800 mb-2">No notifications yet</h3>
                <p class="text-gray-600 mb-6">Start swiping to get matches and chat requests!</p>
                <a href="{{ url_for('dashboard') }}" 
                   class="inline-block btn-primary text-white px-6 py-3 rounded-xl font-semibold">
                    Start Discovering
                </a>
            </div>
            {% endif %}
        </div>
    </div>
    {% endblock %}
    ''', pending_requests=pending_requests, recent_matches=recent_matches, notifications=notifications)

@app.route('/accept-chat-request/<request_id>')
def accept_chat_request(request_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    
    # Update chat request status
    try:
        supabase.table('chat_requests').update({
            'status': 'accepted',
            'updated_at': datetime.now().isoformat()
        }).eq('id', request_id).eq('receiver_id', user_id).execute()
        
        # Get the requester info
        request_info_result = supabase.table('chat_requests').select('requester_id, receiver_id').eq('id', request_id).eq('receiver_id', user_id).execute()
        
        if request_info_result.data:
            request_info = request_info_result.data[0]
            # Create a match if it doesn't exist
            try:
                supabase.table('matches').insert({
                    'user1_id': request_info['requester_id'],
                    'user2_id': request_info['receiver_id']
                }).execute()
            except Exception as e:
                # Match might already exist, that's okay
                pass
            
            # Get user names for notification
            requester_result = supabase.table('users').select('name').eq('id', request_info['requester_id']).execute()
            receiver_result = supabase.table('users').select('name').eq('id', request_info['receiver_id']).execute()
            
            requester_name = requester_result.data[0]['name'] if requester_result.data else 'Someone'
            receiver_name = receiver_result.data[0]['name'] if receiver_result.data else 'Someone'
            
            # Create notification for the requester
            supabase.table('notifications').insert({
                'user_id': request_info['requester_id'],
                'from_user_id': request_info['receiver_id'],
                'type': 'chat_accepted',
                'message': f'{receiver_name} accepted your chat request! 💬'
            }).execute()
            
            flash('Chat request accepted! 💬', 'success')
        else:
            flash('Request not found', 'error')
    except Exception as e:
        flash('Error accepting request', 'error')
    
    return redirect(url_for('notifications'))

@app.route('/reject-chat-request/<request_id>')
def reject_chat_request(request_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    
    try:
        supabase.table('chat_requests').update({
            'status': 'rejected',
            'updated_at': datetime.now().isoformat()
        }).eq('id', request_id).eq('receiver_id', user_id).execute()
        
        flash('Chat request rejected', 'info')
    except Exception as e:
        flash('Error rejecting request', 'error')
    
    return redirect(url_for('notifications'))

@app.route('/chat/<user_id>')
def chat(user_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    current_user_id = session['user_id']
    
    # Check if users can chat (either matched or chat request accepted)
    matches_result = supabase.table('matches').select('*').or_(f'user1_id.eq.{current_user_id},user2_id.eq.{current_user_id}').or_(f'user1_id.eq.{user_id},user2_id.eq.{user_id}').execute()
    
    can_chat = False
    for match in matches_result.data:
        if (match['user1_id'] == current_user_id and match['user2_id'] == user_id) or \
           (match['user1_id'] == user_id and match['user2_id'] == current_user_id):
            can_chat = True
            break
    
    if not can_chat:
        # Check if there's an accepted chat request
        chat_requests_result = supabase.table('chat_requests').select('*').or_(f'requester_id.eq.{current_user_id},receiver_id.eq.{current_user_id}').or_(f'requester_id.eq.{user_id},receiver_id.eq.{user_id}').eq('status', 'accepted').execute()
        
        for request in chat_requests_result.data:
            if (request['requester_id'] == current_user_id and request['receiver_id'] == user_id) or \
               (request['requester_id'] == user_id and request['receiver_id'] == current_user_id):
                can_chat = True
                break
    
    if not can_chat:
        flash('You can only chat with matched users or accepted chat requests', 'error')
        return redirect(url_for('dashboard'))
    
    # Get user info
    other_user_result = supabase.table('users').select('*').eq('id', user_id).execute()
    if not other_user_result.data:
        flash('User not found', 'error')
        return redirect(url_for('dashboard'))
    
    other_user = other_user_result.data[0]
    
    # Get messages
    messages_result = supabase.table('messages').select('*, users!messages_sender_id_fkey(*)').or_(f'sender_id.eq.{current_user_id},receiver_id.eq.{current_user_id}').or_(f'sender_id.eq.{user_id},receiver_id.eq.{user_id}').order('sent_at', desc=False).execute()
    
    messages = []
    for message in messages_result.data:
        if 'users' in message:
            user_data = message['users']
            message_data = {
                'id': message['id'],
                'content': message['content'],
                'sent_at': message['sent_at'],
                'is_read': message['is_read'],
                'sender_id': message['sender_id'],
                'receiver_id': message['receiver_id'],
                'name': user_data['name'],
                'profile_photo': user_data['profile_photo']
            }
            messages.append(message_data)
    
    # Mark messages as read
    try:
        supabase.table('messages').update({'is_read': True}).eq('sender_id', user_id).eq('receiver_id', current_user_id).eq('is_read', False).execute()
    except Exception as e:
        pass
    
    return render_template_string('''
    {% extends "base.html" %}
    {% block content %}
    <div class="bg-gray-50 min-h-screen flex flex-col">
        <!-- Chat Header -->
        <div class="bg-white border-b border-gray-200 px-4 py-3">
            <div class="flex items-center space-x-3">
                <a href="{{ url_for('notifications') }}" class="text-gray-600 hover:text-gray-800">
                    <i class="fas fa-arrow-left text-xl"></i>
                </a>
                <div class="w-10 h-10 bg-gradient-to-br from-pink-200 to-red-200 rounded-full flex items-center justify-center flex-shrink-0">
                    {% if other_user.profile_photo %}
                        {% if other_user.profile_photo.startswith('data:image') %}
                            <img src="{{ other_user.profile_photo }}" 
                                 alt="{{ other_user.name }}" class="w-10 h-10 object-cover rounded-full">
                        {% else %}
                            <img src="{{ url_for('static', filename='uploads/' + other_user.profile_photo) }}" 
                                 alt="{{ other_user.name }}" class="w-10 h-10 object-cover rounded-full">
                        {% endif %}
                    {% else %}
                        <i class="fas fa-user text-lg text-gray-400"></i>
                    {% endif %}
                </div>
                <div class="flex-1">
                    <h3 class="font-semibold text-gray-800">{{ other_user.name }}</h3>
                    <p class="text-sm text-gray-600">{{ other_user.department }}</p>
                </div>
            </div>
        </div>
        
        <!-- Messages -->
        <div class="flex-1 overflow-y-auto p-4 space-y-4" id="messages">
            {% for message in messages %}
            <div class="flex {% if message.sender_id == session.user_id %}justify-end{% else %}justify-start{% endif %}">
                <div class="max-w-xs lg:max-w-md px-4 py-2 rounded-lg {% if message.sender_id == session.user_id %}bg-blue-500 text-white{% else %}bg-white text-gray-800 shadow-sm{% endif %}">
                    <p class="text-sm">{{ message.content }}</p>
                    <p class="text-xs {% if message.sender_id == session.user_id %}text-blue-100{% else %}text-gray-500{% endif %} mt-1">
                        {{ message.sent_at[11:16] }}
                    </p>
                </div>
            </div>
            {% endfor %}
        </div>
        
        <!-- Message Input -->
        <div class="bg-white border-t border-gray-200 px-4 py-3">
            <form id="messageForm" class="flex space-x-3">
                <input type="text" id="messageInput" name="message" placeholder="Type a message..." required
                       class="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent">
                <button type="submit" 
                        class="bg-red-500 text-white px-4 py-2 rounded-lg hover:bg-red-600 transition-colors">
                    <i class="fas fa-paper-plane"></i>
                </button>
            </form>
        </div>
    </div>
    
    <script>
        // Auto-scroll to bottom
        const messagesDiv = document.getElementById('messages');
        messagesDiv.scrollTop = messagesDiv.scrollHeight;
        
        // Real-time message updates
        let lastMessageTime = '{{ messages[-1].sent_at if messages else "" }}';
        let isPolling = true;
        let loadedMessageIds = new Set();
        
        // Initialize loaded message IDs from existing messages
        {% for message in messages %}
        loadedMessageIds.add('{{ message.id }}');
        {% endfor %}
        
        function loadNewMessages() {
            if (!isPolling) return;
            
            fetch(`{{ url_for('get_messages', user_id=other_user.id) }}?last_time=${encodeURIComponent(lastMessageTime)}`)
                .then(response => {
                    if (!response.ok) {
                        throw new Error('Network response was not ok');
                    }
                    return response.json();
                })
                .then(data => {
                    if (data.messages && data.messages.length > 0) {
                        const messagesContainer = document.getElementById('messages');
                        let newMessagesAdded = false;
                        
                        data.messages.forEach(message => {
                            // Check if message is already loaded
                            if (loadedMessageIds.has(message.id)) {
                                return; // Skip already loaded messages
                            }
                            
                            // Add message ID to loaded set
                            loadedMessageIds.add(message.id);
                            
                            const messageDiv = document.createElement('div');
                            messageDiv.className = `flex ${message.sender_id === '{{ session.user_id }}' ? 'justify-end' : 'justify-start'}`;
                            
                            messageDiv.innerHTML = `
                                <div class="max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${message.sender_id === '{{ session.user_id }}' ? 'bg-blue-500 text-white' : 'bg-white text-gray-800 shadow-sm'}">
                                    <p class="text-sm">${message.content}</p>
                                    <p class="text-xs ${message.sender_id === '{{ session.user_id }}' ? 'text-blue-100' : 'text-gray-500'} mt-1">
                                        ${message.sent_at.substring(11, 16)}
                                    </p>
                                </div>
                            `;
                            
                            messagesContainer.appendChild(messageDiv);
                            newMessagesAdded = true;
                        });
                        
                        if (newMessagesAdded) {
                            // Update last message time only if new messages were added
                            lastMessageTime = data.messages[data.messages.length - 1].sent_at;
                            
                            // Auto-scroll to bottom
                            messagesContainer.scrollTop = messagesContainer.scrollHeight;
                        }
                    }
                })
                .catch(error => {
                    console.error('Error loading messages:', error);
                    // Stop polling on error to prevent spam
                    isPolling = false;
                    setTimeout(() => { isPolling = true; }, 5000); // Resume after 5 seconds
                });
        }
        
        // Load new messages every 1 second for faster updates
        setInterval(loadNewMessages, 1000);
        
        // Also load new messages when the page becomes visible
        document.addEventListener('visibilitychange', function() {
            if (!document.hidden) {
                loadNewMessages();
            }
        });
        
        // Handle message form submission
        document.getElementById('messageForm').addEventListener('submit', function(e) {
            e.preventDefault();
            
            const messageInput = document.getElementById('messageInput');
            const message = messageInput.value.trim();
            
            if (!message) return;
            
            // Store the message for immediate display
            const tempMessage = message;
            
            // Clear input immediately
            messageInput.value = '';
            
            // Add message to chat immediately (optimistic update)
            const messagesContainer = document.getElementById('messages');
            const messageDiv = document.createElement('div');
            messageDiv.className = 'flex justify-end';
            messageDiv.id = 'temp-message';
            
            messageDiv.innerHTML = `
                <div class="max-w-xs lg:max-w-md px-4 py-2 rounded-lg bg-blue-500 text-white opacity-75">
                    <p class="text-sm">${tempMessage}</p>
                    <p class="text-xs text-blue-100 mt-1">
                        Sending...
                    </p>
                </div>
            `;
            
            messagesContainer.appendChild(messageDiv);
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
            
            // Send message via AJAX
            fetch('{{ url_for("send_message", receiver_id=other_user.id) }}', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: `message=${encodeURIComponent(tempMessage)}`
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(data => {
                if (data.success) {
                    // Add the message ID to loaded set to prevent duplicates
                    loadedMessageIds.add(data.message.id);
                    
                    // Update the temporary message with real data
                    messageDiv.innerHTML = `
                        <div class="max-w-xs lg:max-w-md px-4 py-2 rounded-lg bg-blue-500 text-white">
                            <p class="text-sm">${data.message.content}</p>
                            <p class="text-xs text-blue-100 mt-1">
                                ${data.message.sent_at.substring(11, 16)}
                            </p>
                        </div>
                    `;
                    
                    // Update last message time
                    lastMessageTime = data.message.sent_at;
                } else {
                    // Show error and restore message to input
                    console.error('Error sending message:', data.error);
                    messageInput.value = tempMessage;
                    messageDiv.remove();
                }
            })
            .catch(error => {
                console.error('Error sending message:', error);
                // Show error and restore message to input
                messageInput.value = tempMessage;
                messageDiv.remove();
            });
        });
    </script>
    {% endblock %}
    ''', other_user=other_user, messages=messages)

@app.route('/send-message/<receiver_id>', methods=['POST'])
def send_message(receiver_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    message_content = request.form.get('message', '').strip()
    if not message_content:
        flash('Message cannot be empty', 'error')
        return redirect(url_for('chat', user_id=receiver_id))
    
    current_user_id = session['user_id']
    
    # Check if users can chat
    matches_result = supabase.table('matches').select('*').or_(f'user1_id.eq.{current_user_id},user2_id.eq.{current_user_id}').or_(f'user1_id.eq.{receiver_id},user2_id.eq.{receiver_id}').execute()
    
    can_chat = False
    for match in matches_result.data:
        if (match['user1_id'] == current_user_id and match['user2_id'] == receiver_id) or \
           (match['user1_id'] == receiver_id and match['user2_id'] == current_user_id):
            can_chat = True
            break
    
    if not can_chat:
        # Check if there's an accepted chat request
        chat_requests_result = supabase.table('chat_requests').select('*').or_(f'requester_id.eq.{current_user_id},receiver_id.eq.{current_user_id}').or_(f'requester_id.eq.{receiver_id},receiver_id.eq.{receiver_id}').eq('status', 'accepted').execute()
        
        for chat_request in chat_requests_result.data:
            if (chat_request['requester_id'] == current_user_id and chat_request['receiver_id'] == receiver_id) or \
               (chat_request['requester_id'] == receiver_id and chat_request['receiver_id'] == current_user_id):
                can_chat = True
                break
    
    if not can_chat:
        flash('You can only send messages to matched users or accepted chat requests', 'error')
        return redirect(url_for('dashboard'))
    
    # Send message
    try:
        result = supabase.table('messages').insert({
            'sender_id': current_user_id,
            'receiver_id': receiver_id,
            'content': message_content
        }).execute()
        
        if result.data:
            # Return the new message data
            new_message = result.data[0]
            return jsonify({
                'success': True,
                'message': {
                    'id': new_message['id'],
                    'content': new_message['content'],
                    'sent_at': new_message['sent_at'],
                    'sender_id': new_message['sender_id'],
                    'receiver_id': new_message['receiver_id']
                }
            })
        else:
            return jsonify({'error': 'Failed to send message'}), 500
            
    except Exception as e:
        return jsonify({'error': 'Error sending message'}), 500

@app.route('/get-messages/<user_id>')
def get_messages(user_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    current_user_id = session['user_id']
    last_time = request.args.get('last_time', '')
    
    # Check if users can chat
    matches_result = supabase.table('matches').select('*').or_(f'user1_id.eq.{current_user_id},user2_id.eq.{current_user_id}').or_(f'user1_id.eq.{user_id},user2_id.eq.{user_id}').execute()
    
    can_chat = False
    for match in matches_result.data:
        if (match['user1_id'] == current_user_id and match['user2_id'] == user_id) or \
           (match['user1_id'] == user_id and match['user2_id'] == current_user_id):
            can_chat = True
            break
    
    if not can_chat:
        # Check if there's an accepted chat request
        chat_requests_result = supabase.table('chat_requests').select('*').or_(f'requester_id.eq.{current_user_id},receiver_id.eq.{current_user_id}').or_(f'requester_id.eq.{user_id},receiver_id.eq.{user_id}').eq('status', 'accepted').execute()
        
        for chat_request in chat_requests_result.data:
            if (chat_request['requester_id'] == current_user_id and chat_request['receiver_id'] == user_id) or \
               (chat_request['requester_id'] == user_id and chat_request['receiver_id'] == current_user_id):
                can_chat = True
                break
    
    if not can_chat:
        return jsonify({'error': 'Cannot access messages'}), 403
    
    # Get messages after the last_time
    query = supabase.table('messages').select('*, users!messages_sender_id_fkey(*)').or_(f'sender_id.eq.{current_user_id},receiver_id.eq.{current_user_id}').or_(f'sender_id.eq.{user_id},receiver_id.eq.{user_id}').order('sent_at', desc=False)
    
    if last_time and last_time.strip():
        # Clean the timestamp format for Supabase
        try:
            # Remove timezone info and format properly
            clean_time = last_time.split('+')[0].split('.')[0] + 'Z'
            query = query.gt('sent_at', clean_time)
        except:
            # If timestamp parsing fails, don't get any messages to avoid duplicates
            return jsonify({'messages': []})
    else:
        # If no last_time, don't get any messages to avoid loading all messages
        return jsonify({'messages': []})
    
    messages_result = query.execute()
    
    messages = []
    for message in messages_result.data:
        if 'users' in message:
            user_data = message['users']
            message_data = {
                'id': message['id'],
                'content': message['content'],
                'sent_at': message['sent_at'],
                'is_read': message['is_read'],
                'sender_id': message['sender_id'],
                'receiver_id': message['receiver_id'],
                'name': user_data['name'],
                'profile_photo': user_data['profile_photo']
            }
            messages.append(message_data)
    
    # Mark messages as read
    try:
        supabase.table('messages').update({'is_read': True}).eq('sender_id', user_id).eq('receiver_id', current_user_id).eq('is_read', False).execute()
    except Exception as e:
        pass
    
    return jsonify({'messages': messages})

@app.route('/request-chat/<user_id>')
def request_chat(user_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if session['user_id'] == user_id:
        flash('You cannot request chat with yourself', 'error')
        return redirect(url_for('dashboard'))
    
    current_user_id = session['user_id']
    
    # Check if request already exists
    existing_request_result = supabase.table('chat_requests').select('*').eq('requester_id', current_user_id).eq('receiver_id', user_id).execute()
    
    if existing_request_result.data:
        flash('Chat request already sent', 'info')
    else:
        # Create chat request
        try:
            supabase.table('chat_requests').insert({
                'requester_id': current_user_id,
                'receiver_id': user_id
            }).execute()
            
            # Get user names for notification
            requester_result = supabase.table('users').select('name').eq('id', current_user_id).execute()
            receiver_result = supabase.table('users').select('name').eq('id', user_id).execute()
            
            requester_name = requester_result.data[0]['name'] if requester_result.data else 'Someone'
            receiver_name = receiver_result.data[0]['name'] if receiver_result.data else 'Someone'
            
            # Create notification for the receiver
            supabase.table('notifications').insert({
                'user_id': user_id,
                'from_user_id': current_user_id,
                'type': 'chat_request',
                'message': f'{requester_name} wants to chat with you! 💬'
            }).execute()
            
            flash('Chat request sent! 📬', 'success')
        except Exception as e:
            flash('Error sending chat request', 'error')
    
    return redirect(url_for('dashboard'))

@app.route('/accept-like-and-chat/<user_id>')
def accept_like_and_chat(user_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    current_user_id = session['user_id']
    
    # Create a match between the two users
    user1_id = min(current_user_id, user_id)
    user2_id = max(current_user_id, user_id)
    
    try:
        # Create match
        supabase.table('matches').insert({'user1_id': user1_id, 'user2_id': user2_id}).execute()
        
        # Get user names for notifications
        user1_result = supabase.table('users').select('name').eq('id', user1_id).execute()
        user2_result = supabase.table('users').select('name').eq('id', user2_id).execute()
        
        user1_name = user1_result.data[0]['name'] if user1_result.data else 'Someone'
        user2_name = user2_result.data[0]['name'] if user2_result.data else 'Someone'
        
        # Create match notifications for both users
        supabase.table('notifications').insert([
            {
                'user_id': user1_id,
                'from_user_id': user2_id,
                'type': 'match',
                'message': f'It\'s a match with {user2_name}! 💖'
            },
            {
                'user_id': user2_id,
                'from_user_id': user1_id,
                'type': 'match',
                'message': f'It\'s a match with {user1_name}! 💖'
            }
        ]).execute()
        
        flash('It\'s a match! 💖 You can now chat!', 'success')
        
    except Exception as e:
        # Match might already exist, that's okay
        pass
    
    # Redirect to chat with the person who liked you
    return redirect(url_for('chat', user_id=user_id))

@app.route('/accept-chat-and-start-chat/<user_id>')
def accept_chat_and_start_chat(user_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    current_user_id = session['user_id']
    
    # Update any pending chat requests to accepted
    try:
        supabase.table('chat_requests').update({
            'status': 'accepted',
            'updated_at': datetime.now().isoformat()
        }).or_(f'requester_id.eq.{current_user_id},receiver_id.eq.{current_user_id}').or_(f'requester_id.eq.{user_id},receiver_id.eq.{user_id}').eq('status', 'pending').execute()
        
        # Create a match if it doesn't exist
        user1_id = min(current_user_id, user_id)
        user2_id = max(current_user_id, user_id)
        
        supabase.table('matches').insert({'user1_id': user1_id, 'user2_id': user2_id}).execute()
        
        # Get user names for notification
        requester_result = supabase.table('users').select('name').eq('id', user_id).execute()
        requester_name = requester_result.data[0]['name'] if requester_result.data else 'Someone'
        
        # Create notification for the other person
        supabase.table('notifications').insert({
            'user_id': user_id,
            'from_user_id': current_user_id,
            'type': 'chat_accepted',
            'message': f'{requester_name} accepted your chat request! 💬'
        }).execute()
        
        flash('Chat request accepted! You can now chat! 💬', 'success')
        
    except Exception as e:
        # Request might already be accepted, that's okay
        pass
    
    # Redirect to chat with the person
    return redirect(url_for('chat', user_id=user_id))

@app.route('/chats')
def chats():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    current_user_id = session['user_id']
    
    # Get all users the current user can chat with (matches + accepted chat requests)
    # First get matches
    matches_result = supabase.table('matches').select('*').or_(f'user1_id.eq.{current_user_id},user2_id.eq.{current_user_id}').execute()
    
    # Get accepted chat requests
    chat_requests_result = supabase.table('chat_requests').select('*').or_(f'requester_id.eq.{current_user_id},receiver_id.eq.{current_user_id}').eq('status', 'accepted').execute()
    
    # Collect all user IDs that can be chatted with
    chat_user_ids = set()
    for match in matches_result.data:
        other_id = match['user2_id'] if match['user1_id'] == current_user_id else match['user1_id']
        chat_user_ids.add(other_id)
    
    for request in chat_requests_result.data:
        other_id = request['receiver_id'] if request['requester_id'] == current_user_id else request['requester_id']
        chat_user_ids.add(other_id)
    
    # Get user details and message info
    chat_users = []
    for user_id in chat_user_ids:
        if user_id == current_user_id:
            continue
            
        # Get user details
        user_result = supabase.table('users').select('*').eq('id', user_id).execute()
        if not user_result.data:
            continue
            
        user_data = user_result.data[0]
        
        # Get unread count
        unread_result = supabase.table('messages').select('*', count='exact').eq('sender_id', user_id).eq('receiver_id', current_user_id).eq('is_read', False).execute()
        unread_count = len(unread_result.data) if unread_result.data else 0
        
        # Get last message
        last_message_result = supabase.table('messages').select('*').or_(f'sender_id.eq.{user_id},receiver_id.eq.{user_id}').or_(f'sender_id.eq.{current_user_id},receiver_id.eq.{current_user_id}').order('sent_at', desc=True).limit(1).execute()
        
        last_message = None
        last_message_time = None
        if last_message_result.data:
            last_message = last_message_result.data[0]['content']
            last_message_time = last_message_result.data[0]['sent_at']
        
        # Check if it's a match
        is_match = any((match['user1_id'] == current_user_id and match['user2_id'] == user_id) or 
                      (match['user1_id'] == user_id and match['user2_id'] == current_user_id) 
                      for match in matches_result.data)
        
        chat_user = {
            'user_id': user_id,
            'name': user_data['name'],
            'profile_photo': user_data['profile_photo'],
            'department': user_data['department'],
            'unread_count': unread_count,
            'last_message': last_message,
            'last_message_time': last_message_time,
            'is_match': is_match
        }
        chat_users.append(chat_user)
    
    # Sort by last message time
    chat_users.sort(key=lambda x: x['last_message_time'] or '', reverse=True)
    
    return render_template('chat_list.html', chat_list=chat_users)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8000)