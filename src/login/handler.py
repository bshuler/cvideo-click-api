"""
Login API Lambda function - handles user authentication endpoints.
"""

import json
import os
import sys
from typing import Dict, Any

# Setup path for shared modules
sys.path.append(os.path.dirname(os.path.dirname(__file__)))  # noqa: E402

from shared.utils import (  # noqa: E402
    setup_logging,
    create_response,
    create_error_response,
    validate_required_fields,
)
from shared.auth import (  # noqa: E402
    create_jwt_token,
    require_authentication,
    hash_password,
    verify_password,
    validate_email,
    validate_password_strength,
    generate_user_id,
    sanitize_user_data,
)
from shared.database import UserManager  # noqa: E402

logger = setup_logging(__name__)


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for Login API endpoints.

    Args:
        event: API Gateway event data
        context: Lambda context object

    Returns:
        API Gateway response format
    """
    try:
        logger.info(
            f"Processing request: {event.get('httpMethod')} {event.get('path')}"
        )

        # Get request details
        http_method = event.get("httpMethod", "GET")
        path = event.get("path", "")

        # Route requests to appropriate handlers
        if http_method == "POST" and path.endswith("/register"):
            return handle_register(event)
        elif http_method == "POST" and path.endswith("/login"):
            return handle_login(event)
        elif http_method == "POST" and path.endswith("/refresh"):
            return handle_token_refresh(event)
        elif http_method == "GET" and path.endswith("/profile"):
            return handle_get_profile(event)
        elif http_method == "PUT" and path.endswith("/profile"):
            return handle_update_profile(event)
        else:
            return create_error_response(404, "Endpoint not found", "NOT_FOUND")

    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return create_error_response(500, "Internal server error", "INTERNAL_ERROR")


def handle_register(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle user registration.

    Args:
        event: API Gateway event

    Returns:
        API Gateway response
    """
    try:
        # Parse request body
        body = json.loads(event.get("body", "{}"))

        # Validate required fields
        required_fields = ["email", "password", "first_name", "last_name"]
        validation_error = validate_required_fields(body, required_fields)
        if validation_error:
            return create_error_response(400, validation_error, "MISSING_FIELDS")

        email = body["email"].lower().strip()
        password = body["password"]
        first_name = body["first_name"].strip()
        last_name = body["last_name"].strip()

        # Validate email format
        if not validate_email(email):
            return create_error_response(400, "Invalid email format", "INVALID_EMAIL")

        # Validate password strength
        password_validation = validate_password_strength(password)
        if not password_validation["valid"]:
            return create_error_response(
                400,
                "Password does not meet requirements",
                "WEAK_PASSWORD",
                {"errors": password_validation["errors"]},
            )

        # Initialize user manager
        user_manager = UserManager()

        # Check if email already exists
        if user_manager.email_exists(email):
            return create_error_response(
                400, "Email address already registered", "EMAIL_EXISTS"
            )

        # Create new user
        user_id = generate_user_id()
        password_hash = hash_password(password)

        user_data = {
            "user_id": user_id,
            "email": email,
            "password_hash": password_hash,
            "first_name": first_name,
            "last_name": last_name,
        }

        # Store user in database
        created_user = user_manager.create_user(user_data)
        if not created_user:
            return create_error_response(
                500, "Failed to create user account", "CREATE_FAILED"
            )

        # Generate JWT token
        token = create_jwt_token(
            user_id=user_id, email=email, first_name=first_name, last_name=last_name
        )

        # Return success response with sanitized user data
        safe_user_data = sanitize_user_data(created_user)

        return create_response(201, {"user": safe_user_data, "token": token})

    except json.JSONDecodeError:
        return create_error_response(
            400, "Invalid JSON in request body", "INVALID_JSON"
        )
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        return create_error_response(500, "Registration failed", "REGISTRATION_ERROR")


def handle_login(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle user login.

    Args:
        event: API Gateway event

    Returns:
        API Gateway response
    """
    try:
        # Parse request body
        body = json.loads(event.get("body", "{}"))

        # Validate required fields
        required_fields = ["email", "password"]
        validation_error = validate_required_fields(body, required_fields)
        if validation_error:
            return create_error_response(400, validation_error, "MISSING_FIELDS")

        email = body["email"].lower().strip()
        password = body["password"]

        # Initialize user manager
        user_manager = UserManager()

        # Get user by email
        user = user_manager.get_user_by_email(email)
        if not user:
            return create_error_response(
                401, "Invalid credentials", "INVALID_CREDENTIALS"
            )

        # Check if account is active
        if not user.get("is_active", False):
            return create_error_response(403, "Account is inactive", "ACCOUNT_INACTIVE")

        # Verify password
        if not verify_password(password, user.get("password_hash", "")):
            return create_error_response(
                401, "Invalid credentials", "INVALID_CREDENTIALS"
            )

        # Update last login timestamp
        user_manager.update_last_login(user["user_id"])

        # Generate JWT token
        token = create_jwt_token(
            user_id=user["user_id"],
            email=user["email"],
            first_name=user.get("first_name", ""),
            last_name=user.get("last_name", ""),
        )

        # Return success response with sanitized user data
        safe_user_data = sanitize_user_data(user)

        return create_response(200, {"user": safe_user_data, "token": token})

    except json.JSONDecodeError:
        return create_error_response(
            400, "Invalid JSON in request body", "INVALID_JSON"
        )
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        return create_error_response(500, "Login failed", "LOGIN_ERROR")


def handle_token_refresh(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle JWT token refresh.

    Args:
        event: API Gateway event

    Returns:
        API Gateway response
    """
    try:
        # Require authentication
        user_data = require_authentication(event)
        if not user_data:
            return create_error_response(401, "Authentication required", "UNAUTHORIZED")

        # Initialize user manager
        user_manager = UserManager()

        # Get current user data from database
        user = user_manager.get_user_by_id(user_data["user_id"])
        if not user:
            return create_error_response(404, "User not found", "USER_NOT_FOUND")

        # Check if account is still active
        if not user.get("is_active", False):
            return create_error_response(403, "Account is inactive", "ACCOUNT_INACTIVE")

        # Generate new JWT token
        token = create_jwt_token(
            user_id=user["user_id"],
            email=user["email"],
            first_name=user.get("first_name", ""),
            last_name=user.get("last_name", ""),
        )

        return create_response(200, {"token": token})

    except Exception as e:
        logger.error(f"Token refresh error: {str(e)}")
        return create_error_response(500, "Token refresh failed", "REFRESH_ERROR")


def handle_get_profile(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle get user profile.

    Args:
        event: API Gateway event

    Returns:
        API Gateway response
    """
    try:
        # Require authentication
        user_data = require_authentication(event)
        if not user_data:
            return create_error_response(401, "Authentication required", "UNAUTHORIZED")

        # Initialize user manager
        user_manager = UserManager()

        # Get current user data from database
        user = user_manager.get_user_by_id(user_data["user_id"])
        if not user:
            return create_error_response(404, "User not found", "USER_NOT_FOUND")

        # Return sanitized user data
        safe_user_data = sanitize_user_data(user)

        return create_response(200, {"user": safe_user_data})

    except Exception as e:
        logger.error(f"Get profile error: {str(e)}")
        return create_error_response(500, "Failed to get profile", "PROFILE_ERROR")


def handle_update_profile(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle update user profile.

    Args:
        event: API Gateway event

    Returns:
        API Gateway response
    """
    try:
        # Require authentication
        user_data = require_authentication(event)
        if not user_data:
            return create_error_response(401, "Authentication required", "UNAUTHORIZED")

        # Parse request body
        body = json.loads(event.get("body", "{}"))

        # Define allowed fields for update
        allowed_fields = ["first_name", "last_name", "profile_data"]
        updates = {}

        for field in allowed_fields:
            if field in body:
                if field in ["first_name", "last_name"]:
                    updates[field] = str(body[field]).strip()
                else:
                    updates[field] = body[field]

        if not updates:
            return create_error_response(400, "No valid fields to update", "NO_UPDATES")

        # Initialize user manager
        user_manager = UserManager()

        # Update user profile
        updated_user = user_manager.update_user(user_data["user_id"], updates)
        if not updated_user:
            return create_error_response(
                500, "Failed to update profile", "UPDATE_FAILED"
            )

        # Return sanitized updated user data
        safe_user_data = sanitize_user_data(updated_user)

        return create_response(200, {"user": safe_user_data})

    except json.JSONDecodeError:
        return create_error_response(
            400, "Invalid JSON in request body", "INVALID_JSON"
        )
    except Exception as e:
        logger.error(f"Update profile error: {str(e)}")
        return create_error_response(500, "Failed to update profile", "UPDATE_ERROR")
