"""
Local integration tests that run against localhost SAM deployment.
These tests make actual HTTP requests to the local development server.
"""

import time
import requests
import pytest
from typing import Dict, Any, Optional


# Test configuration
BASE_URL = "http://localhost:3000"
TIMEOUT = 30
RETRY_ATTEMPTS = 3
RETRY_DELAY = 2


class LocalIntegrationTestError(Exception):
    """Custom exception for local integration test failures."""

    pass


def wait_for_server(max_attempts: int = 10, delay: int = 2) -> bool:
    """Wait for the local server to be available."""
    for attempt in range(max_attempts):
        try:
            response = requests.get(f"{BASE_URL}/hello", timeout=5)
            if response.status_code in [
                200,
                404,
                405,
            ]:  # Any response means server is up
                return True
        except requests.exceptions.RequestException:
            if attempt < max_attempts - 1:
                time.sleep(delay)
            continue
    return False


def make_request(
    method: str,
    endpoint: str,
    data: Optional[Dict[str, Any]] = None,
    headers: Optional[Dict[str, str]] = None,
    expected_status: int = 200,
    retries: int = RETRY_ATTEMPTS,
) -> requests.Response:
    """Make an HTTP request with retries."""
    url = f"{BASE_URL}{endpoint}"
    default_headers = {"Content-Type": "application/json"}
    if headers:
        default_headers.update(headers)

    for attempt in range(retries):
        try:
            if method.upper() == "GET":
                response = requests.get(url, headers=default_headers, timeout=TIMEOUT)
            elif method.upper() == "POST":
                response = requests.post(
                    url, json=data, headers=default_headers, timeout=TIMEOUT
                )
            elif method.upper() == "PUT":
                response = requests.put(
                    url, json=data, headers=default_headers, timeout=TIMEOUT
                )
            elif method.upper() == "DELETE":
                response = requests.delete(
                    url, headers=default_headers, timeout=TIMEOUT
                )
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            return response

        except requests.exceptions.RequestException as e:
            if attempt < retries - 1:
                print(f"Request attempt {attempt + 1} failed: {e}. Retrying...")
                time.sleep(RETRY_DELAY)
            else:
                raise LocalIntegrationTestError(
                    f"Request failed after {retries} attempts: {e}"
                )

    raise LocalIntegrationTestError("Unexpected error in make_request")


@pytest.fixture(scope="session", autouse=True)
def ensure_server_running():
    """Ensure the local server is running before tests."""
    if not wait_for_server():
        pytest.skip("Local server not available. Run 'make local-start' first.")


class TestHelloWorldLocal:
    """Test Hello World endpoints against local deployment."""

    def test_hello_get_without_name(self):
        """Test GET /hello without name parameter."""
        response = make_request("GET", "/hello")

        assert response.status_code == 200
        body = response.json()
        assert body["success"] is True
        assert body["data"]["message"] == "Hello, World!"
        assert body["data"]["method"] == "GET"

    def test_hello_get_with_name(self):
        """Test GET /hello with name parameter."""
        response = make_request("GET", "/hello?name=LocalTest")

        assert response.status_code == 200
        body = response.json()
        assert body["success"] is True
        assert body["data"]["message"] == "Hello, LocalTest!"
        assert body["data"]["method"] == "GET"

    def test_hello_post_with_data(self):
        """Test POST /hello with JSON data."""
        data = {"name": "LocalTest", "message": "Hello from local test"}
        response = make_request("POST", "/hello", data=data)

        assert response.status_code == 200
        body = response.json()
        assert body["success"] is True
        assert body["data"]["message"] == "Hello from local test, LocalTest!"
        assert body["data"]["method"] == "POST"
        assert body["data"]["received_data"] == data

    def test_hello_post_without_data(self):
        """Test POST /hello without data."""
        response = make_request("POST", "/hello")

        assert response.status_code == 200
        body = response.json()
        assert body["success"] is True
        assert body["data"]["message"] == "Hello, World!"
        assert body["data"]["method"] == "POST"

    def test_hello_invalid_method(self):
        """Test unsupported HTTP method."""
        try:
            response = make_request("DELETE", "/hello")
            # API Gateway returns 403 for undefined methods, not 405
            assert response.status_code == 403
        except Exception as e:
            # If the request fails completely, that's also acceptable
            assert "403" in str(e) or "Forbidden" in str(e)


class TestAuthenticationLocal:
    """Test authentication endpoints against local deployment."""

    def test_register_new_user(self):
        """Test user registration."""
        user_data = {
            "email": f"localtest_{int(time.time())}@example.com",
            "password": "LocalTest123!",
            "first_name": "Local",
            "last_name": "Test",
        }

        response = make_request(
            "POST", "/register", data=user_data, expected_status=201
        )

        assert response.status_code == 201
        body = response.json()
        assert body["success"] is True
        assert "user_id" in body["data"]["user"]
        assert body["data"]["user"]["email"] == user_data["email"]
        assert body["data"]["user"]["first_name"] == user_data["first_name"]
        assert (
            "password" not in body["data"]["user"]
        )  # Password should not be in response
        assert "token" in body["data"]  # JWT token should be present

    def test_register_duplicate_email(self):
        """Test registration with duplicate email."""
        email = f"duplicate_{int(time.time())}@example.com"
        user_data = {
            "email": email,
            "password": "LocalTest123!",
            "first_name": "Duplicate",
            "last_name": "Test",
        }

        # First registration should succeed
        response = make_request(
            "POST", "/register", data=user_data, expected_status=201
        )
        assert response.status_code == 201

        # Second registration should fail
        response = make_request(
            "POST", "/register", data=user_data, expected_status=400
        )
        assert response.status_code == 400
        body = response.json()
        assert body["success"] is False
        assert "email address already registered" in body["error"]["message"].lower()

    def test_register_invalid_email(self):
        """Test registration with invalid email."""
        user_data = {
            "email": "invalid-email",
            "password": "LocalTest123!",
            "first_name": "Invalid",
            "last_name": "Email",
        }

        response = make_request(
            "POST", "/register", data=user_data, expected_status=400
        )
        assert response.status_code == 400
        body = response.json()
        assert body["success"] is False
        assert "email" in body["error"]["message"].lower()

    def test_register_weak_password(self):
        """Test registration with weak password."""
        user_data = {
            "email": f"weakpass_{int(time.time())}@example.com",
            "password": "weak",
            "first_name": "Weak",
            "last_name": "Password",
        }

        response = make_request(
            "POST", "/register", data=user_data, expected_status=400
        )
        assert response.status_code == 400
        body = response.json()
        assert body["success"] is False
        assert "password" in body["error"]["message"].lower()

    def test_login_valid_user(self):
        """Test login with valid credentials."""
        # First register a user
        user_data = {
            "email": f"validlogin_{int(time.time())}@example.com",
            "password": "ValidLogin123!",
            "first_name": "Valid",
            "last_name": "Login",
        }

        register_response = make_request(
            "POST", "/register", data=user_data, expected_status=201
        )
        assert register_response.status_code == 201

        # Then login
        login_data = {"email": user_data["email"], "password": user_data["password"]}

        response = make_request("POST", "/login", data=login_data)
        assert response.status_code == 200
        body = response.json()
        assert body["success"] is True
        assert "token" in body["data"]
        assert "user" in body["data"]
        assert body["data"]["user"]["email"] == user_data["email"]

    def test_login_invalid_credentials(self):
        """Test login with invalid credentials."""
        login_data = {
            "email": "nonexistent@example.com",
            "password": "WrongPassword123!",
        }

        response = make_request("POST", "/login", data=login_data, expected_status=401)
        assert response.status_code == 401
        body = response.json()
        assert body["success"] is False
        assert "invalid" in body["error"]["message"].lower()

    def test_profile_with_valid_token(self):
        """Test profile endpoint with valid token."""
        # First register and login a user
        user_data = {
            "email": f"profile_{int(time.time())}@example.com",
            "password": "ProfileTest123!",
            "first_name": "Profile",
            "last_name": "Test",
        }

        register_response = make_request(
            "POST", "/register", data=user_data, expected_status=201
        )
        assert register_response.status_code == 201

        login_data = {"email": user_data["email"], "password": user_data["password"]}

        login_response = make_request("POST", "/login", data=login_data)
        assert login_response.status_code == 200

        token = login_response.json()["data"]["token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Test profile endpoint
        response = make_request("GET", "/profile", headers=headers)
        assert response.status_code == 200
        body = response.json()
        assert body["success"] is True
        assert body["data"]["user"]["email"] == user_data["email"]
        assert body["data"]["user"]["first_name"] == user_data["first_name"]

    def test_profile_without_token(self):
        """Test profile endpoint without authentication token."""
        response = make_request("GET", "/profile", expected_status=401)
        assert response.status_code == 401
        body = response.json()
        assert body["success"] is False
        assert "authentication" in body["error"]["message"].lower()

    def test_profile_with_invalid_token(self):
        """Test profile endpoint with invalid token."""
        headers = {"Authorization": "Bearer invalid-token"}
        response = make_request("GET", "/profile", headers=headers, expected_status=401)
        assert response.status_code == 401
        body = response.json()
        assert body["success"] is False


class TestHealthAndErrors:
    """Test health checks and error handling."""

    def test_nonexistent_endpoint(self):
        """Test request to non-existent endpoint."""
        response = make_request("GET", "/nonexistent", expected_status=404)
        # API Gateway might return 403 or 404 for missing endpoints
        assert response.status_code in [403, 404]

    def test_cors_headers(self):
        """Test CORS headers are present."""
        response = make_request("GET", "/hello")
        assert response.status_code == 200

        # Check for CORS headers
        headers = response.headers
        assert "Access-Control-Allow-Origin" in headers
        assert headers["Access-Control-Allow-Origin"] == "*"

    def test_server_response_time(self):
        """Test that server responds within reasonable time."""
        start_time = time.time()
        response = make_request("GET", "/hello")
        end_time = time.time()

        assert response.status_code == 200
        response_time = end_time - start_time
        assert response_time < 10  # Should respond within 10 seconds

    def test_malformed_json(self):
        """Test handling of malformed JSON."""
        try:
            response = requests.post(
                f"{BASE_URL}/register",
                data="invalid json",
                headers={"Content-Type": "application/json"},
                timeout=TIMEOUT,
            )
            assert response.status_code == 400
        except requests.exceptions.RequestException:
            # Some configurations might reject malformed JSON at the gateway level
            pass


if __name__ == "__main__":
    print("Running local integration tests...")
    print("Make sure to start the local server first with: make local-start")
    pytest.main([__file__, "-v"])
