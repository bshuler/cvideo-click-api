"""
Unit tests for authentication utilities.
"""

import os
import pytest
from unittest.mock import patch

from shared.auth import (
    create_jwt_token,
    verify_jwt_token,
    hash_password,
    verify_password,
    validate_email,
    validate_password_strength,
    generate_user_id,
    sanitize_user_data,
)


class TestJWTTokens:
    """Test JWT token creation and verification."""

    @patch.dict(os.environ, {"JWT_SECRET_KEY": "test-secret-key"})
    def test_create_and_verify_token(self):
        """Test creating and verifying a JWT token."""
        # Create token
        token = create_jwt_token(
            user_id="test-user-123",
            email="test@example.com",
            first_name="John",
            last_name="Doe",
        )

        assert isinstance(token, str)
        assert len(token) > 0

        # Verify token
        payload = verify_jwt_token(token)
        assert payload is not None
        assert payload["user_id"] == "test-user-123"
        assert payload["email"] == "test@example.com"
        assert payload["first_name"] == "John"
        assert payload["last_name"] == "Doe"
        assert "exp" in payload
        assert "iat" in payload

    @patch.dict(os.environ, {"JWT_SECRET_KEY": "test-secret-key"})
    def test_verify_invalid_token(self):
        """Test verifying an invalid token."""
        invalid_token = "invalid.jwt.token"
        payload = verify_jwt_token(invalid_token)
        assert payload is None

    @patch.dict(os.environ, {"JWT_SECRET_KEY": "test-secret-key"})
    def test_token_expiration(self):
        """Test token with custom expiration."""
        # Create token with 0 hours expiration (expired immediately)
        token = create_jwt_token(
            user_id="test-user-123", email="test@example.com", expires_hours=0
        )

        # Token should be invalid due to expiration
        payload = verify_jwt_token(token)
        assert payload is None


class TestPasswordHashing:
    """Test password hashing and verification."""

    def test_hash_password(self):
        """Test password hashing."""
        password = "TestPassword123!"
        hashed = hash_password(password)

        assert isinstance(hashed, str)
        assert len(hashed) > 0
        assert hashed != password  # Should be hashed
        assert hashed.startswith("$2b$")  # bcrypt format

    def test_verify_password_correct(self):
        """Test password verification with correct password."""
        password = "TestPassword123!"
        hashed = hash_password(password)

        assert verify_password(password, hashed) is True

    def test_verify_password_incorrect(self):
        """Test password verification with incorrect password."""
        password = "TestPassword123!"
        wrong_password = "WrongPassword123!"
        hashed = hash_password(password)

        assert verify_password(wrong_password, hashed) is False

    def test_verify_password_invalid_hash(self):
        """Test password verification with invalid hash."""
        password = "TestPassword123!"
        invalid_hash = "invalid_hash"

        assert verify_password(password, invalid_hash) is False


class TestEmailValidation:
    """Test email address validation."""

    def test_valid_emails(self):
        """Test validation of valid email addresses."""
        valid_emails = [
            "test@example.com",
            "user.name@domain.co.uk",
            "user+tag@example.org",
            "user_name@example-domain.com",
            "123@example.com",
        ]

        for email in valid_emails:
            assert validate_email(email) is True, f"Email should be valid: {email}"

    def test_invalid_emails(self):
        """Test validation of invalid email addresses."""
        invalid_emails = [
            "",
            "invalid",
            "@example.com",
            "user@",
            "user@.com",
            "user..name@example.com",
            "user@example",
            "user name@example.com",  # space
            "a" * 250 + "@example.com",  # too long
        ]

        for email in invalid_emails:
            assert validate_email(email) is False, f"Email should be invalid: {email}"


class TestPasswordStrengthValidation:
    """Test password strength validation."""

    def test_strong_password(self):
        """Test validation of a strong password."""
        strong_password = "StrongPass123!"
        result = validate_password_strength(strong_password)

        assert result["valid"] is True
        assert len(result["errors"]) == 0

    def test_weak_passwords(self):
        """Test validation of weak passwords."""
        weak_passwords = [
            ("", ["Password is required"]),
            ("short", ["Password must be at least 8 characters long"]),
            (
                "nouppercase123!",
                ["Password must contain at least one uppercase letter"],
            ),
            (
                "NOLOWERCASE123!",
                ["Password must contain at least one lowercase letter"],
            ),
            ("NoNumbers!", ["Password must contain at least one number"]),
            (
                "NoSpecialChars123",
                ["Password must contain at least one special character"],
            ),
            ("a" * 130, ["Password must be less than 128 characters"]),
        ]

        for password, expected_errors in weak_passwords:
            result = validate_password_strength(password)
            assert result["valid"] is False
            for expected_error in expected_errors:
                assert expected_error in result["errors"]


class TestUserUtilities:
    """Test user utility functions."""

    def test_generate_user_id(self):
        """Test user ID generation."""
        user_id1 = generate_user_id()
        user_id2 = generate_user_id()

        assert isinstance(user_id1, str)
        assert isinstance(user_id2, str)
        assert len(user_id1) == 36  # UUID v4 length
        assert len(user_id2) == 36  # UUID v4 length
        assert user_id1 != user_id2  # Should be unique

    def test_sanitize_user_data(self):
        """Test user data sanitization."""
        user_data = {
            "user_id": "123",
            "email": "test@example.com",
            "password_hash": "hashed_password",
            "password": "plain_password",
            "first_name": "John",
            "last_name": "Doe",
            "created_at": "2025-01-01T00:00:00Z",
        }

        sanitized = sanitize_user_data(user_data)

        # Should preserve safe fields
        assert sanitized["user_id"] == "123"
        assert sanitized["email"] == "test@example.com"
        assert sanitized["first_name"] == "John"
        assert sanitized["last_name"] == "Doe"
        assert sanitized["created_at"] == "2025-01-01T00:00:00Z"

        # Should remove sensitive fields
        assert "password_hash" not in sanitized
        assert "password" not in sanitized

        # Original data should not be modified
        assert "password_hash" in user_data
        assert "password" in user_data


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
