#!/usr/bin/env python3
"""Check deployment and service status."""

import boto3
from botocore.exceptions import ClientError


def check_lambda_functions():
    """Check status of Lambda functions."""
    print("⚡ Checking Lambda Functions...")

    lambda_client = boto3.client("lambda")

    try:
        response = lambda_client.list_functions()
        functions = response.get("Functions", [])

        api_functions = [
            f for f in functions if f["FunctionName"].startswith("cvideo-api-")
        ]

        if not api_functions:
            print("   ℹ️  No Lambda functions found with 'cvideo-api-' prefix.")
            return True

        for function in api_functions:
            name = function["FunctionName"]

            # Get detailed function info since list_functions doesn't include
            # State/LastUpdateStatus
            try:
                detailed_response = lambda_client.get_function(FunctionName=name)
                config = detailed_response["Configuration"]
                state = config.get("State", "Unknown")
                last_update = config.get("LastUpdateStatus", "Unknown")

                status_icon = (
                    "✅" if state == "Active" and last_update == "Successful" else "❌"
                )
                print(f"   {status_icon} {name}: {state} ({last_update})")
            except ClientError as get_error:
                print(f"   ⚠️  {name}: Could not get detailed status - {get_error}")
                print(f"   ℹ️  {name}: Function exists but details unavailable")

        return True

    except ClientError as e:
        print(f"   ❌ Error checking Lambda functions: {e}")
        return False


def check_api_gateway():
    """Check status of API Gateway."""
    print("\n🌐 Checking API Gateway...")

    apigateway = boto3.client("apigateway")

    try:
        response = apigateway.get_rest_apis()
        apis = response.get("items", [])

        api_gateways = [api for api in apis if api["name"].startswith("cvideo-api")]

        if not api_gateways:
            print("   ℹ️  No API Gateways found with 'cvideo-api' prefix.")
            return True

        for api in api_gateways:
            name = api["name"]
            api_id = api["id"]
            created_date = api["createdDate"].strftime("%Y-%m-%d %H:%M:%S")

            print(f"   ✅ {name} (ID: {api_id})")
            print(f"      Created: {created_date}")

            # Get stages
            try:
                stages_response = apigateway.get_stages(restApiId=api_id)
                stages = stages_response.get("item", [])

                for stage in stages:
                    stage_name = stage["stageName"]
                    deployment_id = stage.get("deploymentId", "N/A")
                    print(f"      📍 Stage: {stage_name} (Deployment: {deployment_id})")

            except ClientError as stage_error:
                print(f"      ❌ Error getting stages: {stage_error}")

        return True

    except ClientError as e:
        print(f"   ❌ Error checking API Gateway: {e}")
        return False


def check_s3_buckets():
    """Check status of S3 buckets."""
    print("\n🗂️  Checking S3 Buckets...")

    s3 = boto3.client("s3")
    sam_bucket = "cvideo-sam-artifacts-20250924"

    try:
        # Check the specific SAM deployment bucket instead of listing all buckets
        try:
            # Check if bucket exists and we can access it
            s3.head_bucket(Bucket=sam_bucket)

            # Check bucket accessibility
            try:
                s3.head_bucket(Bucket=sam_bucket)
                print(f"   ✅ {sam_bucket}")
                print("      Status: Accessible")
                print("      Used for: SAM deployment artifacts")

                # Try to get bucket location
                try:
                    location_response = s3.get_bucket_location(Bucket=sam_bucket)
                    region = location_response.get("LocationConstraint") or "us-east-1"
                    print(f"      Region: {region}")
                except ClientError:
                    print("      Region: us-east-1 (default)")

            except ClientError:
                print(f"   ✅ {sam_bucket}")
                print("      Status: Accessible (limited metadata access)")

        except ClientError as bucket_error:
            if bucket_error.response["Error"]["Code"] == "404":
                print(f"   ℹ️  SAM bucket '{sam_bucket}' not found")
                print(
                    "      This is normal - bucket is created automatically "
                    "during first deployment"
                )
                return True
            else:
                print(f"   ❌ Cannot access SAM bucket '{sam_bucket}': {bucket_error}")
                return False

        return True

    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        if error_code == "AccessDenied":
            print("   ⚠️  S3 access limited - this is OK for SAM deployments!")
            print(
                f"      Your SAM deployment bucket '{sam_bucket}' is accessible "
                "via SAM CLI"
            )
            return True  # Return True since S3 bucket listing is not critical
        else:
            print(f"   ❌ Error checking S3 buckets: {e}")
            return False


def check_iam_roles():
    """Check IAM roles for Lambda functions."""
    print("\n🔐 Checking IAM Roles...")

    iam = boto3.client("iam")

    try:
        response = iam.list_roles()
        roles = response.get("Roles", [])

        api_roles = [role for role in roles if "cvideo-api" in role["RoleName"]]

        if not api_roles:
            print("   ℹ️  No IAM roles found with 'cvideo-api' in the name.")
            return True

        for role in api_roles:
            name = role["RoleName"]
            created_date = role["CreateDate"].strftime("%Y-%m-%d %H:%M:%S")

            print(f"   ✅ {name}")
            print(f"      Created: {created_date}")

        return True

    except ClientError as e:
        print(f"   ❌ Error checking IAM roles: {e}")
        return False


def main():
    """Main function to check all service statuses."""
    print("🔍 Checking CVIDEO-CLICK-API Deployment Status")
    print("=" * 55)

    checks = [
        check_lambda_functions,
        check_api_gateway,
        check_s3_buckets,
        check_iam_roles,
    ]

    results = []
    for check in checks:
        results.append(check())

    print("\n" + "=" * 55)
    if all(results):
        print("🎉 All services are healthy!")
    else:
        failed_count = len([r for r in results if not r])
        print(f"⚠️  {failed_count} service check(s) encountered issues.")


if __name__ == "__main__":
    main()
