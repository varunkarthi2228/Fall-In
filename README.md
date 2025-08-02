# Fall In - University Dating App

A Flask-based dating application designed for university students to connect with each other on campus.

## Features

- 🔐 Email-based authentication with OTP verification
- 👤 User profile creation with photos and prompts
- 💕 Swipe-based matching system
- 💬 Match management
- 📱 Responsive design with Tailwind CSS
- 🎨 Modern UI with Font Awesome icons

## Setup Instructions

### Prerequisites
- Python 3.8 or higher
- pip (Python package installer)

### Installation

1. **Clone or download the project**
   ```bash
   cd fall_in
   ```

2. **Create and activate virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On macOS/Linux
   # or
   venv\Scripts\activate  # On Windows
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application**
   ```bash
   python app.py
   ```

5. **Access the application**
   - Main app: http://localhost:8000
   - Debug page: http://localhost:8000/debug

## Usage

### For Testing
1. Visit http://localhost:8000/debug
2. Click "Add Test Data" to populate the database with sample users
3. Click "Quick Login" to sign in as a test user (Alice)
4. Start exploring the app!

### For New Users
1. Visit http://localhost:8000
2. Click "Get Started" to create an account
3. Use any email address (e.g., test@example.com)
4. Check the terminal/console for the OTP code
5. Complete your profile and start matching!

## Project Structure

```
fall_in/
├── app.py              # Main Flask application
├── requirements.txt    # Python dependencies
├── supabase_schema.sql # Database schema for Supabase
├── env_template.txt   # Environment variables template
├── templates/         # HTML templates
│   ├── base.html
│   ├── dashboard.html
│   ├── chat_list.html
│   ├── index.html
│   ├── login.html
│   ├── profile.html
│   └── signup.html
└── venv/              # Virtual environment
```

## Technical Details

- **Framework**: Flask 2.3.3
- **Database**: PostgreSQL (Supabase) / SQLite (local)
- **Frontend**: Tailwind CSS, Font Awesome
- **Authentication**: Email OTP verification (any email domain)
- **File Upload**: Profile photo support (stored as base64 in database)
- **Email**: SMTP with Gmail (configurable)
- **Cloud**: Supabase for database and hosting

## Image Storage

Profile photos are now stored as base64-encoded strings directly in the database instead of as files on the local filesystem. This approach provides:

- **Better data portability**: Images travel with the database
- **Simplified deployment**: No need to manage file uploads
- **Consistent storage**: All data in one place
- **Easier backups**: Database backups include images

## Development Notes

- OTP codes are printed to the console for development (if email not configured)
- The app runs on port 8000 to avoid conflicts with macOS AirPlay
- Sample data includes 5 test users for easy testing
- All templates use inline HTML for simplicity

## Email Setup

To enable real email sending (instead of console fallback):

### Option 1: Automated Setup (Recommended)
```bash
python setup_env.py
```
This script will guide you through the setup process and create a secure `.env` file.

### Option 2: Manual Setup
1. **Create environment file:**
   ```bash
   cp env_template.txt .env
   ```

2. **Edit .env with your Gmail credentials:**
   - Replace `your-email@gmail.com` with your Gmail address
   - Replace `your-app-password` with your Gmail app password

3. **Set up Gmail App Password:**
   - Go to Google Account settings
   - Enable 2-Step Verification
   - Go to Security > App passwords
   - Generate app password for "Mail"
   - Use the 16-character password in .env

4. **Restart the application**

**Security Note:** The `.env` file is automatically ignored by git to keep your credentials secure.

**Note:** Without email configuration, OTP codes will be printed to the console for development.

## Supabase Setup

To migrate from SQLite to Supabase PostgreSQL:

### 1. Create Supabase Project
1. Go to https://supabase.com and sign up
2. Create a new project
3. Wait for the project to be ready

### 2. Set Up Database Schema
1. Go to your Supabase Dashboard > SQL Editor
2. Copy and paste the contents of `supabase_schema.sql`
3. Run the SQL to create tables and policies

### 3. Get Credentials
1. Go to Settings > API
2. Copy your Project URL and anon key
3. Go to Settings > Database
4. Copy your database connection string

### 4. Update Environment Variables
Add these to your `.env` file:
```env
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_KEY=your-supabase-anon-key
DATABASE_URL=postgresql://postgres:[password]@db.[project-id].supabase.co:5432/postgres
```

### 5. Migrate Data
```bash
python migrate_to_supabase.py
```

### 6. Update App
The app will automatically use Supabase when credentials are configured.

## Troubleshooting

### Port 5000 Already in Use
The app is configured to run on port 8000 to avoid conflicts with macOS AirPlay Receiver. If you need to change the port, modify the `app.run()` call in `app.py`.

### Virtual Environment Issues
If you encounter permission errors, make sure you're using the virtual environment:
```bash
source venv/bin/activate
```

### Database Issues
The database is created automatically when you first run the app. If you need to reset it, simply delete `fall_in.db` and restart the application.

## License

This is a demo project for educational purposes. 