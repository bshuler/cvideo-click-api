#!/usr/bin/env python3
"""Check script to verify AWS developer credentials and permissions."""

import boto3
import sys
from botocore.exceptions import ClientError, NoCredentialsError


def check_aws_credentials():
    """Check if AWS credentials are properly configured."""
    print("🔐 Checking AWS developer credentials...")

    try:
        # Try to get caller identity
        sts = boto3.client("sts")
        identity = sts.get_caller_identity()

        print("✅ AWS credentials verified!")
        print(f"   Account: {identity.get('Account')}")
        print(f"   User ARN: {identity.get('Arn')}")
        return True

    except NoCredentialsError:
        print("❌ No AWS credentials found!")
        print("   Please check your .secrets file or environment variables.")
        return False

    except ClientError as e:
        print(f"❌ AWS credentials error: {e}")
        return False


def check_s3_access():
    """Check S3 access permissions."""
    print("\n🗂️  Checking S3 access...")

    try:
        s3 = boto3.client("s3")
        sam_bucket = "cvideo-sam-artifacts-20250924"

        # Test access to the specific SAM deployment bucket
        try:
            s3.head_bucket(Bucket=sam_bucket)
            print(
                f"✅ S3 access verified! Can access SAM deployment bucket: {sam_bucket}"
            )
            return True
        except ClientError as bucket_error:
            if bucket_error.response["Error"]["Code"] == "404":
                print(f"⚠️  SAM bucket '{sam_bucket}' not found, but S3 access works!")
                print(
                    "   (Bucket will be created automatically during first deployment)"
                )
                return True
            else:
                raise bucket_error

    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        if error_code == "AccessDenied":
            print(
                "❌ S3 access denied! Check IAM permissions for SAM deployment bucket."
            )
            print(f"   Required permissions for bucket: {sam_bucket}")
            print("   - s3:GetObject, s3:PutObject, s3:DeleteObject")
            print("   - s3:GetBucketLocation, s3:ListBucket")
            return False
        else:
            print(f"❌ S3 error: {e}")
        return False


def check_lambda_access():
    """Check Lambda access permissions."""
    print("\n⚡ Checking Lambda access...")

    try:
        lambda_client = boto3.client("lambda")

        # List functions to test basic Lambda access
        response = lambda_client.list_functions()
        function_count = len(response.get("Functions", []))

        print(f"✅ Lambda access verified! Found {function_count} functions.")
        return True

    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        if error_code == "AccessDenied":
            print("❌ Lambda access denied! Check IAM permissions.")
        else:
            print(f"❌ Lambda error: {e}")
        return False


def check_api_gateway_access():
    """Check API Gateway access permissions."""
    print("\n🌐 Checking API Gateway access...")

    try:
        apigateway = boto3.client("apigateway")

        # List REST APIs to test basic API Gateway access
        response = apigateway.get_rest_apis()
        api_count = len(response.get("items", []))

        print(f"✅ API Gateway access verified! Found {api_count} REST APIs.")
        return True

    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        if error_code == "AccessDenied":
            print("❌ API Gateway access denied! Check IAM permissions.")
        else:
            print(f"❌ API Gateway error: {e}")
        return False


def main():
    """Run AWS developer credential checks."""
    print("🚀 Checking AWS Developer Credentials")
    print("💡 Verifying your .secrets file has proper permissions")
    print("=" * 50)

    checks = [
        check_aws_credentials,
        check_s3_access,
        check_lambda_access,
        check_api_gateway_access,
    ]

    results = []
    for check in checks:
        results.append(check())

    print("\n" + "=" * 50)
    if all(results):
        print("🎉 All AWS credential checks passed!")
        print("💡 Your developer account has proper permissions.")
        sys.exit(0)
    else:
        failed_count = len([r for r in results if not r])
        print(f"❌ {failed_count} check(s) failed. Please fix the issues above.")
        print("💡 You may need to update your .secrets file or IAM permissions.")
        sys.exit(1)


if __name__ == "__main__":
    main()
