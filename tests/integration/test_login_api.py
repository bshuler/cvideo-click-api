"""
Integration tests for Login API endpoints.
"""

import json
import os
import pytest
import boto3
from moto import mock_aws
from unittest.mock import patch

from login.handler import lambda_handler
from shared.database import UserManager


@pytest.fixture
def mock_dynamodb_table():
    """Create a mock DynamoDB table for testing."""
    with mock_aws():
        # Create DynamoDB resource
        dynamodb = boto3.resource("dynamodb", region_name="us-east-1")

        # Create table with email as primary key (matching our current schema)
        table = dynamodb.create_table(
            TableName="test-users-table",
            KeySchema=[{"AttributeName": "email", "KeyType": "HASH"}],
            AttributeDefinitions=[
                {"AttributeName": "email", "AttributeType": "S"},
            ],
            ProvisionedThroughput={
                "ReadCapacityUnits": 5,
                "WriteCapacityUnits": 5,
            },
        )

        # Wait for table to be created
        table.wait_until_exists()

        yield table


@pytest.fixture
def sample_user_data():
    """Sample user data for testing."""
    return {
        "email": "test@example.com",
        "password": "SecurePass123!",
        "first_name": "John",
        "last_name": "Doe",
    }


@pytest.fixture
def api_gateway_event():
    """Sample API Gateway event structure."""
    return {
        "httpMethod": "POST",
        "path": "/auth/register",
        "headers": {"Content-Type": "application/json"},
        "body": "",
        "queryStringParameters": None,
    }


class TestUserRegistration:
    """Test user registration functionality."""

    @patch.dict(os.environ, {"DYNAMODB_USERS_TABLE": "test-users-table"})
    def test_successful_registration(
        self, mock_dynamodb_table, sample_user_data, api_gateway_event
    ):
        """Test successful user registration."""
        # Setup
        api_gateway_event["body"] = json.dumps(sample_user_data)

        # Execute
        response = lambda_handler(api_gateway_event, {})

        # Verify
        assert response["statusCode"] == 201
        body = json.loads(response["body"])
        assert body["success"] is True
        assert "user" in body["data"]
        assert "token" in body["data"]
        assert body["data"]["user"]["email"] == sample_user_data["email"]
        assert body["data"]["user"]["first_name"] == sample_user_data["first_name"]
        assert "password_hash" not in body["data"]["user"]  # Sensitive data removed

    @patch.dict(os.environ, {"DYNAMODB_USERS_TABLE": "test-users-table"})
    def test_duplicate_email_registration(
        self, mock_dynamodb_table, sample_user_data, api_gateway_event
    ):
        """Test registration with duplicate email."""
        # Setup - register user first
        api_gateway_event["body"] = json.dumps(sample_user_data)
        response1 = lambda_handler(api_gateway_event, {})
        assert response1["statusCode"] == 201

        # Execute - try to register same email again
        response2 = lambda_handler(api_gateway_event, {})

        # Verify
        assert response2["statusCode"] == 400
        body = json.loads(response2["body"])
        assert body["success"] is False
        assert body["error"]["code"] == "EMAIL_EXISTS"

    def test_invalid_email_format(self, api_gateway_event, sample_user_data):
        """Test registration with invalid email format."""
        # Setup
        sample_user_data["email"] = "invalid-email"
        api_gateway_event["body"] = json.dumps(sample_user_data)

        # Execute
        response = lambda_handler(api_gateway_event, {})

        # Verify
        assert response["statusCode"] == 400
        body = json.loads(response["body"])
        assert body["error"]["code"] == "INVALID_EMAIL"

    def test_weak_password(self, api_gateway_event, sample_user_data):
        """Test registration with weak password."""
        # Setup
        sample_user_data["password"] = "weak"
        api_gateway_event["body"] = json.dumps(sample_user_data)

        # Execute
        response = lambda_handler(api_gateway_event, {})

        # Verify
        assert response["statusCode"] == 400
        body = json.loads(response["body"])
        assert body["error"]["code"] == "WEAK_PASSWORD"
        assert "errors" in body["error"]["details"]

    def test_missing_required_fields(self, api_gateway_event):
        """Test registration with missing required fields."""
        # Setup
        incomplete_data = {"email": "test@example.com"}
        api_gateway_event["body"] = json.dumps(incomplete_data)

        # Execute
        response = lambda_handler(api_gateway_event, {})

        # Verify
        assert response["statusCode"] == 400
        body = json.loads(response["body"])
        assert body["success"] is False


class TestUserLogin:
    """Test user login functionality."""

    @patch.dict(os.environ, {"DYNAMODB_USERS_TABLE": "test-users-table"})
    def test_successful_login(
        self, mock_dynamodb_table, sample_user_data, api_gateway_event
    ):
        """Test successful user login."""
        # Setup - register user first
        api_gateway_event["path"] = "/auth/register"
        api_gateway_event["body"] = json.dumps(sample_user_data)
        register_response = lambda_handler(api_gateway_event, {})
        assert register_response["statusCode"] == 201

        # Execute login
        api_gateway_event["path"] = "/auth/login"
        login_data = {
            "email": sample_user_data["email"],
            "password": sample_user_data["password"],
        }
        api_gateway_event["body"] = json.dumps(login_data)
        response = lambda_handler(api_gateway_event, {})

        # Verify
        assert response["statusCode"] == 200
        body = json.loads(response["body"])
        assert body["success"] is True
        assert "user" in body["data"]
        assert "token" in body["data"]
        assert body["data"]["user"]["email"] == sample_user_data["email"]

    @patch.dict(os.environ, {"DYNAMODB_USERS_TABLE": "test-users-table"})
    def test_invalid_credentials_wrong_password(
        self, mock_dynamodb_table, sample_user_data, api_gateway_event
    ):
        """Test login with wrong password."""
        # Setup - register user first
        api_gateway_event["path"] = "/auth/register"
        api_gateway_event["body"] = json.dumps(sample_user_data)
        register_response = lambda_handler(api_gateway_event, {})
        assert register_response["statusCode"] == 201

        # Execute login with wrong password
        api_gateway_event["path"] = "/auth/login"
        login_data = {"email": sample_user_data["email"], "password": "wrong_password"}
        api_gateway_event["body"] = json.dumps(login_data)
        response = lambda_handler(api_gateway_event, {})

        # Verify
        assert response["statusCode"] == 401
        body = json.loads(response["body"])
        assert body["error"]["code"] == "INVALID_CREDENTIALS"

    @patch.dict(os.environ, {"DYNAMODB_USERS_TABLE": "test-users-table"})
    def test_login_nonexistent_user(self, mock_dynamodb_table, api_gateway_event):
        """Test login with non-existent user."""
        # Execute
        api_gateway_event["path"] = "/auth/login"
        login_data = {
            "email": "nonexistent@example.com",
            "password": "SomePassword123!",
        }
        api_gateway_event["body"] = json.dumps(login_data)
        response = lambda_handler(api_gateway_event, {})

        # Verify
        assert response["statusCode"] == 401
        body = json.loads(response["body"])
        assert body["error"]["code"] == "INVALID_CREDENTIALS"

    @patch.dict(os.environ, {"DYNAMODB_USERS_TABLE": "test-users-table"})
    def test_login_inactive_user(
        self, mock_dynamodb_table, sample_user_data, api_gateway_event
    ):
        """Test login with inactive user account."""
        # Setup - register user first
        api_gateway_event["path"] = "/auth/register"
        api_gateway_event["body"] = json.dumps(sample_user_data)
        register_response = lambda_handler(api_gateway_event, {})
        assert register_response["statusCode"] == 201

        # Deactivate user
        user_manager = UserManager("test-users-table")
        register_body = json.loads(register_response["body"])
        user_id = register_body["data"]["user"]["user_id"]
        user_manager.deactivate_user(user_id)

        # Execute login
        api_gateway_event["path"] = "/auth/login"
        login_data = {
            "email": sample_user_data["email"],
            "password": sample_user_data["password"],
        }
        api_gateway_event["body"] = json.dumps(login_data)
        response = lambda_handler(api_gateway_event, {})

        # Verify
        assert response["statusCode"] == 403
        body = json.loads(response["body"])
        assert body["error"]["code"] == "ACCOUNT_INACTIVE"


class TestTokenRefresh:
    """Test JWT token refresh functionality."""

    @patch.dict(os.environ, {"DYNAMODB_USERS_TABLE": "test-users-table"})
    def test_successful_token_refresh(
        self, mock_dynamodb_table, sample_user_data, api_gateway_event
    ):
        """Test successful token refresh."""
        # Setup - register and login user
        api_gateway_event["path"] = "/auth/register"
        api_gateway_event["body"] = json.dumps(sample_user_data)
        register_response = lambda_handler(api_gateway_event, {})
        assert register_response["statusCode"] == 201

        register_body = json.loads(register_response["body"])
        token = register_body["data"]["token"]

        # Execute token refresh
        api_gateway_event["path"] = "/auth/refresh"
        api_gateway_event["headers"]["Authorization"] = f"Bearer {token}"
        api_gateway_event["body"] = "{}"
        response = lambda_handler(api_gateway_event, {})

        # Verify
        assert response["statusCode"] == 200
        body = json.loads(response["body"])
        assert body["success"] is True
        assert "token" in body["data"]
        assert body["data"]["token"] != token  # New token should be different

    def test_token_refresh_without_auth(self, api_gateway_event):
        """Test token refresh without authentication."""
        # Execute
        api_gateway_event["path"] = "/auth/refresh"
        api_gateway_event["body"] = "{}"
        response = lambda_handler(api_gateway_event, {})

        # Verify
        assert response["statusCode"] == 401
        body = json.loads(response["body"])
        assert body["error"]["code"] == "UNAUTHORIZED"


class TestUserProfile:
    """Test user profile functionality."""

    @patch.dict(os.environ, {"DYNAMODB_USERS_TABLE": "test-users-table"})
    def test_get_profile_success(
        self, mock_dynamodb_table, sample_user_data, api_gateway_event
    ):
        """Test successful profile retrieval."""
        # Setup - register user
        api_gateway_event["path"] = "/auth/register"
        api_gateway_event["body"] = json.dumps(sample_user_data)
        register_response = lambda_handler(api_gateway_event, {})
        assert register_response["statusCode"] == 201

        register_body = json.loads(register_response["body"])
        token = register_body["data"]["token"]

        # Execute get profile
        api_gateway_event["httpMethod"] = "GET"
        api_gateway_event["path"] = "/auth/profile"
        api_gateway_event["headers"]["Authorization"] = f"Bearer {token}"
        api_gateway_event["body"] = None
        response = lambda_handler(api_gateway_event, {})

        # Verify
        assert response["statusCode"] == 200
        body = json.loads(response["body"])
        assert body["success"] is True
        assert "user" in body["data"]
        assert body["data"]["user"]["email"] == sample_user_data["email"]

    @patch.dict(os.environ, {"DYNAMODB_USERS_TABLE": "test-users-table"})
    def test_update_profile_success(
        self, mock_dynamodb_table, sample_user_data, api_gateway_event
    ):
        """Test successful profile update."""
        # Setup - register user
        api_gateway_event["path"] = "/auth/register"
        api_gateway_event["body"] = json.dumps(sample_user_data)
        register_response = lambda_handler(api_gateway_event, {})
        assert register_response["statusCode"] == 201

        register_body = json.loads(register_response["body"])
        token = register_body["data"]["token"]

        # Execute profile update
        api_gateway_event["httpMethod"] = "PUT"
        api_gateway_event["path"] = "/auth/profile"
        api_gateway_event["headers"]["Authorization"] = f"Bearer {token}"
        update_data = {"first_name": "Jane", "profile_data": {"company": "ACME Corp"}}
        api_gateway_event["body"] = json.dumps(update_data)
        response = lambda_handler(api_gateway_event, {})

        # Verify
        assert response["statusCode"] == 200
        body = json.loads(response["body"])
        assert body["success"] is True
        assert body["data"]["user"]["first_name"] == "Jane"
        assert body["data"]["user"]["profile_data"]["company"] == "ACME Corp"

    def test_profile_without_auth(self, api_gateway_event):
        """Test profile access without authentication."""
        # Execute
        api_gateway_event["httpMethod"] = "GET"
        api_gateway_event["path"] = "/auth/profile"
        response = lambda_handler(api_gateway_event, {})

        # Verify
        assert response["statusCode"] == 401
        body = json.loads(response["body"])
        assert body["error"]["code"] == "UNAUTHORIZED"


class TestErrorHandling:
    """Test error handling scenarios."""

    def test_invalid_json_body(self, api_gateway_event):
        """Test handling of invalid JSON in request body."""
        # Execute
        api_gateway_event["path"] = "/auth/register"
        api_gateway_event["body"] = "invalid json"
        response = lambda_handler(api_gateway_event, {})

        # Verify
        assert response["statusCode"] == 400
        body = json.loads(response["body"])
        assert body["error"]["code"] == "INVALID_JSON"

    def test_unsupported_endpoint(self, api_gateway_event):
        """Test handling of unsupported endpoints."""
        # Execute
        api_gateway_event["path"] = "/auth/unsupported"
        api_gateway_event["body"] = "{}"
        response = lambda_handler(api_gateway_event, {})

        # Verify
        assert response["statusCode"] == 404
        body = json.loads(response["body"])
        assert body["error"]["code"] == "NOT_FOUND"

    def test_unsupported_method(self, api_gateway_event):
        """Test handling of unsupported HTTP methods."""
        # Execute
        api_gateway_event["httpMethod"] = "DELETE"
        api_gateway_event["path"] = "/auth/register"
        api_gateway_event["body"] = "{}"
        response = lambda_handler(api_gateway_event, {})

        # Verify
        assert response["statusCode"] == 404
        body = json.loads(response["body"])
        assert body["error"]["code"] == "NOT_FOUND"


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
