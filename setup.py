#!/usr/bin/env python3
"""
Fall In App Setup Script
This script helps you configure your environment and test the Supabase connection.
"""

import os
import sys
from pathlib import Path

def create_env_file():
    """Create .env file from template if it doesn't exist"""
    env_file = Path('.env')
    template_file = Path('env_template.txt')
    
    if env_file.exists():
        print("✅ .env file already exists")
        return True
    
    if not template_file.exists():
        print("❌ env_template.txt not found")
        return False
    
    try:
        # Copy template to .env
        with open(template_file, 'r') as f:
            content = f.read()
        
        with open(env_file, 'w') as f:
            f.write(content)
        
        print("✅ Created .env file from template")
        print("📝 Please edit .env file with your actual Supabase credentials")
        return True
    except Exception as e:
        print(f"❌ Error creating .env file: {e}")
        return False

def check_env_variables():
    """Check if required environment variables are set"""
    from dotenv import load_dotenv
    load_dotenv()
    
    required_vars = ['SUPABASE_URL', 'SUPABASE_KEY']
    missing_vars = []
    
    for var in required_vars:
        value = os.getenv(var)
        if not value or value.startswith('your-') or value.startswith('https://your-'):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing or invalid environment variables: {', '.join(missing_vars)}")
        print("📝 Please update your .env file with actual values")
        return False
    
    print("✅ Environment variables are configured")
    return True

def test_supabase_connection():
    """Test the Supabase connection"""
    try:
        from supabase import create_client, Client
        from dotenv import load_dotenv
        
        load_dotenv()
        
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_KEY')
        
        if not supabase_url or not supabase_key:
            print("❌ Supabase credentials not found in environment")
            return False
        
        # Test connection
        supabase: Client = create_client(supabase_url, supabase_key)
        
        # Try a simple query
        result = supabase.table('users').select('count', count='exact').limit(1).execute()
        
        print("✅ Supabase connection successful")
        return True
        
    except Exception as e:
        print(f"❌ Supabase connection failed: {e}")
        return False

def main():
    print("🚀 Fall In App Setup")
    print("=" * 40)
    
    # Step 1: Create .env file
    print("\n1. Creating .env file...")
    if not create_env_file():
        sys.exit(1)
    
    # Step 2: Check environment variables
    print("\n2. Checking environment variables...")
    if not check_env_variables():
        print("\n📋 Next steps:")
        print("1. Edit .env file with your Supabase credentials")
        print("2. Run this script again to test the connection")
        sys.exit(1)
    
    # Step 3: Test Supabase connection
    print("\n3. Testing Supabase connection...")
    if not test_supabase_connection():
        print("\n📋 Troubleshooting:")
        print("1. Check your Supabase URL and key in .env file")
        print("2. Make sure your Supabase project is active")
        print("3. Verify your database schema is set up")
        sys.exit(1)
    
    print("\n🎉 Setup complete! Your app is ready to run.")
    print("Run 'python app.py' to start the application.")

if __name__ == '__main__':
    main()
