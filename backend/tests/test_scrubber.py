import pytest
from logs.scrubber import sanitize_log_message

def test_scrub_passwords():
    msg = "Connecting to database with password=super_secret_123 and port=5432"
    cleaned, redacted = sanitize_log_message(msg)
    assert redacted is True
    assert "super_secret_123" not in cleaned
    assert "***REDACTED***" in cleaned

def test_scrub_bearer_tokens():
    msg = "User authorization failed: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.e30.signature"
    cleaned, redacted = sanitize_log_message(msg)
    assert redacted is True
    assert "eyJhbGci" not in cleaned
    assert "***REDACTED_JWT***" in cleaned

def test_scrub_database_credentials_in_url():
    msg = "Postgres pool connection to postgres://app_user:prod_db_pass_99@db.internal:5432/core"
    cleaned, redacted = sanitize_log_message(msg)
    assert redacted is True
    assert "prod_db_pass_99" not in cleaned
    assert "***REDACTED***" in cleaned

def test_normal_log_untouched():
    msg = "Server started on port 8080. Ready to accept connections."
    cleaned, redacted = sanitize_log_message(msg)
    assert redacted is False
    assert cleaned == msg
