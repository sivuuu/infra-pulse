import re
from typing import Tuple

SENSITIVE_PATTERNS = [
    # Passwords in URLs or key-value pairs
    (re.compile(r'(password|passwd|pwd|secret|api_key|apikey|access_token|auth_token)\s*[:=]\s*([^\s,;\'"]+)', re.IGNORECASE), r'\1=***REDACTED***'),
    # Bearer tokens and JWTs
    (re.compile(r'(Bearer\s+)[A-Za-z0-9-_=]+\.[A-Za-z0-9-_=]+\.?[A-Za-z0-9-_.+/=]*', re.IGNORECASE), r'\1***REDACTED_JWT***'),
    (re.compile(r'(Bearer\s+)[A-Za-z0-9_\-\.]{20,}', re.IGNORECASE), r'\1***REDACTED_TOKEN***'),
    # Private keys
    (re.compile(r'-----BEGIN\s+([A-Z\s]+)KEY-----[^-]+-----END\s+\1KEY-----', re.DOTALL), r'-----BEGIN \1KEY----- ***REDACTED_PRIVATE_KEY*** -----END \1KEY-----'),
    # Database URIs with credentials: e.g. postgres://user:secret@host:5432/db
    (re.compile(r'(://[^:]+:)([^@]+)(@)', re.IGNORECASE), r'\1***REDACTED***\3'),
    # AWS / Generic Secret keys
    (re.compile(r'(AKIA[0-9A-Z]{16})', re.IGNORECASE), r'***REDACTED_AWS_KEY***'),
]

def sanitize_log_message(message: str) -> Tuple[str, bool]:
    """
    Sanitize sensitive information from log entries.
    Returns: (cleaned_message, was_redacted)
    """
    if not message:
        return "", False

    cleaned = message
    was_redacted = False
    
    for pattern, replacement in SENSITIVE_PATTERNS:
        new_text = pattern.sub(replacement, cleaned)
        if new_text != cleaned:
            was_redacted = True
            cleaned = new_text

    return cleaned, was_redacted
