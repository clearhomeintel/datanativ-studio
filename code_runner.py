"""
code_runner.py
Safely runs a student's generated Python script and returns stdout/stderr.
Uses subprocess with a 30-second timeout (AI API calls need time on first run).
"""

import subprocess
import sys
import tempfile
import os

# Apps that make OpenAI API calls need time on the first scoring run.
# GPT-4o-mini takes ~1-2 s per call; with 2-3 passion questions that's up to 6 s
# before the cache kicks in.  30 s gives ample headroom.
_TIMEOUT = 30


def run_code(source: str) -> dict:
    """
    Run `source` as a Python script.
    Returns {"stdout": str, "stderr": str, "exit_code": int, "timed_out": bool}
    """
    result = {"stdout": "", "stderr": "", "exit_code": -1, "timed_out": False}

    with tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".py",
        delete=False,
        prefix="datanativ_student_"
    ) as f:
        f.write(source)
        tmp_path = f.name

    try:
        proc = subprocess.run(
            [sys.executable, tmp_path],
            capture_output=True,
            text=True,
            timeout=_TIMEOUT,
        )
        result["stdout"]    = proc.stdout
        result["stderr"]    = proc.stderr
        result["exit_code"] = proc.returncode
    except subprocess.TimeoutExpired:
        result["timed_out"] = True
        result["stderr"]    = (
            f"⏱  Your code ran for more than {_TIMEOUT} seconds and was stopped. "
            "Check for infinite loops, or if you're making many API calls, "
            "make sure they are cached so they only run once."
        )
        result["exit_code"] = -1
    except Exception as e:
        result["stderr"]    = f"Runner error: {e}"
        result["exit_code"] = -1
    finally:
        try:
            os.unlink(tmp_path)
        except Exception:
            pass

    return result
