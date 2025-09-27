"""Unit tests for shared utilities."""

import json
from unittest.mock import patch
from src.shared.utils import (
    setup_logging,
    create_response,
    create_error_response,
    validate_required_fields,
)


def test_create_response() -> None:
    """Test create_response utility function."""
    body = {"message": "test"}
    response = create_response(200, body)

    assert response["statusCode"] == 200
    assert response["headers"]["Content-Type"] == "application/json"
    assert response["headers"]["Access-Control-Allow-Origin"] == "*"
    response_body = json.loads(response["body"])
    assert response_body["success"] is True
    assert response_body["data"] == {"message": "test"}


def test_create_error_response() -> None:
    """Test create_error_response utility function."""
    response = create_error_response(
        400, "Bad request", "BAD_REQUEST", {"field": "value"}
    )

    assert response["statusCode"] == 400
    body = json.loads(response["body"])
    assert body["success"] is False
    assert body["error"]["code"] == "BAD_REQUEST"
    assert body["error"]["message"] == "Bad request"
    assert body["error"]["details"] == {"field": "value"}


def test_validate_required_fields() -> None:
    """Test validate_required_fields utility function."""
    data = {"name": "test", "email": "test@example.com"}
    required_fields = ["name", "email"]

    # Should pass validation
    result = validate_required_fields(data, required_fields)
    assert result == ""

    # Should fail validation
    result = validate_required_fields(data, ["name", "email", "phone"])
    assert "Missing required fields: phone" in result


@patch.dict("os.environ", {"LOG_LEVEL": "DEBUG"})
def test_setup_logging() -> None:
    """Test setup_logging utility function."""
    logger = setup_logging("test_logger")
    assert logger.name == "test_logger"
    assert logger.level == 10  # DEBUG level
