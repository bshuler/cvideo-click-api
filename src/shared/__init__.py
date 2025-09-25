"""Shared module initialization."""

from .utils import (
    setup_logging,
    create_response,
    create_error_response,
    validate_required_fields,
)
from .auth import create_jwt_token, verify_jwt_token, require_authentication
from .database import DynamoDBClient, S3Client

__all__ = [
    "setup_logging",
    "create_response",
    "create_error_response",
    "validate_required_fields",
    "create_jwt_token",
    "verify_jwt_token",
    "require_authentication",
    "DynamoDBClient",
    "S3Client",
]
