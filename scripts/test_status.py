#!/usr/bin/env python3
"""
Comprehensive test status and reporting script.
Provides detailed information about all test types and their current status.
"""

import os
import sys
import json
import tempfile
from typing import Dict, Any
from pathlib import Path
from subprocess_utils import run_git_command


def get_sam_pid_file(port: int) -> str:
    """Get the secure path for SAM PID files."""
    temp_dir = tempfile.gettempdir()
    return os.path.join(temp_dir, f"sam-local-{port}.pid")


def get_sam_log_file(port: int) -> str:
    """Get the secure path for SAM log files."""
    temp_dir = tempfile.gettempdir()
    return os.path.join(temp_dir, f"sam-local-{port}.log")


def run_command(cmd: str, capture_output: bool = True):
    """Run a command and return success status and output."""
    try:
        from subprocess_utils import run_secure_command

        exit_code, stdout, stderr = run_secure_command(
            cmd, timeout=30, capture_output=capture_output
        )
        if capture_output:
            return exit_code == 0, stdout
        else:
            return exit_code == 0, ""
    except Exception as e:
        return False, str(e)


def check_local_server_status() -> Dict[str, Any]:
    """Check if local SAM server is running."""
    status: Dict[str, Any] = {
        "running": False,
        "port": None,
        "pid": None,
        "log_file": None,
    }

    # Check port 3000
    pid_file_3000 = get_sam_pid_file(3000)
    if os.path.exists(pid_file_3000):
        try:
            with open(pid_file_3000, "r") as f:
                pid = f.read().strip()
            # Check if process is running
            success, _ = run_command(f"kill -0 {pid}")
            if success:
                status["running"] = True
                status["port"] = 3000
                status["pid"] = pid
                status["log_file"] = get_sam_log_file(3000)
                return status
        except Exception as e:
            # Log the error but continue checking other ports
            print(f"Warning: Error checking port 3000: {e}", file=sys.stderr)

    # Check port 3001
    pid_file_3001 = get_sam_pid_file(3001)
    if os.path.exists(pid_file_3001):
        try:
            with open(pid_file_3001, "r") as f:
                pid = f.read().strip()
            # Check if process is running
            success, _ = run_command(f"kill -0 {pid}")
            if success:
                status["running"] = True
                status["port"] = 3001
                status["pid"] = pid
                status["log_file"] = get_sam_log_file(3001)
                return status
        except Exception as e:
            # Log the error but continue with remaining checks
            print(f"Warning: Error checking port 3001: {e}", file=sys.stderr)

    return status


def check_aws_deployment_status() -> Dict[str, Any]:
    """Check AWS deployment status."""
    # Get branch and stack name
    try:
        exit_code, branch_output, error = run_git_command(
            ["rev-parse", "--abbrev-ref", "HEAD"]
        )
        if exit_code == 0:
            branch = branch_output.strip()
        else:
            branch = "unknown"

        # Clean branch name for namespace
        branch_safe = branch.replace("/", "-").replace("_", "-").lower()
        stack_name = f"cvideo-click-api-{branch_safe}"

        # Check CloudFormation stack
        success, output = run_command(
            f"aws cloudformation describe-stacks --stack-name {stack_name}"
        )

        if success:
            stack_data = json.loads(output)
            stack_status = stack_data["Stacks"][0]["StackStatus"]

            # Get API Gateway URL if available
            api_url = None
            outputs = stack_data["Stacks"][0].get("Outputs", [])
            for output in outputs:
                if output.get("OutputKey") == "ApiGatewayUrl":
                    api_url = output.get("OutputValue")
                    break

            return {
                "deployed": True,
                "stack_name": stack_name,
                "status": stack_status,
                "api_url": api_url,
                "branch": branch,
            }
        else:
            return {
                "deployed": False,
                "stack_name": stack_name,
                "status": "NOT_DEPLOYED",
                "api_url": None,
                "branch": branch,
            }
    except Exception as e:
        return {"deployed": False, "error": str(e), "branch": "unknown"}


def check_test_artifacts() -> Dict[str, Any]:
    """Check for test artifacts and reports."""
    artifacts: Dict[str, Any] = {}

    # Coverage report
    if os.path.exists("htmlcov/index.html"):
        artifacts["coverage_html"] = "htmlcov/index.html"

    if os.path.exists(".coverage"):
        artifacts["coverage_data"] = ".coverage"

    # Security report
    if os.path.exists("security-report.json"):
        artifacts["security_report"] = "security-report.json"

    # Test results
    if os.path.exists(".pytest_cache"):
        artifacts["pytest_cache"] = ".pytest_cache"

    # Logs
    if os.path.exists("logs"):
        log_files = list(Path("logs").glob("*.log"))
        if log_files:
            artifacts["log_files"] = [str(f) for f in log_files]

    return artifacts


def print_status_report():
    """Print comprehensive test status report."""
    print("🔍 COMPREHENSIVE TEST STATUS REPORT")
    print("=" * 50)
    print()

    # 1. Environment Status
    print("🌍 ENVIRONMENT STATUS")
    print("-" * 20)

    # Check Python environment
    python_version = sys.version.split()[0]
    print(f"Python Version: {python_version}")

    # Check current directory
    current_dir = os.getcwd()
    print(f"Working Directory: {current_dir}")

    # Check git branch
    try:
        exit_code, branch_output, error = run_git_command(
            ["rev-parse", "--abbrev-ref", "HEAD"]
        )
        if exit_code == 0:
            branch = branch_output.strip()
            print(f"Git Branch: {branch}")
        else:
            print(f"Git Branch: Unknown (error: {error})")
    except Exception as e:
        print(f"Git Branch: Unknown (exception: {e})")

    print()

    # 2. Test File Status
    print("📁 TEST FILES STATUS")
    print("-" * 20)

    test_dirs = {
        "Unit Tests": "tests/unit/",
        "Integration Tests": "tests/integration/",
        "Local Integration Tests": "tests/local/",
    }

    for test_type, test_dir in test_dirs.items():
        if os.path.exists(test_dir):
            test_files = list(Path(test_dir).glob("test_*.py"))
            print(f"{test_type}: ✅ ({len(test_files)} files)")
        else:
            print(f"{test_type}: ❌ (directory missing)")

    print()

    # 3. Local Development Status
    print("🏠 LOCAL DEVELOPMENT STATUS")
    print("-" * 30)

    local_status = check_local_server_status()
    if local_status["running"]:
        print("SAM Local Server: ✅ Running")
        print(f"  Port: {local_status['port']}")
        print(f"  PID: {local_status['pid']}")
        print(f"  Log: {local_status['log_file']}")
        print(f"  URL: http://localhost:{local_status['port']}")
    else:
        print("SAM Local Server: ❌ Not running")
        print("  Use 'make local-start' to start")

    # Check SAM build status
    if os.path.exists(".aws-sam/build/"):
        print("SAM Build: ✅ Available")
    else:
        print("SAM Build: ❌ Not built")
        print("  Use 'make local-build' to build")

    print()

    # 4. AWS Deployment Status
    print("☁️  AWS DEPLOYMENT STATUS")
    print("-" * 25)

    aws_status = check_aws_deployment_status()
    if aws_status.get("deployed"):
        print("AWS Stack: ✅ Deployed")
        print(f"  Stack: {aws_status['stack_name']}")
        print(f"  Status: {aws_status['status']}")
        print(f"  Branch: {aws_status['branch']}")
        if aws_status.get("api_url"):
            print(f"  API URL: {aws_status['api_url']}")
    else:
        print("AWS Stack: ❌ Not deployed")
        print(f"  Branch: {aws_status.get('branch', 'unknown')}")
        if aws_status.get("error"):
            print(f"  Error: {aws_status['error']}")
        print("  Use 'make remote-deploy' to deploy")

    print()

    # 5. Test Artifacts
    print("📊 TEST ARTIFACTS")
    print("-" * 15)

    artifacts = check_test_artifacts()
    if artifacts:
        for artifact_type, path in artifacts.items():
            if isinstance(path, list):
                print(f"{artifact_type}: ✅ ({len(path)} files)")
            else:
                print(f"{artifact_type}: ✅ {path}")
    else:
        print("No test artifacts found")
        print("  Run tests to generate reports")

    print()

    # 6. Available Test Commands
    print("🧪 AVAILABLE TEST COMMANDS")
    print("-" * 25)

    test_commands = [
        ("make test", "Mock-based unit & integration tests"),
        ("make test-unit", "Unit tests only"),
        ("make test-integration", "Integration tests only"),
        ("make test-local-integration", "Local SAM integration tests"),
        ("make test-all", "🚀 ULTIMATE: All test types + deployments"),
        ("make local-start", "Start local SAM server"),
        ("make remote-deploy", "Deploy to AWS"),
        ("make remote-test", "Test AWS deployment"),
    ]

    for command, description in test_commands:
        print(f"  {command:<30} {description}")

    print()

    # 7. Recommendations
    print("💡 RECOMMENDATIONS")
    print("-" * 15)

    recommendations = []

    if not local_status["running"]:
        recommendations.append("Start local development: make local-start")

    if not aws_status.get("deployed"):
        recommendations.append("Deploy to AWS for remote testing: make remote-deploy")

    if not artifacts.get("coverage_html"):
        recommendations.append("Generate coverage report: make test")

    if not artifacts.get("security_report"):
        recommendations.append("Run security analysis: make test-security")

    if not recommendations:
        recommendations.append(
            "🎉 Everything looks good! Run 'make test-all' for comprehensive testing"
        )

    for i, rec in enumerate(recommendations, 1):
        print(f"  {i}. {rec}")

    print()
    print("=" * 50)
    print("📖 For more commands: make help")


if __name__ == "__main__":
    print_status_report()
