"""Main Textual App for AWS Tools TUI."""

from textual.app import App
from textual.containers import Horizontal, Vertical
from textual.widgets import ContentSwitcher, ListView

from .controller import AWSController
from .views import (
    DashboardView,
    EC2View,
    VPCView,
    S3View,
    QuotasView,
    ConfigView,
)
from .widgets import Sidebar, LogPanel, StatusBar

__all__ = ["AWSToolsApp"]


class AWSToolsApp(App):
    """AWS Tools Textual Application."""

    CSS_PATH = "../styles.tcss"

    BINDINGS = [
        ("f1", "help", "Help"),
        ("ctrl+q", "quit", "Quit"),
        ("1", "goto_dashboard", "Dashboard"),
        ("2", "goto_ec2", "EC2"),
        ("3", "goto_vpc", "VPC"),
        ("4", "goto_s3", "S3"),
        ("5", "goto_quotas", "Quotas"),
        ("6", "goto_config", "Config"),
    ]

    def __init__(self, **kwargs) -> None:
        self.controller = AWSController()
        super().__init__(**kwargs)

    def compose(self):
        """Compose the application layout."""
        yield StatusBar()
        with Horizontal(id="main-layout"):
            yield Sidebar()
            with ContentSwitcher(id="content-switcher", initial="dashboard"):
                yield DashboardView(id="dashboard")
                yield EC2View(id="ec2")
                yield VPCView(id="vpc")
                yield S3View(id="s3")
                yield QuotasView(id="quotas")
                yield ConfigView(id="config")
        yield LogPanel()

    def on_mount(self) -> None:
        """Initialize on mount."""
        self.title = "AWS Tools"
        self.sub_title = "TUI"
        self.query_one(Sidebar).set_active("dashboard")
        self._update_log_panel()
        self.update_status()
        self.set_timer(5, self._update_log_panel)

    def _update_log_panel(self) -> None:
        """Refresh log panel from controller."""
        log_panel = self.query_one(LogPanel)
        log_panel.logs = self.controller.get_logs()
        self.set_timer(2, self._update_log_panel)

    def update_status(self) -> None:
        """Update status bar from controller state."""
        status = self.query_one(StatusBar)
        if self.controller.is_configured:
            status.update_region(self.controller.region)
            status.update_connection(True)
        else:
            status.update_region("Not configured")
            status.update_connection(False)

    def _switch_view(self, name: str) -> None:
        """Switch to named view and update sidebar."""
        switcher = self.query_one("#content-switcher", ContentSwitcher)
        switcher.current = name
        self.query_one(Sidebar).set_active(name)

    # ── Actions ──────────────────────────────────────────────────

    def action_help(self) -> None:
        """Show help message."""
        self.notify(
            "F1=Help | Ctrl+Q=Quit | 1-6=Switch View | R=Refresh",
            severity="information",
            timeout=5,
        )

    def action_goto_dashboard(self) -> None:
        self._switch_view("dashboard")

    def action_goto_ec2(self) -> None:
        self._switch_view("ec2")

    def action_goto_vpc(self) -> None:
        self._switch_view("vpc")

    def action_goto_s3(self) -> None:
        self._switch_view("s3")

    def action_goto_quotas(self) -> None:
        self._switch_view("quotas")

    def action_goto_config(self) -> None:
        self._switch_view("config")

    # ── Sidebar Navigation ───────────────────────────────────────

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        """Handle sidebar menu selection."""
        item_id = event.item.id or ""
        if item_id == "menu-dashboard":
            self._switch_view("dashboard")
        elif item_id == "menu-ec2":
            self._switch_view("ec2")
        elif item_id == "menu-vpc":
            self._switch_view("vpc")
        elif item_id == "menu-s3":
            self._switch_view("s3")
        elif item_id == "menu-quotas":
            self._switch_view("quotas")
        elif item_id == "menu-config":
            self._switch_view("config")
