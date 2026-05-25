#!/usr/bin/env python3
"""Entry point for AWS Tools interactive CLI."""

import sys

if __name__ == "__main__":
    try:
        from app import AWSCli
    except ImportError as exc:
        print(f"Failed to import: {exc}")
        print("Ensure you are in the project root and dependencies are installed:")
        print("  pip install -r requirements.txt")
        sys.exit(1)

    cli = AWSCli()
    cli.run()
