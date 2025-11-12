# queuectl/executor.py

"""
Executor module
---------------
Handles the execution of shell commands for background jobs.

Responsibilities:
- Execute the command in a subprocess
- Capture stdout, stderr, and exit code
- Handle timeouts and unexpected errors
"""

import subprocess
from typing import Tuple, Optional


def execute_command(command: str, timeout: int = 3600) -> Tuple[int, str, str]:
    """
    Run a shell command and capture its output.

    Parameters
    ----------
    command : str
        The shell command to execute (e.g., "echo 'Hello World'")
    timeout : int
        Maximum time allowed for execution, in seconds (default: 1 hour)

    Returns
    -------
    tuple
        (exit_code, stdout, stderr)
        exit_code : int
            0 if success, non-zero if failure or error
        stdout : str
            Captured standard output text
        stderr : str
            Captured standard error text
    """
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        return result.returncode, result.stdout.strip(), result.stderr.strip()

    except subprocess.TimeoutExpired as e:
        # If command exceeds timeout limit
        return 1, "", f"Command timed out after {timeout} seconds"

    except FileNotFoundError:
        # Command binary not found
        return 1, "", "Command not found"

    except Exception as e:
        # Catch-all for any other runtime issue
        return 1, "", f"Execution error: {str(e)}"
