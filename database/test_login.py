#!/usr/bin/env python3
"""
Test script to verify admin login credentials
"""

import requests
import json

def test_admin_login():
    """Test admin login"""
    url = "http://localhost:8000/auth/login"
    
    # Admin credentials
    credentials = {
        "email": "admin@geminiclone.com",
        "password": "admin123"
    }
    
    print("🔐 Testing admin login...")
    print(f"📧 Email: {credentials['email']}")
    print(f"🔑 Password: {credentials['password']}")
    
    try:
        response = requests.post(
            url,
            headers={"Content-Type": "application/json"},
            json=credentials
        )
        
        print(f"\n📊 Response Status: {response.status_code}")
        print(f"📄 Response Content: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Login successful!")
            print(f"👤 User: {data['user']['full_name']} ({data['user']['email']})")
            print(f"🔧 Admin: {data['user']['is_admin']}")
            return True
        else:
            print("❌ Login failed!")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_health():
    """Test health endpoint"""
    try:
        response = requests.get("http://localhost:8000/health")
        print(f"🏥 Health check: {response.status_code}")
        return response.status_code == 200
    except:
        print("❌ Backend not accessible")
        return False

if __name__ == "__main__":
    print("🚀 Testing Gemini Clone Backend...")
    
    if test_health():
        test_admin_login()
    else:
        print("❌ Backend is not running. Please start it first with: python start.py") 