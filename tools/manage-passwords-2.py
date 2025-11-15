#!/usr/bin/env python3
"""
User password management script for frflashy.com
Usage:
    python3 manage-passwords.py list
    python3 manage-passwords.py add <username> <email> <password> <tier>
    python3 manage-passwords.py del <username>
    python3 manage-passwords.py check <username> <password>
"""

import sys
import psycopg2
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv('/home/ubuntu/.env')

# Tier constants for reference
TIER_ADMIN   = 0
TIER_GRATIS  = 1
TIER_BASIC   = 2
TIER_PRO     = 3
TIER_PREMIUM = 4

def get_db_connection():
    """Get database connection"""
    try:
        conn = psycopg2.connect(os.getenv('NEON_DATABASE_URL'))
        return conn
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        sys.exit(1)

def list_users():
    """List all users"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("SELECT id, username, email, tier, created_at FROM users ORDER BY id")
    users = cur.fetchall()
    
    if not users:
        print("No users found.")
    else:
        print("\n" + "="*85)
        print(f"{'ID':<5} {'Username':<20} {'Email':<30} {'Tier':<6} {'Created':<15}")
        print("="*85)
        for user in users:
            user_id, username, email, tier, created_at = user
            created_str = created_at.strftime('%Y-%m-%d') if created_at else 'N/A'
            tier_str = str(tier) if tier is not None else 'N/A'
            print(f"{user_id:<5} {username:<20} {email:<30} {tier_str:<6} {created_str:<15}")
        print("="*85)
        print(f"Total users: {len(users)}\n")
        print("Tier levels: 0=ADMIN, 1=GRATIS, 2=BASIC, 3=PRO, 4=PREMIUM\n")
    
    cur.close()
    conn.close()

def add_user(username, email, password, tier):
    """Add a new user"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Validate tier
    try:
        tier = int(tier)
        if tier < 0 or tier > 4:
            print(f"❌ Error: Tier must be between 0 and 4")
            print("   0=ADMIN, 1=GRATIS, 2=BASIC, 3=PRO, 4=PREMIUM")
            cur.close()
            conn.close()
            return
    except ValueError:
        print(f"❌ Error: Tier must be an integer (0-4)")
        cur.close()
        conn.close()
        return
    
    # Check if user already exists
    cur.execute("SELECT username FROM users WHERE username = %s OR email = %s", (username, email))
    if cur.fetchone():
        print(f"❌ Error: User '{username}' or email '{email}' already exists")
        cur.close()
        conn.close()
        return
    
    # Hash the password
    password_hash = generate_password_hash(password)
    
    try:
        cur.execute(
            "INSERT INTO users (username, email, password_hash, tier) VALUES (%s, %s, %s, %s)",
            (username, email, password_hash, tier)
        )
        conn.commit()
        tier_names = {0: 'ADMIN', 1: 'GRATIS', 2: 'BASIC', 3: 'PRO', 4: 'PREMIUM'}
        print(f"✓ User '{username}' created successfully!")
        print(f"  Email: {email}")
        print(f"  Tier: {tier} ({tier_names.get(tier, 'UNKNOWN')})")
    except Exception as e:
        print(f"❌ Error creating user: {e}")
    
    cur.close()
    conn.close()

def delete_user(username):
    """Delete a user"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Check if user exists
    cur.execute("SELECT id, username, email, tier FROM users WHERE username = %s", (username,))
    user = cur.fetchone()
    
    if not user:
        print(f"❌ Error: User '{username}' not found")
        cur.close()
        conn.close()
        return
    
    # Confirm deletion
    print(f"\n⚠️  WARNING: About to delete user:")
    print(f"  ID: {user[0]}")
    print(f"  Username: {user[1]}")
    print(f"  Email: {user[2]}")
    print(f"  Tier: {user[3]}")
    
    confirm = input("\nType 'yes' to confirm deletion: ")
    
    if confirm.lower() == 'yes':
        cur.execute("DELETE FROM users WHERE username = %s", (username,))
        conn.commit()
        print(f"✓ User '{username}' deleted successfully!")
    else:
        print("Deletion cancelled.")
    
    cur.close()
    conn.close()

def check_password(username, password):
    """Check if a password is correct for a user"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Get user's password hash
    cur.execute("SELECT username, password_hash FROM users WHERE username = %s", (username,))
    user = cur.fetchone()
    
    if not user:
        print(f"❌ Error: User '{username}' not found")
        cur.close()
        conn.close()
        return
    
    stored_hash = user[1]
    
    # Check if password matches
    if check_password_hash(stored_hash, password):
        print(f"✓ Password is CORRECT for user '{username}'")
    else:
        print(f"❌ Password is INCORRECT for user '{username}'")
    
    cur.close()
    conn.close()

def show_usage():
    """Show usage instructions"""
    print(__doc__)

def main():
    if len(sys.argv) < 2:
        show_usage()
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == 'list':
        list_users()
    
    elif command == 'add':
        if len(sys.argv) != 6:
            print("Usage: python3 manage-passwords.py add <username> <email> <password> <tier>")
            print("Tier levels: 0=ADMIN, 1=GRATIS, 2=BASIC, 3=PRO, 4=PREMIUM")
            sys.exit(1)
        username = sys.argv[2]
        email = sys.argv[3]
        password = sys.argv[4]
        tier = sys.argv[5]
        add_user(username, email, password, tier)
    
    elif command == 'del':
        if len(sys.argv) != 3:
            print("Usage: python3 manage-passwords.py del <username>")
            sys.exit(1)
        username = sys.argv[2]
        delete_user(username)
    
    elif command == 'check':
        if len(sys.argv) != 4:
            print("Usage: python3 manage-passwords.py check <username> <password>")
            sys.exit(1)
        username = sys.argv[2]
        password = sys.argv[3]
        check_password(username, password)
    
    else:
        print(f"❌ Unknown command: {command}")
        show_usage()
        sys.exit(1)

if __name__ == '__main__':
    main()
