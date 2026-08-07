import re
import socket
import logging

logger = logging.getLogger(__name__)

EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')


def validate_email_domain(email: str) -> bool:
    """
    Validates email format and verifies DNS host resolution for the domain.
    Returns True if format is valid and domain DNS resolves, False otherwise.
    """
    if not email or not isinstance(email, str):
        return False
    clean_email = email.strip()
    if not EMAIL_REGEX.match(clean_email):
        return False

    parts = clean_email.split('@')
    if len(parts) != 2:
        return False

    domain = parts[1].strip()
    if not domain or '.' not in domain:
        return False

    try:
        # Perform DNS resolution for domain
        socket.gethostbyname(domain)
        return True
    except Exception as e:
        logger.warning(f"Email domain DNS validation failed for '{domain}': {e}")
        return False
