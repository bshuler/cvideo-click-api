"""Unit tests for hello_world Lambda function."""

import json
from unittest.mock import MagicMock
from src.hello_world.handler import (
    lambda_handler,
    handle_get_request,
    handle_post_request,
)


def test_lambda_handler_get() -> None:
    """Test lambda_handler with GET request."""
    event = {
        "httpMethod": "GET",
        "path": "/hello",
        "queryStringParameters": {"name": "Alice"},
    }
    context = MagicMock()

    response = lambda_handler(event, context)

    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert body["message"] == "Hello, Alice!"
    assert body["method"] == "GET"


def test_lambda_handler_post() -> None:
    """Test lambda_handler with POST request."""
    event = {
        "httpMethod": "POST",
        "path": "/hello",
        "body": json.dumps({"name": "Bob", "message": "Hi"}),
    }
    context = MagicMock()

    response = lambda_handler(event, context)

    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert body["message"] == "Hi, Bob!"
    assert body["method"] == "POST"


def test_lambda_handler_invalid_method() -> None:
    """Test lambda_handler with invalid HTTP method."""
    event = {"httpMethod": "DELETE", "path": "/hello"}
    context = MagicMock()

    response = lambda_handler(event, context)

    assert response["statusCode"] == 405
    body = json.loads(response["body"])
    assert "Method DELETE not allowed" in body["error"]


def test_lambda_handler_invalid_json() -> None:
    """Test lambda_handler with invalid JSON in POST request."""
    event = {"httpMethod": "POST", "path": "/hello", "body": "invalid json"}
    context = MagicMock()

    response = lambda_handler(event, context)

    assert response["statusCode"] == 400
    body = json.loads(response["body"])
    assert "Invalid JSON" in body["error"]


def test_handle_get_request() -> None:
    """Test handle_get_request function directly."""
    query_params = {"name": "World"}
    response = handle_get_request(query_params)

    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert body["message"] == "Hello, World!"
    assert body["method"] == "GET"


def test_handle_get_request_no_name() -> None:
    """Test handle_get_request with no name parameter."""
    query_params = {}
    response = handle_get_request(query_params)

    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert body["message"] == "Hello, World!"


def test_handle_post_request() -> None:
    """Test handle_post_request function directly."""
    body_data = {"name": "Alice", "message": "Greetings"}
    response = handle_post_request(body_data)

    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert body["message"] == "Greetings, Alice!"
    assert body["method"] == "POST"
    assert body["received_data"] == body_data
