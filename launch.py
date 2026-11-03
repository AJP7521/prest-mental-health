"""Set up and launch the local app: python3 launch.py (Windows: py launch.py)."""
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import venv

ROOT = Path(__file__).resolve().parent


def main():
    if sys.version_info < (3, 10):
        raise RuntimeError("Install Python 3.10 or newer, then run this command again.")
    npm = shutil.which("npm.cmd" if os.name == "nt" else "npm")
    node = shutil.which("node")
    if not npm or not node:
        raise RuntimeError("Install Node.js 22.12+ (including npm), then reopen your terminal.")
    version = subprocess.check_output([node, "--version"], text=True).strip().lstrip("v")
    major, minor, *_ = map(int, version.split("."))
    if not ((major == 20 and minor >= 19) or (major == 22 and minor >= 12) or major >= 24):
        raise RuntimeError("Use Node.js 20.19+, 22.12+, or 24+.")
    try:
        port = int(os.environ.get("PORT", "8000"))
    except ValueError as error:
        raise RuntimeError("PORT must be a number from 1 to 65535.") from error
    if not 1 <= port <= 65535:
        raise RuntimeError("PORT must be a number from 1 to 65535.")
    with socket.socket() as probe:
        try:
            probe.bind(("127.0.0.1", port))
        except OSError as error:
            raise RuntimeError(f"Port {port} is unavailable. Stop the other server or choose another PORT.") from error

    environment = ROOT / "backend" / ".venv"
    python = environment / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    if not python.exists():
        print("Creating a local Python environment…", flush=True)
        venv.create(environment, with_pip=True)
    commands = [
        ([str(python), "-m", "pip", "install", "-r", "backend/requirements.txt"], ROOT),
        ([npm, "ci"], ROOT / "frontend"),
        ([npm, "run", "build"], ROOT / "frontend"),
    ]
    for command, directory in commands:
        subprocess.run(command, cwd=directory, check=True)
    print(f"\nOpen http://127.0.0.1:{port} once the server starts. Press Ctrl+C to stop.\n", flush=True)
    return subprocess.call([
        str(python), "-m", "uvicorn", "main:app", "--app-dir", "backend",
        "--host", "127.0.0.1", "--port", str(port),
    ], cwd=ROOT)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\nApplication stopped.")
    except (RuntimeError, OSError, subprocess.CalledProcessError) as error:
        print(f"\nLaunch failed: {error}", file=sys.stderr)
        sys.exit(1)
