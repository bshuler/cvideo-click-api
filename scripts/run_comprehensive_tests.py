#!/usr/bin/env python3
"""
Comprehensive test runner for CVIDEO-CLICK-API.
Runs different types of tests in local and remote environments.
"""

import os
import sys
import subprocess
import argparse
import shlex
from typing import Union


def run_command(
    cmd: str, description: str, capture_output: bool = False
) -> Union[bool, str, None]:
    """Run a command and handle output."""
    print(f"🔄 {description}...")

    try:
        # Use shlex.split to safely parse the command without shell=True
        cmd_args = shlex.split(cmd)

        if capture_output:
            result = subprocess.run(cmd_args, capture_output=True, text=True)
            if result.returncode == 0:
                print(f"✅ {description} completed successfully")
                return result.stdout
            else:
                print(f"❌ {description} failed: {result.stderr}")
                return None
        else:
            cmd_result = subprocess.run(cmd_args)
            if cmd_result.returncode == 0:
                print(f"✅ {description} completed successfully")
                return True
            else:
                print(f"❌ {description} failed")
                return False

    except Exception as e:
        print(f"❌ {description} failed with error: {e}")
        return False


def run_local_tests() -> list:
    """Run all local tests."""
    print("🏠 Running Local Tests")
    print("=" * 40)

    tests = [
        ("make test-unit", "Unit Tests"),
        ("make test-integration", "Integration Tests (Mocked)"),
        ("make lint", "Code Linting"),
        ("make type-check", "Type Checking"),
        ("make test-security", "Security Analysis"),
    ]

    results = []
    for cmd, desc in tests:
        result = run_command(cmd, desc)
        results.append((desc, result))

    return results


def run_local_deployment_tests() -> list:
    """Run local deployment tests."""
    print("🏗️  Running Local Deployment Tests")
    print("=" * 40)

    tests = [
        ("make local-build", "Local SAM Build"),
        ("sam validate --template template.yaml", "SAM Template Validation"),
    ]

    results = []
    for cmd, desc in tests:
        result = run_command(cmd, desc)
        results.append((desc, result))

    return results


def run_remote_tests() -> list:
    """Run remote/cloud tests."""
    print("☁️  Running Remote AWS Tests")
    print("=" * 40)

    # Check if we have AWS credentials
    if not os.path.exists(".secrets"):
        print("❌ .secrets file not found. Cannot run remote tests.")
        return [("AWS Credentials", False)]

    tests = [
        ("make check-aws", "AWS Credentials Check"),
        ("python scripts/test_remote_api.py", "Remote API Tests"),
        ("python scripts/check_status.py", "Deployment Status Check"),
    ]

    results = []
    for cmd, desc in tests:
        result = run_command(cmd, desc)
        results.append((desc, result))

    return results


def run_ci_simulation() -> list:
    """Simulate CI/CD pipeline locally."""
    print("🤖 Simulating CI/CD Pipeline")
    print("=" * 40)

    act_check = subprocess.run("command -v act", shell=True, capture_output=True)
    if act_check.returncode != 0:
        print("❌ ACT not installed. Use 'make act-setup' to install.")
        return [("ACT Installation", False)]

    tests = [("make act-test", "GitHub Actions Tests (via ACT)")]

    results = []
    for cmd, desc in tests:
        result = run_command(cmd, desc)
        results.append((desc, result))

    return results


def print_summary(all_results) -> int:
    """Print test summary."""
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)

    total_tests = 0
    passed_tests = 0

    for category, results in all_results.items():
        print(f"\n{category}:")
        for test_name, result in results:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"  {test_name:<40} {status}")
            total_tests += 1
            if result:
                passed_tests += 1

    print(f"\n📈 OVERALL: {passed_tests}/{total_tests} tests passed")

    if passed_tests == total_tests:
        print("🎉 All tests passed!")
        return 0
    else:
        print(f"❌ {total_tests - passed_tests} tests failed")
        return 1


def main() -> int:
    """Main test runner."""
    parser = argparse.ArgumentParser(
        description="Comprehensive test runner for CVIDEO-CLICK-API"
    )
    parser.add_argument("--local", action="store_true", help="Run only local tests")
    parser.add_argument("--remote", action="store_true", help="Run only remote tests")
    parser.add_argument("--ci", action="store_true", help="Run CI simulation tests")
    parser.add_argument("--all", action="store_true", help="Run all tests (default)")

    args = parser.parse_args()

    # Default to all tests if no specific option is given
    if not any([args.local, args.remote, args.ci]):
        args.all = True

    print("🧪 CVIDEO-CLICK-API Comprehensive Test Runner")
    print("=" * 60)

    all_results = {}

    if args.all or args.local:
        all_results["Local Unit & Integration Tests"] = run_local_tests()
        all_results["Local Deployment Tests"] = run_local_deployment_tests()

    if args.all or args.remote:
        all_results["Remote AWS Tests"] = run_remote_tests()

    if args.all or args.ci:
        all_results["CI/CD Simulation"] = run_ci_simulation()

    return print_summary(all_results)


if __name__ == "__main__":
    sys.exit(main())
