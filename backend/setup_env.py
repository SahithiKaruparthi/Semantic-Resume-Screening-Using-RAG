#!/usr/bin/env python3
"""
Setup script to configure environment variables for the recruitment system
"""

import os
import sys

def setup_environment():
    """Set up environment variables for the application"""
    
    print("🚀 Setting up environment variables for Recruitment System")
    print("=" * 60)
    
    # Check if .env file exists
    env_file = os.path.join(os.path.dirname(__file__), '.env')
    
    if os.path.exists(env_file):
        print("✅ .env file already exists")
        return
    
    # Get GROQ API key from user
    print("\n📝 Please provide your GROQ API key:")
    print("   - Get it from: https://console.groq.com/keys")
    print("   - This is required for LLM functionality")
    
    groq_api_key = input("\n🔑 Enter your GROQ API key: ").strip()
    
    if not groq_api_key:
        print("❌ GROQ API key is required!")
        sys.exit(1)
    
    # Create .env file content
    env_content = f"""# Recruitment System Environment Configuration
# Generated automatically by setup_env.py

# GROQ API Configuration
GROQ_API_KEY={groq_api_key}

# Flask Configuration
SECRET_KEY=your-secret-key-here-change-in-production
FLASK_ENV=development
FLASK_DEBUG=1

# Database Configuration
DATABASE_URL=sqlite:///db/resume_screening.db

# File Upload Configuration
MAX_FILE_SIZE=5242880
ALLOWED_EXTENSIONS=.pdf,.docx

# Admin Credentials (change these in production)
ADMIN_USERNAME=admin
ADMIN_PASSWORD=securepassword123
ADMIN_EMAIL=admin@techrecruit.example.com
"""
    
    # Write .env file
    try:
        with open(env_file, 'w') as f:
            f.write(env_content)
        print(f"\n✅ Environment file created: {env_file}")
        print("🔒 Please keep your API key secure and don't commit it to version control")
        
    except Exception as e:
        print(f"❌ Error creating .env file: {e}")
        sys.exit(1)
    
    print("\n🎉 Environment setup complete!")
    print("📖 You can now run: python app.py")

if __name__ == "__main__":
    setup_environment() 