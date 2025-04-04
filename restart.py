import sys
import time
import subprocess
import os

def main():
    # Wait briefly to allow the parent process to shut down
    time.sleep(2)
    if len(sys.argv) < 2:
        print("Usage: restart.py <script_path> [args...]")
        sys.exit(1)
    script_path = sys.argv[1]
    args = sys.argv[2:]
    try:
        new_process = subprocess.Popen(
            [sys.executable, script_path] + args,
            close_fds=True,
            start_new_session=True
        )
        print(f"Started new process with PID: {new_process.pid}")
    except Exception as e:
        print(f"Error restarting: {e}")

if __name__ == "__main__":
    main()
