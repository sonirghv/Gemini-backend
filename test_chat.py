#!/usr/bin/env python3
"""
Test script to verify chat API functionality
"""

import requests
import json

def test_chat_api():
    """Test chat API with admin credentials"""
    
    # Step 1: Login to get token
    login_url = "http://localhost:8000/auth/login"
    login_data = {
        "email": "admin@geminiclone.com",
        "password": "admin123"
    }
    
    print("🔐 Logging in...")
    login_response = requests.post(login_url, json=login_data)
    
    if login_response.status_code != 200:
        print(f"❌ Login failed: {login_response.text}")
        return False
    
    token = login_response.json()["access_token"]
    print("✅ Login successful!")
    
    # Step 2: Test chat API
    chat_url = "http://localhost:8000/chat"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    chat_data = {
        "message": "Hello! Can you tell me about Python programming?",
        "chat_id": None
    }
    
    print("💬 Sending chat message...")
    chat_response = requests.post(chat_url, json=chat_data, headers=headers)
    
    if chat_response.status_code == 200:
        response_data = chat_response.json()
        print("✅ Chat API working!")
        print(f"📝 Response: {response_data['response'][:100]}...")
        print(f"🆔 Chat ID: {response_data['chat_id']}")
        print(f"📨 Message ID: {response_data['message_id']}")
        return True
    else:
        print(f"❌ Chat API failed: {chat_response.text}")
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
    print("🚀 Testing Gemini Clone Chat API...")
    
    if test_health():
        test_chat_api()
    else:
        print("❌ Backend is not running. Please start it first with: python start.py") 