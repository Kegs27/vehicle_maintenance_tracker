#!/usr/bin/env python3
"""
Deployment helper script for Vehicle Maintenance Tracker
This script helps prepare your app for cloud deployment
"""

import os
import shutil
import subprocess
import sys

def check_requirements():
    """Check if all required files exist"""
    required_files = [
        "main.py",
        "models.py", 
        "database.py",
        "importer.py",
        "requirements.txt",
        "Procfile",
        "runtime.txt"
    ]
    
    missing_files = []
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)
    
    if missing_files:
        print(f"❌ Missing required files: {', '.join(missing_files)}")
        return False
    
    print("✅ All required files present")
    return True

def create_static_directory():
    """Create static directory if it doesn't exist"""
    if not os.path.exists("static"):
        os.makedirs("static")
        print("✅ Created static directory")
    else:
        print("✅ Static directory already exists")

def install_dependencies():
    """Install Python dependencies"""
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], check=True)
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError:
        print("❌ Failed to install dependencies")
        return False

def main():
    """Main deployment preparation function"""
    print("🚀 Preparing Vehicle Maintenance Tracker for deployment...")
    print()
    
    # Check requirements
    if not check_requirements():
        print("\n❌ Deployment preparation failed. Please fix the missing files.")
        return False
    
    # Create static directory
    create_static_directory()
    
    # Install dependencies
    if not install_dependencies():
        print("\n❌ Failed to install dependencies.")
        return False
    
    print("\n✅ Deployment preparation completed successfully!")
    print("\n📋 Next steps:")
    print("1. Choose a cloud platform (Railway or Render recommended)")
    print("2. Create a new project and connect your GitHub repository")
    print("3. Set the DATABASE_URL environment variable")
    print("4. Deploy!")
    
    return True

if __name__ == "__main__":
    main()
