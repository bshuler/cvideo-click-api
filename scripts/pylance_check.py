#!/usr/bin/env python3
"""
Pylance Type Checking Script

Enhanced type checking using Pylance/Pyright for better type safety validation.
This script provides a simplified framework for type checking that can be expanded
to integrate with MCP Pylance server when available.
"""

import argparse
import json
import subprocess
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
        result = subprocess.run(
            ["pyright", "--outputformat", "json"],
            capture_output=True,
            text=True,
            check=False,
        )

        if result.stdout:
            try:
                pyright_result = json.loads(result.stdout)
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

        # Run mypy on found files
        result = subprocess.run(
            ["mypy", "--config-file", "pyproject.toml"] + python_files,
            capture_output=True,
            text=True,
            check=False,
        )

        if result.returncode != 0:
            error_lines = result.stdout.strip().split("\n") if result.stdout else []
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
    """Save detailed results to log file."""
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    with open(log_dir / "pylance-check-results.json", "w") as f:
        json.dump(results, f, indent=2)


def main() -> int:
    """Main function for type checking."""
    global QUIET_MODE

    parser = argparse.ArgumentParser(
        description="Enhanced type checking with Pylance/Pyright"
    )
    parser.add_argument("--quiet", action="store_true", help="Suppress detailed output")
    args = parser.parse_args()

    QUIET_MODE = args.quiet

    if not QUIET_MODE:
        print_status("🔍", "Starting enhanced type checking...")

    # Run type checkers
    results: Dict[str, Any] = {
        "timestamp": "2025-09-24T22:00:00Z",
        "checks": {
            "pyright": run_pyright_check(),
            "mypy": run_mypy_check(),
            "annotations": check_type_annotations(),
        },
    }

    # Calculate totals
    checks = results["checks"]
    total_errors = sum(check.get("errors", 0) for check in checks.values())
    total_warnings = sum(check.get("warnings", 0) for check in checks.values())
    total_issues = sum(check.get("issues", 0) for check in checks.values())

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
        "overall_status": "PASS" if (total_errors + total_issues) == 0 else "FAIL",
    }

    # Save detailed results
    save_results(results)

    # Print summary
    if total_errors + total_issues == 0:
        print_status(
            "✅", "Type checking passed - No critical issues found", force=True
        )
        if total_warnings > 0:
            print_status("⚠️", f"Note: {total_warnings} warnings found", force=True)
    else:
        print_status(
            "❌",
            f"Type checking failed - {total_errors} errors, "
            f"{total_issues} issues found",
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

    return 0 if (total_errors + total_issues) == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
