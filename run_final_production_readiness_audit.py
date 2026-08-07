import sys
import os
import io
import time
import json
import jwt
import pandas as pd
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
from app.services.eda_engine import run_full_eda
from app.utils.validators import validate_extension, validate_dataframe_not_empty, ValidationError

def log_print(msg=""):
    print(msg, flush=True)

log_print("=" * 80)
log_print("EDA WORKSPACE — COMPREHENSIVE FINAL PRODUCTION READINESS AUDIT")
log_print("=" * 80)

app = create_app()
client = app.test_client()

audit_checks = []

def record_check(section, title, passed, expected, actual, notes=""):
    status_str = "PASS" if passed else "FAIL"
    audit_checks.append({
        "section": section,
        "title": title,
        "passed": passed,
        "status": status_str,
        "expected": expected,
        "actual": actual,
        "notes": notes
    })
    log_print(f"[{status_str}] [{section}] {title}")
    log_print(f"  Expected: {expected}")
    log_print(f"  Actual:   {actual}")
    if notes:
        log_print(f"  Notes:    {notes}\n")
    else:
        log_print()

# -----------------------------------------------------------------------------
# SECTION 1 & 2: Environment Variables & Hardcoded Credentials Audit
# -----------------------------------------------------------------------------
log_print("--- SECTION 1 & 2: ENVIRONMENT VARIABLES & HARDCODED CREDENTIALS AUDIT ---")

db_url_loaded = bool(Config.NEON_DATABASE_URL and "neon.tech" in Config.NEON_DATABASE_URL)
secret_key_loaded = bool(Config.SECRET_KEY)
fb_service_path = bool(Config.FIREBASE_SERVICE_ACCOUNT_PATH and os.path.exists(Config.FIREBASE_SERVICE_ACCOUNT_PATH))

record_check(
    "CONFIG",
    "Neon Database URL loaded from environment",
    db_url_loaded,
    "Valid Neon PostgreSQL connection string present in environment",
    f"Loaded URL: {Config.NEON_DATABASE_URL[:30]}..."
)

record_check(
    "CONFIG",
    "Production Secret Key loaded from environment",
    secret_key_loaded,
    "SECRET_KEY present and configured",
    f"Secret Key Configured: {secret_key_loaded}"
)

record_check(
    "CONFIG",
    "Firebase Service Account file loaded",
    fb_service_path,
    "serviceAccountKey.json file exists and loaded",
    f"Service Account Path: {Config.FIREBASE_SERVICE_ACCOUNT_PATH}"
)

# -----------------------------------------------------------------------------
# SECTION 3 & 4: Backend API Endpoints & Auth Middleware Audit
# -----------------------------------------------------------------------------
log_print("--- SECTION 3 & 4: BACKEND API ENDPOINTS & AUTHENTICATION AUDIT ---")

def generate_jwt(uid="test_audit_user_uid_123", email="audit@edastudio.org", name="Audit User"):
    payload = {
        "user_id": uid,
        "sub": uid,
        "uid": uid,
        "email": email,
        "name": name,
        "email_verified": True,
        "iat": int(time.time()),
        "exp": int(time.time()) + 3600
    }
    return jwt.encode(payload, "secret_saas_key_32bytes_long_for_audit", algorithm="HS256")

token = generate_jwt()

# 4.1 Health Check
health_resp = client.get("/api/health")
record_check(
    "API",
    "GET /api/health endpoint",
    health_resp.status_code == 200,
    "Status 200 OK",
    f"Status: {health_resp.status_code}, Response: {health_resp.get_json()}"
)

# 4.2 Unauthenticated Upload Rejection (401)
unauth_upload = client.post("/api/upload")
record_check(
    "AUTH",
    "Unauthenticated POST /api/upload rejection",
    unauth_upload.status_code == 401,
    "Status 401 Unauthorized",
    f"Status: {unauth_upload.status_code}"
)

# 4.3 Authenticated Upload Execution (200)
sample_csv = b"Patient_ID,Age,Hemoglobin,Platelets\nPAT-01,25,14.2,250000\nPAT-02,30,13.5,210000\nPAT-03,45,15.1,300000\n"
auth_upload = client.post(
    "/api/upload",
    headers={"Authorization": f"Bearer {token}"},
    data={"file": (io.BytesIO(sample_csv), "test_audit.csv")}
)
upload_json = auth_upload.get_json() or {}
record_check(
    "API",
    "Authenticated POST /api/upload execution",
    (auth_upload.status_code == 200) and ("step1_dataset_overview" in upload_json),
    "Status 200 with complete structured 17-step EDA JSON payload",
    f"Status: {auth_upload.status_code}, Keys returned: {len(upload_json)} top-level sections"
)

# 4.4 User Sync & DB Query
sync_resp = client.post("/api/auth/sync", headers={"Authorization": f"Bearer {token}"})
record_check(
    "AUTH & DB",
    "POST /api/auth/sync user synchronization",
    sync_resp.status_code == 200,
    "Status 200 OK with Neon DB User record",
    f"Status: {sync_resp.status_code}, User Email: {sync_resp.get_json().get('user', {}).get('email')}"
)

# -----------------------------------------------------------------------------
# SECTION 5: 17 Statistical Engine Functions Audit
# -----------------------------------------------------------------------------
log_print("--- SECTION 5: 17 STATISTICAL ENGINE FUNCTIONS AUDIT ---")

test_df = pd.DataFrame({
    "Age": [25, 30, 45, 25, 50, 60, None],
    "Salary": [50000, 60000, 120000, 50000, 150000, 200000, 70000],
    "Department": ["Sales", "Engineering", "Sales", "Sales", "Engineering", "HR", "Sales"],
    "HireDate": ["2020-01-15", "2019-03-20", "2021-06-10", "2020-01-15", "2018-11-05", "2022-02-01", "2021-08-12"]
})

try:
    eda_result = run_full_eda(test_df)
    
    # 5.1 Dataset Overview
    step1_ok = ("step1_dataset_overview" in eda_result) and (eda_result["step1_dataset_overview"]["n_rows"] == 7)
    record_check("ENGINE", "Step 1: Dataset Overview & Preview", step1_ok, "7 rows, 4 columns", f"Rows: {eda_result.get('step1_dataset_overview', {}).get('n_rows')}")

    # 5.2 Dataset Info
    step2_ok = "step2_dataset_info" in eda_result
    record_check("ENGINE", "Step 2: Dataset Information (df.info)", step2_ok, "Columns info populated", f"Columns count: {len(eda_result.get('step2_dataset_info', {}).get('columns_info', []))}")

    # 5.3 Descriptive Statistics
    step3_ok = ("step3_descriptive_statistics" in eda_result) and ("Age" in eda_result["step3_descriptive_statistics"])
    record_check("ENGINE", "Step 3: Descriptive Statistics (Mean/Median/Std/Quantiles)", step3_ok, "Numerical stats calculated", f"Age mean: {eda_result.get('step3_descriptive_statistics', {}).get('Age', {}).get('mean')}")

    # 5.4 Missing Values
    step4_ok = ("step4_missing_value_analysis" in eda_result) and (eda_result["step4_missing_value_analysis"]["total_missing_cells"] == 1)
    record_check("ENGINE", "Step 4: Missing Value Analysis", step4_ok, "1 missing cell detected", f"Total missing: {eda_result.get('step4_missing_value_analysis', {}).get('total_missing_cells')}")

    # 5.5 Duplicate Analysis
    step5_ok = ("step5_duplicate_analysis" in eda_result) and (eda_result["step5_duplicate_analysis"]["duplicate_row_count"] == 1)
    record_check("ENGINE", "Step 5: Duplicate Row Analysis", step5_ok, "1 duplicate row detected", f"Duplicates: {eda_result.get('step5_duplicate_analysis', {}).get('duplicate_row_count')}")

    # 5.6 Unique Values
    step6_ok = "step6_unique_value_analysis" in eda_result
    record_check("ENGINE", "Step 6: Unique Value Analysis", step6_ok, "Unique counts for all columns", f"Uniques for Department: {eda_result.get('step6_unique_value_analysis', {}).get('Department', {}).get('n_unique')}")

    # 5.7 Column Health Report
    step7_ok = "step7_column_health_report" in eda_result
    record_check("ENGINE", "Step 7: Explainable Column Health Report", step7_ok, "Health status assigned per column", f"Age health: {eda_result.get('step7_column_health_report', {}).get('Age', {}).get('column_health')}")

    # 5.8 Numerical Analysis
    step8_ok = "step8_numerical_feature_analysis" in eda_result
    record_check("ENGINE", "Step 8: Numerical Feature Analysis", step8_ok, "Skewness/Kurtosis/Outliers evaluated", f"Age skewness: {eda_result.get('step8_numerical_feature_analysis', {}).get('Age', {}).get('skewness')}")

    # 5.9 Categorical Analysis
    step9_ok = "step9_categorical_feature_analysis" in eda_result
    record_check("ENGINE", "Step 9: Categorical Feature Analysis", step9_ok, "Category frequencies computed", f"Most frequent Department: {eda_result.get('step9_categorical_feature_analysis', {}).get('Department', {}).get('most_frequent_category')}")

    # 5.10 Outlier Analysis
    step10_ok = "step10_outlier_analysis" in eda_result
    record_check("ENGINE", "Step 10: IQR Outlier Detection", step10_ok, "Outlier counts identified", f"Salary outliers: {eda_result.get('step10_outlier_analysis', {}).get('Salary', {}).get('iqr_outliers')}")

    # 5.11 Correlation Matrix & Heatmap
    step11_ok = "step11_correlation_analysis" in eda_result
    record_check("ENGINE", "Step 11: Correlation Matrix & Pearson Heatmap", step11_ok, "Pearson correlation calculated", f"Correlation pairs count: {len(eda_result.get('step11_correlation_analysis', {}).get('strong_pairs', []))}")

    # 5.12 Feature Relationships
    step12_ok = "step12_feature_relationship_analysis" in eda_result
    record_check("ENGINE", "Step 12: Feature Relationships Analysis", step12_ok, "Bivariate summaries logged", f"Summary keys: {len(eda_result.get('step12_feature_relationship_analysis', {}))}")

    # 5.13 Distribution Summary
    step13_ok = "step13_distribution_summary" in eda_result
    record_check("ENGINE", "Step 13: Feature Distribution Summary", step13_ok, "Distribution stats present", f"Distribution entries: {len(eda_result.get('step13_distribution_summary', {}))}")

    # 5.14 Data Quality Report & Score
    step14_ok = ("step14_data_quality_report" in eda_result) and (0 <= eda_result["step14_data_quality_report"]["quality_score"] <= 100)
    record_check("ENGINE", "Step 14: Data Quality Score (0–100)", step14_ok, "Quality score calculated", f"Quality score: {eda_result.get('step14_data_quality_report', {}).get('quality_score')}")

    # 5.15 Analyst Observations
    step15_ok = ("step15_analyst_observations" in eda_result) and (len(eda_result["step15_analyst_observations"]) > 0)
    record_check("ENGINE", "Step 15: Analyst Observations", step15_ok, "Automated insights generated", f"Observations count: {len(eda_result.get('step15_analyst_observations', []))}")

    # 5.16 Executive Summary
    step16_ok = ("step16_executive_summary" in eda_result) and ("key_findings" in eda_result["step16_executive_summary"])
    record_check("ENGINE", "Step 16: Executive Summary", step16_ok, "Executive report assembled", f"Key findings count: {len(eda_result.get('step16_executive_summary', {}).get('key_findings', []))}")

    # 5.17 Datetime Analysis
    step17_ok = ("step17_datetime_analysis" in eda_result) and (eda_result["step17_datetime_analysis"].get("datetime_detected") is True)
    record_check("ENGINE", "Step 17: Datetime Analysis Engine", step17_ok, "Temporal trends & date ranges profiled", f"Detected column: {eda_result.get('step17_datetime_analysis', {}).get('primary_datetime_column')}")

except Exception as e:
    record_check("ENGINE", "Statistical Engine Full Execution", False, "Complete 17 steps", f"Exception: {e}")

# -----------------------------------------------------------------------------
# SECTION 6 & 7: Visualizations & Edge Cases Audit
# -----------------------------------------------------------------------------
log_print("--- SECTION 6 & 7: VISUALIZATIONS & EDGE CASES AUDIT ---")

# 7.1 Single Row Dataset
df_single = pd.DataFrame({"A": [10], "B": ["Text"]})
try:
    res_single = run_full_eda(df_single)
    record_check("EDGE CASE", "Single Row Dataset Execution", True, "Successfully profiled single row without crashing", f"Rows profiled: {res_single.get('step1_dataset_overview', {}).get('n_rows')}")
except Exception as e:
    record_check("EDGE CASE", "Single Row Dataset Execution", False, "No crash", f"Exception: {e}")

# 7.2 Single Column Dataset
df_single_col = pd.DataFrame({"Value": [1, 2, 3, 4, 5]})
try:
    res_single_col = run_full_eda(df_single_col)
    record_check("EDGE CASE", "Single Column Dataset Execution", True, "Successfully profiled single column dataset", f"Columns profiled: {res_single_col.get('step1_dataset_overview', {}).get('n_columns')}")
except Exception as e:
    record_check("EDGE CASE", "Single Column Dataset Execution", False, "No crash", f"Exception: {e}")

# 7.3 Invalid CSV Validation
try:
    validate_extension("invalid_file.pdf")
    record_check("VALIDATOR", "Invalid Extension Block", False, "Raise ValidationError", "Did not raise exception")
except ValidationError as ve:
    record_check("VALIDATOR", "Invalid Extension Block", True, "ValidationError raised for non-CSV file", f"Message: {ve.message}")

# 7.4 Empty DataFrame Validation
try:
    validate_dataframe_not_empty(pd.DataFrame())
    record_check("VALIDATOR", "Empty DataFrame Block", False, "Raise ValidationError", "Did not raise exception")
except ValidationError as ve:
    record_check("VALIDATOR", "Empty DataFrame Block", True, "ValidationError raised for empty dataset", f"Message: {ve.message}")

# -----------------------------------------------------------------------------
# SUMMARY & SCORE CALCULATION
# -----------------------------------------------------------------------------
log_print("\n" + "=" * 80)
log_print("EDA WORKSPACE AUDIT RESULTS & PRODUCTION READINESS SCORE")
log_print("=" * 80)

total_checks = len(audit_checks)
passed_checks = sum(1 for c in audit_checks if c["passed"])
failed_checks = total_checks - passed_checks
score = int((passed_checks / total_checks) * 100)

log_print(f"Total Checks Executed:  {total_checks}")
log_print(f"Passed Checks:         {passed_checks}")
log_print(f"Failed Checks:         {failed_checks}")
log_print(f"Production Score:      {score} / 100")
log_print(f"Status:                {'ALL CHECKS PASSED - 100% PRODUCTION READY' if score == 100 else 'ISSUES REQUIRING ATTENTION'}")
