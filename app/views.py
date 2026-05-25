"""Textual screens for AWS Tools TUI."""


from textual.containers import Horizontal, Vertical, Grid
from textual.widgets import (
    Static,
    Button,
    DataTable,
    Tree,
    Input,
    TabbedContent,
    TabPane,
    Select,
)
from textual.reactive import reactive
from textual.widget import Widget
from textual.app import ComposeResult

from .widgets import SummaryCard, FilteredDataTable, LogPanel
from .modals import (
    ConfirmModal,
    CreateInstanceModal,
    CreateKeyPairModal,
    CreateSecurityGroupModal,
)
from .utils import format_datetime, mb_to_gb
from .config import RegionConfig

__all__ = [
    "DashboardView",
    "EC2View",
    "VPCView",
    "S3View",
    "QuotasView",
    "ConfigView",
]


# ── Dashboard Screen ───────────────────────────────────────────

class DashboardView(Widget):
    """Dashboard overview screen."""

    DEFAULT_CSS = """
    DashboardScreen {
        padding: 1;
    }
    DashboardScreen #summary-grid {
        height: auto;
        grid-size: 4;
        grid-gutter: 1;
        margin-bottom: 1;
    }
    DashboardScreen #activity-panel {
        height: 1fr;
        border: solid $primary;
        padding: 1;
    }
    DashboardScreen #activity-title {
        text-style: bold;
        height: 2;
    }
    """

    BINDINGS = [
        ("r", "refresh", "Refresh"),
    ]

    def compose(self) -> ComposeResult:
        with Grid(id="summary-grid"):
            yield SummaryCard("EC2 Instances", "-", id="card-instances")
            yield SummaryCard("S3 Buckets", "-", id="card-buckets")
            yield SummaryCard("VPCs", "-", id="card-vpcs")
            yield SummaryCard("Key Pairs", "-", id="card-keypairs")
        with Vertical(id="activity-panel"):
            yield Static("Recent Activity", id="activity-title")
            yield Static("Press [bold green]R[/bold green] to refresh", id="activity-content")

    def on_mount(self) -> None:
        """Load data on mount."""
        self.action_refresh()

    def action_refresh(self) -> None:
        """Refresh dashboard data."""
        ctrl = self.app.controller
        if not ctrl.is_configured:
            self.notify("Not configured", severity="warning")
            return

        instances = ctrl.get_instances()
        buckets = ctrl.get_buckets()
        vpcs = ctrl.get_vpcs()
        keypairs = ctrl.get_key_pairs()

        instance_count = sum(len(r.get("Instances", [])) for r in instances)
        self.query_one("#card-instances", SummaryCard).set_value(str(instance_count))
        self.query_one("#card-buckets", SummaryCard).set_value(str(len(buckets)))
        self.query_one("#card-vpcs", SummaryCard).set_value(str(len(vpcs)))
        self.query_one("#card-keypairs", SummaryCard).set_value(str(len(keypairs)))

        logs = ctrl.get_logs()
        content = "\n".join(logs[-10:]) if logs else "No activity yet."
        self.query_one("#activity-content", Static).update(content)


# ── EC2 Screen ─────────────────────────────────────────────────

class EC2View(Widget):
    """EC2 management screen with tabs."""

    DEFAULT_CSS = """
    EC2Screen {
        padding: 1;
    }
    EC2Screen #action-bar {
        height: auto;
        margin-bottom: 1;
    }
    EC2Screen Button {
        margin: 0 1;
    }
    """

    BINDINGS = [
        ("r", "refresh", "Refresh"),
        ("c", "create", "Create Instance"),
        ("s", "start", "Start"),
        ("x", "stop", "Stop"),
        ("b", "reboot", "Reboot"),
        ("d", "terminate", "Terminate"),
    ]

    def compose(self) -> ComposeResult:
        with Horizontal(id="action-bar"):
            yield Button("🔄 Refresh", id="btn-refresh")
            yield Button("➕ Create", id="btn-create")
            yield Button("▶ Start", id="btn-start")
            yield Button("⏹ Stop", id="btn-stop")
            yield Button("🔄 Reboot", id="btn-reboot")
            yield Button("🗑 Terminate", variant="error", id="btn-terminate")
        with TabbedContent():
            with TabPane("Instances", id="tab-instances"):
                yield FilteredDataTable(id="table-instances")
            with TabPane("Types", id="tab-types"):
                yield FilteredDataTable(id="table-types")
            with TabPane("Images", id="tab-images"):
                yield FilteredDataTable(id="table-images")
            with TabPane("Key Pairs", id="tab-keypairs"):
                yield FilteredDataTable(id="table-keypairs")
            with TabPane("Security Groups", id="tab-sg"):
                yield FilteredDataTable(id="table-sg")

    def on_mount(self) -> None:
        """Load data on mount."""
        self.action_refresh()

    def action_refresh(self) -> None:
        """Refresh all EC2 data."""
        ctrl = self.app.controller
        if not ctrl.is_configured:
            return

        self._load_instances(ctrl)
        self._load_types(ctrl)
        self._load_images(ctrl)
        self._load_keypairs(ctrl)
        self._load_security_groups(ctrl)

    def _load_instances(self, ctrl) -> None:
        table = self.query_one("#table-instances", FilteredDataTable)
        table.set_columns(["ID", "Type", "State", "Public IP", "Key", "Launch Time"])
        data = ctrl.get_instances()
        rows = []
        for reservation in data:
            for inst in reservation.get("Instances", []):
                rows.append(
                    (
                        inst["InstanceId"],
                        inst["InstanceType"],
                        inst["State"]["Name"],
                        inst.get("PublicIpAddress", "N/A"),
                        inst.get("KeyName", "N/A"),
                        format_datetime(inst.get("LaunchTime")),
                    )
                )
        table.set_rows(rows)

    def _load_types(self, ctrl) -> None:
        table = self.query_one("#table-types", FilteredDataTable)
        table.set_columns(["Type", "vCPU", "Memory", "Arch", "Storage", "Network"])
        data = ctrl.get_instance_types()
        rows = []
        for it in data:
            storage = "EBS-Only"
            if it.get("InstanceStorageSupported"):
                total = it.get("InstanceStorageInfo", {}).get("TotalSizeInGB", 0)
                storage = f"{total} GB"
            rows.append(
                (
                    it["InstanceType"],
                    str(it["VCpuInfo"]["DefaultVCpus"]),
                    f"{mb_to_gb(it['MemoryInfo']['SizeInMiB'])} GB",
                    ", ".join(it["ProcessorInfo"].get("SupportedArchitectures", [])),
                    storage,
                    it["NetworkInfo"].get("NetworkPerformance", "N/A"),
                )
            )
        table.set_rows(rows)

    def _load_images(self, ctrl) -> None:
        table = self.query_one("#table-images", FilteredDataTable)
        table.set_columns(["Image ID", "Name", "Arch", "State", "Created"])
        data = ctrl.get_images()
        rows = []
        for image in data[:100]:
            rows.append(
                (
                    image["ImageId"],
                    image.get("Name", "N/A")[:40],
                    image.get("Architecture", "N/A"),
                    image.get("State", "N/A"),
                    image.get("CreationDate", "N/A")[:10],
                )
            )
        table.set_rows(rows)

    def _load_keypairs(self, ctrl) -> None:
        table = self.query_one("#table-keypairs", FilteredDataTable)
        table.set_columns(["Name", "ID", "Created"])
        data = ctrl.get_key_pairs()
        rows = []
        for kp in data:
            rows.append(
                (
                    kp["KeyName"],
                    kp.get("KeyPairId", "N/A"),
                    format_datetime(kp.get("CreateTime")),
                )
            )
        table.set_rows(rows)

    def _load_security_groups(self, ctrl) -> None:
        table = self.query_one("#table-sg", FilteredDataTable)
        table.set_columns(["Name", "Description", "Group ID", "VPC ID"])
        data = ctrl.get_security_groups()
        rows = []
        for sg in data:
            rows.append(
                (
                    sg["GroupName"],
                    sg.get("Description", "")[:30],
                    sg["GroupId"],
                    sg.get("VpcId", "N/A"),
                )
            )
        table.set_rows(rows)

    def _get_selected_instance_id(self) -> str:
        """Get selected instance ID from instances table."""
        table = self.query_one("#table-instances", FilteredDataTable)
        row_idx = table.get_selected_row()
        if row_idx is None or row_idx < 0:
            return ""
        rows = table._all_rows
        if row_idx >= len(rows):
            return ""
        return str(rows[row_idx][0])

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle action buttons."""
        ctrl = self.app.controller
        btn_id = event.button.id

        if btn_id == "btn-refresh":
            self.action_refresh()
        elif btn_id == "btn-create":
            self.action_create()
        elif btn_id == "btn-start":
            self.action_start()
        elif btn_id == "btn-stop":
            self.action_stop()
        elif btn_id == "btn-reboot":
            self.action_reboot()
        elif btn_id == "btn-terminate":
            self.action_terminate()

    def action_create(self) -> None:
        """Open create instance modal."""
        self.app.push_screen(CreateInstanceModal(), self._on_create_result)

    def _on_create_result(self, result: dict) -> None:
        """Handle create instance modal result."""
        if not result:
            return
        ctrl = self.app.controller
        try:
            storage = int(result.get("storage", 8))
        except ValueError:
            storage = 8
        instance_id = ctrl.create_instance(
            result.get("image_id", ""),
            result.get("instance_type", ""),
            result.get("key_name", ""),
            storage,
            result.get("security_group", "default"),
        )
        if instance_id:
            self.notify(f"Instance {instance_id} created", severity="information")
            self.action_refresh()
        else:
            self.notify(ctrl.last_error or "Failed to create instance", severity="error")

    def action_start(self) -> None:
        """Start selected instance."""
        instance_id = self._get_selected_instance_id()
        if not instance_id:
            self.notify("Select an instance first", severity="warning")
            return
        if self.app.controller.start_instance(instance_id):
            self.notify(f"Started {instance_id}")
            self.action_refresh()
        else:
            self.notify(self.app.controller.last_error or "Failed", severity="error")

    def action_stop(self) -> None:
        """Stop selected instance."""
        instance_id = self._get_selected_instance_id()
        if not instance_id:
            self.notify("Select an instance first", severity="warning")
            return
        if self.app.controller.stop_instance(instance_id):
            self.notify(f"Stopped {instance_id}")
            self.action_refresh()
        else:
            self.notify(self.app.controller.last_error or "Failed", severity="error")

    def action_reboot(self) -> None:
        """Reboot selected instance."""
        instance_id = self._get_selected_instance_id()
        if not instance_id:
            self.notify("Select an instance first", severity="warning")
            return
        if self.app.controller.reboot_instance(instance_id):
            self.notify(f"Rebooted {instance_id}")
            self.action_refresh()
        else:
            self.notify(self.app.controller.last_error or "Failed", severity="error")

    def action_terminate(self) -> None:
        """Terminate selected instance."""
        instance_id = self._get_selected_instance_id()
        if not instance_id:
            self.notify("Select an instance first", severity="warning")
            return

        def on_confirm(confirmed: bool) -> None:
            if not confirmed:
                return
            if self.app.controller.terminate_instance(instance_id):
                self.notify(f"Terminated {instance_id}")
                self.action_refresh()
            else:
                self.notify(self.app.controller.last_error or "Failed", severity="error")

        self.app.push_screen(
            ConfirmModal(f"Terminate instance {instance_id}?"), on_confirm
        )


# ── VPC Screen ─────────────────────────────────────────────────

class VPCView(Widget):
    """VPC and networking screen."""

    DEFAULT_CSS = """
    VPCScreen {
        padding: 1;
    }
    VPCScreen #vpc-container {
        height: 100%;
    }
    VPCScreen Tree {
        width: 40%;
        height: 100%;
        border: solid $primary;
    }
    VPCScreen #subnet-panel {
        width: 60%;
        height: 100%;
        border: solid $primary;
        padding: 1;
    }
    """

    BINDINGS = [
        ("r", "refresh", "Refresh"),
    ]

    def compose(self) -> ComposeResult:
        with Horizontal(id="vpc-container"):
            yield Tree("VPCs", id="vpc-tree")
            with Vertical(id="subnet-panel"):
                yield Static("Select a VPC to view subnets", id="subnet-info")
                yield FilteredDataTable(id="table-subnets")

    def on_mount(self) -> None:
        """Load VPC data on mount."""
        self.action_refresh()

    def action_refresh(self) -> None:
        """Refresh VPC data."""
        ctrl = self.app.controller
        if not ctrl.is_configured:
            return

        tree = self.query_one("#vpc-tree", Tree)
        tree.clear()
        root = tree.root
        root.expand()

        vpcs = ctrl.get_vpcs()
        for vpc in vpcs:
            name = next(
                (t["Value"] for t in vpc.get("Tags", []) if t["Key"] == "Name"),
                "Unnamed",
            )
            label = f"{vpc['VpcId']} ({name})"
            node = root.add(label, data=vpc["VpcId"])
            node.add_leaf(f"CIDR: {vpc['CidrBlock']}")
            node.add_leaf(f"Default: {'Yes' if vpc['IsDefault'] else 'No'}")

    def on_tree_node_selected(self, event: Tree.NodeSelected) -> None:
        """Show subnets when VPC is selected."""
        vpc_id = event.node.data
        if not vpc_id:
            return

        ctrl = self.app.controller
        subnets = ctrl.get_subnets(vpc_id)
        self.query_one("#subnet-info", Static).update(f"Subnets for {vpc_id}")

        table = self.query_one("#table-subnets", FilteredDataTable)
        table.set_columns(["Subnet ID", "CIDR", "AZ", "Available IPs", "Default"])
        rows = []
        for sn in subnets:
            rows.append(
                (
                    sn["SubnetId"],
                    sn["CidrBlock"],
                    sn["AvailabilityZone"],
                    str(sn.get("AvailableIpAddressCount", 0)),
                    "Yes" if sn.get("DefaultForAz") else "No",
                )
            )
        table.set_rows(rows)


# ── S3 Screen ──────────────────────────────────────────────────

class S3View(Widget):
    """S3 management screen."""

    DEFAULT_CSS = """
    S3Screen {
        padding: 1;
    }
    S3Screen #s3-container {
        height: 100%;
    }
    S3Screen Tree {
        width: 35%;
        height: 100%;
        border: solid $primary;
    }
    S3Screen #object-panel {
        width: 65%;
        height: 100%;
        border: solid $primary;
        padding: 1;
    }
    """

    BINDINGS = [
        ("r", "refresh", "Refresh"),
    ]

    def compose(self) -> ComposeResult:
        with Horizontal(id="s3-container"):
            yield Tree("Buckets", id="bucket-tree")
            with Vertical(id="object-panel"):
                yield Static("Select a bucket to view objects", id="object-info")
                yield FilteredDataTable(id="table-objects")

    def on_mount(self) -> None:
        """Load S3 data on mount."""
        self.action_refresh()

    def action_refresh(self) -> None:
        """Refresh bucket list."""
        ctrl = self.app.controller
        if not ctrl.is_configured:
            return

        tree = self.query_one("#bucket-tree", Tree)
        tree.clear()
        root = tree.root
        root.expand()

        buckets = ctrl.get_buckets()
        for bucket in buckets:
            root.add(bucket["Name"], data=bucket["Name"])

    def on_tree_node_selected(self, event: Tree.NodeSelected) -> None:
        """Show objects when bucket is selected."""
        bucket = event.node.data
        if not bucket:
            return

        ctrl = self.app.controller
        objects = ctrl.get_objects(bucket)
        info = ctrl.get_bucket_info(bucket)
        count = info.get("ObjectCount", 0)
        size = info.get("TotalSizeBytes", 0)
        size_str = f"{size / (1024 * 1024):.2f} MB" if size > 1024 * 1024 else f"{size / 1024:.2f} KB" if size > 1024 else f"{size} B"

        self.query_one("#object-info", Static).update(
            f"Bucket: {bucket} | Objects: {count} | Size: {size_str}"
        )

        table = self.query_one("#table-objects", FilteredDataTable)
        table.set_columns(["Key", "Size", "Last Modified", "Storage Class"])
        rows = []
        for obj in objects[:200]:
            osize = obj.get("Size", 0)
            osize_str = (
                f"{osize / (1024 * 1024):.2f} MB"
                if osize > 1024 * 1024
                else f"{osize / 1024:.2f} KB"
                if osize > 1024
                else f"{osize} B"
            )
            rows.append(
                (
                    obj.get("Key", "")[:50],
                    osize_str,
                    format_datetime(obj.get("LastModified"))[:19],
                    obj.get("StorageClass", "STANDARD"),
                )
            )
        table.set_rows(rows)


# ── Quotas Screen ──────────────────────────────────────────────

class QuotasView(Widget):
    """Service Quotas screen."""

    DEFAULT_CSS = """
    QuotasScreen {
        padding: 1;
    }
    QuotasScreen #quota-input {
        height: auto;
        margin-bottom: 1;
    }
    QuotasScreen Input {
        width: 40;
    }
    QuotasScreen Button {
        margin-left: 1;
    }
    """

    BINDINGS = [
        ("r", "refresh", "Refresh"),
    ]

    def compose(self) -> ComposeResult:
        with Horizontal(id="quota-input"):
            yield Input(placeholder="Service code (e.g. ec2)", id="input-code")
            yield Button("Load", id="btn-load")
        yield FilteredDataTable(id="table-quotas")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle load button."""
        if event.button.id == "btn-load":
            self.action_refresh()

    def action_refresh(self) -> None:
        """Load quotas."""
        ctrl = self.app.controller
        if not ctrl.is_configured:
            self.notify("Not configured", severity="warning")
            return

        code = self.query_one("#input-code", Input).value
        if not code:
            self.notify("Enter a service code", severity="warning")
            return

        self.notify(f"Loading quotas for {code}...", severity="information")
        data = ctrl.get_service_quotas(code)
        if not data and ctrl.last_error:
            self.notify(ctrl.last_error, severity="error")
            return

        table = self.query_one("#table-quotas", FilteredDataTable)
        table.set_columns(["Service", "Quota Name", "Value", "Unit", "Adjustable"])
        rows = []
        for quota in data:
            rows.append(
                (
                    quota.get("ServiceName", "N/A"),
                    quota["QuotaName"][:40],
                    str(quota.get("Value", "N/A")),
                    quota.get("Unit", "N/A"),
                    "Yes" if quota.get("Adjustable") else "No",
                )
            )
        table.set_rows(rows)
        self.notify(f"Loaded {len(rows)} quotas", severity="information")


# ── Config Screen ──────────────────────────────────────────────

class ConfigView(Widget):
    """AWS configuration screen."""

    DEFAULT_CSS = """
    ConfigScreen {
        padding: 1;
        align: center middle;
    }
    ConfigScreen #config-form {
        width: 60;
        height: auto;
        border: solid $primary;
        padding: 1 2;
    }
    ConfigScreen #config-title {
        text-align: center;
        text-style: bold;
        height: 3;
        content-align: center middle;
    }
    ConfigScreen Input {
        margin: 0 0 1 0;
    }
    ConfigScreen #config-buttons {
        height: auto;
        align: center middle;
        margin-top: 1;
    }
    ConfigScreen Button {
        margin: 0 1;
    }
    """

    def compose(self) -> ComposeResult:
        with Vertical(id="config-form"):
            yield Static("AWS Configuration", id="config-title")
            yield Input(placeholder="AWS Access Key ID", id="input-key", password=True)
            yield Input(placeholder="AWS Secret Access Key", id="input-secret", password=True)
            regions = [(r["name"], r["name"]) for r in RegionConfig.REGIONS]
            yield Select(regions, prompt="Select Region", id="select-region")
            with Horizontal(id="config-buttons"):
                yield Button("Configure", variant="success", id="btn-configure")
                yield Button("Test", variant="primary", id="btn-test")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle config buttons."""
        if event.button.id == "btn-configure":
            self._do_configure()
        elif event.button.id == "btn-test":
            self._do_test()

    def _do_configure(self) -> None:
        """Save configuration."""
        key = self.query_one("#input-key", Input).value
        secret = self.query_one("#input-secret", Input).value
        region_select = self.query_one("#select-region", Select)
        region = str(region_select.value) if region_select.value and region_select.value != Select.BLANK else "us-east-1"

        if not key or not secret:
            self.notify("Access Key and Secret are required", severity="error")
            return

        result = self.app.controller.configure(key, secret, region)
        if result["status"]:
            self.notify(result["response"], severity="information")
            self.app.update_status()
        else:
            self.notify(result["response"], severity="error")

    def _do_test(self) -> None:
        """Test connection by listing instances."""
        if not self.app.controller.is_configured:
            self.notify("Not configured yet", severity="warning")
            return
        data = self.app.controller.get_instances()
        if data is not None:
            self.notify("Connection OK", severity="information")
        else:
            self.notify(self.app.controller.last_error or "Connection failed", severity="error")
