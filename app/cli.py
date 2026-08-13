"""Interactive CLI for AWS Tools using Questionary + Rich."""

from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich import box

from .controller import AWSController
from .config import RegionConfig
import os

from .ui import (
    console,
    select_menu,
    ask_text,
    ask_password,
    ask_confirm,
    ask_select,
    ask_autocomplete,
    press_any_key,
    print_error,
    print_success,
    print_info,
    print_warning,
    print_panel,
)
from .utils import (
    format_datetime,
    mb_to_gb,
    validate_instance_id,
    validate_ami_id,
    ensure_results_dir,
)

__all__ = ["AWSCli"]


class AWSCli:
    """Interactive CLI for AWS management."""

    def __init__(self) -> None:
        self._ctrl = AWSController()

    def _require_config(self) -> bool:
        """Ensure AWS is configured, prompt if not."""
        if self._ctrl.is_configured:
            return True
        print_warning("AWS not configured yet.")
        self._configure()
        return self._ctrl.is_configured

    def _wait_spinner(self, message: str, func, *args, **kwargs):
        """Execute function with a spinner."""
        with Progress(
            SpinnerColumn(),
            TextColumn("[bold green]{task.description}"),
            transient=True,
            console=console,
        ) as progress:
            progress.add_task(description=message, total=None)
            return func(*args, **kwargs)

    # ── Main Menu ────────────────────────────────────────────────

    def run(self) -> None:
        """Main menu loop."""
        print_panel(
            "AWS Tools",
            ":sparkles: Welcome to AWS Tools CLI :sparkles:\n"
            "Navigate using [bold]arrow keys[/bold] and [bold]Enter[/bold]",
            style="cyan",
        )

        while True:
            choices = [
                "🖥️  EC2 Management",
                "🌐 VPC & Networking",
                "🪣 S3",
                "📊 Service Quotas",
                "📤 Export",
                "⚙️  Configuration",
                "🚪 Exit",
            ]
            choice = select_menu("Main Menu", choices)

            if choice == "🖥️  EC2 Management":
                self._ec2_menu()
            elif choice == "🌐 VPC & Networking":
                self._vpc_menu()
            elif choice == "🪣 S3":
                self._s3_menu()
            elif choice == "📊 Service Quotas":
                self._quotas_menu()
            elif choice == "📤 Export":
                self._export_menu()
            elif choice == "⚙️  Configuration":
                self._config_menu()
            elif choice in ("🚪 Exit", ""):
                print_success("Goodbye! 👋")
                break

    # ── EC2 Menu ─────────────────────────────────────────────────

    def _ec2_menu(self) -> None:
        while True:
            if not self._require_config():
                return
            choice = select_menu(
                "EC2 Management",
                [
                    "📋 Show Instances",
                    "📦 Show Instance Types",
                    "🖼️  Show Images (AMIs)",
                    "🔑 Show Key Pairs",
                    "🔒 Show Security Groups",
                    "➕ Create Instance",
                    "🔐 Create Key Pair",
                    "🔓 Create Security Group",
                    "🌐 Authorize Security Group",
                    "▶ Start Instance",
                    "⏹ Stop Instance",
                    "🔄 Reboot Instance",
                    "🗑 Terminate Instance",
                    "🔙 Back",
                ],
            )

            if choice == "📋 Show Instances":
                self._show_instances()
            elif choice == "📦 Show Instance Types":
                self._show_instance_types()
            elif choice == "🖼️  Show Images (AMIs)":
                self._show_images()
            elif choice == "🔑 Show Key Pairs":
                self._show_key_pairs()
            elif choice == "🔒 Show Security Groups":
                self._show_security_groups()
            elif choice == "➕ Create Instance":
                self._create_instance()
            elif choice == "🔐 Create Key Pair":
                self._create_key_pair()
            elif choice == "🔓 Create Security Group":
                self._create_security_group()
            elif choice == "🌐 Authorize Security Group":
                self._authorize_security_group()
            elif choice == "▶ Start Instance":
                self._start_instance()
            elif choice == "⏹ Stop Instance":
                self._stop_instance()
            elif choice == "🔄 Reboot Instance":
                self._reboot_instance()
            elif choice == "🗑 Terminate Instance":
                self._terminate_instance()
            else:
                break

    def _show_instances(self) -> None:
        data = self._wait_spinner("Fetching instances...", self._ctrl.get_instances)
        if not data:
            if self._ctrl.last_error:
                print_error(self._ctrl.last_error)
            else:
                print_info("Info", "No instances found.")
            return

        table = Table(title="EC2 Instances", box=box.ROUNDED)
        table.add_column("ID", style="cyan", no_wrap=True)
        table.add_column("Type", style="magenta")
        table.add_column("State", style="green")
        table.add_column("Public IP", style="blue")
        table.add_column("Key", style="purple")
        table.add_column("Launch Time", style="yellow")

        for reservation in data:
            for inst in reservation.get("Instances", []):
                table.add_row(
                    inst["InstanceId"],
                    inst["InstanceType"],
                    inst["State"]["Name"],
                    inst.get("PublicIpAddress", "N/A"),
                    inst.get("KeyName", "N/A"),
                    format_datetime(inst.get("LaunchTime")),
                )
        console.print(table)
        press_any_key()

    def _show_instance_types(self) -> None:
        data = self._wait_spinner(
            "Fetching instance types...", self._ctrl.get_instance_types
        )
        if not data:
            if self._ctrl.last_error:
                print_error(self._ctrl.last_error)
            else:
                print_info("Info", "No instance types found.")
            return

        table = Table(title="EC2 Instance Types", box=box.ROUNDED)
        table.add_column("Type", style="cyan", no_wrap=True)
        table.add_column("vCPU", justify="right")
        table.add_column("Memory", justify="right")
        table.add_column("Arch", style="yellow")
        table.add_column("Storage", style="blue")
        table.add_column("Network", style="purple")

        for it in data[:100]:
            storage = "EBS-Only"
            if it.get("InstanceStorageSupported"):
                total = it.get("InstanceStorageInfo", {}).get("TotalSizeInGB", 0)
                storage = f"{total} GB"
            table.add_row(
                it["InstanceType"],
                str(it["VCpuInfo"]["DefaultVCpus"]),
                f"{mb_to_gb(it['MemoryInfo']['SizeInMiB'])} GB",
                ", ".join(it["ProcessorInfo"].get("SupportedArchitectures", [])),
                storage,
                it["NetworkInfo"].get("NetworkPerformance", "N/A"),
            )
        console.print(table)
        if len(data) > 100:
            print_info("Note", f"Showing 100 of {len(data)} instance types")
        press_any_key()

    def _show_images(self) -> None:
        name = ask_text(
            "AMI name filter (e.g. ubuntu/images/hvm-ssd/*, debian-12-*, amzn2-*)"
        )
        if not name:
            print_warning("A name filter is required to search public AMIs.")
            return
        data = self._wait_spinner("Fetching images...", self._ctrl.get_images, name)
        if not data:
            if self._ctrl.last_error:
                print_error(self._ctrl.last_error)
            else:
                print_info("Info", "No images found.")
            return

        table = Table(title="Public AMIs", box=box.ROUNDED)
        table.add_column("Image ID", style="cyan", no_wrap=True)
        table.add_column("Name", style="magenta")
        table.add_column("Arch", style="yellow")
        table.add_column("Created", style="green")

        for image in data[:50]:
            table.add_row(
                image["ImageId"],
                image.get("Name", "N/A")[:40],
                image.get("Architecture", "N/A"),
                image.get("CreationDate", "N/A")[:10],
            )
        console.print(table)
        if len(data) > 50:
            print_info("Note", f"Showing 50 of {len(data)} results")
        press_any_key()

    def _show_key_pairs(self) -> None:
        data = self._wait_spinner("Fetching key pairs...", self._ctrl.get_key_pairs)
        if not data:
            if self._ctrl.last_error:
                print_error(self._ctrl.last_error)
            else:
                print_info("Info", "No key pairs found.")
            return

        table = Table(title="EC2 Key Pairs", box=box.ROUNDED)
        table.add_column("Name", style="cyan")
        table.add_column("ID", style="green")
        table.add_column("Created", style="magenta")

        for kp in data:
            table.add_row(
                kp["KeyName"],
                kp.get("KeyPairId", "N/A"),
                format_datetime(kp.get("CreateTime")),
            )
        console.print(table)
        press_any_key()

    def _show_security_groups(self) -> None:
        data = self._wait_spinner(
            "Fetching security groups...", self._ctrl.get_security_groups
        )
        if not data:
            if self._ctrl.last_error:
                print_error(self._ctrl.last_error)
            else:
                print_info("Info", "No security groups found.")
            return

        table = Table(title="Security Groups", box=box.ROUNDED)
        table.add_column("Name", style="cyan")
        table.add_column("Description", style="magenta")
        table.add_column("Group ID", style="green", no_wrap=True)
        table.add_column("VPC ID", style="blue")

        for sg in data:
            table.add_row(
                sg["GroupName"],
                sg.get("Description", "")[:30],
                sg["GroupId"],
                sg.get("VpcId", "N/A"),
            )
        console.print(table)
        press_any_key()

    def _create_instance(self) -> None:
        instance_type = ask_text("Instance Type (e.g. t2.micro)", default="t2.micro")
        if not instance_type:
            return
        image_id = ask_text("AMI ID (e.g. ami-12345678)")
        if not image_id:
            return
        if not validate_ami_id(image_id):
            if not ask_confirm("AMI ID format looks invalid. Continue anyway?"):
                return

        key_pairs = self._ctrl.get_key_pairs()
        if not key_pairs:
            print_warning("No key pairs found. Creating one...")
            self._create_key_pair()
            key_pairs = self._ctrl.get_key_pairs()

        key_choices = [kp["KeyName"] for kp in key_pairs]
        key_name = (
            ask_autocomplete("Select Key Name", key_choices)
            if key_choices
            else ask_text("Key Name")
        )

        sg_groups = self._ctrl.get_security_groups()
        sg_choices = [sg["GroupName"] for sg in sg_groups]
        sg_name = (
            ask_autocomplete("Security Group", sg_choices)
            if sg_choices
            else ask_text("Security Group Name")
        )

        storage_str = ask_text("Storage Size (GB)", default="8")
        try:
            storage = int(storage_str)
        except ValueError:
            storage = 8

        root_device = ask_text("Root Device", default="/dev/sda1") or "/dev/sda1"
        disable_api_termination = ask_confirm("Enable API termination protection?")

        instance_id = self._wait_spinner(
            "Creating instance...",
            self._ctrl.create_instance,
            image_id,
            instance_type,
            key_name,
            storage,
            sg_name or "default",
            root_device,
            disable_api_termination,
        )
        if instance_id:
            print_success(f"Instance {instance_id} created successfully!")
        else:
            print_error(self._ctrl.last_error or "Failed to create instance.")

    def _create_key_pair(self) -> str:
        """Create a key pair and save the .pem file.

        Returns:
            Key pair name if successful, empty string otherwise.
        """
        key_name = ask_text("Key Pair Name")
        if not key_name:
            return ""
        result = self._wait_spinner(
            "Creating key pair...", self._ctrl.create_key_pair, key_name
        )
        if not result:
            print_error(self._ctrl.last_error or "Failed.")
            return ""

        ensure_results_dir()
        outfile = f"results/keypairs/{result['KeyName']}-{result['KeyPairId']}.pem"
        with os.fdopen(os.open(outfile, os.O_WRONLY | os.O_CREAT, 0o600), "w") as f:
            f.write(result["KeyMaterial"])
        print_success(f"Key pair '{key_name}' created! Saved to {outfile}")
        return key_name

    def _create_security_group(self) -> None:
        name = ask_text("Security Group Name")
        if not name:
            return
        description = ask_text("Description", default=f"Security group {name}")
        group_id = self._wait_spinner(
            "Creating security group...",
            self._ctrl.create_security_group,
            name,
            description,
        )
        if group_id:
            print_success(f"Security group '{name}' created! ID: {group_id}")
        else:
            print_error(self._ctrl.last_error or "Failed.")

    def _authorize_security_group(self) -> None:
        group_id = ask_text("Security Group ID")
        if not group_id:
            return
        if self._ctrl.authorize_security_group(group_id):
            print_success(f"All traffic authorized for {group_id}")
            print_warning("This opens ALL ports to 0.0.0.0/0 — use with caution!")
        else:
            print_error(self._ctrl.last_error or "Failed.")

    def _start_instance(self) -> None:
        instance_id = ask_text("Instance ID")
        if not instance_id or not validate_instance_id(instance_id):
            print_error("Valid Instance ID is required.")
            return
        if self._ctrl.start_instance(instance_id):
            print_success(f"Instance {instance_id} started.")
        else:
            print_error(self._ctrl.last_error or "Failed.")

    def _stop_instance(self) -> None:
        instance_id = ask_text("Instance ID")
        if not instance_id or not validate_instance_id(instance_id):
            print_error("Valid Instance ID is required.")
            return
        if self._ctrl.stop_instance(instance_id):
            print_success(f"Instance {instance_id} stopped.")
        else:
            print_error(self._ctrl.last_error or "Failed.")

    def _reboot_instance(self) -> None:
        instance_id = ask_text("Instance ID")
        if not instance_id or not validate_instance_id(instance_id):
            print_error("Valid Instance ID is required.")
            return
        if self._ctrl.reboot_instance(instance_id):
            print_success(f"Instance {instance_id} rebooted.")
        else:
            print_error(self._ctrl.last_error or "Failed.")

    def _terminate_instance(self) -> None:
        instance_id = ask_text("Instance ID")
        if not instance_id or not validate_instance_id(instance_id):
            print_error("Valid Instance ID is required.")
            return
        if not ask_confirm(f"Are you sure you want to terminate {instance_id}?"):
            return
        if self._ctrl.terminate_instance(instance_id):
            print_success(f"Instance {instance_id} terminated.")
        else:
            print_error(self._ctrl.last_error or "Failed.")

    # ── VPC Menu ─────────────────────────────────────────────────

    def _vpc_menu(self) -> None:
        while True:
            if not self._require_config():
                return
            choice = select_menu(
                "VPC & Networking",
                [
                    "🌐 Show VPCs",
                    "📡 Show Subnets",
                    "🔙 Back",
                ],
            )
            if choice == "🌐 Show VPCs":
                self._show_vpcs()
            elif choice == "📡 Show Subnets":
                self._show_subnets()
            else:
                break

    def _show_vpcs(self) -> None:
        data = self._wait_spinner("Fetching VPCs...", self._ctrl.get_vpcs)
        if not data:
            if self._ctrl.last_error:
                print_error(self._ctrl.last_error)
            else:
                print_info("Info", "No VPCs found.")
            return

        table = Table(title="VPCs", box=box.ROUNDED)
        table.add_column("VPC ID", style="cyan", no_wrap=True)
        table.add_column("Name", style="magenta")
        table.add_column("CIDR", style="green")
        table.add_column("Default", style="yellow")

        for vpc in data:
            name = next(
                (t["Value"] for t in vpc.get("Tags", []) if t["Key"] == "Name"),
                "Unnamed",
            )
            table.add_row(
                vpc["VpcId"],
                name,
                vpc["CidrBlock"],
                "Yes" if vpc["IsDefault"] else "No",
            )
        console.print(table)
        press_any_key()

    def _show_subnets(self) -> None:
        vpc_id = ask_text("VPC ID (optional, leave empty for all)")
        data = self._wait_spinner("Fetching subnets...", self._ctrl.get_subnets, vpc_id)
        if not data:
            if self._ctrl.last_error:
                print_error(self._ctrl.last_error)
            else:
                print_info("Info", "No subnets found.")
            return

        table = Table(title="Subnets", box=box.ROUNDED)
        table.add_column("Subnet ID", style="cyan", no_wrap=True)
        table.add_column("VPC ID", style="blue")
        table.add_column("CIDR", style="green")
        table.add_column("AZ", style="magenta")
        table.add_column("Available IPs", justify="right")

        for sn in data:
            table.add_row(
                sn["SubnetId"],
                sn["VpcId"],
                sn["CidrBlock"],
                sn["AvailabilityZone"],
                str(sn.get("AvailableIpAddressCount", 0)),
            )
        console.print(table)
        press_any_key()

    # ── S3 Menu ──────────────────────────────────────────────────

    def _s3_menu(self) -> None:
        while True:
            if not self._require_config():
                return
            choice = select_menu(
                "S3",
                [
                    "🪣 Show Buckets",
                    "📁 Show Objects",
                    "🔙 Back",
                ],
            )
            if choice == "🪣 Show Buckets":
                self._show_buckets()
            elif choice == "📁 Show Objects":
                self._show_objects()
            else:
                break

    def _show_buckets(self) -> None:
        data = self._wait_spinner("Fetching buckets...", self._ctrl.get_buckets)
        if not data:
            if self._ctrl.last_error:
                print_error(self._ctrl.last_error)
            else:
                print_info("Info", "No buckets found.")
            return

        table = Table(title="S3 Buckets", box=box.ROUNDED)
        table.add_column("Bucket Name", style="cyan")
        table.add_column("Created", style="green")

        for bucket in data:
            table.add_row(bucket["Name"], format_datetime(bucket.get("CreationDate")))
        console.print(table)
        press_any_key()

    def _show_objects(self) -> None:
        bucket = ask_text("Bucket Name")
        if not bucket:
            return

        data = self._wait_spinner(
            f"Fetching objects from {bucket}...", self._ctrl.get_objects, bucket
        )
        if not data:
            if self._ctrl.last_error:
                print_error(self._ctrl.last_error)
            else:
                print_info("Info", "No objects found.")
            return

        table = Table(title=f"Objects in {bucket}", box=box.ROUNDED)
        table.add_column("Key", style="cyan")
        table.add_column("Size", justify="right")
        table.add_column("Last Modified", style="magenta")
        table.add_column("Storage Class", style="yellow")

        for obj in data[:100]:
            size = obj.get("Size", 0)
            size_str = (
                f"{size / (1024 * 1024):.2f} MB"
                if size > 1024 * 1024
                else f"{size / 1024:.2f} KB"
                if size > 1024
                else f"{size} B"
            )
            table.add_row(
                obj.get("Key", "")[:50],
                size_str,
                format_datetime(obj.get("LastModified"))[:19],
                obj.get("StorageClass", "STANDARD"),
            )
        console.print(table)
        if len(data) > 100:
            print_info("Note", f"Showing 100 of {len(data)} objects")
        press_any_key()

    # ── Quotas Menu ──────────────────────────────────────────────

    def _quotas_menu(self) -> None:
        while True:
            if not self._require_config():
                return
            choice = select_menu(
                "Service Quotas",
                [
                    "📊 Show Quotas",
                    "🔙 Back",
                ],
            )
            if choice == "📊 Show Quotas":
                self._show_quotas()
            else:
                break

    def _show_quotas(self) -> None:
        code = ask_text("Service Code (e.g. ec2, s3, vpc)", default="ec2")
        if not code:
            return

        data = self._wait_spinner(
            f"Fetching quotas for {code}...", self._ctrl.get_service_quotas, code
        )
        if not data:
            if self._ctrl.last_error:
                print_error(self._ctrl.last_error)
            else:
                print_info("Info", "No quotas found.")
            return

        table = Table(title=f"Service Quotas — {code}", box=box.ROUNDED)
        table.add_column("Service", style="cyan")
        table.add_column("Quota Name", style="magenta")
        table.add_column("Value", justify="right")
        table.add_column("Unit", style="blue")
        table.add_column("Adjustable", style="yellow")

        for quota in data:
            table.add_row(
                quota.get("ServiceName", "N/A"),
                quota["QuotaName"][:40],
                str(quota.get("Value", "N/A")),
                quota.get("Unit", "N/A"),
                "Yes" if quota.get("Adjustable") else "No",
            )
        console.print(table)
        press_any_key()

    # ── Export Menu ──────────────────────────────────────────────

    def _export_menu(self) -> None:
        while True:
            if not self._require_config():
                return
            choice = select_menu(
                "Export",
                [
                    "📤 Export Instances to JSON",
                    "📤 Export Images to JSON",
                    "🔙 Back",
                ],
            )
            if choice == "📤 Export Instances to JSON":
                filename = ask_text("Filename", default="instances_export")
                path = self._ctrl.export_instances(filename)
                if path:
                    print_success(f"Exported to {path}")
                else:
                    print_error(self._ctrl.last_error or "Export failed.")
            elif choice == "📤 Export Images to JSON":
                filename = ask_text("Filename", default="images_export")
                name = ask_text(
                    "AMI name filter (e.g. ubuntu/images/hvm-ssd/*, debian-12-*, amzn2-*)"
                )
                if not name:
                    print_warning("A name filter is required to export images.")
                    continue
                path = self._ctrl.export_images(filename, name)
                if path:
                    print_success(f"Exported to {path}")
                else:
                    print_error(self._ctrl.last_error or "Export failed.")
            else:
                break

    # ── Config Menu ──────────────────────────────────────────────

    def _config_menu(self) -> None:
        while True:
            choice = select_menu(
                "Configuration",
                [
                    "🔑 Configure AWS Credentials",
                    "🌍 Change Region",
                    "🗺️  Show Supported Regions",
                    "🔙 Back",
                ],
            )
            if choice == "🔑 Configure AWS Credentials":
                self._configure()
            elif choice == "🌍 Change Region":
                self._change_region()
            elif choice == "🗺️  Show Supported Regions":
                self._show_regions()
            else:
                break

    def _configure(self) -> None:
        key = ask_text("AWS Access Key ID")
        if not key:
            return
        secret = ask_password("AWS Secret Access Key")
        if not secret:
            return
        region = ask_select("Select Region", [r["name"] for r in RegionConfig.REGIONS])
        if not region:
            region = "us-east-1"

        result = self._ctrl.configure(key, secret, region)
        if result["status"]:
            print_success(result["response"])
        else:
            print_error(result["response"])

    def _change_region(self) -> None:
        if not self._ctrl.is_configured:
            print_warning("Please configure AWS credentials first.")
            return
        region = ask_select("Select Region", [r["name"] for r in RegionConfig.REGIONS])
        if not region:
            return
        result = self._ctrl.change_region(region)
        if result["status"]:
            print_success(result["response"])
        else:
            print_error(result["response"])

    def _show_regions(self) -> None:
        table = Table(title="Supported Regions", box=box.ROUNDED)
        table.add_column("Region Name", style="cyan")
        table.add_column("Description", style="green")
        for region in RegionConfig.REGIONS:
            table.add_row(region["name"], region["description"])
        console.print(table)
        press_any_key()
