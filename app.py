# Fall In - University Dating App (FIXED VERSION)
# Complete Flask Application with Debug Routes

import os
import secrets
import uuid
import base64
from datetime import datetime, timedelta, timezone
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






# Main Routes
@app.route('/')
def index():
    # Check if Supabase is configured
    if not supabase:
        return redirect(url_for('setup'))
    
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
                
            </div>
        </div>
    </div>
    {% endblock %}
    ''')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    # Check if Supabase is configured
    if not supabase:
        return redirect(url_for('setup'))
    
    if request.method == 'POST':
        email = request.form['email'].lower().strip()
        
        try:
            # Check if user already exists
            existing_user_result = supabase.table('users').select('*').eq('email', email).execute()
        except Exception as e:
            flash(f'Database connection error: {str(e)}. Please check your configuration.', 'error')
            return render_template('signup.html')
        
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
    # Check if Supabase is configured
    if not supabase:
        return redirect(url_for('setup'))
    
    if request.method == 'POST':
        email = request.form['email'].lower().strip()
        
        try:
            # Find user by email
            user_result = supabase.table('users').select('*').eq('email', email).execute()
        except Exception as e:
            flash(f'Database connection error: {str(e)}. Please check your configuration.', 'error')
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
    # Check if Supabase is configured
    if not supabase:
        return redirect(url_for('setup'))
    
    if 'login_email' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        otp = request.form['otp']
        email = session['login_email']
        
        try:
            # Find user with matching email, OTP, and non-expired OTP
            user_result = supabase.table('users').select('*').eq('email', email).eq('otp_code', otp).gt('otp_expires', datetime.now().isoformat()).execute()
        except Exception as e:
            flash(f'Database connection error: {str(e)}. Please check your configuration.', 'error')
            return redirect(url_for('login'))
        
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
    
    # Check if Supabase is configured
    if not supabase:
        flash('Database not configured. Please set up Supabase credentials in .env file.', 'error')
        return render_template('dashboard.html', user=None, potential_matches=[])
    
    try:
        # Get user data
        user_result = supabase.table('users').select('*').eq('id', session['user_id']).execute()
        if not user_result.data:
            return redirect(url_for('login'))
    except Exception as e:
        flash(f'Database connection error: {str(e)}. Please check your Supabase configuration.', 'error')
        return render_template('dashboard.html', user=None, potential_matches=[])
    
    user = user_result.data[0]
    
    if not user['name']:
        return redirect(url_for('create_profile'))
    
    try:
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
    except Exception as e:
        flash(f'Error loading dashboard: {str(e)}', 'error')
        return render_template('dashboard.html', user=user, potential_matches=[])

@app.route('/like/<user_id>')
def like_user(user_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # Check if Supabase is configured
    if not supabase:
        flash('Database not configured. Please set up Supabase credentials in .env file.', 'error')
        return redirect(url_for('dashboard'))
    
    current_user_id = session['user_id']
    
    if current_user_id == user_id:
        flash('You cannot like yourself!', 'error')
        return redirect(url_for('dashboard'))
    
    try:
        # Check if already liked
        existing_like = supabase.table('likes').select('*').eq('liker_id', current_user_id).eq('liked_id', user_id).execute()
        
        if existing_like.data:
            flash('You already liked this person!', 'info')
            return redirect(url_for('dashboard'))
        
        # Add the like
        supabase.table('likes').insert({
            'liker_id': current_user_id,
            'liked_id': user_id
        }).execute()
        
        # Check if it's a mutual like (match)
        mutual_like = supabase.table('likes').select('*').eq('liker_id', user_id).eq('liked_id', current_user_id).execute()
        
        if mutual_like.data:
            # It's a match! Create match record
            user1_id = min(current_user_id, user_id)
            user2_id = max(current_user_id, user_id)
            
            supabase.table('matches').insert({
                'user1_id': user1_id,
                'user2_id': user2_id
            }).execute()
            
            # Get user names
            current_user_result = supabase.table('users').select('name').eq('id', current_user_id).execute()
            other_user_result = supabase.table('users').select('name').eq('id', user_id).execute()
            
            current_user_name = current_user_result.data[0]['name'] if current_user_result.data else 'Someone'
            other_user_name = other_user_result.data[0]['name'] if other_user_result.data else 'Someone'
            
            # Delete all existing notifications between these users
            supabase.table('notifications').delete().or_(f'user_id.eq.{current_user_id},from_user_id.eq.{user_id}').execute()
            supabase.table('notifications').delete().or_(f'user_id.eq.{user_id},from_user_id.eq.{current_user_id}').execute()
            
            # Create match notifications
            supabase.table('notifications').insert([
                {
                    'user_id': current_user_id,
                    'from_user_id': user_id,
                    'type': 'match',
                    'message': f'It\'s a match with {other_user_name}! 💕'
                },
                {
                    'user_id': user_id,
                    'from_user_id': current_user_id,
                    'type': 'match',
                    'message': f'It\'s a match with {current_user_name}! 💕'
                }
            ]).execute()
            
            flash(f'It\'s a match with {other_user_name}! 💕', 'success')
        else:
            # Just a like, create notification
            current_user_result = supabase.table('users').select('name').eq('id', current_user_id).execute()
            current_user_name = current_user_result.data[0]['name'] if current_user_result.data else 'Someone'
            
            # Delete any existing like notifications from this user to avoid duplicates
            supabase.table('notifications').delete().eq('user_id', user_id).eq('from_user_id', current_user_id).eq('type', 'like').execute()
            
            # Create like notification
            supabase.table('notifications').insert({
                'user_id': user_id,
                'from_user_id': current_user_id,
                'type': 'like',
                'message': f'{current_user_name} liked your profile! 💖'
            }).execute()
            
            flash('Profile liked! 💖', 'success')
        
    except Exception as e:
        flash('Error processing like', 'error')
    
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
    
    # Check if Supabase is configured
    if not supabase:
        flash('Database not configured. Please set up Supabase credentials in .env file.', 'error')
        return render_template('chat_list.html', matches=[])
    
    user_id = session['user_id']
    
    try:
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
    except Exception as e:
        flash(f'Error loading matches: {str(e)}', 'error')
        user_matches = []
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
                            
                            <div class="flex space-x-2">
                                <a href="{{ url_for('chat', user_id=match.match_id) }}" class="btn-primary text-white px-4 py-2 rounded-lg text-sm">
                                    Chat
                                </a>
                                <button onclick="removeConnection('{{ match.match_id }}', '{{ match.name }}')" 
                                        class="bg-red-500 hover:bg-red-600 text-white px-3 py-2 rounded-lg text-sm transition-colors">
                                    <i class="fas fa-times"></i>
                                </button>
                            </div>
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
    
    <script>
    function removeConnection(userId, userName) {
        // Create custom modal
        const modal = document.createElement('div');
        modal.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50';
        modal.innerHTML = `
            <div class="bg-white rounded-2xl p-6 mx-4 max-w-sm w-full transform transition-all duration-300 scale-95 opacity-0">
                <div class="text-center">
                    <div class="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
                        <i class="fas fa-exclamation-triangle text-2xl text-red-500"></i>
                    </div>
                    <h3 class="text-lg font-bold text-gray-800 mb-2">Remove Connection</h3>
                    <p class="text-gray-600 mb-6">Are you sure you want to remove <span class="font-semibold text-pink-600">${userName}</span> from your connections? This action cannot be undone.</p>
                    
                    <div class="flex space-x-3">
                        <button onclick="closeModal()" class="flex-1 bg-gray-200 hover:bg-gray-300 text-gray-800 px-4 py-3 rounded-xl font-semibold transition-colors">
                            Cancel
                        </button>
                        <button onclick="confirmRemove('${userId}', '${userName}')" class="flex-1 bg-red-500 hover:bg-red-600 text-white px-4 py-3 rounded-xl font-semibold transition-colors">
                            Remove
                        </button>
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        
        // Animate in
        setTimeout(() => {
            const dialog = modal.querySelector('.bg-white');
            dialog.classList.remove('scale-95', 'opacity-0');
            dialog.classList.add('scale-100', 'opacity-100');
        }, 10);
        
        // Close on backdrop click
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                closeModal();
            }
        });
        
        // Close on escape key
        document.addEventListener('keydown', function escapeHandler(e) {
            if (e.key === 'Escape') {
                closeModal();
                document.removeEventListener('keydown', escapeHandler);
            }
        });
    }
    
    function closeModal() {
        const modal = document.querySelector('.fixed.inset-0.bg-black.bg-opacity-50');
        if (modal) {
            const dialog = modal.querySelector('.bg-white');
            dialog.classList.add('scale-95', 'opacity-0');
            setTimeout(() => {
                modal.remove();
            }, 300);
        }
    }
    
    function confirmRemove(userId, userName) {
        closeModal();
        
        fetch(`/unmatch/${userId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Remove the match card from the UI
                const matchCard = document.querySelector(`[onclick*="${userId}"]`).closest('.bg-white');
                matchCard.style.transform = 'translateX(-100%)';
                matchCard.style.opacity = '0';
                setTimeout(() => {
                    matchCard.remove();
                    // Update the connection count
                    const countElement = document.querySelector('.text-gray-600');
                    const currentCount = parseInt(countElement.textContent.split(' ')[0]);
                    const newCount = currentCount - 1;
                    countElement.textContent = `${newCount} connection${newCount !== 1 ? 's' : ''}`;
                    
                    // Show empty state if no more matches
                    if (newCount === 0) {
                        location.reload();
                    }
                }, 300);
                
                // Show success message
                showSuccessMessage('Connection removed successfully');
            } else {
                showErrorMessage(data.error || 'Failed to remove connection');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showErrorMessage('Network error. Please try again.');
        });
    }
    
    function showSuccessMessage(message) {
        const toast = document.createElement('div');
        toast.className = 'fixed top-24 right-4 z-50 bg-green-500 text-white px-6 py-3 rounded-xl shadow-lg transform translate-x-full transition-transform duration-300';
        toast.innerHTML = `
            <div class="flex items-center space-x-2">
                <i class="fas fa-check-circle"></i>
                <span>${message}</span>
            </div>
        `;
        document.body.appendChild(toast);
        
        setTimeout(() => {
            toast.classList.remove('translate-x-full');
        }, 100);
        
        setTimeout(() => {
            toast.classList.add('translate-x-full');
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }
    
    function showErrorMessage(message) {
        const toast = document.createElement('div');
        toast.className = 'fixed top-24 right-4 z-50 bg-red-500 text-white px-6 py-3 rounded-xl shadow-lg transform translate-x-full transition-transform duration-300';
        toast.innerHTML = `
            <div class="flex items-center space-x-2">
                <i class="fas fa-exclamation-circle"></i>
                <span>${message}</span>
            </div>
        `;
        document.body.appendChild(toast);
        
        setTimeout(() => {
            toast.classList.remove('translate-x-full');
        }, 100);
        
        setTimeout(() => {
            toast.classList.add('translate-x-full');
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }
    </script>
    {% endblock %}
    ''', matches=user_matches)

@app.route('/unmatch/<user_id>', methods=['POST'])
def unmatch_user(user_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    current_user_id = session['user_id']
    
    try:
        # Find the match record
        match_result = supabase.table('matches').select('*').or_(f'user1_id.eq.{current_user_id},user2_id.eq.{current_user_id}').or_(f'user1_id.eq.{user_id},user2_id.eq.{user_id}').execute()
        
        if not match_result.data:
            return jsonify({'error': 'Match not found'}), 404
        
        # Delete the match
        match_id = match_result.data[0]['id']
        supabase.table('matches').delete().eq('id', match_id).execute()
        
        # Delete all notifications between these users
        supabase.table('notifications').delete().or_(f'user_id.eq.{current_user_id},from_user_id.eq.{user_id}').execute()
        supabase.table('notifications').delete().or_(f'user_id.eq.{user_id},from_user_id.eq.{current_user_id}').execute()
        
        # Also delete any chat requests between these users
        supabase.table('chat_requests').delete().or_(f'requester_id.eq.{current_user_id},receiver_id.eq.{current_user_id}').or_(f'requester_id.eq.{user_id},receiver_id.eq.{user_id}').execute()
        
        # Delete all messages between these users
        supabase.table('messages').delete().or_(f'sender_id.eq.{current_user_id},receiver_id.eq.{current_user_id}').or_(f'sender_id.eq.{user_id},receiver_id.eq.{user_id}').execute()
        
        # Delete likes between these users
        supabase.table('likes').delete().or_(f'liker_id.eq.{current_user_id},liked_id.eq.{current_user_id}').or_(f'liker_id.eq.{user_id},liked_id.eq.{user_id}').execute()
        
        return jsonify({
            'success': True,
            'message': 'Connection removed successfully'
        })
        
    except Exception as e:
        return jsonify({'error': 'Server error'}), 500

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
                <a href="/edit-profile" class="block w-full btn-primary text-white py-3 rounded-xl font-semibold text-center">
                    Edit Profile
                </a>
                <a href="{{ url_for('dashboard') }}" class="block w-full bg-gray-200 text-gray-700 text-center py-3 rounded-xl font-semibold hover:bg-gray-300 transition-colors">
                    Back to Discover
                </a>
            </div>
        </div>
    </div>
    {% endblock %}
    ''', user=user, prompts=prompts)

@app.route('/edit-profile', methods=['GET', 'POST'])
def edit_profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # Get user data
    user_result = supabase.table('users').select('*').eq('id', session['user_id']).execute()
    if not user_result.data:
        return redirect(url_for('login'))
    
    user = user_result.data[0]
    
    if request.method == 'POST':
        name = request.form['name']
        age = request.form['age']
        pronouns = request.form['pronouns']
        department = request.form['department']
        year = request.form['year']
        looking_for = request.form['looking_for']
        bio = request.form['bio']
        
        # Handle file upload - convert to base64 and store in database
        profile_photo = user.get('profile_photo')  # Keep existing photo if no new one uploaded
        if 'profile_photo' in request.files:
            file = request.files['profile_photo']
            if file and allowed_file(file.filename):
                # Convert image to base64
                profile_photo = image_to_base64(file)
                if not profile_photo:
                    flash('Error processing image. Please try again.', 'error')
                    return redirect(url_for('edit_profile'))
        
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
        
        # Delete existing prompts
        supabase.table('user_prompts').delete().eq('user_id', session['user_id']).execute()
        
        # Add new prompts
        for question, answer in prompts:
            if answer:
                supabase.table('user_prompts').insert({
                    'user_id': session['user_id'],
                    'prompt_question': question,
                    'prompt_answer': answer
                }).execute()
        
        flash('Profile updated successfully! 🎉', 'success')
        return redirect(url_for('profile'))
    
    # Get user prompts for pre-filling the form
    prompts_result = supabase.table('user_prompts').select('*').eq('user_id', session['user_id']).execute()
    prompts = {p['prompt_question']: p['prompt_answer'] for p in prompts_result.data}
    
    return render_template_string('''
    {% extends "base.html" %}
    {% block content %}
    <div class="bg-gray-50 min-h-screen py-8">
        <div class="max-w-md mx-auto px-4">
            <div class="text-center mb-8 slide-up">
                <h1 class="text-2xl font-bold text-gray-800">Edit Your Profile</h1>
                <p class="text-gray-600 mt-2">Update your information</p>
            </div>
            
            <form method="POST" enctype="multipart/form-data" class="space-y-6">
                <div class="bg-white rounded-xl p-6 shadow-sm slide-up">
                    <h3 class="font-semibold text-gray-800 mb-4">Profile Photo</h3>
                    <input type="file" name="profile_photo" accept="image/*" 
                           class="w-full px-4 py-3 border border-gray-300 rounded-xl">
                    {% if user.profile_photo %}
                    <p class="text-xs text-gray-500 mt-2">Current photo will be kept if no new photo is selected</p>
                    {% endif %}
                </div>
                
                <div class="bg-white rounded-xl p-6 shadow-sm space-y-4 slide-up">
                    <h3 class="font-semibold text-gray-800 mb-4">Basic Info</h3>
                    
                    <input type="text" name="name" required placeholder="Your Name" value="{{ user.name or '' }}"
                           class="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-red-500">
                    
                    <div class="grid grid-cols-2 gap-4">
                        <input type="number" name="age" required min="18" max="100" placeholder="Age" value="{{ user.age or '' }}"
                               class="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-red-500">
                        
                        <select name="pronouns" required 
                                class="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-red-500">
                            <option value="">Pronouns</option>
                            <option value="she/her" {% if user.pronouns == 'she/her' %}selected{% endif %}>she/her</option>
                            <option value="he/him" {% if user.pronouns == 'he/him' %}selected{% endif %}>he/him</option>
                            <option value="they/them" {% if user.pronouns == 'they/them' %}selected{% endif %}>they/them</option>
                            <option value="other" {% if user.pronouns == 'other' %}selected{% endif %}>other</option>
                        </select>
                    </div>
                    
                    <input type="text" name="department" required placeholder="Department (e.g., Computer Science)" value="{{ user.department or '' }}"
                           class="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-red-500">
                    
                    <select name="year" required 
                            class="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-red-500">
                        <option value="">Year</option>
                        <option value="Freshman" {% if user.year == 'Freshman' %}selected{% endif %}>Freshman</option>
                        <option value="Sophomore" {% if user.year == 'Sophomore' %}selected{% endif %}>Sophomore</option>
                        <option value="Junior" {% if user.year == 'Junior' %}selected{% endif %}>Junior</option>
                        <option value="Senior" {% if user.year == 'Senior' %}selected{% endif %}>Senior</option>
                        <option value="Graduate" {% if user.year == 'Graduate' %}selected{% endif %}>Graduate</option>
                        <option value="PhD" {% if user.year == 'PhD' %}selected{% endif %}>PhD</option>
                    </select>
                    
                    <select name="looking_for" required 
                            class="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-red-500">
                        <option value="">Looking for</option>
                        <option value="friendship" {% if user.looking_for == 'friendship' %}selected{% endif %}>Friendship</option>
                        <option value="dating" {% if user.looking_for == 'dating' %}selected{% endif %}>Dating</option>
                        <option value="relationship" {% if user.looking_for == 'relationship' %}selected{% endif %}>Relationship</option>
                        <option value="networking" {% if user.looking_for == 'networking' %}selected{% endif %}>Networking</option>
                    </select>
                </div>
                
                <div class="bg-white rounded-xl p-6 shadow-sm slide-up">
                    <h3 class="font-semibold text-gray-800 mb-4">About You</h3>
                    <textarea name="bio" rows="4" placeholder="Tell people about yourself..."
                              class="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-red-500"></textarea>
                </div>
                
                <div class="bg-white rounded-xl p-6 shadow-sm space-y-4 slide-up">
                    <h3 class="font-semibold text-gray-800 mb-4">Fun Prompts</h3>
                    
                    <input type="text" name="prompt1" placeholder="What makes you laugh?" value="{{ prompts.get('What makes you laugh?', '') }}"
                           class="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-red-500">
                    
                    <input type="text" name="prompt2" placeholder="My ideal study buddy is..." value="{{ prompts.get('My ideal study buddy is...', '') }}"
                           class="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-red-500">
                    
                    <input type="text" name="prompt3" placeholder="Best campus spot?" value="{{ prompts.get('Best campus spot?', '') }}"
                           class="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-red-500">
                </div>
                
                <div class="space-y-3 slide-up">
                    <button type="submit" 
                            class="w-full btn-primary text-white py-4 rounded-xl font-semibold shadow-lg">
                        Update Profile
                    </button>
                    <a href="{{ url_for('profile') }}" class="block w-full bg-gray-200 text-gray-700 text-center py-3 rounded-xl font-semibold hover:bg-gray-300 transition-colors">
                        Cancel
                    </a>
                </div>
            </form>
        </div>
    </div>
    {% endblock %}
    ''', user=user, prompts=prompts)

@app.route('/notification-count')
def notification_count():
    if 'user_id' not in session:
        return jsonify({'count': 0})
    
    user_id = session['user_id']
    
    # Get unread notification count
    notifications_result = supabase.table('notifications').select('id').eq('user_id', user_id).eq('is_read', False).execute()
    
    count = len(notifications_result.data)
    return jsonify({'count': count})

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
    
    # Mark notifications as read
    supabase.table('notifications').update({'is_read': True}).eq('user_id', user_id).eq('is_read', False).execute()
    
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
                <div class="bg-white rounded-xl p-4 shadow-sm hover:shadow-md transition-all duration-300 slide-up {% if not notification.is_read %}border-l-4 border-red-500{% endif %}" data-notification-id="{{ notification.id }}">
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
                        <div class="flex space-x-2">
                            <span class="bg-red-500 text-white px-2 py-1 rounded-full text-xs">
                                Match! 💕
                            </span>
                            <button onclick="deleteNotification('{{ notification.id }}')" 
                                    class="bg-gray-500 hover:bg-gray-600 text-white px-2 py-1 rounded text-xs transition-colors">
                                <i class="fas fa-times"></i>
                            </button>
                        </div>
                        {% elif notification.type == 'like' %}
                        <div class="flex space-x-2">
                            <span class="bg-pink-500 text-white px-2 py-1 rounded-full text-xs">
                                Like 💖
                            </span>
                            <a href="{{ url_for('accept_like_and_chat', user_id=notification.from_user_id) }}" 
                               class="bg-green-500 text-white px-3 py-1 rounded-lg text-xs hover:bg-green-600 transition-colors">
                                Match
                            </a>
                            <button onclick="deleteNotification('{{ notification.id }}')" 
                                    class="bg-red-500 hover:bg-red-600 text-white px-2 py-1 rounded text-xs transition-colors">
                                <i class="fas fa-times"></i>
                            </button>
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
                            <button onclick="deleteNotification('{{ notification.id }}')" 
                                    class="bg-red-500 hover:bg-red-600 text-white px-2 py-1 rounded text-xs transition-colors">
                                <i class="fas fa-times"></i>
                            </button>
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
                            <button onclick="deleteNotification('{{ notification.id }}')" 
                                    class="bg-gray-500 hover:bg-gray-600 text-white px-2 py-1 rounded text-xs transition-colors">
                                <i class="fas fa-times"></i>
                            </button>
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
    
    <script>
    function deleteNotification(notificationId) {
        // Create custom modal
        const modal = document.createElement('div');
        modal.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50';
        modal.innerHTML = `
            <div class="bg-white rounded-2xl p-6 mx-4 max-w-sm w-full transform transition-all duration-300 scale-95 opacity-0">
                <div class="text-center">
                    <div class="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
                        <i class="fas fa-trash-alt text-2xl text-red-500"></i>
                    </div>
                    <h3 class="text-lg font-bold text-gray-800 mb-2">Remove Notification</h3>
                    <p class="text-gray-600 mb-6">Are you sure you want to remove this notification? This action cannot be undone.</p>
                    
                    <div class="flex space-x-3">
                        <button onclick="closeDeleteModal()" class="flex-1 bg-gray-200 hover:bg-gray-300 text-gray-800 px-4 py-3 rounded-xl font-semibold transition-colors">
                            Cancel
                        </button>
                        <button onclick="confirmDeleteNotification('${notificationId}')" class="flex-1 bg-red-500 hover:bg-red-600 text-white px-4 py-3 rounded-xl font-semibold transition-colors">
                            Remove
                        </button>
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        
        // Animate in
        setTimeout(() => {
            const dialog = modal.querySelector('.bg-white');
            dialog.classList.remove('scale-95', 'opacity-0');
            dialog.classList.add('scale-100', 'opacity-100');
        }, 10);
        
        // Close on backdrop click
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                closeDeleteModal();
            }
        });
        
        // Close on escape key
        document.addEventListener('keydown', function escapeHandler(e) {
            if (e.key === 'Escape') {
                closeDeleteModal();
                document.removeEventListener('keydown', escapeHandler);
            }
        });
    }
    
    function closeDeleteModal() {
        const modal = document.querySelector('.fixed.inset-0.bg-black.bg-opacity-50');
        if (modal) {
            const dialog = modal.querySelector('.bg-white');
            dialog.classList.add('scale-95', 'opacity-0');
            setTimeout(() => {
                modal.remove();
            }, 300);
        }
    }
    
    function confirmDeleteNotification(notificationId) {
        closeDeleteModal();
        
        fetch(`/delete-notification/${notificationId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Remove the notification card from the UI
                const notificationCard = document.querySelector(`[data-notification-id="${notificationId}"]`);
                notificationCard.style.transform = 'translateX(-100%)';
                notificationCard.style.opacity = '0';
                setTimeout(() => {
                    notificationCard.remove();
                    // Update the notification count
                    const countElement = document.querySelector('.text-gray-600');
                    const currentCount = parseInt(countElement.textContent.split(' ')[0]);
                    const newCount = currentCount - 1;
                    countElement.textContent = `${newCount} new notifications`;
                    
                    // Show empty state if no more notifications
                    if (newCount === 0 && document.querySelectorAll('.bg-white.rounded-xl').length === 0) {
                        location.reload();
                    }
                }, 300);
                
                // Show success message
                showSuccessMessage('Notification removed successfully');
            } else {
                showErrorMessage(data.error || 'Failed to remove notification');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showErrorMessage('Network error. Please try again.');
        });
    }
    
    function showSuccessMessage(message) {
        const toast = document.createElement('div');
        toast.className = 'fixed top-24 right-4 z-50 bg-green-500 text-white px-6 py-3 rounded-xl shadow-lg transform translate-x-full transition-transform duration-300';
        toast.innerHTML = `
            <div class="flex items-center space-x-2">
                <i class="fas fa-check-circle"></i>
                <span>${message}</span>
            </div>
        `;
        document.body.appendChild(toast);
        
        setTimeout(() => {
            toast.classList.remove('translate-x-full');
        }, 100);
        
        setTimeout(() => {
            toast.classList.add('translate-x-full');
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }
    
    function showErrorMessage(message) {
        const toast = document.createElement('div');
        toast.className = 'fixed top-24 right-4 z-50 bg-red-500 text-white px-6 py-3 rounded-xl shadow-lg transform translate-x-full transition-transform duration-300';
        toast.innerHTML = `
            <div class="flex items-center space-x-2">
                <i class="fas fa-exclamation-circle"></i>
                <span>${message}</span>
            </div>
        `;
        document.body.appendChild(toast);
        
        setTimeout(() => {
            toast.classList.remove('translate-x-full');
        }, 100);
        
        setTimeout(() => {
            toast.classList.add('translate-x-full');
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }
    </script>
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
            
            # Delete older notifications between these users to avoid duplicates
            supabase.table('notifications').delete().eq('user_id', request_info['requester_id']).eq('from_user_id', request_info['receiver_id']).execute()
            supabase.table('notifications').delete().eq('user_id', request_info['receiver_id']).eq('from_user_id', request_info['requester_id']).execute()
            
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
    
    current_user_id = session['user_id']
    
    try:
        # Get the chat request details
        request_result = supabase.table('chat_requests').select('*').eq('id', request_id).execute()
        if not request_result.data:
            flash('Chat request not found', 'error')
            return redirect(url_for('notifications'))
        
        chat_request = request_result.data[0]
        
        # Make sure the current user is the receiver
        if chat_request['receiver_id'] != current_user_id:
            flash('Unauthorized', 'error')
            return redirect(url_for('notifications'))
        
        # Delete the chat request
        supabase.table('chat_requests').delete().eq('id', request_id).execute()
        
        # Delete all notifications between these users related to this chat request
        supabase.table('notifications').delete().eq('user_id', current_user_id).eq('from_user_id', chat_request['requester_id']).eq('type', 'chat_request').execute()
        supabase.table('notifications').delete().eq('user_id', chat_request['requester_id']).eq('from_user_id', current_user_id).eq('type', 'chat_request').execute()
        
        flash('Chat request rejected', 'success')
        
    except Exception as e:
        flash('Error rejecting chat request', 'error')
    
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
    <style>
        /* Hide the main navbar in chat view */
        .navbar {
            display: none !important;
        }
        
        /* Chat-specific styles */
        .chat-container {
            height: 100vh;
            display: flex;
            flex-direction: column;
        }
        
        .chat-header {
            background: linear-gradient(135deg, #fdf2f8, #fce7f3);
            border-bottom: 1px solid rgba(244, 114, 182, 0.2);
            padding: 1rem;
            position: sticky;
            top: 0;
            z-index: 10;
        }
        
        .chat-header-content {
            display: flex;
            align-items: center;
            gap: 0.75rem;
            max-width: 600px;
            margin: 0 auto;
        }
        
        .back-button {
            background: rgba(255, 255, 255, 0.8);
            border-radius: 50%;
            width: 40px;
            height: 40px;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.2s ease;
            backdrop-filter: blur(10px);
        }
        
        .back-button:hover {
            background: rgba(255, 255, 255, 0.9);
            transform: scale(1.05);
        }
        
        .user-info {
            flex: 1;
            text-align: center;
        }
        
        .user-name {
            font-size: 1.25rem;
            font-weight: 700;
            color: #1f2937;
            margin-bottom: 0.25rem;
        }
        
        .user-details {
            font-size: 0.875rem;
            color: #6b7280;
        }
        
        .profile-image {
            width: 48px;
            height: 48px;
            border-radius: 50%;
            object-fit: cover;
            border: 3px solid rgba(255, 255, 255, 0.8);
            box-shadow: 0 4px 12px rgba(244, 114, 182, 0.2);
        }
        
        .messages-container {
            flex: 1;
            overflow-y: auto;
            padding: 1rem;
            background: linear-gradient(135deg, #fdf2f8, #fef3f2);
        }
        
        .message-input-container {
            background: white;
            border-top: 1px solid rgba(244, 114, 182, 0.1);
            padding: 1rem;
            position: sticky;
            bottom: 0;
        }
        
        .message-input-wrapper {
            max-width: 600px;
            margin: 0 auto;
            display: flex;
            gap: 0.75rem;
            align-items: center;
        }
        
        .message-input {
            flex: 1;
            padding: 0.75rem 1rem;
            border: 2px solid rgba(244, 114, 182, 0.2);
            border-radius: 25px;
            font-size: 0.875rem;
            transition: all 0.2s ease;
            background: white;
        }
        
        .message-input:focus {
            outline: none;
            border-color: #ec4899;
            box-shadow: 0 0 0 3px rgba(236, 72, 153, 0.1);
        }
        
        .send-button {
            background: linear-gradient(135deg, #ec4899, #be185d);
            color: white;
            border: none;
            border-radius: 50%;
            width: 44px;
            height: 44px;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.2s ease;
            box-shadow: 0 4px 12px rgba(236, 72, 153, 0.3);
        }
        
        .send-button:hover {
            transform: scale(1.05);
            box-shadow: 0 6px 16px rgba(236, 72, 153, 0.4);
        }
        
        .send-button:active {
            transform: scale(0.95);
        }
        
        /* Message bubbles */
        .message-bubble {
            max-width: 280px;
            padding: 0.75rem 1rem;
            border-radius: 18px;
            margin-bottom: 0.5rem;
            position: relative;
        }
        
        .message-bubble.sent {
            background: linear-gradient(135deg, #ec4899, #be185d);
            color: white;
            margin-left: auto;
            border-bottom-right-radius: 6px;
        }
        
        .message-bubble.received {
            background: white;
            color: #1f2937;
            margin-right: auto;
            border-bottom-left-radius: 6px;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
        }
        
        .message-time {
            font-size: 0.75rem;
            opacity: 0.7;
            margin-top: 0.25rem;
        }
        
        /* Responsive design for all devices */
        @media (max-width: 640px) {
            .chat-header {
                padding: 0.75rem;
            }
            
            .user-name {
                font-size: 1.125rem;
            }
            
            .messages-container {
                padding: 0.75rem;
            }
            
            .message-input-container {
                padding: 0.75rem;
            }
            
            .message-bubble {
                max-width: 240px;
            }
        }
        
        /* Desktop optimizations - More compact */
        @media (min-width: 768px) {
            .chat-container {
                max-width: 700px;
                margin: 0 auto;
                height: 85vh;
                border-radius: 16px;
                box-shadow: 0 15px 30px rgba(0, 0, 0, 0.1);
                margin-top: 7.5vh;
                margin-bottom: 7.5vh;
            }
            
            .chat-header {
                border-radius: 16px 16px 0 0;
                padding: 1.25rem;
            }
            
            .chat-header-content {
                max-width: 600px;
            }
            
            .user-name {
                font-size: 1.25rem;
            }
            
            .user-details {
                font-size: 0.9rem;
            }
            
            .profile-image {
                width: 48px;
                height: 48px;
            }
            
            .messages-container {
                padding: 1.25rem;
                max-height: 65vh;
            }
            
            .message-bubble {
                max-width: 350px;
                font-size: 0.9rem;
                padding: 0.875rem 1.125rem;
            }
            
            .message-input-container {
                padding: 1.25rem;
                border-radius: 0 0 16px 16px;
            }
            
            .message-input-wrapper {
                max-width: 600px;
            }
            
            .message-input {
                padding: 0.875rem 1.25rem;
                font-size: 0.9rem;
                border-radius: 25px;
            }
            
            .send-button {
                width: 48px;
                height: 48px;
                font-size: 1rem;
            }
        }
        
        /* Large desktop screens - Moderate scaling */
        @media (min-width: 1024px) {
            .chat-container {
                max-width: 800px;
            }
            
            .chat-header-content {
                max-width: 700px;
            }
            
            .message-input-wrapper {
                max-width: 700px;
            }
            
            .message-bubble {
                max-width: 400px;
            }
        }
        
        /* Extra large screens - Reasonable scaling */
        @media (min-width: 1280px) {
            .chat-container {
                max-width: 900px;
            }
            
            .chat-header-content {
                max-width: 800px;
            }
            
            .message-input-wrapper {
                max-width: 800px;
            }
            
            .message-bubble {
                max-width: 450px;
            }
        }
    </style>
    
    <div class="chat-container">
        <!-- Enhanced Chat Header -->
        <div class="chat-header">
            <div class="chat-header-content">
                <a href="{{ url_for('chats') }}" class="back-button">
                    <i class="fas fa-arrow-left text-gray-600"></i>
                </a>
                
                <div class="user-info">
                    <div class="user-name">{{ other_user.name }}</div>
                    <div class="user-details">{{ other_user.department }} • {{ other_user.year }}</div>
                </div>
                
                <div class="w-12 h-12 bg-gradient-to-br from-pink-200 to-red-200 rounded-full flex items-center justify-center flex-shrink-0">
                    {% if other_user.profile_photo %}
                        {% if other_user.profile_photo.startswith('data:image') %}
                            <img src="{{ other_user.profile_photo }}" 
                                 alt="{{ other_user.name }}" class="profile-image">
                        {% else %}
                            <img src="{{ url_for('static', filename='uploads/' + other_user.profile_photo) }}" 
                                 alt="{{ other_user.name }}" class="profile-image">
                        {% endif %}
                    {% else %}
                        <i class="fas fa-user text-lg text-gray-400"></i>
                    {% endif %}
                </div>
            </div>
        </div>
        
        <!-- Messages -->
        <div class="messages-container" id="messages">
            {% for message in messages %}
            <div class="flex {% if message.sender_id == session.user_id %}justify-end{% else %}justify-start{% endif %}">
                <div class="message-bubble {% if message.sender_id == session.user_id %}sent{% else %}received{% endif %}">
                    <p class="text-sm">{{ message.content }}</p>
                    <p class="message-time">
                        {{ message.sent_at[11:16] }}
                    </p>
                </div>
            </div>
            {% endfor %}
        </div>
        
        <!-- Message Input -->
        <div class="message-input-container">
            <form id="messageForm" class="message-input-wrapper">
                <input type="text" id="messageInput" name="message" placeholder="Type a message..." required
                       class="message-input">
                <button type="submit" class="send-button">
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
                                <div class="message-bubble ${message.sender_id === '{{ session.user_id }}' ? 'sent' : 'received'}">
                                    <p class="text-sm">${message.content}</p>
                                    <p class="message-time">
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
                <div class="message-bubble sent" style="opacity: 0.75;">
                    <p class="text-sm">${tempMessage}</p>
                    <p class="message-time">
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
                        <div class="message-bubble sent">
                            <p class="text-sm">${data.message.content}</p>
                            <p class="message-time">
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
    
    try:
        # Create match
        supabase.table('matches').insert({
            'user1_id': current_user_id,
            'user2_id': user_id
        }).execute()
        
        # Delete any existing chat requests
        supabase.table('chat_requests').delete().eq('requester_id', user_id).eq('receiver_id', current_user_id).execute()
        supabase.table('chat_requests').delete().eq('requester_id', current_user_id).eq('receiver_id', user_id).execute()
        
        # Delete all notifications between these users (like notifications, chat request notifications, etc.)
        supabase.table('notifications').delete().or_(f'user_id.eq.{current_user_id},from_user_id.eq.{user_id}').execute()
        supabase.table('notifications').delete().or_(f'user_id.eq.{user_id},from_user_id.eq.{current_user_id}').execute()
        
        # Get user names for notification
        user_result = supabase.table('users').select('name').eq('id', user_id).execute()
        user_name = user_result.data[0]['name'] if user_result.data else 'Someone'
        
        # Create new notification for the other person about the match
        supabase.table('notifications').insert({
            'user_id': user_id,
            'from_user_id': current_user_id,
            'type': 'match',
            'message': f'You matched with {user_name}! 💕'
        }).execute()
        
        flash('It\'s a match! You can now chat! 💕', 'success')
        
    except Exception as e:
        # Match might already exist, that's okay
        pass
    
    # Redirect to chat with the person
    return redirect(url_for('chat', user_id=user_id))

@app.route('/accept-chat-and-start-chat/<user_id>')
def accept_chat_and_start_chat(user_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    current_user_id = session['user_id']
    
    try:
        # Update chat request status to accepted
        supabase.table('chat_requests').update({'status': 'accepted'}).eq('requester_id', user_id).eq('receiver_id', current_user_id).execute()
        
        # Delete all notifications between these users (chat request notifications, etc.)
        supabase.table('notifications').delete().or_(f'user_id.eq.{current_user_id},from_user_id.eq.{user_id}').execute()
        supabase.table('notifications').delete().or_(f'user_id.eq.{user_id},from_user_id.eq.{current_user_id}').execute()
        
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

def time_ago(dt_str):
    try:
        dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
        now = datetime.now(timezone.utc)
        diff = (now - dt)
        seconds = diff.total_seconds()
        if seconds < 60:
            return "Just now"
        elif seconds < 3600:
            return f"{int(seconds // 60)} minutes ago"
        elif seconds < 86400:
            return f"{int(seconds // 3600)} hours ago"
        else:
            return f"{int(seconds // 86400)} days ago"
    except Exception:
        return "Recently"

@app.route('/confessions')
def confessions():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    current_user_id = session['user_id']
    category_filter = request.args.get('category', 'all')
    
    # Build query for confessions
    query = supabase.table('confessions').select('*').eq('is_approved', True).order('created_at', desc=True)
    
    # Apply category filter if specified
    if category_filter != 'all':
        query = query.eq('category', category_filter)
    
    # Get confessions
    result = query.execute()
    confessions = result.data if result.data else []
    
    # Get user's liked confessions for UI state
    user_likes_result = supabase.table('confession_likes').select('confession_id').eq('user_id', current_user_id).execute()
    user_liked_confession_ids = {like['confession_id'] for like in user_likes_result.data} if user_likes_result.data else set()
    
    # Add user like status and time_ago to confessions
    for confession in confessions:
        confession['user_liked'] = confession['id'] in user_liked_confession_ids
        confession['anonymous_letter'] = chr(65 + (hash(confession['id']) % 26))
        confession['time_ago'] = time_ago(confession['created_at'])
    
    return render_template('confessions_page.html', confessions=confessions, category_filter=category_filter)

@app.route('/post-confession', methods=['POST'])
def post_confession():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    current_user_id = session['user_id']
    content = request.form.get('content', '').strip()
    category = request.form.get('category', 'confession')
    
    if not content:
        return jsonify({'error': 'Confession content is required'}), 400
    
    # Removed character limit - allow longer confessions
    
    # Valid categories
    valid_categories = ['crush', 'missed', 'confession', 'rant', 'appreciation', 'advice']
    if category not in valid_categories:
        category = 'confession'
    
    try:
        # Insert confession
        result = supabase.table('confessions').insert({
            'user_id': current_user_id,
            'content': content,
            'category': category,
            'likes_count': 0,
            'views_count': 0,
            'is_approved': True
        }).execute()
        
        if result.data:
            confession = result.data[0]
            confession['anonymous_letter'] = chr(65 + (hash(confession['id']) % 26))
            confession['user_liked'] = False
            confession['time_ago'] = time_ago(confession['created_at'])
            
            return jsonify({
                'success': True,
                'confession': confession,
                'message': 'Confession posted successfully!'
            })
        else:
            return jsonify({'error': 'Failed to post confession'}), 500
            
    except Exception as e:
        return jsonify({'error': 'Server error'}), 500

@app.route('/post-comment', methods=['POST'])
def post_comment():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    current_user_id = session['user_id']
    confession_id = request.form.get('confession_id')
    parent_comment_id = request.form.get('parent_comment_id')  # For nested replies
    content = request.form.get('content', '').strip()
    
    if not content:
        return jsonify({'error': 'Comment content is required'}), 400
    
    if not confession_id:
        return jsonify({'error': 'Confession ID is required'}), 400
    
    try:
        # Insert comment
        comment_data = {
            'confession_id': confession_id,
            'user_id': current_user_id,
            'content': content,
            'likes_count': 0,
            'is_approved': True
        }
        
        if parent_comment_id:
            comment_data['parent_comment_id'] = parent_comment_id
        
        result = supabase.table('confession_comments').insert(comment_data).execute()
        
        if result.data:
            comment = result.data[0]
            comment['anonymous_letter'] = chr(65 + (hash(comment['id']) % 26))
            comment['user_liked'] = False
            comment['time_ago'] = time_ago(comment['created_at'])
            
            return jsonify({
                'success': True,
                'comment': comment,
                'message': 'Comment posted successfully!'
            })
        else:
            return jsonify({'error': 'Failed to post comment'}), 500
            
    except Exception as e:
        return jsonify({'error': 'Server error'}), 500

@app.route('/get-comments/<confession_id>')
def get_comments(confession_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    current_user_id = session['user_id']
    
    try:
        # Get all comments for this confession
        result = supabase.table('confession_comments').select('*').eq('confession_id', confession_id).eq('is_approved', True).order('created_at', desc=True).execute()
        comments = result.data if result.data else []
        
        # Get user's liked comments
        user_likes_result = supabase.table('comment_likes').select('comment_id').eq('user_id', current_user_id).execute()
        user_liked_comment_ids = {like['comment_id'] for like in user_likes_result.data} if user_likes_result.data else set()
        
        # Process comments
        for comment in comments:
            comment['user_liked'] = comment['id'] in user_liked_comment_ids
            comment['anonymous_letter'] = chr(65 + (hash(comment['id']) % 26))
            comment['time_ago'] = time_ago(comment['created_at'])
        
        # Organize comments into a tree structure (parent-child)
        comment_tree = []
        comment_dict = {comment['id']: comment for comment in comments}
        
        for comment in comments:
            if not comment.get('parent_comment_id'):
                # Top-level comment
                comment['replies'] = []
                comment_tree.append(comment)
            else:
                # Reply to another comment
                parent = comment_dict.get(comment['parent_comment_id'])
                if parent:
                    if 'replies' not in parent:
                        parent['replies'] = []
                    parent['replies'].append(comment)
        
        return jsonify({
            'success': True,
            'comments': comment_tree
        })
        
    except Exception as e:
        return jsonify({'error': 'Server error'}), 500

@app.route('/like-comment/<comment_id>', methods=['POST'])
def like_comment(comment_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    current_user_id = session['user_id']
    
    try:
        # Check if user already liked this comment
        existing_like = supabase.table('comment_likes').select('*').eq('comment_id', comment_id).eq('user_id', current_user_id).execute()
        
        if existing_like.data:
            # Unlike - remove the like
            supabase.table('comment_likes').delete().eq('comment_id', comment_id).eq('user_id', current_user_id).execute()
            
            # Decrease likes count
            supabase.table('confession_comments').update({'likes_count': supabase.table('confession_comments').select('likes_count').eq('id', comment_id).execute().data[0]['likes_count'] - 1}).eq('id', comment_id).execute()
            
            return jsonify({
                'success': True,
                'liked': False,
                'message': 'Comment unliked'
            })
        else:
            # Like - add the like
            supabase.table('comment_likes').insert({
                'comment_id': comment_id,
                'user_id': current_user_id
            }).execute()
            
            # Increase likes count
            supabase.table('confession_comments').update({'likes_count': supabase.table('confession_comments').select('likes_count').eq('id', comment_id).execute().data[0]['likes_count'] + 1}).eq('id', comment_id).execute()
            
            return jsonify({
                'success': True,
                'liked': True,
                'message': 'Comment liked'
            })
            
    except Exception as e:
        return jsonify({'error': 'Server error'}), 500

@app.route('/like-confession/<confession_id>', methods=['POST'])
def like_confession(confession_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    current_user_id = session['user_id']
    
    try:
        # Check if user already liked this confession
        existing_like = supabase.table('confession_likes').select('*').eq('confession_id', confession_id).eq('user_id', current_user_id).execute()
        
        if existing_like.data:
            # Unlike - remove the like
            supabase.table('confession_likes').delete().eq('confession_id', confession_id).eq('user_id', current_user_id).execute()
            
            # Decrease likes count
            supabase.table('confessions').update({'likes_count': supabase.table('confessions').select('likes_count').eq('id', confession_id).execute().data[0]['likes_count'] - 1}).eq('id', confession_id).execute()
            
            return jsonify({
                'success': True,
                'liked': False,
                'message': 'Confession unliked'
            })
        else:
            # Like - add the like
            supabase.table('confession_likes').insert({
                'confession_id': confession_id,
                'user_id': current_user_id
            }).execute()
            
            # Increase likes count
            supabase.table('confessions').update({'likes_count': supabase.table('confessions').select('likes_count').eq('id', confession_id).execute().data[0]['likes_count'] + 1}).eq('id', confession_id).execute()
            
            return jsonify({
                'success': True,
                'liked': True,
                'message': 'Confession liked'
            })
            
    except Exception as e:
        return jsonify({'error': 'Server error'}), 500

@app.route('/view-confession/<confession_id>', methods=['POST'])
def view_confession(confession_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        # Increment view count
        supabase.table('confessions').update({'views_count': supabase.table('confessions').select('views_count').eq('id', confession_id).execute().data[0]['views_count'] + 1}).eq('id', confession_id).execute()
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': 'Server error'}), 500

@app.route('/get-confessions')
def get_confessions():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    current_user_id = session['user_id']
    category_filter = request.args.get('category', 'all')
    page = int(request.args.get('page', 1))
    limit = 10
    offset = (page - 1) * limit
    
    # Build query
    query = supabase.table('confessions').select('*').eq('is_approved', True).order('created_at', desc=True).range(offset, offset + limit - 1)
    
    if category_filter != 'all':
        query = query.eq('category', category_filter)
    
    result = query.execute()
    confessions = result.data if result.data else []
    
    # Get user's liked confessions
    user_likes_result = supabase.table('confession_likes').select('confession_id').eq('user_id', current_user_id).execute()
    user_liked_confession_ids = {like['confession_id'] for like in user_likes_result.data} if user_likes_result.data else set()
    
    # Add user like status and anonymous letter
    for confession in confessions:
        confession['user_liked'] = confession['id'] in user_liked_confession_ids
        confession['anonymous_letter'] = chr(65 + (hash(confession['id']) % 26))
    
    return jsonify({
        'confessions': confessions,
        'has_more': len(confessions) == limit
    })

@app.route('/delete-notification/<notification_id>', methods=['POST'])
def delete_notification(notification_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    current_user_id = session['user_id']
    
    try:
        # Delete the notification (only if it belongs to the current user)
        result = supabase.table('notifications').delete().eq('id', notification_id).eq('user_id', current_user_id).execute()
        
        if result.data:
            return jsonify({
                'success': True,
                'message': 'Notification removed successfully'
            })
        else:
            return jsonify({'error': 'Notification not found or unauthorized'}), 404
        
    except Exception as e:
        return jsonify({'error': 'Server error'}), 500

@app.route('/setup')
def setup():
    """Setup page to help users configure the application"""
    return render_template_string('''
    {% extends "base.html" %}
    {% block content %}
    <div class="bg-gray-50 min-h-screen py-8">
        <div class="max-w-2xl mx-auto px-4">
            <div class="bg-white rounded-2xl shadow-lg p-8">
                <div class="text-center mb-8">
                    <h1 class="text-3xl font-bold text-gray-800 mb-4">Setup Required</h1>
                    <p class="text-gray-600">Your Fall In app needs to be configured before you can use it.</p>
                </div>
                
                <div class="space-y-6">
                    <div class="border-l-4 border-blue-500 pl-4">
                        <h3 class="text-lg font-semibold text-gray-800 mb-2">1. Create a .env file</h3>
                        <p class="text-gray-600 mb-2">Copy the env_template.txt file to .env in your project root:</p>
                        <code class="bg-gray-100 p-2 rounded text-sm block">cp env_template.txt .env</code>
                    </div>
                    
                    <div class="border-l-4 border-green-500 pl-4">
                        <h3 class="text-lg font-semibold text-gray-800 mb-2">2. Set up Supabase</h3>
                        <ol class="text-gray-600 space-y-1 ml-4">
                            <li>• Go to <a href="https://supabase.com" target="_blank" class="text-blue-500 hover:underline">supabase.com</a> and create a new project</li>
                            <li>• Get your project URL and anon key from Settings > API</li>
                            <li>• Update the .env file with your credentials</li>
                        </ol>
                    </div>
                    
                    <div class="border-l-4 border-purple-500 pl-4">
                        <h3 class="text-lg font-semibold text-gray-800 mb-2">3. Set up the database</h3>
                        <p class="text-gray-600 mb-2">Run the SQL schema in your Supabase SQL editor:</p>
                        <code class="bg-gray-100 p-2 rounded text-sm block">Copy and paste the contents of supabase_schema.sql</code>
                    </div>
                    
                    <div class="border-l-4 border-yellow-500 pl-4">
                        <h3 class="text-lg font-semibold text-gray-800 mb-2">4. Restart the application</h3>
                        <p class="text-gray-600">After configuring everything, restart your Flask application.</p>
                    </div>
                </div>
                
                <div class="mt-8 text-center">
                    <a href="{{ url_for('index') }}" class="btn-primary text-white px-6 py-3 rounded-xl font-semibold">
                        Go to Home
                    </a>
                </div>
            </div>
        </div>
    </div>
    {% endblock %}
    ''')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8000)