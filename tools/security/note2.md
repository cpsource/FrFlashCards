You generate a secret key and give it to the user securely. Here's how:

## **1. Generate a strong API key:**

```bash
# On your server, generate a random key
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
# Output: something like "xK9mP4vN2wQ7rT8sY3zL6hJ5gF1dC0bA4eR9tY2"
```

## **2. Store it in your `.env` file:**

```bash
nano /var/www/FrFlashCards/.env
```

Add:
```
OPENAI_API_KEY=sk-your-openai-key
INTERNAL_API_KEY=xK9mP4vN2wQ7rT8sY3zL6hJ5gF1dC0bA4eR9tY2
```

## **3. Update your Flask app to check for it:**

```python
from functools import wraps
from flask import request, jsonify
import os

def require_api_key(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Get the API key from request header
        api_key = request.headers.get('X-API-Key')
        
        # Check if it matches your stored key
        if api_key != os.getenv('INTERNAL_API_KEY'):
            return jsonify({'error': 'Unauthorized - Invalid API Key'}), 401
        
        return f(*args, **kwargs)
    return decorated_function

# Protect your routes
@app.route("/hello")
@require_api_key
def hello():
    return {"message": "Hello from Flask!"}

@app.route("/upload-audio", methods=['POST'])
@require_api_key
def upload_audio():
    # Your code here
    pass
```

## **4. Give the key to your user SECURELY:**

**Bad ways (DON'T do this):**
- ❌ Email it in plain text
- ❌ Put it in Slack
- ❌ Write it on paper

**Good ways:**
- ✅ Use a password manager (1Password, Bitwarden) to share
- ✅ Use an encrypted messaging app (Signal)
- ✅ Share in person
- ✅ Use a one-time secret sharing service like https://onetimesecret.com

## **5. How the user uses it:**

**In curl:**
```bash
curl -H "X-API-Key: xK9mP4vN2wQ7rT8sY3zL6hJ5gF1dC0bA4eR9tY2" \
     https://frflashy.com/api/hello
```

**In Python:**
```python
import requests

headers = {
    'X-API-Key': 'xK9mP4vN2wQ7rT8sY3zL6hJ5gF1dC0bA4eR9tY2'
}

response = requests.get('https://frflashy.com/api/hello', headers=headers)
print(response.json())
```

**In JavaScript:**
```javascript
fetch('https://frflashy.com/api/hello', {
    headers: {
        'X-API-Key': 'xK9mP4vN2wQ7rT8sY3zL6hJ5gF1dC0bA4eR9tY2'
    }
})
.then(res => res.json())
.then(data => console.log(data));
```

## **Better: Support multiple users with different keys**

```python
# In .env
API_KEYS=user1:key1abc123,user2:key2def456,user3:key3ghi789
```

```python
# In Flask
import os

def get_valid_api_keys():
    """Parse API keys from environment variable"""
    keys_str = os.getenv('API_KEYS', '')
    keys = {}
    for pair in keys_str.split(','):
        if ':' in pair:
            user, key = pair.split(':', 1)
            keys[key] = user
    return keys

def require_api_key(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        valid_keys = get_valid_api_keys()
        
        if api_key not in valid_keys:
            return jsonify({'error': 'Unauthorized'}), 401
        
        # Optional: log who's using it
        print(f"Request from: {valid_keys[api_key]}")
        
        return f(*args, **kwargs)
    return decorated_function
```

## **Even better: Use a database for API keys**

```python
# Store API keys in your PostgreSQL database
CREATE TABLE api_keys (
    id SERIAL PRIMARY KEY,
    user_name TEXT NOT NULL,
    api_key TEXT NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_used TIMESTAMP,
    is_active BOOLEAN DEFAULT true
);

INSERT INTO api_keys (user_name, api_key) 
VALUES ('john_doe', 'xK9mP4vN2wQ7rT8sY3zL6hJ5gF1dC0bA4eR9tY2');
```

```python
# In Flask
import psycopg2

def require_api_key(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        
        conn = psycopg2.connect(os.getenv('DATABASE_URL'))
        cur = conn.cursor()
        
        cur.execute(
            "SELECT user_name, is_active FROM api_keys WHERE api_key = %s",
            (api_key,)
        )
        result = cur.fetchone()
        
        if not result or not result[1]:  # Not found or inactive
            conn.close()
            return jsonify({'error': 'Unauthorized'}), 401
        
        # Update last_used timestamp
        cur.execute(
            "UPDATE api_keys SET last_used = NOW() WHERE api_key = %s",
            (api_key,)
        )
        conn.commit()
        conn.close()
        
        return f(*args, **kwargs)
    return decorated_function
```

Think of it like this Python class analogy:

```python
class APIKeyManager:
    def __init__(self):
        self.valid_keys = {
            'xK9mP4vN2w': 'user1',
            'Q7rT8sY3zL': 'user2'
        }
    
    def verify(self, key):
        return key in self.valid_keys
```

**Summary:**
1. Generate a secure random key
2. Store it in `.env` or database
3. Share it securely with the user
4. User sends it in `X-API-Key` header with every request
5. Your Flask app validates it before processing the request
