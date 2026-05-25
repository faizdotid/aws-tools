"""Command-line interface with Rich-enhanced UX."""

import os
import signal
import sys
from typing import Any, Dict, List

from rich.console import Console
from rich.prompt import Prompt
from rich.panel import Panel
from rich.text import Text
from rich.columns import Columns

from .client import Client


class Command:
    """Main CLI command loop."""

    def __init__(self):
        self.__console = Console()
        self.__prompt = Prompt()
        self.__client = Client(console=self.__console, prompt=self.__prompt)
        self.__running = True
        self.init()
        self._setup_signal_handlers()

    def _setup_signal_handlers(self):
        """Handle Ctrl+C gracefully."""
        signal.signal(signal.SIGINT, self._signal_handler)

    def _signal_handler(self, signum, frame):
        self.__console.print("\n")
        if self.__prompt.ask('[bold red]Exit?[/bold red]', choices=['y', 'n'], default='n') == 'y':
            self.__console.print(':wave: [bold cyan]Goodbye![/bold cyan] :wave:')
            sys.exit(0)

    def init(self):
        """Initialize directories and welcome message."""
        os.makedirs('results', exist_ok=True)
        os.makedirs('results/keypairs', exist_ok=True)
        os.makedirs('results/exports', exist_ok=True)

        welcome = Text.from_markup(
            ":sparkles: [bold cyan]Welcome to AWS Tools CLI[/bold cyan] :sparkles:\n"
            "[dim]Type[/dim] [bold green]help[/bold green] [dim]to see available commands[/dim]\n"
            "[dim]Type[/dim] [bold green]exit[/bold green] [dim]to quit[/dim]"
        )
        self.__console.print(Panel(welcome, border_style="cyan", title="AWS Tools"))

    def _get_commands(self) -> List[Dict[str, Any]]:
        """Command registry."""
        return [
            # ── Configuration ──
            {"command": "configure", "skip": 1, "method": "configure",
             "args": ["aws_access_key_id", "aws_secret_access_key", "region_name"],
             "desc": "Configure AWS credentials"},
            {"command": "change region", "skip": 2, "method": "change_region",
             "args": ["region_name"], "desc": "Change AWS region"},
            {"command": "show regions", "skip": 2, "method": "show_regions",
             "args": [], "desc": "Show supported regions"},

            # ── EC2 Instances ──
            {"command": "show instances", "skip": 2, "method": "show_instances",
             "args": ["instance_id"], "desc": "Show EC2 instances"},
            {"command": "show instance types", "skip": 3, "method": "show_instance_types",
             "args": ["instance_type"], "desc": "Show EC2 instance types"},
            {"command": "create instance", "skip": 2, "method": "create_instance",
             "args": [], "desc": "Create a new EC2 instance"},
            {"command": "start instance", "skip": 2, "method": "start_instance",
             "args": ["instance_id"], "desc": "Start a stopped instance"},
            {"command": "stop instance", "skip": 2, "method": "stop_instance",
             "args": ["instance_id"], "desc": "Stop a running instance"},
            {"command": "reboot instance", "skip": 2, "method": "reboot_instance",
             "args": ["instance_id"], "desc": "Reboot an instance"},
            {"command": "terminate instance", "skip": 2, "method": "terminate_instance",
             "args": ["instance_id"], "desc": "Terminate an instance"},

            # ── AMIs ──
            {"command": "show images", "skip": 2, "method": "show_images",
             "args": ["image_name"], "desc": "Show Amazon Machine Images"},

            # ── Key Pairs ──
            {"command": "show keypairs", "skip": 2, "method": "show_key_pairs",
             "args": ["key_name"], "desc": "Show EC2 key pairs"},
            {"command": "create keypair", "skip": 2, "method": "create_key_pair",
             "args": ["key_name"], "desc": "Create a new key pair"},

            # ── Security Groups ──
            {"command": "show security groups", "skip": 3, "method": "show_security_groups",
             "args": ["group_name"], "desc": "Show security groups"},
            {"command": "create security group", "skip": 3, "method": "create_security_group",
             "args": ["group_name", "description"], "desc": "Create a security group"},
            {"command": "authorize security group", "skip": 3, "method": "authorize_all_traffic",
             "args": ["group_id"], "desc": "Authorize all traffic for a security group"},

            # ── VPC & Networking ──
            {"command": "show vpcs", "skip": 2, "method": "show_vpcs",
             "args": [], "desc": "Show all VPCs"},
            {"command": "show subnets", "skip": 2, "method": "show_subnets",
             "args": ["vpc_id"], "desc": "Show subnets (optionally by VPC)"},

            # ── S3 ──
            {"command": "show buckets", "skip": 2, "method": "show_buckets",
             "args": [], "desc": "Show S3 buckets"},
            {"command": "show objects", "skip": 2, "method": "show_objects",
             "args": ["bucket"], "desc": "Show objects in a bucket"},

            # ── Service Quotas ──
            {"command": "show service quotas", "skip": 3, "method": "show_service_quotas",
             "args": ["service_code"], "desc": "Show service quotas"},

            # ── Export ──
            {"command": "export instances", "skip": 2, "method": "export_instances",
             "args": ["filename"], "desc": "Export instances to JSON"},
            {"command": "export images", "skip": 2, "method": "export_images",
             "args": ["filename"], "desc": "Export images to JSON"},
        ]

    def _extract_args(self, command: str, skip: int) -> List[str]:
        """Extract arguments from raw command string."""
        parts = command.split()
        return parts[skip:] if len(parts) > skip else []

    def _show_help(self):
        """Display styled help with columns."""
        self.__console.print(Panel(
            Text.from_markup(":information_source: [bold cyan]Available Commands[/bold cyan]"),
            border_style="blue"
        ))

        commands = self._get_commands()
        items = []
        for cmd in sorted(commands, key=lambda x: x['command']):
            args = ' '.join([f"[dim]<{a}>[/dim]" for a in cmd['args']])
            items.append(
                f"[bold yellow]{cmd['command']}[/bold yellow] {args}\n"
                f"[dim]{cmd['desc']}[/dim]"
            )

        self.__console.print(Columns(items, equal=True, expand=True))
        self.__console.print()
        self.__console.print(
            Panel(
                "[bold green]help[/bold green] — show this message | "
                "[bold green]clear[/bold green] — clear screen | "
                "[bold green]exit[/bold green] — quit",
                border_style="dim"
            )
        )

    def _find_command(self, input_cmd: str) -> Dict[str, Any]:
        """Find matching command from registry."""
        commands = self._get_commands()
        # Exact match first
        for cmd in commands:
            if input_cmd == cmd['command']:
                return cmd
        # Prefix match
        for cmd in commands:
            if input_cmd.startswith(cmd['command']):
                return cmd
        return {}

    def _suggest_commands(self, input_cmd: str):
        """Suggest similar commands on not found."""
        commands = self._get_commands()
        words = input_cmd.split()
        suggestions = []
        for cmd in commands:
            if any(word in cmd['command'] for word in words if len(word) > 2):
                suggestions.append(cmd['command'])
        if suggestions:
            self.__console.print(
                f"[dim]Did you mean:[/dim] [bold green]{', '.join(suggestions[:5])}[/bold green]?"
            )

    def execute_command(self, input_cmd: str, cmd_def: Dict[str, Any]) -> None:
        """Execute a matched command."""
        args = self._extract_args(input_cmd, cmd_def['skip'])
        method = getattr(self.__client, cmd_def['method'])
        method(*args)

    def start(self):
        """Main command loop."""
        while self.__running:
            try:
                input_cmd = self.__prompt.ask(
                    ':keyboard: [bold cyan]aws[/bold cyan]',
                )
                input_cmd = input_cmd.strip()

                if not input_cmd:
                    continue
                if input_cmd == 'exit':
                    self.__console.print(':wave: [bold cyan]Goodbye![/bold cyan] :wave:')
                    break
                if input_cmd == 'help':
                    self._show_help()
                    continue
                if input_cmd == 'clear':
                    os.system('clear' if os.name != 'nt' else 'cls')
                    continue

                cmd_def = self._find_command(input_cmd)
                if cmd_def:
                    # Require config except for configure itself
                    if not self.__client.is_configured and cmd_def['method'] != 'configure':
                        self.__console.print(
                            Panel(
                                ":exclamation: [bold red]Please configure AWS credentials first[/bold red] :exclamation:\n"
                                "Run: [bold green]configure[/bold green]",
                                border_style="red"
                            )
                        )
                        continue
                    self.execute_command(input_cmd, cmd_def)
                else:
                    self.__console.print(
                        Panel(
                            ":exclamation: [bold red]Command not found[/bold red] :exclamation:",
                            border_style="red"
                        )
                    )
                    self._suggest_commands(input_cmd)

            except KeyboardInterrupt:
                self.__console.print()
                if self.__prompt.ask('[bold red]Exit?[/bold red]', choices=['y', 'n'], default='n') == 'y':
                    self.__console.print(':wave: [bold cyan]Goodbye![/bold cyan] :wave:')
                    break
            except EOFError:
                self.__console.print('\n:wave: [bold cyan]Goodbye![/bold cyan] :wave:')
                break
