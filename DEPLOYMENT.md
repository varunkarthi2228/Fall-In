# 🚀 Deployment Guide for Fall In

## GitHub Deployment

### 1. Create GitHub Repository
1. Go to [GitHub.com](https://github.com) and sign in
2. Click the "+" icon in the top right corner
3. Select "New repository"
4. Name it: `fall-in` or `fall_in`
5. Make it **Public** (for free hosting options)
6. **Don't** initialize with README (we already have one)
7. Click "Create repository"

### 2. Connect Local Repository to GitHub
```bash
# Replace YOUR_USERNAME with your GitHub username
git remote add origin https://github.com/YOUR_USERNAME/fall-in.git
git branch -M main
git push -u origin main
```

### 3. Enable GitHub Pages (Optional)
- Go to your repository Settings
- Scroll down to "Pages"
- Select "Deploy from a branch"
- Choose "main" branch
- Save

## 🐍 Python Anywhere Deployment

### 1. Sign up at PythonAnywhere
- Go to [www.pythonanywhere.com](https://www.pythonanywhere.com)
- Create a free account

### 2. Upload Your Code
```bash
# Clone your repository
git clone https://github.com/YOUR_USERNAME/fall-in.git
```

### 3. Set Up Virtual Environment
```bash
cd fall-in
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 4. Configure Environment Variables
- Create `.env` file with your Supabase credentials
- Set up email configuration

### 5. Create WSGI File
Create `passenger_wsgi.py`:
```python
import sys
import os

# Add your project directory to Python path
path = '/home/YOUR_USERNAME/fall-in'
if path not in sys.path:
    sys.path.append(path)

# Import your Flask app
from app import app as application
```

## 🌐 Railway Deployment

### 1. Sign up at Railway
- Go to [railway.app](https://railway.app)
- Connect your GitHub account

### 2. Deploy from GitHub
- Click "New Project"
- Select "Deploy from GitHub repo"
- Choose your `fall-in` repository
- Railway will automatically detect Flask and deploy

### 3. Set Environment Variables
Add these in Railway dashboard:
```
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
MAIL_USERNAME=your_email
MAIL_PASSWORD=your_app_password
```

## 🔧 Environment Setup

### Required Environment Variables
Create a `.env` file with:
```env
# Supabase Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-supabase-anon-key

# Email Configuration (Optional)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
```

## 📱 Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Run the app
python app.py

# Access at http://localhost:8000
```

## 🔒 Security Notes
- Never commit `.env` files to GitHub
- Use environment variables for sensitive data
- Set up proper CORS for production
- Enable HTTPS in production

## 🎯 Next Steps
1. Deploy to your chosen platform
2. Set up custom domain (optional)
3. Configure monitoring and logging
4. Set up automated backups 