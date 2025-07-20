#!/usr/bin/env python3
"""
Startup script for the AI-First CRM HCP Module Backend
"""

import os
import sys
import uvicorn
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def check_environment():
    """Check if all required environment variables are set"""
    print("🔍 Checking environment variables...")
    
    required_vars = ['GROQ_API_KEY', 'DATABASE_URL']
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
        else:
            print(f"✅ {var} is set")
    
    if missing_vars:
        print(f"❌ Missing environment variables: {', '.join(missing_vars)}")
        print("Please create a .env file with the required variables:")
        print("GROQ_API_KEY=your_groq_api_key_here")
        print("DATABASE_URL=postgresql://postgres:password@localhost:5432/aihcp")
        return False
    
    return True

def check_dependencies():
    """Check if all required packages are installed"""
    print("📦 Checking dependencies...")
    
    required_packages = [
        ('fastapi', 'fastapi'),
        ('uvicorn', 'uvicorn'),
        ('sqlalchemy', 'sqlalchemy'),
        ('psycopg2', 'psycopg2'),
        ('pydantic_settings', 'pydantic_settings'),
        ('python-dotenv', 'dotenv'),
        ('langchain', 'langchain'),
        ('langgraph', 'langgraph'),
        ('groq', 'groq'),
        ('langchain_groq', 'langchain_groq')
    ]
    
    missing_packages = []
    
    for pip_name, import_name in required_packages:
        try:
            __import__(import_name)
            print(f"✅ {pip_name} is installed")
        except ImportError:
            missing_packages.append(pip_name)
            print(f"❌ {pip_name} is missing")
    
    if missing_packages:
        print(f"\n📥 Install missing packages with:")
        print(f"pip install {' '.join(missing_packages)}")
        return False
    
    return True

def main():
    """Main startup function"""
    print("🚀 Starting AI-First CRM HCP Module Backend")
    print("=" * 50)
    
    # Check environment
    if not check_environment():
        sys.exit(1)
    
    # Check dependencies
    if not check_dependencies():
        print("\n💡 You can install all dependencies with:")
        print("pip install -r requirements.txt")
        sys.exit(1)
    
    print("\n✅ All checks passed! Starting server...")
    print("🌐 Backend will be available at: http://localhost:8000")
    print("📚 API documentation: http://localhost:8000/docs")
    print("🔧 Health check: http://localhost:8000/health")
    print("\n🛑 Press Ctrl+C to stop the server")
    print("=" * 50)
    
    try:
        uvicorn.run(
            "app.main:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
    except Exception as e:
        print(f"\n❌ Server error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()