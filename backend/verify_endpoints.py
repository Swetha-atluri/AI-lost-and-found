import requests
import sys
import os
import json
from pathlib import Path

BASE_URL = "http://127.0.0.1:8000"

def test_api():
    print("[API TEST] Starting end-to-end API verification on running server...")
    
    # 1. Register User
    print("\n--- 1. Registering user 'charlie' ---")
    reg_payload = {
        "username": "charlie",
        "email": "charlie@example.com",
        "password": "password123"
    }
    r = requests.post(f"{BASE_URL}/api/auth/register", json=reg_payload)
    if r.status_code == 200:
        print("[SUCCESS] User charlie registered.")
    elif r.status_code == 400 and "already registered" in r.text:
        print("[INFO] User charlie already registered, proceeding...")
    else:
        print(f"[FAIL] Registration failed: {r.status_code} - {r.text}")
        return False
        
    # 2. Login User
    print("\n--- 2. Logging in as 'charlie' ---")
    login_data = {
        "username": "charlie",
        "password": "password123"
    }
    r = requests.post(f"{BASE_URL}/api/auth/login", data=login_data)
    if r.status_code != 200:
        print(f"[FAIL] Login failed: {r.status_code} - {r.text}")
        return False
        
    token = r.json()["access_token"]
    print(f"[SUCCESS] Login token obtained: {token[:15]}...")
    headers = {"Authorization": f"Bearer {token}"}
    
    # 3. Create Lost Item
    print("\n--- 3. Submitting Lost Item: Blue Canvas Backpack ---")
    lost_data = {
        "name": "Blue Canvas Backpack",
        "category": "Accessories",
        "description": "A dark blue canvas backpack containing a laptop, a charger, and a red notebook.",
        "date_lost": "2026-08-03T11:00:00",
        "location": "Campus Library Hallway"
    }
    
    dummy_lost_path = Path("dummy_lost.jpg")
    if not dummy_lost_path.exists():
        # Fallback if image not generated
        with open(dummy_lost_path, "wb") as f:
            f.write(b"dummy")
            
    files = {"image": ("dummy_lost.jpg", open(dummy_lost_path, "rb"), "image/jpeg")}
    r = requests.post(f"{BASE_URL}/api/items/lost", data=lost_data, files=files, headers=headers)
    if r.status_code != 200:
        print(f"[FAIL] Creating lost item failed: {r.status_code} - {r.text}")
        return False
        
    lost_item = r.json()
    print(f"[SUCCESS] Lost Item created: ID {lost_item['id']} - Status: {lost_item['status']}")
    
    # 4. Create Found Item (Should trigger AI matching in background)
    print("\n--- 4. Submitting Found Item (Triggering AI Engine) ---")
    found_data = {
        "description": "Found a blue canvas backpack containing computer accessories and cables in the library.",
        "date_found": "2026-08-03T11:15:00",
        "location": "Library lobby counter"
    }
    dummy_found_path = Path("dummy_found.jpg")
    if not dummy_found_path.exists():
        with open(dummy_found_path, "wb") as f:
            f.write(b"dummy")
            
    files = {"image": ("dummy_found.jpg", open(dummy_found_path, "rb"), "image/jpeg")}
    r = requests.post(f"{BASE_URL}/api/items/found", data=found_data, files=files, headers=headers)
    if r.status_code != 200:
        print(f"[FAIL] Creating found item failed: {r.status_code} - {r.text}")
        return False
        
    found_item = r.json()
    print(f"[SUCCESS] Found Item created: ID {found_item['id']} - Status: {found_item['status']}")
    
    # 5. Query Matches
    print("\n--- 5. Checking Matches list for 'charlie' ---")
    r = requests.get(f"{BASE_URL}/api/matches/my", headers=headers)
    if r.status_code != 200:
        print(f"[FAIL] Querying matches failed: {r.status_code} - {r.text}")
        return False
        
    matches = r.json()
    print(f"[SUCCESS] Found {len(matches)} matches.")
    if len(matches) == 0:
        print("[FAIL] Expected a match between backpack items but list is empty. Check threshold.")
        return False
        
    match = matches[0]
    print(f"  - Match ID {match['id']}: Score {match['confidence_score']:.2%}")
    print(f"    Lost Item: {match['lost_item']['name']}")
    print(f"    Found Item: {match['found_item']['description'][:50]}...")
    
    # 6. Check Email inbox alerts list
    print("\n--- 6. Checking generated mock email files ---")
    r = requests.get(f"{BASE_URL}/api/mock-emails")
    if r.status_code != 200:
        print(f"[FAIL] Querying mock emails failed: {r.status_code} - {r.text}")
        return False
    email_files = r.json()
    print(f"[SUCCESS] Mock email files in directory: {email_files}")
    
    # 7. Approve Match
    print(f"\n--- 7. Approving Match ID {match['id']} ---")
    r = requests.put(f"{BASE_URL}/api/matches/{match['id']}/status", json={"status": "approved"}, headers=headers)
    if r.status_code != 200:
        print(f"[FAIL] Approving match failed: {r.status_code} - {r.text}")
        return False
    print(f"[SUCCESS] Match approved. Status: {r.json()['status']}")
    
    # 8. Claim & Resolve Match
    print(f"\n--- 8. Resolving Match (Claiming Item) ---")
    r = requests.put(f"{BASE_URL}/api/matches/{match['id']}/status", json={"status": "resolved"}, headers=headers)
    if r.status_code != 200:
        print(f"[FAIL] Resolving match failed: {r.status_code} - {r.text}")
        return False
    print(f"[SUCCESS] Match resolved. Status: {r.json()['status']}")
    
    print("\n[VERIFICATION COMPLETED] End-to-end API test was fully successful!")
    return True

if __name__ == "__main__":
    test_api()
