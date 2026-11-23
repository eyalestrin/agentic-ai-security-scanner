#!/usr/bin/env python3
"""Install the Copilot skill and its dependencies without a virtual environment."""

import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


NAME = "agentic-ai-security-scanner"
SOURCE = Path(__file__).resolve().parent / ".github" / "skills" / NAME


def install():
    if sys.version_info < (3, 10):
        raise RuntimeError("Python 3.10 or newer is required")
    skills = Path.home() / ".copilot" / "skills"
    destination = skills / NAME
    skills.mkdir(parents=True, exist_ok=True)
    if os.path.lexists(destination):
        raise FileExistsError(f"{destination} already exists; move or remove it before installing")

    with tempfile.TemporaryDirectory(prefix=f".{NAME}-", dir=skills) as staging:
        staged = Path(staging) / NAME
        shutil.copytree(
            SOURCE, staged,
            ignore=shutil.ignore_patterns(".venv", "venv", ".python-deps", "__pycache__", "*.pyc"),
        )
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "--target", str(staged / ".python-deps"),
             "-r", str(staged / "requirements.txt")],
            check=True,
        )
        (staged / "python-interpreter.txt").write_text(sys.executable + "\n", encoding="utf-8")
        if os.path.lexists(destination):
            raise FileExistsError(f"{destination} appeared during installation; it was not overwritten")
        staged.rename(destination)
    print(f"Installed skill at {destination}")
    print(f"Python interpreter: {sys.executable}")


def main():
    try:
        install()
    except (OSError, RuntimeError, subprocess.CalledProcessError) as exc:
        print(f"Installation failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
