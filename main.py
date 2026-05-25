#!/usr/bin/env python3
"""Entry point for AWS Tools CLI."""

import sys

# Ensure app package is importable
if __name__ == '__main__':
    try:
        from app import Command
    except ImportError as e:
        print(f"Failed to import: {e}")
        print("Make sure you are in the project root and dependencies are installed:")
        print("  pip install -r requirements.txt")
        sys.exit(1)

    def main():
        command = Command()
        command.start()

    main()
