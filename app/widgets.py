"""Custom Textual widgets for AWS Tools TUI."""

from textual.widgets import DataTable, Static, Input, ListView, ListItem, Label
from textual.containers import Horizontal, Vertical
from textual.reactive import reactive
from textual.app import ComposeResult

__all__ = [
    "Sidebar",
    "LogPanel",
    "StatusBar",
    "FilteredDataTable",
    "SummaryCard",
]


class Sidebar(Vertical):
    """Navigation sidebar with menu items."""

    DEFAULT_CSS = """
    Sidebar {
        width: 20;
        height: 100%;
        dock: left;
        background: $surface-darken-1;
        border-right: solid $primary;
    }
    Sidebar ListView {
        height: 1fr;
        border: none;
        background: transparent;
    }
    Sidebar ListView > ListItem {
        background: transparent;
        color: $text;
        height: 3;
    }
    Sidebar ListView > ListItem:hover {
        background: $primary-darken-2;
    }
    Sidebar ListView > ListItem.--highlight {
        background: $primary;
        color: $text;
        text-style: bold;
    }
    Sidebar #sidebar-title {
        height: 3;
        content-align: center middle;
        text-style: bold;
        background: $primary-darken-1;
    }
    """

    def compose(self) -> ComposeResult:
        yield Static("AWS Tools", id="sidebar-title")
        yield ListView(
            ListItem(Label("🏠  Dashboard"), id="menu-dashboard"),
            ListItem(Label("💻  EC2"), id="menu-ec2"),
            ListItem(Label("🌐  VPC"), id="menu-vpc"),
            ListItem(Label("🪣  S3"), id="menu-s3"),
            ListItem(Label("📊  Quotas"), id="menu-quotas"),
            ListItem(Label("⚙️  Config"), id="menu-config"),
            id="sidebar-list",
        )

    def set_active(self, view_name: str) -> None:
        """Highlight active menu item."""
        list_view = self.query_one("#sidebar-list", ListView)
        for idx, item in enumerate(list_view.children):
            if item.id == f"menu-{view_name}":
                list_view.index = idx
                break


class LogPanel(Static):
    """Bottom panel displaying activity logs."""

    logs: reactive[list] = reactive(list)

    DEFAULT_CSS = """
    LogPanel {
        height: 6;
        border-top: solid $primary;
        background: $surface-darken-1;
        padding: 0 1;
    }
    LogPanel #log-content {
        height: 100%;
        color: $text-muted;
    }
    """

    def compose(self) -> ComposeResult:
        yield Static(id="log-content")

    def watch_logs(self, logs: list) -> None:
        """Update display when logs change."""
        content = self.query_one("#log-content", Static)
        text = "\n".join(logs[-5:]) if logs else "Ready..."
        content.update(text)

    def add_log(self, message: str) -> None:
        """Add a log entry."""
        self.logs = self.logs + [message]


class StatusBar(Horizontal):
    """Top status bar showing region and connection status."""

    DEFAULT_CSS = """
    StatusBar {
        height: 1;
        background: $primary-darken-2;
        color: $text;
        padding: 0 1;
    }
    StatusBar Static {
        width: auto;
    }
    """

    def compose(self) -> ComposeResult:
        yield Static("AWS Tools TUI", id="status-title")
        yield Static(" | Region: ", id="status-sep")
        yield Static("Not configured", id="status-region")
        yield Static(" | ", id="status-sep2")
        yield Static("⏹ Disconnected", id="status-connection")

    def update_region(self, region: str) -> None:
        """Update region display."""
        self.query_one("#status-region", Static).update(region)

    def update_connection(self, connected: bool) -> None:
        """Update connection status."""
        label = "🟢 Connected" if connected else "⏹ Disconnected"
        self.query_one("#status-connection", Static).update(label)


class FilteredDataTable(Vertical):
    """DataTable with a filter input above it."""

    DEFAULT_CSS = """
    FilteredDataTable {
        height: 100%;
    }
    FilteredDataTable Input {
        height: 3;
        margin: 0 0 1 0;
    }
    FilteredDataTable DataTable {
        height: 1fr;
    }
    """

    def __init__(self, *args, **kwargs) -> None:
        self._all_rows: list = []
        super().__init__(*args, **kwargs)

    def compose(self) -> ComposeResult:
        yield Input(placeholder="Filter...", id="filter-input")
        yield DataTable(id="data-table")

    def on_input_changed(self, event: Input.Changed) -> None:
        """Filter rows when input changes."""
        table = self.query_one("#data-table", DataTable)
        query = event.value.lower()
        table.clear()
        for row in self._all_rows:
            if any(query in str(cell).lower() for cell in row):
                table.add_row(*row)

    def set_columns(self, columns: list) -> None:
        """Set table columns."""
        table = self.query_one("#data-table", DataTable)
        table.clear(columns=True)
        for col in columns:
            if isinstance(col, tuple):
                table.add_column(*col)
            else:
                table.add_column(col)

    def set_rows(self, rows: list) -> None:
        """Set table rows and store for filtering."""
        self._all_rows = rows
        table = self.query_one("#data-table", DataTable)
        table.clear()
        for row in rows:
            table.add_row(*row)

    def get_selected_row(self) -> tuple:
        """Get currently selected row coordinates."""
        table = self.query_one("#data-table", DataTable)
        return table.cursor_row


class SummaryCard(Vertical):
    """Card widget for dashboard summary."""

    DEFAULT_CSS = """
    SummaryCard {
        width: 1fr;
        height: auto;
        border: solid $primary;
        padding: 1;
        margin: 0 1;
    }
    SummaryCard .card-title {
        text-align: center;
        text-style: bold;
        color: $text-muted;
    }
    SummaryCard .card-value {
        text-align: center;
        text-style: bold;
        height: 3;
        content-align: center middle;
        color: $text;
    }
    """

    def __init__(self, title: str, value: str = "-", **kwargs) -> None:
        self._title = title
        self._value = value
        super().__init__(**kwargs)

    def compose(self) -> ComposeResult:
        yield Static(self._title, classes="card-title")
        yield Static(self._value, classes="card-value", id="card-value")

    def set_value(self, value: str) -> None:
        """Update card value."""
        self.query_one("#card-value", Static).update(value)
