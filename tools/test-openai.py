#!/usr/bin/env python3
"""
Test OpenAI API connection
"""

from openai import OpenAI
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv('/home/ubuntu/.env')

# Get API key
api_key = os.getenv('OPENAI_API_KEY')

if not api_key:
    print("❌ ERROR: OPENAI_API_KEY not found in environment variables")
    exit(1)

print(f"✓ API Key found: {api_key[:8]}...{api_key[-4:]}")
print("Testing connection to OpenAI...\n")

try:
    # Initialize client
    client = OpenAI(api_key=api_key)
    
    # Test 1: Simple completion
    print("Test 1: Testing chat completion...")
    response = client.chat.completions.create(
        model="gpt-4o-mini",  # Cheapest model for testing
        messages=[
            {"role": "user", "content": "Say 'Connection successful!' in French"}
        ],
        max_tokens=20
    )
    
    result = response.choices[0].message.content
    print(f"✓ Chat completion works!")
    print(f"  Response: {result}\n")
    
    # Test 2: List models (verify API access)
    print("Test 2: Listing available models...")
    models = client.models.list()
    model_count = len(models.data)
    print(f"✓ Can access {model_count} models\n")
    
    print("=" * 50)
    print("✓ ALL TESTS PASSED!")
    print("✓ OpenAI API connection is working correctly")
    print("=" * 50)
    
except Exception as e:
    print(f"❌ ERROR: {str(e)}")
    print("\nPossible issues:")
    print("  - Invalid API key")
    print("  - No internet connection")
    print("  - OpenAI API is down")
    print("  - IP address not whitelisted (if you set restrictions)")
    exit(1)
