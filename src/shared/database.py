"""Database utilities for Lambda functions."""

import boto3
from typing import Dict, Any, List, Optional
from botocore.exceptions import ClientError


class DynamoDBClient:
    """DynamoDB client wrapper with common operations."""

    def __init__(self, table_name: str):
        """
        Initialize DynamoDB client.

        Args:
            table_name: DynamoDB table name
        """
        self.dynamodb = boto3.resource("dynamodb")
        self.table = self.dynamodb.Table(table_name)
        self.table_name = table_name

    def get_item(self, key: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Get a single item from DynamoDB.

        Args:
            key: Primary key dictionary

        Returns:
            Item dictionary or None if not found
        """
        try:
            response = self.table.get_item(Key=key)
            return response.get("Item")
        except ClientError as e:
            print(f"Error getting item from {self.table_name}: {e}")
            return None

    def put_item(self, item: Dict[str, Any]) -> bool:
        """
        Put an item into DynamoDB.

        Args:
            item: Item dictionary to store

        Returns:
            True if successful, False otherwise
        """
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
    ) -> bool:
        """
        Update an item in DynamoDB.

        Args:
            key: Primary key dictionary
            update_expression: DynamoDB update expression
            expression_attribute_values: Values for the update expression

        Returns:
            True if successful, False otherwise
        """
        try:
            self.table.update_item(
                Key=key,
                UpdateExpression=update_expression,
                ExpressionAttributeValues=expression_attribute_values,
            )
            return True
        except ClientError as e:
            print(f"Error updating item in {self.table_name}: {e}")
            return False

    def delete_item(self, key: Dict[str, Any]) -> bool:
        """
        Delete an item from DynamoDB.

        Args:
            key: Primary key dictionary

        Returns:
            True if successful, False otherwise
        """
        try:
            self.table.delete_item(Key=key)
            return True
        except ClientError as e:
            print(f"Error deleting item from {self.table_name}: {e}")
            return False

    def scan_table(
        self, filter_expression: Optional[str] = None, limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Scan the entire table.

        Args:
            filter_expression: Optional filter expression
            limit: Optional limit on number of items

        Returns:
            List of items
        """
        try:
            scan_kwargs: Dict[str, Any] = {}
            if filter_expression:
                scan_kwargs["FilterExpression"] = filter_expression
            if limit:
                scan_kwargs["Limit"] = limit

            response = self.table.scan(**scan_kwargs)
            return response.get("Items", [])
        except ClientError as e:
            print(f"Error scanning table {self.table_name}: {e}")
            return []


class S3Client:
    """S3 client wrapper with common operations."""

    def __init__(self):
        """Initialize S3 client."""
        self.s3 = boto3.client("s3")

    def upload_file(self, file_path: str, bucket: str, key: str) -> bool:
        """
        Upload a file to S3.

        Args:
            file_path: Local file path
            bucket: S3 bucket name
            key: S3 object key

        Returns:
            True if successful, False otherwise
        """
        try:
            self.s3.upload_file(file_path, bucket, key)
            return True
        except ClientError as e:
            print(f"Error uploading file to S3: {e}")
            return False

    def download_file(self, bucket: str, key: str, file_path: str) -> bool:
        """
        Download a file from S3.

        Args:
            bucket: S3 bucket name
            key: S3 object key
            file_path: Local file path to save to

        Returns:
            True if successful, False otherwise
        """
        try:
            self.s3.download_file(bucket, key, file_path)
            return True
        except ClientError as e:
            print(f"Error downloading file from S3: {e}")
            return False

    def get_object(self, bucket: str, key: str) -> Optional[bytes]:
        """
        Get an object from S3.

        Args:
            bucket: S3 bucket name
            key: S3 object key

        Returns:
            Object bytes or None if error
        """
        try:
            response = self.s3.get_object(Bucket=bucket, Key=key)
            return response["Body"].read()
        except ClientError as e:
            print(f"Error getting object from S3: {e}")
            return None
