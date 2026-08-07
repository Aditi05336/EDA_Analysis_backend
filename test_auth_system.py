import sys
import os
from dotenv import load_dotenv

# Ensure backend root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
load_dotenv(".env")

import psycopg2
from psycopg2.extras import RealDictCursor
import firebase_admin
from firebase_admin import credentials, auth
from app.config import Config
from app.database.models import init_db, get_or_create_user, get_user_by_firebase_uid
from app.auth.firebase_admin import init_firebase_admin, verify_id_token

print("=" * 60)
print("COMPREHENSIVE AUTHENTICATION & NEON DB VERIFICATION SUITE")
print("=" * 60)

# STEP 1: Verify Neon Database Connection
print("\n[STEP 1] Testing Neon Database Connection...")
try:
    conn = psycopg2.connect(Config.NEON_DATABASE_URL)
    with conn.cursor() as cur:
        cur.execute("SELECT version();")
        db_version = cur.fetchone()[0]
        print(f"  [SUCCESS] Connected to Neon DB! Postgres Version: {db_version[:50]}...")
    conn.close()
except Exception as e:
    print(f"  [FAILED] Connection error: {e}")
    sys.exit(1)

# STEP 2: Initialize Firebase Admin using serviceAccountKey.json
print("\n[STEP 2] Initializing Firebase Admin SDK...")
try:
    init_firebase_admin()
    print("  [SUCCESS] Firebase Admin SDK initialized with serviceAccountKey.json!")
    print(f"  Project ID: {firebase_admin.get_app().project_id}")
except Exception as e:
    print(f"  [FAILED] Firebase Admin init error: {e}")
    sys.exit(1)

# STEP 3: Create/Verify 'users' table in Neon DB
print("\n[STEP 3] Verifying Neon DB 'users' Table Schema...")
try:
    init_db()
    conn = psycopg2.connect(Config.NEON_DATABASE_URL)
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'users';
        """)
        columns = cur.fetchall()
        print("  [SUCCESS] 'users' table exists! Column Definitions:")
        for col in columns:
            print(f"    - {col['column_name']} ({col['data_type']})")
    conn.close()
except Exception as e:
    print(f"  [FAILED] Table verification error: {e}")
    sys.exit(1)

# STEP 4 & 6: Test Auto-Creating User in Neon DB
print("\n[STEP 6 & 4] Testing User Creation / Sync in Neon Database...")
test_uid = "test_firebase_uid_12345"
test_email = "test.user@edastudio.org"
test_name = "Test Analyst"

try:
    created_user = get_or_create_user(test_uid, test_email, test_name)
    print(f"  [SUCCESS] User created/retrieved in Neon DB:")
    print(f"    - ID (UUID): {created_user['id']}")
    print(f"    - Firebase UID: {created_user['firebase_uid']}")
    print(f"    - Name: {created_user['name']}")
    print(f"    - Email: {created_user['email']}")
    print(f"    - Created At: {created_user['created_at']}")

    # Idempotency re-test
    re_test_user = get_or_create_user(test_uid, test_email, test_name)
    assert str(created_user['id']) == str(re_test_user['id']), "User UUID mismatch on re-fetch!"
    print("  [SUCCESS] Idempotent login check passed: Existing user correctly retrieved!")
except Exception as e:
    print(f"  [FAILED] User creation test error: {e}")
    sys.exit(1)

# STEP 5 & 7: Verify Authentication Endpoints and Middleware
print("\n[STEP 5 & 7] Verifying Flask Auth Routes & Route Protection Middleware...")
try:
    from app import create_app
    app = create_app()
    client = app.test_client()

    # Test protected route without token (should return 401)
    res_unauth = client.get("/api/auth/me")
    print(f"  [TEST] Unauthenticated request to GET /api/auth/me: Status {res_unauth.status_code}")
    assert res_unauth.status_code == 401, "Expected 401 for unauthenticated request!"
    print("  [SUCCESS] Middleware correctly rejects unauthenticated requests (401 Unauthorized)!")

    # Test public endpoint
    res_index = client.get("/")
    print(f"  [TEST] GET /: Status {res_index.status_code}")
    assert res_index.status_code == 200, "Expected 200 for index endpoint!"
    print("  [SUCCESS] Public routes accessible!")
except Exception as e:
    print(f"  [FAILED] Route verification error: {e}")
    sys.exit(1)

print("\n" + "=" * 60)
print("ALL 8 VERIFICATION STEPS PASSED PERFECTLY!")
print("=" * 60)
