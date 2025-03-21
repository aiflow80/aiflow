"""
Command-line entry point for running Python scripts through aiflow.
This module re-exports functionality from aiflow.events.run to provide a shorter import path.
"""
from aiflow.events.run import run_module

# When run as a module, delegate to events.run
if __name__ == "__main__":
    import sys
    from aiflow.events.run import run_module
    
    if len(sys.argv) < 2:
        print("Usage: python -m aiflow.run <script_path> [args...]")
        sys.exit(1)
    
    success = run_module(sys.argv[1])
    sys.exit(0 if success else 1)
