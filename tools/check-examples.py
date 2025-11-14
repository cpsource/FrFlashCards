#!/usr/bin/env python3
"""
Check for duplicate identical French sentences in the examples table.
Delete duplicates, keeping only one unique sentence per expression.

Usage:
    python3 check_examples.py --trial-run    # Show what would be deleted
    python3 check_examples.py                # Actually delete duplicates
"""

import psycopg2
from dotenv import load_dotenv
import os
import sys

# Load environment variables
load_dotenv('/home/ubuntu/.env')

def check_and_cleanup_examples(trial_run=False):
    conn = psycopg2.connect(os.getenv('NEON_DATABASE_URL'))
    cur = conn.cursor()
    
    # Get all distinct expressions starting from id 2
    cur.execute("""
        SELECT DISTINCT expression 
        FROM examples 
        WHERE id >= 2 
        ORDER BY expression
    """)
    
    expressions = [row[0] for row in cur.fetchall()]
    
    mode = "TRIAL RUN" if trial_run else "LIVE MODE"
    print(f"{mode}: Checking {len(expressions)} expressions...\n")
    
    duplicates_found = 0
    total_deleted = 0
    
    for expression in expressions:
        # Get all records for this expression
        cur.execute("""
            SELECT id, french, english 
            FROM examples 
            WHERE expression = %s AND id >= 2
            ORDER BY id
        """, (expression,))
        
        rows = cur.fetchall()
        
        if len(rows) < 2:
            # Only 1 record - leave it alone
            continue
        
        # Group by identical French sentences
        french_groups = {}
        for row in rows:
            french_text = row[1]
            if french_text not in french_groups:
                french_groups[french_text] = []
            french_groups[french_text].append(row)
        
        # Check each group for duplicates
        for french_text, group_rows in french_groups.items():
            if len(group_rows) > 1:
                # Found duplicates!
                duplicates_found += 1
                keep_id = group_rows[0][0]  # Keep the first one (lowest ID)
                delete_ids = [row[0] for row in group_rows[1:]]  # Delete the rest
                
                print(f"{'❌ DUPLICATE' if not trial_run else '⚠️  WOULD DELETE'}: Expression '{expression}'")
                print(f"   Identical French: '{french_text[:60]}{'...' if len(french_text) > 60 else ''}'")
                print(f"   Found {len(group_rows)} identical records")
                print(f"   Keeping ID: {keep_id}")
                print(f"   {'Deleting' if not trial_run else 'Would delete'} IDs: {', '.join(map(str, delete_ids))}")
                
                if not trial_run:
                    # Actually delete the duplicates
                    for del_id in delete_ids:
                        cur.execute("DELETE FROM examples WHERE id = %s", (del_id,))
                        total_deleted += 1
                    conn.commit()
                    print(f"   ✓ Deleted {len(delete_ids)} duplicate(s)")
                else:
                    total_deleted += len(delete_ids)
                
                print()
    
    cur.close()
    conn.close()
    
    print(f"\n{'='*60}")
    if duplicates_found > 0:
        if trial_run:
            print(f"⚠️  TRIAL RUN: Found {duplicates_found} expressions with duplicates")
            print(f"⚠️  Would delete {total_deleted} duplicate records")
            print(f"\nRun without --trial-run to actually delete them")
        else:
            print(f"✅ CLEANED: Found and removed {duplicates_found} expressions with duplicates")
            print(f"✅ Deleted {total_deleted} duplicate records")
    else:
        print("✅ All expressions have unique French sentences!")
    print(f"{'='*60}")

if __name__ == '__main__':
    # Check for --trial-run flag
    trial_run = '--trial-run' in sys.argv
    
    if trial_run:
        print("🔍 Running in TRIAL RUN mode - no changes will be made\n")
    else:
        print("⚠️  Running in LIVE mode - duplicates will be DELETED\n")
        confirm = input("Are you sure? Type 'yes' to continue: ")
        if confirm.lower() != 'yes':
            print("Cancelled.")
            sys.exit(0)
    
    check_and_cleanup_examples(trial_run)
