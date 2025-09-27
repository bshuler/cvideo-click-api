#!/usr/bin/env python3
"""
Secure subprocess utilities for administrative scripts.
Provides secure wrappers for common external tool calls.
"""

import shutil
import subprocess
from typing import List, Optional, Tuple, Union


def find_executable(name: str) -> Optional[str]:
    """Securely find the full path to an executable."""
    return shutil.which(name)


def run_secure_command(
    cmd: Union[str, List[str]],
    cwd: Optional[str] = None,
    timeout: int = 30,
    capture_output: bool = True,
    check: bool = False,
) -> Tuple[int, str, str]:
    """
    Run a command securely with full path validation.

    Args:
        cmd: Command string or list of arguments
        cwd: Working directory
        timeout: Command timeout in seconds
        capture_output: Whether to capture stdout/stderr
        check: Whether to raise exception on non-zero exit

    Returns:
        Tuple of (return_code, stdout, stderr)
    """
    if isinstance(cmd, str):
        cmd_args = cmd.split()
    else:
        cmd_args = list(cmd)

    # Validate that the executable exists and get full path
    executable = find_executable(cmd_args[0])
    if not executable:
        raise FileNotFoundError(f"Executable '{cmd_args[0]}' not found in PATH")

    # Replace first argument with full path
    cmd_args[0] = executable

    try:
        result = subprocess.run(
            cmd_args,
            cwd=cwd,
            capture_output=capture_output,
            text=True,
            timeout=timeout,
            check=check,
        )
        return result.returncode, result.stdout or "", result.stderr or ""
    except subprocess.TimeoutExpired as e:
        return -1, "", f"Command timed out after {timeout} seconds: {e}"
    except subprocess.CalledProcessError as e:
        return e.returncode, e.stdout or "", e.stderr or ""
    except FileNotFoundError as e:
        return -1, "", f"Command not found: {e}"
    except Exception as e:
        return -1, "", f"Unexpected error: {e}"


def run_git_command(args: List[str], cwd: Optional[str] = None) -> Tuple[int, str, str]:
    """Run a git command securely."""
    git_path = find_executable("git")
    if not git_path:
        return -1, "", "Git not found in PATH"

    full_cmd = [git_path] + args
    return run_secure_command(full_cmd, cwd=cwd)


def run_terraform_command(
    args: List[str], cwd: Optional[str] = None
) -> Tuple[int, str, str]:
    """Run a terraform command securely."""
    terraform_path = find_executable("terraform")
    if not terraform_path:
        return -1, "", "Terraform not found in PATH"

    full_cmd = [terraform_path] + args
    return run_secure_command(full_cmd, cwd=cwd)


def run_python_module(
    module: str, args: List[str], cwd: Optional[str] = None
) -> Tuple[int, str, str]:
    """Run a Python module securely."""
    python_path = find_executable("python3")
    if not python_path:
        return -1, "", "Python3 not found in PATH"

    full_cmd = [python_path, "-m", module] + args
    return run_secure_command(full_cmd, cwd=cwd)
