"""Shared utilities for Lambda functions."""

import json
import logging
import os
from typing import Any, Dict, Optional


def setup_logging(name: str) -> logging.Logger:
    """
    Set up structured logging for Lambda functions.

    Args:
        name: Logger name (usually __name__)

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)

    # Set log level from environment variable
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    logger.setLevel(getattr(logging, log_level))

    # Configure handler if not already configured
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger


def create_response(
    status_code: int, data: Dict[str, Any], headers: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """
    Create a standardized API Gateway response.

    Args:
        status_code: HTTP status code
        data: Response data dictionary
        headers: Optional additional headers

    Returns:
        API Gateway response format
    """
    default_headers = {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Headers": (
            "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token"
        ),
        "Access-Control-Allow-Methods": "GET,POST,PUT,DELETE,OPTIONS",
    }

    if headers:
        default_headers.update(headers)

    # Format response with success field and data wrapper
    response_body = {"success": True, "data": data}

    return {
        "statusCode": status_code,
        "headers": default_headers,
        "body": json.dumps(response_body),
    }


def create_error_response(
    status_code: int,
    error_message: str,
    error_code: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Create a standardized error response.

    Args:
        status_code: HTTP status code
        error_message: Human-readable error message
        error_code: Optional error code for client handling
        details: Optional additional error details

    Returns:
        API Gateway error response
    """
    default_headers = {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Headers": (
            "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token"
        ),
        "Access-Control-Allow-Methods": "GET,POST,PUT,DELETE,OPTIONS",
    }

    # Format error response with nested structure
    error_obj: Dict[str, Any] = {"message": error_message}
    if error_code:
        error_obj["code"] = error_code
    if details is not None:
        error_obj["details"] = details

    response_body = {"success": False, "error": error_obj}

    return {
        "statusCode": status_code,
        "headers": default_headers,
        "body": json.dumps(response_body),
    }


def validate_required_fields(data: Dict[str, Any], required_fields: list) -> str:
    """
    Validate that required fields are present in the data.

    Args:
        data: Dictionary to validate
        required_fields: List of required field names

    Returns:
        Empty string if valid, error message if invalid
    """
    missing_fields = [field for field in required_fields if field not in data]

    if missing_fields:
        return f"Missing required fields: {', '.join(missing_fields)}"

    return ""
