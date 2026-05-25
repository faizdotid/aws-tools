"""Utility functions for AWS Tools."""

import datetime
import json
import os
from pathlib import Path
from typing import Any, Optional

from rich.console import Console
from rich.panel import Panel
from rich.text import Text

__all__ = [
    "mb_to_gb",
    "format_datetime",
    "ensure_results_dir",
    "validate_instance_id",
    "validate_ami_id",
    "save_json",
    "print_error",
    "print_success",
    "print_warning",
    "print_info",
]


def mb_to_gb(mb: int) -> int:
    """Convert megabytes to gigabytes."""
    return mb // 1024


def format_datetime(dt: Any) -> str:
    """Format datetime object to string safely."""
    if isinstance(dt, datetime.datetime):
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    return str(dt)


def ensure_results_dir() -> None:
    """Create results directories if they do not exist."""
    dirs = ["results", "results/keypairs", "results/exports"]
    for d in dirs:
        Path(d).mkdir(parents=True, exist_ok=True)


def validate_instance_id(instance_id: str) -> bool:
    """Validate EC2 instance ID format."""
    return isinstance(instance_id, str) and instance_id.startswith("i-") and len(instance_id) >= 10


def validate_ami_id(ami_id: str) -> bool:
    """Validate AMI ID format."""
    return isinstance(ami_id, str) and ami_id.startswith("ami-") and len(ami_id) >= 12


def save_json(data: Any, filename: str) -> str:
    """Save data to JSON file in results/exports.

    Args:
        data: Data to serialize.
        filename: Base filename without extension.

    Returns:
        Absolute path to saved file.
    """
    ensure_results_dir()
    filepath = Path("results/exports") / f"{filename}.json"
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, default=str, ensure_ascii=False)
    return str(filepath)


def print_error(console: Console, message: str) -> None:
    """Print styled error message."""
    text = Text.from_markup(f":x: [bold red]{message}[/bold red]")
    console.print(Panel(text, border_style="red", title="Error"))


def print_success(console: Console, message: str) -> None:
    """Print styled success message."""
    text = Text.from_markup(f":white_check_mark: [bold green]{message}[/bold green]")
    console.print(Panel(text, border_style="green", title="Success"))


def print_warning(console: Console, message: str) -> None:
    """Print styled warning message."""
    text = Text.from_markup(f":warning: [bold yellow]{message}[/bold yellow]")
    console.print(Panel(text, border_style="yellow", title="Warning"))


def print_info(console: Console, label: str, value: str) -> None:
    """Print info line with label."""
    console.print(f":information_source: [bold cyan]{label}[/bold cyan]: {value}")
