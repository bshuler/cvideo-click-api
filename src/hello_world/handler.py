"""
Hello World Lambda function - example API endpoint.
"""

import json
import os
import sys
from typing import Dict, Any

# Setup path for shared modules
sys.path.append(os.path.dirname(os.path.dirname(__file__)))  # noqa: E402

import shared.utils  # noqa: E402

# Import specific functions to avoid bcrypt dependency
setup_logging = shared.utils.setup_logging
create_response = shared.utils.create_response
create_error_response = shared.utils.create_error_response

logger = setup_logging(__name__)


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for Hello World API endpoint.

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
        query_params = event.get("queryStringParameters") or {}

        # Optional: Require authentication
        # user = require_authentication(event)
        # if not user:
        #     return create_error_response(
        #         401, "Authentication required", "UNAUTHORIZED"
        #     )

        # Handle different HTTP methods
        if http_method == "GET":
            return handle_get_request(query_params)
        elif http_method == "POST":
            body_str = event.get("body")
            if body_str is None:
                body = {}
            else:
                body = json.loads(body_str)
            return handle_post_request(body)
        else:
            return create_error_response(
                405, f"Method {http_method} not allowed", "METHOD_NOT_ALLOWED"
            )

    except json.JSONDecodeError:
        logger.error("Invalid JSON in request body")
        return create_error_response(
            400, "Invalid JSON in request body", "INVALID_JSON"
        )

    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return create_error_response(500, "Internal server error", "INTERNAL_ERROR")


def handle_get_request(query_params: Dict[str, str]) -> Dict[str, Any]:
    """
    Handle GET request to hello world endpoint.

    Args:
        query_params: Query string parameters

    Returns:
        API Gateway response
    """
    name = query_params.get("name", "World")

    response_data = {
        "message": f"Hello, {name}!",
        "timestamp": "2024-01-01T00:00:00Z",  # Use datetime.utcnow().isoformat()
        "method": "GET",
        "version": "1.0.0",
    }

    return create_response(200, response_data)


def handle_post_request(body: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle POST request to hello world endpoint.

    Args:
        body: Request body data

    Returns:
        API Gateway response
    """
    name = body.get("name", "World")
    message = body.get("message", "Hello")

    response_data = {
        "message": f"{message}, {name}!",
        "timestamp": "2024-01-01T00:00:00Z",  # Use datetime.utcnow().isoformat()
        "method": "POST",
        "received_data": body,
        "version": "1.0.0",
    }

    return create_response(200, response_data)
