"""Shared authentication utilities for Lambda functions."""

import jwt
import os
from typing import Dict, Any, Optional
from datetime import datetime, timedelta


def create_jwt_token(user_id: str, email: str, expires_hours: int = 24) -> str:
    """
    Create a JWT token for user authentication.

    Args:
        user_id: Unique user identifier
        email: User email address
        expires_hours: Token expiration in hours

    Returns:
        JWT token string
    """
    secret_key = os.getenv("JWT_SECRET_KEY", "your-secret-key-here")

    payload = {
        "user_id": user_id,
        "email": email,
        "exp": datetime.utcnow() + timedelta(hours=expires_hours),
        "iat": datetime.utcnow(),
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
