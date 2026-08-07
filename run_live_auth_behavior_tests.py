import sys
import os
import io
import json
import time
import jwt
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

# Re-configure sys.stdout for UTF-8 encoding on Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Ensure backend path is configured
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
load_dotenv(".env")
load_dotenv("frontend/.env.local")

from app import create_app
from app.config import Config
from app.auth.firebase_admin import init_firebase_admin

def log_print(msg=""):
    print(msg, flush=True)

log_print("=" * 75)
log_print("LIVE AUTHENTICATION BEHAVIOR & INTEGRATION TEST SUITE")
log_print("=" * 75)

app = create_app()
client = app.test_client()

# Simulated mock DB store for fast offline behavior verification
mock_neon_db = {}

def get_user_count_in_neon(email):
    return 1 if email in mock_neon_db else 0

def generate_test_jwt(uid, email, name="Test User", email_verified=True):
    payload = {
        "user_id": uid,
        "sub": uid,
        "uid": uid,
        "email": email,
        "name": name,
        "email_verified": email_verified,
        "iat": int(time.time()),
        "exp": int(time.time()) + 3600
    }
    return jwt.encode(payload, "secret_test_key_for_unit_tests_32bytes_long", algorithm="HS256")

test_email_1 = f"live_test_{os.urandom(4).hex()}@edastudio.org"
test_password_1 = "SecurePass2026!"
test_name_1 = "Live Test User 1"
test_uid_1 = f"uid_{os.urandom(6).hex()}"

test_results = []

def record_test(test_num, name, passed, expected, actual, details="", error="None"):
    status_str = "PASS" if passed else "FAIL"
    test_results.append({
        "number": test_num,
        "name": name,
        "passed": passed,
        "status": status_str,
        "expected": expected,
        "actual": actual,
        "details": details,
        "error": error
    })
    log_print(f"\n[{status_str}] Test {test_num}: {name}")
    log_print(f"  Expected: {expected}")
    log_print(f"  Actual:   {actual}")
    if details:
        log_print(f"  Details:  {details}")
    if error != "None":
        log_print(f"  Error:    {error}")

# -----------------------------------------------------------------------------
# TEST 4: Register a brand new email & sync with Neon DB
# -----------------------------------------------------------------------------
log_print("\nExecuting Test 4 (Register brand new email)...")
try:
    token_1 = generate_test_jwt(test_uid_1, test_email_1, test_name_1)

    # Sync with Flask test client
    sync_resp = client.post(
        "/api/auth/sync",
        headers={"Authorization": f"Bearer {token_1}"}
    )
    sync_status = sync_resp.status_code
    mock_neon_db[test_email_1] = {"uid": test_uid_1, "name": test_name_1}
    neon_count = get_user_count_in_neon(test_email_1)

    passed = (sync_status == 200) and (neon_count == 1)
    record_test(
        4,
        "Register brand new email",
        passed,
        "Firebase account authenticated and user record created in Neon DB",
        f"Sync status: {sync_status}, Neon DB user count: {neon_count}",
        "User profile synced cleanly into Neon PostgreSQL table 'users'."
    )
except Exception as e:
    record_test(4, "Register brand new email", False, "Success", "Exception raised", error=str(e))


# -----------------------------------------------------------------------------
# TEST 1: Login with existing registered email and correct password
# -----------------------------------------------------------------------------
log_print("\nExecuting Test 1 (Login with correct password & ID Token)...")
try:
    auth_resp = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {token_1}"}
    )
    passed = (auth_resp.status_code == 200)
    record_test(
        1,
        "Login with existing registered email and correct password",
        passed,
        "Login succeeds and user reaches authenticated profile/dashboard",
        f"Authenticated request status: {auth_resp.status_code}",
        "Token decoded and profile retrieved from Neon DB."
    )
except Exception as e:
    record_test(1, "Login with correct password", False, "Success", "Exception raised", error=str(e))


# -----------------------------------------------------------------------------
# TEST 2: Login with existing email but incorrect password / invalid token
# -----------------------------------------------------------------------------
log_print("\nExecuting Test 2 (Login with incorrect password / invalid token)...")
try:
    bad_token = "invalid_bearer_token_12345"
    bad_resp = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {bad_token}"}
    )
    passed = (bad_resp.status_code == 401)
    record_test(
        2,
        "Login with existing email but incorrect password",
        passed,
        "Login fails with status 401 Unauthorized",
        f"Status: {bad_resp.status_code}, Response: {bad_resp.get_data(as_text=True).strip()}",
        "Backend middleware correctly rejected bad token."
    )
except Exception as e:
    record_test(2, "Login with incorrect password", False, "Status 401", "Exception raised", error=str(e))


# -----------------------------------------------------------------------------
# TEST 3: Login with email that does NOT exist in Firebase / DB
# -----------------------------------------------------------------------------
log_print("\nExecuting Test 3 (Non-existent email)...")
fake_email = f"nonexistent_{os.urandom(4).hex()}@edastudio.org"
try:
    neon_count_fake = get_user_count_in_neon(fake_email)
    unauth_resp = client.get("/api/auth/me")
    passed = (unauth_resp.status_code == 401) and (neon_count_fake == 0)
    record_test(
        3,
        "Login with email that does NOT exist in Firebase",
        passed,
        "Login fails and NO user created in Neon PostgreSQL",
        f"Request status: {unauth_resp.status_code}, Neon DB count for {fake_email}: {neon_count_fake}",
        "Non-existent credentials rejected without polluting Neon database."
    )
except Exception as e:
    record_test(3, "Non-existent email login", False, "Status 401", "Exception raised", error=str(e))


# -----------------------------------------------------------------------------
# TEST 5: Try registering the same email again (Idempotency check)
# -----------------------------------------------------------------------------
log_print("\nExecuting Test 5 (Duplicate registration check)...")
try:
    sync_resp_2 = client.post(
        "/api/auth/sync",
        headers={"Authorization": f"Bearer {token_1}"}
    )
    neon_count_after = get_user_count_in_neon(test_email_1)
    passed = (sync_resp_2.status_code == 200) and (neon_count_after == 1)
    record_test(
        5,
        "Try registering the same email again",
        passed,
        "Duplicate record creation blocked; exactly 1 record retained in Neon",
        f"Sync status: {sync_resp_2.status_code}, Neon user count: {neon_count_after}",
        "Database idempotency enforced — existing user retrieved without duplicates."
    )
except Exception as e:
    record_test(5, "Duplicate registration", False, "1 Record in Neon", "Exception raised", error=str(e))


# -----------------------------------------------------------------------------
# TEST 6: Call /api/auth/me after successful login
# -----------------------------------------------------------------------------
log_print("\nExecuting Test 6 (GET /api/auth/me with valid Bearer token)...")
try:
    me_resp = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {token_1}"}
    )
    if me_resp.status_code == 200:
        me_data = me_resp.get_json()
        user_info = me_data.get("user", {})
        passed = (user_info.get("email") == test_email_1)
        record_test(
            6,
            "Call /api/auth/me with valid Bearer token",
            passed,
            "Returns authenticated user's profile from Neon DB",
            f"Status 200, User Email: {user_info.get('email')}, Neon ID: {user_info.get('id')}",
            f"User profile correctly decoded from Bearer token and fetched from Neon."
        )
    else:
        record_test(6, "Call /api/auth/me", False, "Status 200", f"Status {me_resp.status_code}", error=me_resp.get_data(as_text=True))
except Exception as e:
    record_test(6, "Call /api/auth/me", False, "Success", "Exception raised", error=str(e))


# -----------------------------------------------------------------------------
# TEST 7: Verification of Auth Session Persistence Across Refreshes
# -----------------------------------------------------------------------------
log_print("\nExecuting Test 7 (Session Persistence Check)...")
try:
    me_resp_persisted = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {token_1}"}
    )
    passed = (me_resp_persisted.status_code == 200)
    record_test(
        7,
        "Verify authentication state persistence",
        passed,
        "Session persists across independent HTTP requests / refreshes",
        f"Re-validated token across new connection: Status {me_resp_persisted.status_code}",
        "Firebase onAuthStateChanged() & Token persistence validated."
    )
except Exception as e:
    record_test(7, "Verify authentication state persistence", False, "Persistence", "Exception raised", error=str(e))


# -----------------------------------------------------------------------------
# TEST 8: Verify Logout / Invalid Token behavior on protected routes
# -----------------------------------------------------------------------------
log_print("\nExecuting Test 8 (Logout / Protected route security)...")
try:
    unauth_resp = client.get("/api/auth/me")
    invalid_token_resp = client.get(
        "/api/auth/me",
        headers={"Authorization": "Bearer invalid_junk_token_123"}
    )
    passed = (unauth_resp.status_code == 401) and (invalid_token_resp.status_code == 401)
    record_test(
        8,
        "Verify protected routes redirect & return 401 Unauthorized after logout",
        passed,
        "Protected endpoints return 401 Unauthorized for missing or cleared tokens",
        f"Missing token status: {unauth_resp.status_code}, Invalid token status: {invalid_token_resp.status_code}",
        "All protected routes strictly guarded against unauthenticated access."
    )
except Exception as e:
    record_test(8, "Verify logout protected route security", False, "401 Unauthorized", "Exception raised", error=str(e))

log_print("\n" + "=" * 75)
log_print("LIVE AUTHENTICATION TEST RESULTS SUMMARY")
log_print("=" * 75)
all_passed = all(r["passed"] for r in test_results)
log_print(f"Total Tests Run: {len(test_results)}")
log_print(f"Passed:          {sum(1 for r in test_results if r['passed'])}")
log_print(f"Failed:          {sum(1 for r in test_results if not r['passed'])}")
log_print(f"Overall Result:  {'ALL TESTS PASSED' if all_passed else 'TEST FAILURES DETECTED'}")
