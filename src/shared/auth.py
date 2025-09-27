"""Shared authentication utilities for Lambda functions."""

import jwt
import os
import re
import uuid
import bcrypt
from typing import Dict, Any, Optional
from datetime import datetime, timedelta


def create_jwt_token(
    user_id: str,
    email: str,
    first_name: str = "",
    last_name: str = "",
    expires_hours: int = 24,
) -> str:
    """
    Create a JWT token for user authentication.

    Args:
        user_id: Unique user identifier
        email: User email address
        first_name: User's first name
        last_name: User's last name
        expires_hours: Token expiration in hours

    Returns:
        JWT token string
    """
    secret_key = os.getenv("JWT_SECRET_KEY", "your-secret-key-here")

    now = datetime.utcnow()
    payload = {
        "user_id": user_id,
        "email": email,
        "first_name": first_name,
        "last_name": last_name,
        "exp": now + timedelta(hours=expires_hours),
        "iat": now,
        "jti": str(uuid.uuid4()),  # Add unique token ID
    }

    return str(jwt.encode(payload, secret_key, algorithm="HS256"))


def verify_jwt_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Verify and decode a JWT token.

    Args:
        token: JWT token string

    Returns:
        Decoded token payload or None if invalid
    """
    try:
        secret_key = os.getenv("JWT_SECRET_KEY", "your-secret-key-here")
        payload = jwt.decode(token, secret_key, algorithms=["HS256"])
        return dict(payload)
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def extract_token_from_event(event: Dict[str, Any]) -> Optional[str]:
    """
    Extract JWT token from API Gateway event.

    Args:
        event: API Gateway event

    Returns:
        JWT token string or None if not found
    """
    # Check Authorization header
    headers = event.get("headers", {})
    auth_header = headers.get("Authorization") or headers.get("authorization")

    if auth_header and auth_header.startswith("Bearer "):
        return str(auth_header[7:])  # Remove 'Bearer ' prefix

    # Check query parameters
    query_params = event.get("queryStringParameters", {})
    if query_params and "token" in query_params:
        return str(query_params["token"])

    return None


def require_authentication(event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Require authentication for a Lambda function.

    Args:
        event: API Gateway event

    Returns:
        User data if authenticated, None if not authenticated
    """
    token = extract_token_from_event(event)

    if not token:
        return None

    return verify_jwt_token(token)


# Password Management Functions


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt.

    Args:
        password: Plain text password

    Returns:
        Hashed password string
    """
    # Get salt rounds from environment or use default
    salt_rounds = int(os.getenv("BCRYPT_ROUNDS", "12"))

    # Generate salt and hash password
    salt = bcrypt.gensalt(rounds=salt_rounds)
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)

    return hashed.decode("utf-8")


def verify_password(password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash.

    Args:
        password: Plain text password
        hashed_password: Bcrypt hashed password

    Returns:
        True if password matches, False otherwise
    """
    try:
        return bcrypt.checkpw(password.encode("utf-8"), hashed_password.encode("utf-8"))
    except (ValueError, TypeError):
        return False


def validate_email(email: str) -> bool:
    """
    Validate email format.

    Args:
        email: Email address to validate

    Returns:
        True if valid email format, False otherwise
    """
    if not email or len(email) > 254:
        return False

    # Check for consecutive dots or leading/trailing dots
    if ".." in email or email.startswith(".") or email.endswith("."):
        return False

    # Split into local and domain parts
    try:
        local, domain = email.rsplit("@", 1)
    except ValueError:
        return False

    if not local or not domain:
        return False

    # Local part validation - no consecutive dots, no leading/trailing dots
    if ".." in local or local.startswith(".") or local.endswith("."):
        return False

    # RFC 5322 compliant email regex (more strict)
    email_pattern = re.compile(r"^[a-zA-Z0-9._+%-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")

    return bool(email_pattern.match(email))


def validate_password_strength(password: str) -> Dict[str, Any]:
    """
    Validate password strength according to security requirements.

    Args:
        password: Password to validate

    Returns:
        Dictionary with validation result and details
    """
    result: Dict[str, Any] = {"valid": True, "errors": []}

    if not password:
        result["valid"] = False
        result["errors"].append("Password is required")
        return result

    if len(password) < 8:
        result["valid"] = False
        result["errors"].append("Password must be at least 8 characters long")

    if len(password) > 128:
        result["valid"] = False
        result["errors"].append("Password must be less than 128 characters")

    if not re.search(r"[A-Z]", password):
        result["valid"] = False
        result["errors"].append("Password must contain at least one uppercase letter")

    if not re.search(r"[a-z]", password):
        result["valid"] = False
        result["errors"].append("Password must contain at least one lowercase letter")

    if not re.search(r"[0-9]", password):
        result["valid"] = False
        result["errors"].append("Password must contain at least one number")

    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        result["valid"] = False
        result["errors"].append("Password must contain at least one special character")

    return result


def generate_user_id() -> str:
    """
    Generate a unique user ID.

    Returns:
        UUID v4 string
    """
    return str(uuid.uuid4())


def sanitize_user_data(user_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Sanitize user data for safe storage and response.

    Args:
        user_data: Raw user data dictionary

    Returns:
        Sanitized user data dictionary (without password_hash)
    """
    safe_data = user_data.copy()

    # Remove sensitive fields
    sensitive_fields = ["password_hash", "password"]
    for field in sensitive_fields:
        safe_data.pop(field, None)

    return safe_data
