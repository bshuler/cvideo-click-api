#!/usr/bin/env python3
"""
Comprehensive test script for remote API endpoints deployed to AWS.
This script tests the deployed API Gateway endpoints with full authentication flows.
"""

import sys
import os
import time
import boto3
import requests
from botocore.exceptions import ClientError
from typing import Optional, Any, Dict


def get_api_gateway_url(stack_name: Optional[str] = None) -> Optional[str]:
    """Get the API Gateway URL from CloudFormation outputs."""
    try:
        cf = boto3.client("cloudformation")

        # Use environment variable or default stack name
        if not stack_name:
            stack_name = os.environ.get("STACK_NAME", "cvideo-click-api-sam")

        print(f"🔍 Looking for stack: {stack_name}")
        response = cf.describe_stacks(StackName=stack_name)
        stacks = response.get("Stacks", [])

        if not stacks:
            print(f"❌ Stack '{stack_name}' not found")
            return None

        outputs = stacks[0].get("Outputs", [])

        for output in outputs:
            if output.get("OutputKey") == "ApiGatewayUrl":
                return output.get("OutputValue")

        print("❌ ApiGatewayUrl output not found in stack")
        return None

    except ClientError as e:
        print(f"❌ Error getting API Gateway URL: {e}")
        return None


def get_lambda_function_url(function_name: str) -> Optional[str]:
    """Get Lambda function URL if API Gateway is not available."""
    try:
        lambda_client = boto3.client("lambda")

        # Try to get function URL configuration
        try:
            response = lambda_client.get_function_url_config(FunctionName=function_name)
            return response.get("FunctionUrl")
        except ClientError:
            # Function URL not configured
            return None

    except ClientError as e:
        print(f"❌ Error getting Lambda function URL: {e}")
        return None


def test_endpoint(
    url: str,
    method: str = "GET",
    data: Optional[Any] = None,
    headers: Optional[Dict[str, str]] = None,
    expected_status: int = 200,
) -> Dict[str, Any]:
    """Test a specific API endpoint and return detailed results."""
    try:
        request_headers = {"Content-Type": "application/json"}
        if headers:
            request_headers.update(headers)

        if method == "GET":
            response = requests.get(url, headers=request_headers, timeout=30)
        elif method == "POST":
            response = requests.post(
                url, json=data, headers=request_headers, timeout=30
            )
        elif method == "PUT":
            response = requests.put(url, json=data, headers=request_headers, timeout=30)
        else:
            return {
                "success": False,
                "error": f"Unsupported method: {method}",
                "status_code": None,
                "response_data": None,
            }

        print(f"   Status: {response.status_code}")

        try:
            response_data = response.json()
            print(f"   Response: {response_data}")
        except Exception:
            response_data = response.text
            print(f"   Response: {response_data}")

        success = response.status_code == expected_status
        if success:
            print("   ✅ Test passed!")
        else:
            print(f"   ❌ Expected {expected_status}, got {response.status_code}")

        return {
            "success": success,
            "status_code": response.status_code,
            "response_data": response_data,
            "error": None,
        }

    except requests.exceptions.RequestException as e:
        error_msg = f"Request failed: {e}"
        print(f"   ❌ {error_msg}")
        return {
            "success": False,
            "error": error_msg,
            "status_code": None,
            "response_data": None,
        }


def run_authentication_flow_test(base_url: str) -> Dict[str, Any]:
    """Run complete authentication flow test."""
    print("🔐 Testing Complete Authentication Flow...")

    # Generate unique email for this test
    unique_id = int(time.time())
    test_user = {
        "email": f"remotetest_{unique_id}@example.com",
        "password": "RemoteTest123!",
        "first_name": "Remote",
        "last_name": "Test",
    }

    results = {}

    # 1. Test user registration
    print("   🧪 Testing user registration...")
    register_result = test_endpoint(
        f"{base_url}/auth/register", "POST", data=test_user, expected_status=201
    )
    results["register"] = register_result

    if not register_result["success"]:
        return results

    # 2. Test user login
    print("   🧪 Testing user login...")
    login_data = {"email": test_user["email"], "password": test_user["password"]}
    login_result = test_endpoint(
        f"{base_url}/auth/login", "POST", data=login_data, expected_status=200
    )
    results["login"] = login_result

    if not login_result["success"]:
        return results

    # Extract token from login response
    try:
        access_token = login_result["response_data"]["data"]["access_token"]
    except (KeyError, TypeError):
        print("   ❌ Could not extract access token from login response")
        results["token_extraction"] = {
            "success": False,
            "error": "Token extraction failed",
        }
        return results

    # 3. Test profile access with token
    print("   🧪 Testing profile access with token...")
    headers = {"Authorization": f"Bearer {access_token}"}
    profile_result = test_endpoint(
        f"{base_url}/auth/profile", "GET", headers=headers, expected_status=200
    )
    results["profile"] = profile_result

    # 4. Test profile access without token (should fail)
    print("   🧪 Testing profile access without token...")
    no_token_result = test_endpoint(
        f"{base_url}/auth/profile", "GET", expected_status=401
    )
    results["profile_no_token"] = no_token_result

    return results


def main() -> None:
    """Run comprehensive remote API tests."""
    print("🌐 Testing Remote API Endpoints (Comprehensive)")
    print("=" * 50)

    # Get API Gateway URL
    base_url = get_api_gateway_url()
    if not base_url:
        print("⚠️  API Gateway URL not found, trying Lambda function URLs...")

        # Try common function names
        function_names = [
            "cvideo-api-develop-hello-world-dev",
            "cvideo-api-main-hello-world-dev",
            "HelloWorldFunction",
        ]

        for func_name in function_names:
            func_url = get_lambda_function_url(func_name)
            if func_url:
                base_url = func_url.rstrip("/")
                print(f"🔗 Using Lambda Function URL: {base_url}")
                break

        if not base_url:
            print("❌ Cannot proceed without API Gateway URL or Lambda Function URL")
            sys.exit(1)
    else:
        base_url = base_url.rstrip("/")
        print(f"🔗 API Base URL: {base_url}")

    print()

    # Basic endpoint tests
    basic_tests = [
        {
            "name": "GET /hello (no parameters)",
            "url": f"{base_url}/hello",
            "method": "GET",
            "expected_status": 200,
        },
        {
            "name": "GET /hello (with name parameter)",
            "url": f"{base_url}/hello?name=RemoteTest",
            "method": "GET",
            "expected_status": 200,
        },
        {
            "name": "POST /hello (with data)",
            "url": f"{base_url}/hello",
            "method": "POST",
            "data": {"name": "RemoteTest", "message": "Hello from remote test"},
            "expected_status": 200,
        },
    ]

    # Run basic tests
    basic_results = []
    print("🧪 Running Basic Endpoint Tests...")
    print("-" * 30)

    for test in basic_tests:
        print(f"🧪 Testing {test['name']}...")
        result = test_endpoint(
            str(test["url"]),
            str(test.get("method", "GET")),
            test.get("data"),
            test.get("headers"),  # type: ignore
            test.get("expected_status", 200),  # type: ignore
        )
        basic_results.append(result)
        print()

    # Run authentication flow tests
    print("🔐 Running Authentication Flow Tests...")
    print("-" * 30)
    auth_results = run_authentication_flow_test(base_url)
    print()

    # Test error handling
    print("🚨 Testing Error Handling...")
    print("-" * 30)
    error_tests = [
        {
            "name": "Invalid email registration",
            "url": f"{base_url}/auth/register",
            "method": "POST",
            "data": {
                "email": "invalid-email",
                "password": "Test123!",
                "first_name": "Test",
                "last_name": "User",
            },
            "expected_status": 400,
        },
        {
            "name": "Weak password registration",
            "url": f"{base_url}/auth/register",
            "method": "POST",
            "data": {
                "email": f"weakpass_{int(time.time())}@example.com",
                "password": "weak",
                "first_name": "Test",
                "last_name": "User",
            },
            "expected_status": 400,
        },
        {
            "name": "Invalid login credentials",
            "url": f"{base_url}/auth/login",
            "method": "POST",
            "data": {
                "email": "nonexistent@example.com",
                "password": "WrongPassword123!",
            },
            "expected_status": 401,
        },
    ]

    error_results = []
    for test in error_tests:
        print(f"🧪 Testing {test['name']}...")
        result = test_endpoint(
            str(test["url"]),
            str(test.get("method", "GET")),
            test.get("data"),
            test.get("headers"),  # type: ignore
            test.get("expected_status", 400),  # type: ignore
        )
        error_results.append(result)
        print()

    # Summary
    print("=" * 50)
    print("📊 Test Results Summary:")
    print("=" * 50)

    basic_passed = sum(1 for r in basic_results if r["success"])
    basic_total = len(basic_results)
    print(f"🔧 Basic Endpoint Tests: {basic_passed}/{basic_total} passed")

    auth_passed = sum(1 for r in auth_results.values() if r.get("success", False))
    auth_total = len(auth_results)
    print(f"🔐 Authentication Flow Tests: {auth_passed}/{auth_total} passed")

    error_passed = sum(1 for r in error_results if r["success"])
    error_total = len(error_results)
    print(f"🚨 Error Handling Tests: {error_passed}/{error_total} passed")

    total_passed = basic_passed + auth_passed + error_passed
    total_tests = basic_total + auth_total + error_total

    print("-" * 50)
    print(f"📈 Overall: {total_passed}/{total_tests} tests passed")

    if total_passed == total_tests:
        print("🎉 All remote tests passed!")
        sys.exit(0)
    else:
        print(f"❌ {total_tests - total_passed} tests failed")

        # Print failed test details
        print("\n🔍 Failed Test Details:")
        if basic_passed < basic_total:
            print("   Basic endpoint failures detected")
        if auth_passed < auth_total:
            print("   Authentication flow failures detected")
            for test_name, result in auth_results.items():
                if not result.get("success", False):
                    print(f"     - {test_name}: {result.get('error', 'Unknown error')}")
        if error_passed < error_total:
            print("   Error handling failures detected")

        sys.exit(1)


if __name__ == "__main__":
    main()
