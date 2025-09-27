"""
Unit tests for database utilities and user management.
"""

import pytest
import boto3
from moto import mock_aws

from shared.database import DynamoDBClient, UserManager
from shared.auth import hash_password, generate_user_id


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
def sample_user():
    """Sample user data for testing."""
    return {
        "user_id": generate_user_id(),
        "email": "test@example.com",
        "password_hash": hash_password("TestPassword123!"),
        "first_name": "John",
        "last_name": "Doe",
    }


class TestDynamoDBClient:
    """Test DynamoDB client wrapper."""

    def test_put_and_get_item(self, mock_dynamodb_table):
        """Test putting and getting an item."""
        db_client = DynamoDBClient("test-users-table")

        # Test data - must include email as primary key
        item = {"email": "test@example.com", "user_id": "test-123", "name": "Test User"}

        # Put item
        result = db_client.put_item(item)
        assert result is True

        # Get item
        retrieved_item = db_client.get_item({"email": "test@example.com"})
        assert retrieved_item is not None
        assert retrieved_item["user_id"] == "test-123"
        assert retrieved_item["name"] == "Test User"
        assert retrieved_item["email"] == "test@example.com"

    def test_get_nonexistent_item(self, mock_dynamodb_table):
        """Test getting a non-existent item."""
        db_client = DynamoDBClient("test-users-table")

        retrieved_item = db_client.get_item({"email": "nonexistent@example.com"})
        assert retrieved_item is None

    def test_update_item(self, mock_dynamodb_table):
        """Test updating an item."""
        db_client = DynamoDBClient("test-users-table")

        # Put initial item
        item = {"email": "test@example.com", "user_id": "test-123", "name": "Test User"}
        db_client.put_item(item)

        # Update item
        result = db_client.update_item(
            key={"email": "test@example.com"},
            update_expression="SET #name = :name",
            expression_attribute_values={":name": "Updated User"},
            expression_attribute_names={"#name": "name"},
        )
        assert result is True

        # Verify update
        retrieved_item = db_client.get_item({"email": "test@example.com"})
        assert retrieved_item["name"] == "Updated User"

    def test_delete_item(self, mock_dynamodb_table):
        """Test deleting an item."""
        db_client = DynamoDBClient("test-users-table")

        # Put item
        item = {"email": "test@example.com", "user_id": "test-123", "name": "Test User"}
        db_client.put_item(item)

        # Verify item exists
        retrieved_item = db_client.get_item({"email": "test@example.com"})
        assert retrieved_item is not None

        # Delete item
        result = db_client.delete_item({"email": "test@example.com"})
        assert result is True

        # Verify item is deleted
        retrieved_item = db_client.get_item({"email": "test@example.com"})
        assert retrieved_item is None

    def test_scan_table(self, mock_dynamodb_table):
        """Test scanning the table."""
        db_client = DynamoDBClient("test-users-table")

        # Put multiple items
        items = [
            {
                "email": "user1@example.com",
                "user_id": "test-1",
                "name": "User 1",
                "active": True,
            },
            {
                "email": "user2@example.com",
                "user_id": "test-2",
                "name": "User 2",
                "active": False,
            },
            {
                "email": "user3@example.com",
                "user_id": "test-3",
                "name": "User 3",
                "active": True,
            },
        ]

        for item in items:
            db_client.put_item(item)

        # Scan all items
        all_items = db_client.scan_table()
        assert len(all_items) == 3

        # Scan with limit
        limited_items = db_client.scan_table(limit=2)
        assert len(limited_items) <= 2


class TestUserManager:
    """Test user management operations."""

    def test_create_user(self, mock_dynamodb_table, sample_user):
        """Test creating a user."""
        user_manager = UserManager("test-users-table")

        created_user = user_manager.create_user(sample_user)

        assert created_user is not None
        assert created_user["user_id"] == sample_user["user_id"]
        assert created_user["email"] == sample_user["email"]
        assert created_user["is_active"] is True
        assert created_user["email_verified"] is False
        assert "created_at" in created_user
        assert "updated_at" in created_user

    def test_get_user_by_id(self, mock_dynamodb_table, sample_user):
        """Test getting user by ID."""
        user_manager = UserManager("test-users-table")

        # Create user
        created_user = user_manager.create_user(sample_user)
        assert created_user is not None

        # Get user by ID
        retrieved_user = user_manager.get_user_by_id(sample_user["user_id"])
        assert retrieved_user is not None
        assert retrieved_user["user_id"] == sample_user["user_id"]
        assert retrieved_user["email"] == sample_user["email"]

    def test_get_user_by_email(self, mock_dynamodb_table, sample_user):
        """Test getting user by email."""
        user_manager = UserManager("test-users-table")

        # Create user
        created_user = user_manager.create_user(sample_user)
        assert created_user is not None

        # Get user by email
        retrieved_user = user_manager.get_user_by_email(sample_user["email"])
        assert retrieved_user is not None
        assert retrieved_user["user_id"] == sample_user["user_id"]
        assert retrieved_user["email"] == sample_user["email"]

    def test_get_nonexistent_user(self, mock_dynamodb_table):
        """Test getting non-existent user."""
        user_manager = UserManager("test-users-table")

        # Get by ID
        user_by_id = user_manager.get_user_by_id("nonexistent")
        assert user_by_id is None

        # Get by email
        user_by_email = user_manager.get_user_by_email("nonexistent@example.com")
        assert user_by_email is None

    def test_update_user(self, mock_dynamodb_table, sample_user):
        """Test updating user."""
        user_manager = UserManager("test-users-table")

        # Create user
        created_user = user_manager.create_user(sample_user)
        assert created_user is not None

        # Update user
        updates = {"first_name": "Jane", "profile_data": {"company": "ACME Corp"}}
        updated_user = user_manager.update_user(sample_user["user_id"], updates)

        assert updated_user is not None
        assert updated_user["first_name"] == "Jane"
        assert updated_user["profile_data"]["company"] == "ACME Corp"
        assert "updated_at" in updated_user

    def test_update_last_login(self, mock_dynamodb_table, sample_user):
        """Test updating last login timestamp."""
        user_manager = UserManager("test-users-table")

        # Create user
        created_user = user_manager.create_user(sample_user)
        assert created_user is not None

        # Update last login
        result = user_manager.update_last_login(sample_user["user_id"])
        assert result is True

        # Verify update
        updated_user = user_manager.get_user_by_id(sample_user["user_id"])
        assert "last_login_at" in updated_user

    def test_deactivate_and_activate_user(self, mock_dynamodb_table, sample_user):
        """Test deactivating and activating user."""
        user_manager = UserManager("test-users-table")

        # Create user
        created_user = user_manager.create_user(sample_user)
        assert created_user is not None
        assert created_user["is_active"] is True

        # Deactivate user
        result = user_manager.deactivate_user(sample_user["user_id"])
        assert result is True

        # Verify deactivation
        user = user_manager.get_user_by_id(sample_user["user_id"])
        assert user["is_active"] is False

        # Activate user
        result = user_manager.activate_user(sample_user["user_id"])
        assert result is True

        # Verify activation
        user = user_manager.get_user_by_id(sample_user["user_id"])
        assert user["is_active"] is True

    def test_verify_email(self, mock_dynamodb_table, sample_user):
        """Test email verification."""
        user_manager = UserManager("test-users-table")

        # Create user
        created_user = user_manager.create_user(sample_user)
        assert created_user is not None
        assert created_user["email_verified"] is False

        # Verify email
        result = user_manager.verify_email(sample_user["user_id"])
        assert result is True

        # Check verification
        user = user_manager.get_user_by_id(sample_user["user_id"])
        assert user["email_verified"] is True

    def test_email_exists(self, mock_dynamodb_table, sample_user):
        """Test checking if email exists."""
        user_manager = UserManager("test-users-table")

        # Initially email should not exist
        assert user_manager.email_exists(sample_user["email"]) is False

        # Create user
        created_user = user_manager.create_user(sample_user)
        assert created_user is not None

        # Now email should exist
        assert user_manager.email_exists(sample_user["email"]) is True

        # Different email should not exist
        assert user_manager.email_exists("different@example.com") is False

    def test_delete_user(self, mock_dynamodb_table, sample_user):
        """Test deleting user."""
        user_manager = UserManager("test-users-table")

        # Create user
        created_user = user_manager.create_user(sample_user)
        assert created_user is not None

        # Verify user exists
        user = user_manager.get_user_by_id(sample_user["user_id"])
        assert user is not None

        # Delete user
        result = user_manager.delete_user(sample_user["user_id"])
        assert result is True

        # Verify user is deleted
        user = user_manager.get_user_by_id(sample_user["user_id"])
        assert user is None

    def test_list_users(self, mock_dynamodb_table):
        """Test listing users."""
        user_manager = UserManager("test-users-table")

        # Create multiple users
        users = []
        for i in range(3):
            user_data = {
                "user_id": generate_user_id(),
                "email": f"user{i}@example.com",
                "password_hash": hash_password("TestPassword123!"),
                "first_name": f"User{i}",
                "last_name": "Test",
            }
            created_user = user_manager.create_user(user_data)
            users.append(created_user)

        # Deactivate one user
        user_manager.deactivate_user(users[1]["user_id"])

        # List all users
        all_users = user_manager.list_users(active_only=False)
        assert len(all_users) == 3

        # List only active users
        active_users = user_manager.list_users(active_only=True)
        assert len(active_users) == 2

        # List with limit
        limited_users = user_manager.list_users(limit=2, active_only=False)
        assert len(limited_users) <= 2


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
