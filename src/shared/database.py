"""Database utilities for Lambda functions."""

import boto3
import os
from typing import Dict, Any, List, Optional
from datetime import datetime
from botocore.exceptions import ClientError


class DynamoDBClient:
    """DynamoDB client wrapper with common operations."""

    def __init__(self, table_name: str):
        """Initialize DynamoDB client."""
        dynamodb_kwargs = {}
        endpoint_url = os.getenv("DYNAMODB_ENDPOINT_URL")

        # For local development, use host.docker.internal if endpoint_url is not set
        if not endpoint_url and os.getenv("ENVIRONMENT") == "local":
            endpoint_url = "http://host.docker.internal:8000"

        print(f"DEBUG: DynamoDBClient endpoint_url={endpoint_url}")
        if endpoint_url:
            dynamodb_kwargs["endpoint_url"] = endpoint_url
        self.dynamodb = boto3.resource("dynamodb", **dynamodb_kwargs)  # type: ignore
        self.table = self.dynamodb.Table(table_name)
        self.table_name = table_name

    def get_item(self, key: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Get a single item from DynamoDB."""
        try:
            response = self.table.get_item(Key=key)
            return response.get("Item")  # type: ignore
        except ClientError as e:
            print(f"Error getting item from {self.table_name}: {e}")
            return None

    def put_item(self, item: Dict[str, Any]) -> bool:
        """Put an item into DynamoDB."""
        try:
            self.table.put_item(Item=item)
            return True
        except ClientError as e:
            print(f"Error putting item to {self.table_name}: {e}")
            return False

    def update_item(
        self,
        key: Dict[str, Any],
        update_expression: str,
        expression_attribute_values: Dict[str, Any],
        expression_attribute_names: Optional[Dict[str, str]] = None,
    ) -> bool:
        """Update an item in DynamoDB."""
        try:
            update_kwargs: Dict[str, Any] = {
                "Key": key,
                "UpdateExpression": update_expression,
                "ExpressionAttributeValues": expression_attribute_values,
            }

            # Add expression attribute names if provided
            if expression_attribute_names:
                update_kwargs["ExpressionAttributeNames"] = expression_attribute_names

            self.table.update_item(**update_kwargs)
            return True
        except ClientError as e:
            print(f"Error updating item in {self.table_name}: {e}")
            return False

    def delete_item(self, key: Dict[str, Any]) -> bool:
        """Delete an item from DynamoDB."""
        try:
            self.table.delete_item(Key=key)
            return True
        except ClientError as e:
            print(f"Error deleting item from {self.table_name}: {e}")
            return False

    def scan_table(
        self, filter_expression: Optional[str] = None, limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Scan the entire table."""
        try:
            scan_kwargs: Dict[str, Any] = {}
            if filter_expression:
                scan_kwargs["FilterExpression"] = filter_expression
            if limit:
                scan_kwargs["Limit"] = limit

            response = self.table.scan(**scan_kwargs)
            return response.get("Items", [])  # type: ignore
        except ClientError as e:
            print(f"Error scanning table {self.table_name}: {e}")
            return []


class S3Client:
    """S3 client wrapper with common operations."""

    def __init__(self):
        """Initialize S3 client."""
        self.s3 = boto3.client("s3")

    def upload_file(self, file_path: str, bucket: str, key: str) -> bool:
        """Upload a file to S3."""
        try:
            self.s3.upload_file(file_path, bucket, key)
            return True
        except ClientError as e:
            print(f"Error uploading file to S3: {e}")
            return False


class UserManager:
    """User management operations with DynamoDB backend."""

    def __init__(self, table_name: Optional[str] = None):
        """Initialize UserManager."""
        env_table = os.getenv("DYNAMODB_USERS_TABLE")
        env_environment = os.getenv("ENVIRONMENT")
        print(f"DEBUG: DYNAMODB_USERS_TABLE={env_table}, ENVIRONMENT={env_environment}")

        # For local development, use the correct table name
        if env_environment == "local":
            self.table_name = table_name or env_table or "cvideo-api-local-users-dev"
        else:
            self.table_name = (
                table_name
                or env_table
                or f"cvideo-api-{env_environment or 'dev'}-users"
            )

        print(f"DEBUG: Using table_name={self.table_name}")
        # Ensure table_name is never None
        assert self.table_name is not None, "Table name must be provided"
        self.db_client = DynamoDBClient(self.table_name)

    def create_user(self, user_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a new user in the database."""
        try:
            # Add timestamps
            now = datetime.utcnow().isoformat() + "Z"
            user_data.update(
                {
                    "created_at": now,
                    "updated_at": now,
                    "is_active": True,
                    "email_verified": False,
                    "profile_data": user_data.get("profile_data", {}),
                }
            )

            # Store user
            if self.db_client.put_item(user_data):
                return user_data
            return None

        except Exception as e:
            print(f"Error creating user: {e}")
            return None

    def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by ID."""
        try:
            # Since we're using email as primary key, we need to find user by user_id
            # This requires scanning the table, which is inefficient but works for
            # small datasets
            users = self.db_client.scan_table()
            for user in users:
                if user.get("user_id") == user_id:
                    return user
            return None
        except Exception as e:
            print(f"Error getting user by ID: {e}")
            return None

    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user by email address."""
        try:
            # Since email is the primary key, we can get it directly
            return self.db_client.get_item({"email": email})
        except Exception as e:
            print(f"Error getting user by email: {e}")
            return None

    def update_user(
        self, user_id: str, updates: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Update user information."""
        try:
            # First get the user to find their email
            user = self.get_user_by_id(user_id)
            if not user:
                return None

            email = user["email"]

            # Add updated timestamp
            updates["updated_at"] = datetime.utcnow().isoformat() + "Z"

            # Build update expression
            update_expression_parts = []
            expression_attribute_values = {}

            for key, value in updates.items():
                update_expression_parts.append(f"{key} = :{key}")
                expression_attribute_values[f":{key}"] = value

            update_expression = "SET " + ", ".join(update_expression_parts)

            # Perform update using email as key
            response = self.db_client.table.update_item(
                Key={"email": email},
                UpdateExpression=update_expression,
                ExpressionAttributeValues=expression_attribute_values,
                ReturnValues="ALL_NEW",
            )

            return response.get("Attributes")  # type: ignore

        except Exception as e:
            print(f"Error updating user: {e}")
            return None

    def update_last_login(self, user_id: str) -> bool:
        """Update user's last login timestamp."""
        try:
            # First get the user to find their email
            user = self.get_user_by_id(user_id)
            if not user:
                return False

            email = user["email"]
            last_login_at = datetime.utcnow().isoformat() + "Z"

            return self.db_client.update_item(
                key={"email": email},
                update_expression=(
                    "SET last_login_at = :last_login_at, updated_at = :updated_at"
                ),
                expression_attribute_values={
                    ":last_login_at": last_login_at,
                    ":updated_at": last_login_at,
                },
            )

        except Exception as e:
            print(f"Error updating last login: {e}")
            return False

    def deactivate_user(self, user_id: str) -> bool:
        """Deactivate a user account."""
        try:
            # First get the user to find their email
            user = self.get_user_by_id(user_id)
            if not user:
                return False

            email = user["email"]

            return self.db_client.update_item(
                key={"email": email},
                update_expression=(
                    "SET is_active = :is_active, updated_at = :updated_at"
                ),
                expression_attribute_values={
                    ":is_active": False,
                    ":updated_at": datetime.utcnow().isoformat() + "Z",
                },
            )

        except Exception as e:
            print(f"Error deactivating user: {e}")
            return False

    def activate_user(self, user_id: str) -> bool:
        """Activate a user account."""
        try:
            # First get the user to find their email
            user = self.get_user_by_id(user_id)
            if not user:
                return False

            email = user["email"]

            return self.db_client.update_item(
                key={"email": email},
                update_expression=(
                    "SET is_active = :is_active, updated_at = :updated_at"
                ),
                expression_attribute_values={
                    ":is_active": True,
                    ":updated_at": datetime.utcnow().isoformat() + "Z",
                },
            )

        except Exception as e:
            print(f"Error activating user: {e}")
            return False

    def verify_email(self, user_id: str) -> bool:
        """Mark user's email as verified."""
        try:
            # First get the user to find their email
            user = self.get_user_by_id(user_id)
            if not user:
                return False

            email = user["email"]

            return self.db_client.update_item(
                key={"email": email},
                update_expression=(
                    "SET email_verified = :email_verified, updated_at = :updated_at"
                ),
                expression_attribute_values={
                    ":email_verified": True,
                    ":updated_at": datetime.utcnow().isoformat() + "Z",
                },
            )

        except Exception as e:
            print(f"Error verifying email: {e}")
            return False

    def delete_user(self, user_id: str) -> bool:
        """Delete a user from the database."""
        try:
            # First get the user to find their email
            user = self.get_user_by_id(user_id)
            if not user:
                return False

            email = user["email"]
            return self.db_client.delete_item({"email": email})

        except Exception as e:
            print(f"Error deleting user: {e}")
            return False

    def email_exists(self, email: str) -> bool:
        """Check if an email address already exists."""
        user = self.get_user_by_email(email)
        return user is not None

    def list_users(
        self, limit: Optional[int] = None, active_only: bool = True
    ) -> List[Dict[str, Any]]:
        """List users with optional filtering."""
        try:
            scan_kwargs: Dict[str, Any] = {}
            if active_only:
                filter_expression = "is_active = :is_active"
                scan_kwargs.update(
                    {
                        "FilterExpression": filter_expression,
                        "ExpressionAttributeValues": {":is_active": True},
                    }
                )

            if limit:
                scan_kwargs["Limit"] = limit

            response = self.db_client.table.scan(**scan_kwargs)
            return response.get("Items", [])  # type: ignore

        except Exception as e:
            print(f"Error listing users: {e}")
            return []
