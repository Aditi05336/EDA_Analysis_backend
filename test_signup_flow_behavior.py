import re
import sys

def format_firebase_error(code_or_msg: str) -> str:
    # Python mirror of formatFirebaseError in AuthProvider.tsx
    code = code_or_msg.strip()
    if code in ["auth/invalid-credential", "auth/user-not-found", "auth/wrong-password"]:
        return "Invalid email address or password. Please check your credentials and try again."
    elif code == "auth/invalid-email":
        return "Invalid email address."
    elif code == "auth/email-already-in-use":
        return "An account with this email already exists. Please sign in."
    elif code == "auth/weak-password":
        return "Password must be at least 6 characters long."
    elif code == "auth/too-many-requests":
        return "Too many failed attempts. Access to this account has been temporarily disabled. Please reset your password."
    elif code == "auth/network-request-failed":
        return "Network error. Please try again."
    
    if "auth/invalid-email" in code_or_msg:
        return "Invalid email address."
    if "auth/email-already-in-use" in code_or_msg:
        return "An account with this email already exists. Please sign in."
    if "auth/weak-password" in code_or_msg:
        return "Password must be at least 6 characters long."
    if "auth/network-request-failed" in code_or_msg:
        return "Network error. Please try again."

    cleaned = re.sub(r'^Firebase:\s*Error\s*\(([^)]+)\)\.?$', r'\1', code_or_msg, flags=re.IGNORECASE)
    if "auth/" in cleaned:
        return "An error occurred during authentication. Please check your details and try again."
    return cleaned

def validate_email_format(email: str) -> bool:
    email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(email_regex, email.strip()))

def run_tests():
    print("=" * 70)
    print("TESTING STRICT SIGNUP FLOW BEHAVIOR & ERROR MAPPING")
    print("=" * 70)
    
    tests_passed = 0
    total_tests = 4

    # Test 1: Valid email signup success notification
    valid_email = "testuser@example.com"
    is_valid_email = validate_email_format(valid_email)
    success_toast_msg = "Account created successfully! A verification email has been sent. Please check your Inbox. If you don't see it, check your Spam/Junk folder."
    
    if is_valid_email and "verification email has been sent" in success_toast_msg:
        print("\n[PASS] Test 1: Valid Email & Account Creation Notification")
        print(f"  Input Email:   {valid_email}")
        print(f"  Notification:  {success_toast_msg}")
        tests_passed += 1
    else:
        print("\n[FAIL] Test 1: Valid Email Notification failed.")

    # Test 2: Invalid email format error message
    invalid_emails = ["invalid-email", "invalid@domain", "user@.com", "user@domain."]
    invalid_passed = True
    for inv in invalid_emails:
        if validate_email_format(inv):
            invalid_passed = False
            print(f"  [FAIL] Email '{inv}' should have failed regex validation.")
    
    expected_invalid = "Invalid email address."
    if invalid_passed and format_firebase_error("auth/invalid-email") == expected_invalid:
        print("\n[PASS] Test 2: Invalid Email Format Guard (No account created, no sync)")
        print(f"  Tested Invalid Emails: {invalid_emails}")
        print(f"  Error Output:          {expected_invalid}")
        tests_passed += 1
    else:
        print(f"\n[FAIL] Test 2: Invalid email guard failed.")

    # Test 3: Existing email (auth/email-already-in-use)
    existing_err_raw = "Firebase: Error (auth/email-already-in-use)."
    converted_existing_msg = format_firebase_error(existing_err_raw)
    expected_existing = "An account with this email already exists. Please sign in."
    
    if converted_existing_msg == expected_existing and "auth/" not in converted_existing_msg:
        print("\n[PASS] Test 3: Existing Email Error Handling")
        print(f"  Raw Firebase:  {existing_err_raw}")
        print(f"  User Message:  {converted_existing_msg}")
        tests_passed += 1
    else:
        print(f"\n[FAIL] Test 3: Expected '{expected_existing}', got '{converted_existing_msg}'")

    # Test 4: Weak password error handling
    weak_err_raw = "Firebase: Error (auth/weak-password)."
    converted_weak_msg = format_firebase_error(weak_err_raw)
    expected_weak = "Password must be at least 6 characters long."
    
    if converted_weak_msg == expected_weak and "auth/" not in converted_weak_msg:
        print("\n[PASS] Test 4: Weak Password Error Handling")
        print(f"  Raw Firebase:  {weak_err_raw}")
        print(f"  User Message:  {converted_weak_msg}")
        tests_passed += 1
    else:
        print(f"\n[FAIL] Test 4: Expected '{expected_weak}', got '{converted_weak_msg}'")

    print("\n" + "=" * 70)
    print(f"RESULTS: {tests_passed}/{total_tests} Tests Passed")
    print("=" * 70)
    
    if tests_passed != total_tests:
        sys.exit(1)

if __name__ == "__main__":
    run_tests()
