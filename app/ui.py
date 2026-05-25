"""Interactive UI helpers using Questionary and Rich."""

import questionary
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from .utils import print_error as _print_error, print_success as _print_success

__all__ = [
    "console",
    "select_menu",
    "ask_text",
    "ask_password",
    "ask_confirm",
    "ask_select",
    "ask_autocomplete",
    "press_any_key",
    "print_error",
    "print_success",
    "print_info",
    "print_warning",
    "print_panel",
]

console = Console()


def select_menu(title: str, choices: list) -> str:
    """Show an interactive dropdown menu.

    Args:
        title: Menu title.
        choices: List of choice strings.

    Returns:
        Selected choice string or empty string if cancelled.
    """
    result = questionary.select(title, choices=choices).ask()
    return result or ""


def ask_text(message: str, default: str = "") -> str:
    """Ask for text input."""
    result = questionary.text(message, default=default).ask()
    return result or ""


def ask_password(message: str) -> str:
    """Ask for password input (hidden)."""
    result = questionary.password(message).ask()
    return result or ""


def ask_confirm(message: str) -> bool:
    """Ask yes/no confirmation."""
    return questionary.confirm(message, default=False).ask() or False


def ask_select(message: str, choices: list) -> str:
    """Ask user to select one option from dropdown."""
    result = questionary.select(message, choices=choices).ask()
    return result or ""


def ask_autocomplete(message: str, choices: list) -> str:
    """Ask with autocomplete suggestions."""
    result = questionary.autocomplete(message, choices=choices).ask()
    return result or ""


def press_any_key(message: str = "Press any key to continue...") -> None:
    """Wait for user to press any key."""
    questionary.press_any_key_to_continue(message).ask()


def print_error(message: str) -> None:
    """Print styled error message."""
    _print_error(console, message)


def print_success(message: str) -> None:
    """Print styled success message."""
    _print_success(console, message)


def print_info(label: str, value: str) -> None:
    """Print info line."""
    console.print(f":information_source: [bold cyan]{label}[/bold cyan]: {value}")


def print_warning(message: str) -> None:
    """Print styled warning message."""
    from .utils import print_warning as _pw

    _pw(console, message)


def print_panel(title: str, content: str, style: str = "blue") -> None:
    """Print a panel."""
    text = Text.from_markup(content)
    console.print(Panel(text, border_style=style, title=title))
