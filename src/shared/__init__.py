"""Shared module initialization."""

from .utils import (
    setup_logging,
    create_response,
    create_error_response,
    validate_required_fields,
)
from .auth import (
    create_jwt_token,
    verify_jwt_token,
    require_authentication,
    hash_password,
    verify_password,
    validate_email,
    validate_password_strength,
    generate_user_id,
    sanitize_user_data,
)
from .database import DynamoDBClient, S3Client, UserManager

__all__ = [
    "setup_logging",
    "create_response",
    "create_error_response",
    "validate_required_fields",
    "create_jwt_token",
    "verify_jwt_token",
    "require_authentication",
    "hash_password",
    "verify_password",
    "validate_email",
    "validate_password_strength",
    "generate_user_id",
    "sanitize_user_data",
    "DynamoDBClient",
    "S3Client",
    "UserManager",
]
