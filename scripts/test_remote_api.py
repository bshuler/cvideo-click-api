#!/usr/bin/env python3
"""
Test script for remote API endpoints deployed to AWS.
This script tests the deployed API Gateway endpoints.
"""

import sys
import boto3
import requests
from botocore.exceptions import ClientError
from typing import Optional, Any


def get_api_gateway_url() -> Optional[str]:
    """Get the API Gateway URL from CloudFormation outputs."""
    try:
        cf = boto3.client("cloudformation")

        response = cf.describe_stacks(StackName="cvideo-click-api-sam")
        stacks = response.get("Stacks", [])

        if not stacks:
            print("❌ Stack 'cvideo-click-api-sam' not found")
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


def test_endpoint(
    url: str,
    method: str = "GET",
    data: Optional[Any] = None,
    expected_status: int = 200,
) -> bool:
    """Test a specific API endpoint."""
    try:
        if method == "GET":
            response = requests.get(url, timeout=30)
        elif method == "POST":
            response = requests.post(
                url, json=data, headers={"Content-Type": "application/json"}, timeout=30
            )
        else:
            print(f"❌ Unsupported method: {method}")
            return False

        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.text}")

        if response.status_code == expected_status:
            print("   ✅ Test passed!")
            return True
        else:
            print(f"   ❌ Expected {expected_status}, got {response.status_code}")
            return False

    except requests.exceptions.RequestException as e:
        print(f"   ❌ Request failed: {e}")
        return False


def main() -> None:
    """Run remote API tests."""
    print("🌐 Testing Remote API Endpoints")
    print("=" * 40)

    # Get API Gateway URL
    base_url = get_api_gateway_url()
    if not base_url:
        print("❌ Cannot proceed without API Gateway URL")
        sys.exit(1)

    print(f"🔗 API Base URL: {base_url}")
    print()

    # Test cases
    tests = [
        {
            "name": "GET /hello",
            "url": f"{base_url}/hello",
            "method": "GET",
            "expected_status": 200,
        },
        {
            "name": "POST /hello",
            "url": f"{base_url}/hello",
            "method": "POST",
            "data": {"name": "remote-test"},
            "expected_status": 200,
        },
    ]

    # Run tests
    results = []
    for test in tests:
        print(f"🧪 Testing {test['name']}...")
        expected_status = test.get("expected_status", 200)
        result = test_endpoint(
            str(test["url"]),
            str(test.get("method", "GET")),
            test.get("data"),
            expected_status if isinstance(expected_status, int) else 200,
        )
        results.append(result)
        print()

    # Summary
    passed = sum(results)
    total = len(results)

    print("=" * 40)
    if passed == total:
        print(f"🎉 All {total} tests passed!")
        sys.exit(0)
    else:
        print(f"❌ {total - passed} of {total} tests failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
