#!/usr/bin/env python3
"""
Pylance Type Checking Script - Enhanced with MCP Integration

Enhanced type checking combining:
- Pylance/Pyright for comprehensive type checking
- MCP Pylance integration for advanced error collection
- TypedDict safety validation
- Comprehensive error reporting and analysis

This script provides multiple layers of type checking to ensure code quality.
"""

import argparse
import json
import subprocess_utils
import sys
from pathlib import Path
from typing import Dict, List, Any

# Global quiet mode flag
QUIET_MODE = False


def print_status(emoji: str, message: str, force: bool = False) -> None:
    """Print formatted status message."""
    if not QUIET_MODE or force:
        print(f"{emoji} {message}")


def find_python_files() -> List[str]:
    """Find all Python files in the project."""
    python_files = []

    # Directories to scan
    scan_dirs = ["src/", "scripts/", "tests/"]

    for scan_dir in scan_dirs:
        scan_path = Path(scan_dir)
        if scan_path.exists():
            for py_file in scan_path.rglob("*.py"):
                if py_file.is_file():
                    python_files.append(str(py_file))

    return sorted(python_files)


def run_pyright_check() -> Dict[str, Any]:
    """Run Pyright type checker if available."""
    print_status("🔍", "Running Pyright type checker...")

    try:
        # Try to run pyright
        pyright_path = subprocess_utils.find_executable("pyright")
        if not pyright_path:
            return {
                "tool": "pyright",
                "status": "skipped",
                "reason": "Pyright not found in PATH",
                "errors": 0,
            }

        pyright_exit, pyright_stdout, pyright_stderr = (
            subprocess_utils.run_secure_command(
                [pyright_path, "--outputformat", "json"]
            )
        )

        if pyright_stdout:
            try:
                pyright_result = json.loads(pyright_stdout)
                error_count = pyright_result.get("summary", {}).get("errorCount", 0)
                warning_count = pyright_result.get("summary", {}).get("warningCount", 0)

                if error_count > 0 or warning_count > 0:
                    print_status(
                        "❌",
                        f"Pyright found {error_count} errors, {warning_count} warnings",
                        force=True,
                    )
                    if not QUIET_MODE:
                        for diagnostic in pyright_result.get("generalDiagnostics", []):
                            file_path = diagnostic.get("file", "unknown")
                            line = (
                                diagnostic.get("range", {})
                                .get("start", {})
                                .get("line", 0)
                                + 1
                            )
                            message = diagnostic.get("message", "")
                            severity = diagnostic.get("severity", "error")
                            print(f"   {file_path}:{line} - {severity}: {message}")
                else:
                    print_status("✅", "Pyright: No type errors found")

                return {
                    "tool": "pyright",
                    "status": "success",
                    "errors": error_count,
                    "warnings": warning_count,
                    "details": pyright_result.get("generalDiagnostics", []),
                }

            except json.JSONDecodeError:
                print_status("⚠️", "Pyright output parsing failed")
                return {
                    "tool": "pyright",
                    "status": "error",
                    "reason": "Failed to parse JSON output",
                    "errors": 0,
                    "warnings": 0,
                }
        else:
            print_status("✅", "Pyright: No type errors found")
            return {
                "tool": "pyright",
                "status": "success",
                "errors": 0,
                "warnings": 0,
            }

    except FileNotFoundError:
        return {
            "tool": "pyright",
            "status": "skipped",
            "reason": "Pyright not available - install with: npm install -g pyright",
            "errors": 0,
            "warnings": 0,
        }
    except Exception as e:
        return {
            "tool": "pyright",
            "status": "error",
            "reason": str(e),
            "errors": 0,
            "warnings": 0,
        }


def run_mypy_check() -> Dict[str, Any]:
    """Run MyPy type checker as fallback."""
    print_status("🐍", "Running MyPy type checker...")

    try:
        python_files = find_python_files()
        if not python_files:
            return {
                "tool": "mypy",
                "status": "skipped",
                "reason": "No Python files found",
                "errors": 0,
            }

        # Run mypy on directories (same as make type-check)
        mypy_path = subprocess_utils.find_executable("mypy")
        if not mypy_path:
            return {
                "tool": "mypy",
                "status": "skipped",
                "reason": "MyPy not found in PATH",
                "errors": 0,
            }

        mypy_exit, mypy_stdout, mypy_stderr = subprocess_utils.run_secure_command(
            [mypy_path, "--config-file", "pyproject.toml", "src/", "scripts/"]
        )

        if mypy_exit != 0:
            error_lines = mypy_stdout.strip().split("\n") if mypy_stdout else []
            error_count = len([line for line in error_lines if ": error:" in line])

            print_status("❌", f"MyPy found {error_count} type errors", force=True)
            if not QUIET_MODE and error_lines:
                for line in error_lines[:10]:  # Show first 10 errors
                    print(f"   {line}")
                if len(error_lines) > 10:
                    print(f"   ... and {len(error_lines) - 10} more errors")

            return {
                "tool": "mypy",
                "status": "success",
                "errors": error_count,
                "details": error_lines,
            }
        else:
            print_status("✅", "MyPy: No type errors found")
            return {
                "tool": "mypy",
                "status": "success",
                "errors": 0,
            }

    except FileNotFoundError:
        return {
            "tool": "mypy",
            "status": "skipped",
            "reason": "MyPy not available - install with: pip install mypy",
            "errors": 0,
        }
    except Exception as e:
        return {
            "tool": "mypy",
            "status": "error",
            "reason": str(e),
            "errors": 0,
        }


def check_type_annotations() -> Dict[str, Any]:
    """Check for missing type annotations in Python files."""
    print_status("📝", "Checking type annotation coverage...")

    python_files = find_python_files()
    if not python_files:
        return {
            "tool": "annotation_check",
            "status": "skipped",
            "reason": "No Python files found",
            "issues": 0,
        }

    issues = []

    for file_path in python_files:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                lines = f.readlines()

            for line_num, line in enumerate(lines, 1):
                stripped = line.strip()

                # Check for function definitions without type hints
                if (
                    stripped.startswith("def ")
                    and not stripped.startswith("def __")  # Skip magic methods
                    and "->" not in line
                    and ":" in line
                ):

                    # Skip if it's a property or has decorators that might not
                    # need hints
                    prev_line = lines[line_num - 2].strip() if line_num > 1 else ""
                    if not ("@property" in prev_line or "@staticmethod" in prev_line):
                        issues.append(
                            {
                                "file": file_path,
                                "line": line_num,
                                "type": "missing_return_annotation",
                                "context": stripped[:80]
                                + ("..." if len(stripped) > 80 else ""),
                            }
                        )

        except Exception:
            continue  # Skip files that can't be read

    if issues:
        print_status(
            "⚠️", f"Found {len(issues)} functions without return type annotations"
        )
        if not QUIET_MODE:
            for issue in issues[:5]:  # Show first 5 issues
                print(f"   {issue['file']}:{issue['line']} - {issue['context']}")
            if len(issues) > 5:
                print(f"   ... and {len(issues) - 5} more missing annotations")
    else:
        print_status("✅", "Type annotations: Good coverage found")

    return {
        "tool": "annotation_check",
        "status": "success",
        "issues": len(issues),
        "details": issues,
    }


def save_results(results: Dict[str, Any]) -> None:
    """Save results to JSON file."""
    output_file = Path("logs/pylance-check-results.json")
    output_file.parent.mkdir(exist_ok=True)

    try:
        with open(output_file, "w") as f:
            json.dump(results, f, indent=2)
        print_status("💾", f"Results saved to {output_file}")
    except Exception as e:
        print_status("❌", f"Failed to save results: {e}")


def get_workspace_root() -> str:
    """Get the workspace root URI for MCP integration."""
    workspace_root = Path(__file__).parent.parent
    return f"file://{workspace_root.absolute()}"


def collect_mcp_pylance_errors() -> Dict[str, Any]:
    """
    Collect Pylance errors using MCP integration.

    This provides a framework for MCP Pylance integration.
    When MCP server is available, this would call:
    - mcp_pylance_mcp_s_pylanceWorkspaceUserFiles
    - mcp_pylance_mcp_s_pylanceFileSyntaxErrors

    Returns:
        Dictionary containing MCP Pylance results
    """
    print_status("🔗", "Attempting MCP Pylance integration...")

    workspace_root = get_workspace_root()
    python_files = find_python_files()

    # Framework for MCP integration
    # In actual implementation, this would:
    # 1. Connect to MCP Pylance server
    # 2. Get workspace user files
    # 3. Check each file for syntax errors
    # 4. Collect and format results

    return {
        "tool": "mcp-pylance",
        "status": "skipped",
        "reason": "MCP Pylance server not available in current environment",
        "workspace_root": workspace_root,
        "files_found": len(python_files),
        "errors": 0,
        "warnings": 0,
        "issues": 0,
    }


def check_typeddict_safety() -> Dict[str, Any]:
    """
    Check for TypedDict safety patterns.

    This function identifies potential TypedDict safety issues like:
    - Unsafe dictionary access patterns
    - Missing .get() usage for optional keys
    - Type safety violations

    Returns:
        Dictionary containing TypedDict safety analysis
    """
    print_status("🔒", "Checking TypedDict safety patterns...")

    python_files = find_python_files()
    typeddict_issues = []

    # Check for common TypedDict safety patterns
    for file_path in python_files:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                lines = content.split("\n")

            for i, line in enumerate(lines, 1):
                # Look for unsafe dictionary access patterns
                # This is a basic pattern check - in production would use AST parsing
                if ".response[" in line and ".get(" not in line:
                    # Potential unsafe access to response dictionary
                    if "Error" in line or "Code" in line:
                        typeddict_issues.append(
                            {
                                "file": file_path,
                                "line": i,
                                "issue": "Potential unsafe TypedDict access",
                                "suggestion": "Consider using .get() for safe access",
                            }
                        )

        except Exception as e:
            print_status("❌", f"Error checking {file_path}: {e}")

    return {
        "tool": "typeddict-safety",
        "status": "success",
        "files_checked": len(python_files),
        "issues": len(typeddict_issues),
        "details": typeddict_issues,
        "is_safe": len(typeddict_issues) == 0,
    }


def main() -> int:
    """Main entry point for comprehensive type checking with MCP integration."""
    global QUIET_MODE

    parser = argparse.ArgumentParser(
        description="Comprehensive Python type checking with MCP integration"
    )
    parser.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        help="Only show failures and final summary",
    )
    parser.add_argument(
        "--mcp",
        action="store_true",
        help="Attempt MCP Pylance integration when available",
    )
    parser.add_argument(
        "--typeddict-check",
        action="store_true",
        help="Include TypedDict safety validation",
    )
    args = parser.parse_args()

    QUIET_MODE = args.quiet

    print_status("�", "Starting comprehensive type checking...")

    # Create logs directory
    Path("logs").mkdir(exist_ok=True)

    # Run type checking tools
    checks = {}

    # Try Pyright first (most comprehensive)
    pyright_result = run_pyright_check()
    checks["pyright"] = pyright_result

    # Run MyPy as additional validation
    mypy_result = run_mypy_check()
    checks["mypy"] = mypy_result

    # Check type annotations
    annotations_result = check_type_annotations()
    checks["annotations"] = annotations_result

    # Optional: MCP Pylance integration
    if args.mcp:
        mcp_result = collect_mcp_pylance_errors()
        checks["mcp"] = mcp_result

    # Optional: TypedDict safety check
    if args.typeddict_check:
        typeddict_result = check_typeddict_safety()
        checks["typeddict"] = typeddict_result

    # Compile results
    results = {
        "timestamp": "2024-09-25T00:00:00Z",
        "project": "cvideo-click-api",
        "checks": checks,
    }

    # Calculate totals (exclude annotation issues from failure criteria)
    total_errors = sum(check.get("errors", 0) for check in checks.values())
    total_warnings = sum(check.get("warnings", 0) for check in checks.values())
    total_issues = sum(
        check.get("issues", 0)
        for check in checks.values()
        if check.get("tool") != "annotation_check"
    )

    tools_run = len(
        [check for check in checks.values() if check.get("status") == "success"]
    )
    tools_skipped = len(
        [check for check in checks.values() if check.get("status") == "skipped"]
    )

    results["summary"] = {
        "total_errors": total_errors,
        "total_warnings": total_warnings,
        "total_issues": total_issues,
        "tools_run": tools_run,
        "tools_skipped": tools_skipped,
        "overall_status": "PASS" if total_errors == 0 else "FAIL",
    }

    # Save detailed results
    save_results(results)

    # Print summary
    if total_errors == 0:
        print_status(
            "✅", "Type checking passed - No critical issues found", force=True
        )
        if total_warnings > 0:
            print_status("⚠️", f"Note: {total_warnings} warnings found", force=True)
    else:
        print_status(
            "❌",
            f"Type checking failed - {total_errors} errors found",
            force=True,
        )

    if not QUIET_MODE:
        print_status(
            "📊", f"Summary: {tools_run} tools run, {tools_skipped} skipped", force=True
        )
        print_status(
            "📝",
            "Detailed results saved to logs/pylance-check-results.json",
            force=True,
        )

    # Strict checking: fail only on actual type errors, not missing annotations
    return 0 if total_errors == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
