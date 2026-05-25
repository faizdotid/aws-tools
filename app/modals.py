"""Modal dialogs for AWS Tools TUI."""

from textual.screen import ModalScreen
from textual.containers import Vertical, Horizontal
from textual.widgets import Static, Input, Button, Select
from textual.app import ComposeResult

__all__ = [
    "ConfirmModal",
    "CreateInstanceModal",
    "CreateKeyPairModal",
    "CreateSecurityGroupModal",
]


class ConfirmModal(ModalScreen[bool]):
    """Modal confirmation dialog."""

    DEFAULT_CSS = """
    ConfirmModal {
        align: center middle;
    }
    ConfirmModal > Vertical {
        width: 50;
        height: auto;
        border: solid $primary;
        background: $surface;
        padding: 1 2;
    }
    ConfirmModal #confirm-title {
        text-align: center;
        text-style: bold;
        height: 3;
        content-align: center middle;
    }
    ConfirmModal #confirm-buttons {
        height: auto;
        align: center middle;
    }
    ConfirmModal Button {
        margin: 0 1;
    }
    """

    def __init__(self, message: str, title: str = "Confirm", **kwargs) -> None:
        self._message = message
        self._title = title
        super().__init__(**kwargs)

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Static(self._title, id="confirm-title")
            yield Static(self._message)
            with Horizontal(id="confirm-buttons"):
                yield Button("Yes", variant="success", id="btn-yes")
                yield Button("No", variant="error", id="btn-no")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press."""
        self.dismiss(event.button.id == "btn-yes")


class CreateInstanceModal(ModalScreen[dict]):
    """Modal form for creating an EC2 instance."""

    DEFAULT_CSS = """
    CreateInstanceModal {
        align: center middle;
    }
    CreateInstanceModal > Vertical {
        width: 60;
        height: auto;
        border: solid $primary;
        background: $surface;
        padding: 1 2;
    }
    CreateInstanceModal #modal-title {
        text-align: center;
        text-style: bold;
        height: 3;
        content-align: center middle;
    }
    CreateInstanceModal Input {
        margin: 0 0 1 0;
    }
    CreateInstanceModal #form-buttons {
        height: auto;
        align: center middle;
        margin-top: 1;
    }
    CreateInstanceModal Button {
        margin: 0 1;
    }
    """

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Static("Create EC2 Instance", id="modal-title")
            yield Input(placeholder="Instance Type (e.g. t2.micro)", id="input-type")
            yield Input(placeholder="AMI ID (e.g. ami-12345678)", id="input-ami")
            yield Input(placeholder="Key Name", id="input-key")
            yield Input(placeholder="Security Group", id="input-sg", value="default")
            yield Input(placeholder="Storage Size (GB)", id="input-storage", value="8")
            with Horizontal(id="form-buttons"):
                yield Button("Create", variant="success", id="btn-create")
                yield Button("Cancel", variant="primary", id="btn-cancel")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle form submission."""
        if event.button.id == "btn-cancel":
            self.dismiss(None)
            return

        data = {
            "instance_type": self.query_one("#input-type", Input).value,
            "image_id": self.query_one("#input-ami", Input).value,
            "key_name": self.query_one("#input-key", Input).value,
            "security_group": self.query_one("#input-sg", Input).value,
            "storage": self.query_one("#input-storage", Input).value,
        }
        self.dismiss(data)


class CreateKeyPairModal(ModalScreen[str]):
    """Modal form for creating a key pair."""

    DEFAULT_CSS = """
    CreateKeyPairModal {
        align: center middle;
    }
    CreateKeyPairModal > Vertical {
        width: 45;
        height: auto;
        border: solid $primary;
        background: $surface;
        padding: 1 2;
    }
    CreateKeyPairModal #modal-title {
        text-align: center;
        text-style: bold;
        height: 3;
        content-align: center middle;
    }
    CreateKeyPairModal Input {
        margin: 0 0 1 0;
    }
    CreateKeyPairModal #form-buttons {
        height: auto;
        align: center middle;
        margin-top: 1;
    }
    CreateKeyPairModal Button {
        margin: 0 1;
    }
    """

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Static("Create Key Pair", id="modal-title")
            yield Input(placeholder="Key Pair Name", id="input-name")
            with Horizontal(id="form-buttons"):
                yield Button("Create", variant="success", id="btn-create")
                yield Button("Cancel", variant="primary", id="btn-cancel")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press."""
        if event.button.id == "btn-cancel":
            self.dismiss(None)
        else:
            name = self.query_one("#input-name", Input).value
            self.dismiss(name if name else None)


class CreateSecurityGroupModal(ModalScreen[dict]):
    """Modal form for creating a security group."""

    DEFAULT_CSS = """
    CreateSecurityGroupModal {
        align: center middle;
    }
    CreateSecurityGroupModal > Vertical {
        width: 50;
        height: auto;
        border: solid $primary;
        background: $surface;
        padding: 1 2;
    }
    CreateSecurityGroupModal #modal-title {
        text-align: center;
        text-style: bold;
        height: 3;
        content-align: center middle;
    }
    CreateSecurityGroupModal Input {
        margin: 0 0 1 0;
    }
    CreateSecurityGroupModal #form-buttons {
        height: auto;
        align: center middle;
        margin-top: 1;
    }
    CreateSecurityGroupModal Button {
        margin: 0 1;
    }
    """

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Static("Create Security Group", id="modal-title")
            yield Input(placeholder="Group Name", id="input-name")
            yield Input(placeholder="Description", id="input-desc")
            with Horizontal(id="form-buttons"):
                yield Button("Create", variant="success", id="btn-create")
                yield Button("Cancel", variant="primary", id="btn-cancel")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press."""
        if event.button.id == "btn-cancel":
            self.dismiss(None)
        else:
            data = {
                "name": self.query_one("#input-name", Input).value,
                "description": self.query_one("#input-desc", Input).value,
            }
            self.dismiss(data)
