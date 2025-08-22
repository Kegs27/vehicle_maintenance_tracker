#!/usr/bin/env python3
"""
Test script to verify all imports work correctly
Run this before deploying to catch import issues early
"""

import sys
import os

print("🧪 Testing imports...")
print(f"📁 Current directory: {os.getcwd()}")
print(f"🐍 Python version: {sys.version}")
print()

# Test basic imports
try:
    from fastapi import FastAPI
    print("✅ FastAPI import successful")
except Exception as e:
    print(f"❌ FastAPI import failed: {e}")

try:
    from sqlmodel import SQLModel
    print("✅ SQLModel import successful")
except Exception as e:
    print(f"❌ SQLModel import failed: {e}")

# Test app-specific imports
try:
    from app.database import engine, init_db, get_session
    print("✅ Database imports successful")
except Exception as e:
    print(f"❌ Database import failed: {e}")

try:
    from app.models import Vehicle, MaintenanceRecord
    print("✅ Model imports successful")
except Exception as e:
    print(f"❌ Model import failed: {e}")

try:
    from app.importer import import_csv, ImportResult
    print("✅ Importer imports successful")
except Exception as e:
    print(f"❌ Importer import failed: {e}")

print()
print("🎯 Import test complete!")
