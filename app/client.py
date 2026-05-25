"""Business logic layer with Rich-enhanced UI."""

import os
import time
import json
import logging
from typing import Any, Dict, List, Optional, Tuple

from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.tree import Tree
from rich.columns import Columns
from rich import box

from .session import SessionManager
from .ec2 import EC2Client
from .s3 import S3Client
from .service_quotas import ServiceQuotasClient
from .config import RegionConfig, AWSConfig
from .utils import (
    mb_to_gb, format_datetime, ensure_results_dir,
    validate_instance_id, validate_ami_id,
    save_json, print_error, print_success, print_warning, print_info,
)


class Client:
    """Client for handling commands with Rich UI."""

    def __init__(self, console: Console, prompt: Prompt) -> None:
        self.__console = console
        self.__prompt = prompt
        self.__ec2 = EC2Client()
        self.__s3 = S3Client()
        self.__quotas = ServiceQuotasClient()

        ensure_results_dir()
        logging.basicConfig(
            filename='client.log',
            level=logging.INFO,
            format='%(asctime)s | %(levelname)s | %(message)s'
        )

    # ── Helpers ──────────────────────────────────────────────────

    def _get_key_pairs(self) -> List[Dict[str, Any]]:
        """Fetch key pairs via safe call wrapper."""
        return self.__ec2.call(self.__ec2.client.describe_key_pairs).get('response', {}).get('KeyPairs', [])

    def _get_security_groups(self) -> List[Dict[str, Any]]:
        """Fetch security groups via safe call wrapper."""
        return self.__ec2.call(self.__ec2.client.describe_security_groups).get('response', {}).get('SecurityGroups', [])

    def _call_ec2(self, method_name: str, *args, **kwargs):
        """Call EC2 method with error handling."""
        method = getattr(self.__ec2, method_name)
        return self.__ec2.call(method, *args, **kwargs)

    def _call_s3(self, method_name: str, *args, **kwargs):
        """Call S3 method with error handling."""
        method = getattr(self.__s3, method_name)
        return self.__s3.call(method, *args, **kwargs)

    def _call_quotas(self, method_name: str, *args, **kwargs):
        """Call Service Quotas method with error handling."""
        method = getattr(self.__quotas, method_name)
        return self.__quotas.call(method, *args, **kwargs)

    # ── Configuration ────────────────────────────────────────────

    @property
    def is_configured(self) -> bool:
        return SessionManager.is_configured()

    def validate_configure(self, *args) -> Tuple[str, str, str]:
        if len(args) >= 3:
            return args[0], args[1], args[2]
        if len(args) == 2:
            return args[0], args[1], 'us-east-1'
        aws_access_key_id = self.__prompt.ask(':key: [bold cyan]AWS Access Key ID[/bold cyan]')
        aws_secret_access_key = self.__prompt.ask(':lock: [bold cyan]AWS Secret Access Key[/bold cyan]')
        region_name = self.__prompt.ask(':globe_with_meridians: [bold cyan]Region Name[/bold cyan]', default='us-east-1')
        return aws_access_key_id, aws_secret_access_key, region_name

    def configure(self, *args):
        aws_access_key_id, aws_secret_access_key, region_name = self.validate_configure(*args)

        if not RegionConfig.validate(region_name):
            print_error(self.__console, f"Region {region_name} is not supported.")
            return

        try:
            SessionManager.configure(aws_access_key_id, aws_secret_access_key, region_name)
            self.__ec2.client = SessionManager.get_client('ec2', region_name)
            self.__s3.client = SessionManager.get_client('s3', region_name)
            self.__quotas.client = SessionManager.get_client('service-quotas', region_name)
            print_success(self.__console, f"Configured successfully for region [bold]{region_name}[/bold]")
            logging.info('AWS configured successfully.')
        except Exception as e:
            print_error(self.__console, f"Configuration failed: {e}")
            logging.error(f'Configuration failed: {e}')

    def change_region(self, *args) -> None:
        region_name = args[0] if args else self.__prompt.ask(
            ':globe_with_meridians: [bold cyan]Region Name[/bold cyan]',
            default='us-east-1'
        )
        if not RegionConfig.validate(region_name):
            print_error(self.__console, f"Region {region_name} is not supported.")
            return
        self.__ec2.client = SessionManager.get_client('ec2', region_name)
        self.__s3.client = SessionManager.get_client('s3', region_name)
        self.__quotas.client = SessionManager.get_client('service-quotas', region_name)
        print_success(self.__console, f"Region changed to {region_name}")
        logging.info(f'Region changed to {region_name}')

    def show_regions(self) -> None:
        table = Table(
            title=':globe_with_meridians: Supported Regions',
            box=box.ROUNDED,
            show_header=True,
            header_style="bold magenta"
        )
        table.add_column('Region Name', style='cyan')
        table.add_column('Description', style='green')
        for region in RegionConfig.REGIONS:
            table.add_row(region['name'], region['description'])
        self.__console.print(table)

    # ── Instance Types ───────────────────────────────────────────

    def show_instance_types(self, *args) -> None:
        instance_type = args[0] if args else ''
        with self.__console.status("[bold green]Fetching instance types..."):
            result = self._call_ec2('describe_instance_types', instance_type)

        if not result['status']:
            print_error(self.__console, result['response'])
            return

        response = result['response']
        table = Table(title=':package: EC2 Instance Types', box=box.ROUNDED)
        table.add_column('Instance Type', style='cyan', no_wrap=True)
        table.add_column('VCPU', style='magenta', justify='right')
        table.add_column('Memory', style='green', justify='right')
        table.add_column('Architecture', style='yellow')
        table.add_column('Storage', style='blue')
        table.add_column('Network', style='purple')

        for it in response:
            storage = 'EBS-Only'
            if it.get('InstanceStorageSupported'):
                total = it.get('InstanceStorageInfo', {}).get('TotalSizeInGB', 0)
                storage = f"{total} GB"
            table.add_row(
                it['InstanceType'],
                str(it['VCpuInfo']['DefaultVCpus']),
                f"{mb_to_gb(it['MemoryInfo']['SizeInMiB'])} GB",
                ', '.join(it['ProcessorInfo'].get('SupportedArchitectures', [])),
                storage,
                it['NetworkInfo'].get('NetworkPerformance', 'N/A')
            )
        self.__console.print(table)

    # ── Instances ────────────────────────────────────────────────

    def show_instances(self, *args) -> None:
        instance_id = args[0] if args else ''
        if instance_id and not validate_instance_id(instance_id):
            print_warning(self.__console, "Instance ID format looks invalid. Showing results anyway.")

        with self.__console.status("[bold green]Fetching instances..."):
            result = self._call_ec2('describe_instances', instance_id)

        if not result['status']:
            print_error(self.__console, result['response'])
            return

        response = result['response']
        table = Table(title=':computer: EC2 Instances', box=box.ROUNDED)
        table.add_column('Instance ID', style='cyan', no_wrap=True)
        table.add_column('Type', style='magenta')
        table.add_column('State', style='green')
        table.add_column('Public IP', style='blue')
        table.add_column('Key Name', style='purple')
        table.add_column('Launch Time', style='yellow')

        for reservation in response:
            for inst in reservation.get('Instances', []):
                table.add_row(
                    inst['InstanceId'],
                    inst['InstanceType'],
                    inst['State']['Name'],
                    inst.get('PublicIpAddress', 'N/A'),
                    inst.get('KeyName', 'N/A'),
                    format_datetime(inst.get('LaunchTime'))
                )
        self.__console.print(table)

    def create_instance(self) -> None:
        instance_type = self.__prompt.ask(':package: [bold cyan]Instance Type[/bold cyan] [dim](e.g. t2.micro)[/dim]')
        image_id = self.__prompt.ask(':frame_with_picture: [bold cyan]Image ID[/bold cyan]')

        if not validate_ami_id(image_id):
            if not Confirm.ask("AMI ID format looks invalid. Continue anyway?"):
                return

        # Key pairs
        kp_result = self._call_ec2('describe_key_pairs')
        if not kp_result['status']:
            print_error(self.__console, kp_result['response'])
            return

        key_pairs = kp_result['response']
        if not key_pairs:
            print_warning(self.__console, "No key pairs found. Creating one now...")
            self.create_key_pair()
            kp_result = self._call_ec2('describe_key_pairs')
            key_pairs = kp_result['response']

        self.__console.print(
            f":key: [bold cyan]Available Key Pairs:[/bold cyan] [green]"
            f"{', '.join([kp['KeyName'] for kp in key_pairs])}"
            f"[/green]"
        )
        key_name = self.__prompt.ask(':key: [bold cyan]Key Name[/bold cyan]')
        if key_name not in [kp['KeyName'] for kp in key_pairs]:
            print_warning(self.__console, "Key pair not found. Creating a new one...")
            self.create_key_pair(key_name)

        # Security groups
        sg_result = self._call_ec2('describe_security_groups')
        security_groups = sg_result.get('response', [])
        if not security_groups:
            print_warning(self.__console, "No security groups found. Creating default...")
            self._call_ec2('create_security_group', 'default', 'Default security group')
            self._call_ec2('authorize_all_traffic', 'default')
            sg_result = self._call_ec2('describe_security_groups')
            security_groups = sg_result.get('response', [])

        self.__console.print(
            f":lock: [bold cyan]Available Security Groups:[/bold cyan] [green]"
            f"{', '.join([sg['GroupName'] for sg in security_groups])}"
            f"[/green]"
        )
        sg_name = self.__prompt.ask(':lock: [bold cyan]Security Group[/bold cyan]', default='default')
        if sg_name not in [sg['GroupName'] for sg in security_groups]:
            print_warning(self.__console, "Security group not found. Creating default...")
            self._call_ec2('create_security_group', sg_name, f'Security group {sg_name}')

        storage = self.__prompt.ask(':floppy_disk: [bold cyan]Storage Size (GB)[/bold cyan]', default='8')

        with self.__console.status("[bold green]Launching instance..."):
            result = self._call_ec2(
                'run_instance', image_id, instance_type,
                key_name, int(storage), sg_name
            )

        if not result['status']:
            print_error(self.__console, result['response'])
            return

        instance_data = result['response']['Instances'][0]
        instance_id = instance_data['InstanceId']
        print_success(self.__console, f"Instance {instance_id} created successfully!")

        # Progress bar for readiness
        with Progress(
            SpinnerColumn(),
            TextColumn('[progress.description]{task.description}'),
            transient=True,
        ) as progress:
            task = progress.add_task('[cyan]Waiting for instance to be ready...', total=60)
            for _ in range(60):
                progress.update(task, advance=1)
                time.sleep(1)

        # Fetch and display
        inst_result = self._call_ec2('describe_instances', instance_id)
        if not inst_result['status']:
            return
        inst = inst_result['response'][0]['Instances'][0]

        info_table = Table(title=f":computer: Instance {instance_id}", box=box.ROUNDED)
        info_table.add_column('Property', style='cyan')
        info_table.add_column('Value', style='green')
        info_table.add_row('Instance ID', inst['InstanceId'])
        info_table.add_row('Public IP', inst.get('PublicIpAddress', 'N/A'))
        info_table.add_row('Key Name', inst.get('KeyName', 'N/A'))
        info_table.add_row('State', inst['State']['Name'])
        self.__console.print(info_table)

        # Save to file
        with open('results/instances.txt', 'a') as f:
            f.write(f"Instance ID: {inst['InstanceId']}\n")
            f.write(f"Public IP: {inst.get('PublicIpAddress', 'N/A')}\n")
            f.write(f"Key Name: {inst.get('KeyName', 'N/A')}\n")
            f.write('-' * 50 + '\n')

    # ── Instance Control ─────────────────────────────────────────

    def start_instance(self, *args) -> None:
        instance_id = args[0] if args else self.__prompt.ask(':play_button: [bold cyan]Instance ID[/bold cyan]')
        if not instance_id:
            print_error(self.__console, "Instance ID is required")
            return
        with self.__console.status(f"[bold green]Starting {instance_id}..."):
            result = self._call_ec2('start_instances', [instance_id])
        if result['status']:
            print_success(self.__console, f"Instance {instance_id} started")
        else:
            print_error(self.__console, result['response'])

    def stop_instance(self, *args) -> None:
        instance_id = args[0] if args else self.__prompt.ask(':stop_button: [bold cyan]Instance ID[/bold cyan]')
        if not instance_id:
            print_error(self.__console, "Instance ID is required")
            return
        with self.__console.status(f"[bold yellow]Stopping {instance_id}..."):
            result = self._call_ec2('stop_instances', [instance_id])
        if result['status']:
            print_success(self.__console, f"Instance {instance_id} stopped")
        else:
            print_error(self.__console, result['response'])

    def reboot_instance(self, *args) -> None:
        instance_id = args[0] if args else self.__prompt.ask(':arrows_counterclockwise: [bold cyan]Instance ID[/bold cyan]')
        if not instance_id:
            print_error(self.__console, "Instance ID is required")
            return
        with self.__console.status(f"[bold blue]Rebooting {instance_id}..."):
            result = self._call_ec2('reboot_instances', [instance_id])
        if result['status']:
            print_success(self.__console, f"Instance {instance_id} rebooted")
        else:
            print_error(self.__console, result['response'])

    def terminate_instance(self, *args) -> None:
        instance_id = args[0] if args else self.__prompt.ask(':warning: [bold cyan]Instance ID[/bold cyan]')
        if not instance_id:
            print_error(self.__console, "Instance ID is required")
            return
        if not Confirm.ask(f"[bold red]Are you sure you want to terminate {instance_id}?[/bold red]"):
            return
        with self.__console.status(f"[bold red]Terminating {instance_id}..."):
            result = self._call_ec2('terminate_instance', instance_id)
        if result['status']:
            print_success(self.__console, f"Instance {instance_id} terminated")
        else:
            print_error(self.__console, result['response'])

    # ── Images ───────────────────────────────────────────────────

    def show_images(self, *args) -> None:
        image_name = ' '.join(args) if args else ''
        with self.__console.status("[bold green]Fetching images..."):
            result = self._call_ec2('describe_images', image_name)

        if not result['status']:
            print_error(self.__console, result['response'])
            return

        response = result['response']
        table = Table(title=':frame_with_picture: Amazon Machine Images', box=box.ROUNDED)
        table.add_column('Image ID', style='cyan', no_wrap=True)
        table.add_column('Name', style='magenta')
        table.add_column('Arch', style='yellow')
        table.add_column('State', style='green')
        table.add_column('Created', style='blue')

        for image in response[:50]:  # Limit to 50 for performance
            table.add_row(
                image['ImageId'],
                image.get('Name', 'N/A')[:40],
                image.get('Architecture', 'N/A'),
                image.get('State', 'N/A'),
                image.get('CreationDate', 'N/A')[:10]
            )
        self.__console.print(table)
        if len(response) > 50:
            print_info(self.__console, "Note", f"Showing 50 of {len(response)} results. Filter with: show images <name>")

    # ── Key Pairs ────────────────────────────────────────────────

    def show_key_pairs(self, *args) -> None:
        key_name = args[0] if args else ''
        with self.__console.status("[bold green]Fetching key pairs..."):
            result = self._call_ec2('describe_key_pairs', key_name)

        if not result['status']:
            print_error(self.__console, result['response'])
            return

        response = result['response']
        table = Table(title=':key: EC2 Key Pairs', box=box.ROUNDED)
        table.add_column('Key Name', style='cyan')
        table.add_column('Key ID', style='green')
        table.add_column('Created', style='magenta')

        for kp in response:
            table.add_row(
                kp['KeyName'],
                kp.get('KeyPairId', 'N/A'),
                format_datetime(kp.get('CreateTime'))
            )
        self.__console.print(table)

    def create_key_pair(self, *args) -> Optional[Tuple[str, str]]:
        key_name = args[0] if args else self.__prompt.ask(':key: [bold cyan]Key Name[/bold cyan]')
        if not key_name:
            print_error(self.__console, "Key name is required")
            return None

        with self.__console.status(f"[bold green]Creating key pair {key_name}..."):
            result = self._call_ec2('create_key_pair', key_name)

        if not result['status']:
            print_error(self.__console, result['response'])
            return None

        resp = result['response']
        outfile = f"results/keypairs/{resp['KeyName']}-{resp['KeyPairId']}.pem"
        with os.fdopen(os.open(outfile, os.O_WRONLY | os.O_CREAT, 0o600), 'w') as f:
            f.write(resp['KeyMaterial'])

        print_success(self.__console, f"Key pair saved to [bold]{outfile}[/bold]")
        return key_name, resp['KeyPairId']

    # ── Security Groups ──────────────────────────────────────────

    def show_security_groups(self, *args) -> None:
        group_name = args[0] if args else ''
        with self.__console.status("[bold green]Fetching security groups..."):
            result = self._call_ec2('describe_security_groups', group_name)

        if not result['status']:
            print_error(self.__console, result['response'])
            return

        response = result['response']
        table = Table(title=':lock: Security Groups', box=box.ROUNDED)
        table.add_column('Group Name', style='cyan')
        table.add_column('Description', style='magenta')
        table.add_column('Group ID', style='green', no_wrap=True)
        table.add_column('VPC ID', style='blue')

        for sg in response:
            table.add_row(
                sg['GroupName'],
                sg.get('Description', '')[:30],
                sg['GroupId'],
                sg.get('VpcId', 'N/A')
            )
        self.__console.print(table)

    def create_security_group(self, *args) -> None:
        if len(args) >= 2:
            group_name, description = args[0], ' '.join(args[1:])
        else:
            group_name = self.__prompt.ask(':lock: [bold cyan]Security Group Name[/bold cyan]')
            description = self.__prompt.ask(':lock: [bold cyan]Description[/bold cyan]')

        with self.__console.status("[bold green]Creating security group..."):
            result = self._call_ec2('create_security_group', group_name, description)

        if not result['status']:
            print_error(self.__console, result['response'])
            return

        resp = result['response']
        print_success(self.__console, f"Security group '{group_name}' created")
        print_info(self.__console, "Group ID", resp['GroupId'])

    def authorize_all_traffic(self, *args) -> None:
        group_id = args[0] if args else self.__prompt.ask(':lock: [bold cyan]Security Group ID[/bold cyan]')
        if not group_id:
            print_error(self.__console, "Group ID is required")
            return

        with self.__console.status(f"[bold yellow]Authorizing all traffic for {group_id}..."):
            self.__ec2.authorize_all_traffic(group_id)

        print_success(self.__console, f"All traffic authorized for {group_id}")
        print_warning(self.__console, "This opens ALL ports to 0.0.0.0/0 — use with caution!")

    # ── VPCs & Subnets ───────────────────────────────────────────

    def show_vpcs(self) -> None:
        with self.__console.status("[bold green]Fetching VPCs..."):
            result = self._call_ec2('describe_vpcs')

        if not result['status']:
            print_error(self.__console, result['response'])
            return

        response = result['response']
        tree = Tree(":globe_with_meridians: [bold cyan]VPCs[/bold cyan]")
        for vpc in response:
            name = next((t['Value'] for t in vpc.get('Tags', []) if t['Key'] == 'Name'), 'Unnamed')
            node = tree.add(f"[bold]{vpc['VpcId']}[/bold] [dim]({name})[/dim]")
            node.add(f"CIDR: [green]{vpc['CidrBlock']}[/green]")
            node.add(f"Default: {'Yes' if vpc['IsDefault'] else 'No'}")
        self.__console.print(tree)

    def show_subnets(self, *args) -> None:
        vpc_id = args[0] if args else self.__prompt.ask(':globe_with_meridians: [bold cyan]VPC ID (optional)[/bold cyan]')
        with self.__console.status("[bold green]Fetching subnets..."):
            result = self._call_ec2('describe_subnets', vpc_id)

        if not result['status']:
            print_error(self.__console, result['response'])
            return

        response = result['response']
        table = Table(title=':map: Subnets', box=box.ROUNDED)
        table.add_column('Subnet ID', style='cyan', no_wrap=True)
        table.add_column('VPC ID', style='blue')
        table.add_column('CIDR', style='green')
        table.add_column('AZ', style='magenta')
        table.add_column('Available IPs', style='yellow', justify='right')
        table.add_column('Default', style='white')

        for sn in response:
            table.add_row(
                sn['SubnetId'],
                sn['VpcId'],
                sn['CidrBlock'],
                sn['AvailabilityZone'],
                str(sn.get('AvailableIpAddressCount', 0)),
                'Yes' if sn.get('DefaultForAz') else 'No'
            )
        self.__console.print(table)

    # ── S3 ───────────────────────────────────────────────────────

    def show_buckets(self) -> None:
        with self.__console.status("[bold green]Fetching S3 buckets..."):
            result = self._call_s3('list_buckets')

        if not result['status']:
            print_error(self.__console, result['response'])
            return

        response = result['response']
        table = Table(title=':bucket: S3 Buckets', box=box.ROUNDED)
        table.add_column('Bucket Name', style='cyan')
        table.add_column('Created', style='green')

        for bucket in response:
            table.add_row(
                bucket['Name'],
                format_datetime(bucket.get('CreationDate'))
            )
        self.__console.print(table)

    def show_objects(self, *args) -> None:
        bucket = args[0] if args else self.__prompt.ask(':bucket: [bold cyan]Bucket Name[/bold cyan]')
        if not bucket:
            print_error(self.__console, "Bucket name is required")
            return

        with self.__console.status(f"[bold green]Fetching objects from {bucket}..."):
            result = self._call_s3('list_objects', bucket)

        if not result['status']:
            print_error(self.__console, result['response'])
            return

        response = result['response']
        table = Table(title=f':file_folder: Objects in {bucket}', box=box.ROUNDED)
        table.add_column('Key', style='cyan')
        table.add_column('Size', style='green', justify='right')
        table.add_column('Last Modified', style='magenta')
        table.add_column('Storage Class', style='yellow')

        for obj in response[:100]:
            size = obj.get('Size', 0)
            size_str = f"{size / (1024*1024):.2f} MB" if size > 1024*1024 else f"{size / 1024:.2f} KB" if size > 1024 else f"{size} B"
            table.add_row(
                obj.get('Key', '')[:50],
                size_str,
                format_datetime(obj.get('LastModified'))[:19],
                obj.get('StorageClass', 'STANDARD')
            )
        self.__console.print(table)
        if len(response) > 100:
            print_info(self.__console, "Note", f"Showing 100 of {len(response)} objects")

    # ── Service Quotas ───────────────────────────────────────────

    def show_service_quotas(self, *args) -> None:
        service_code = ' '.join(args) if args else self.__prompt.ask(
            ':chart_with_upwards_trend: [bold cyan]Service Code[/bold cyan] [dim](e.g. ec2)[/dim]'
        )
        if not service_code:
            print_error(self.__console, "Service code is required")
            return

        with self.__console.status(f"[bold green]Fetching quotas for {service_code}..."):
            result = self._call_quotas('list_service_quotas', service_code)

        if not result['status']:
            print_error(self.__console, result['response'])
            return

        response = result['response']
        table = Table(title=f':chart_with_upwards_trend: Service Quotas — {service_code}', box=box.ROUNDED)
        table.add_column('Service', style='cyan')
        table.add_column('Quota Name', style='magenta')
        table.add_column('Value', style='green', justify='right')
        table.add_column('Unit', style='blue')
        table.add_column('Adjustable', style='yellow')

        for quota in response:
            table.add_row(
                quota.get('ServiceName', 'N/A'),
                quota['QuotaName'][:40],
                str(quota.get('Value', 'N/A')),
                quota.get('Unit', 'N/A'),
                'Yes' if quota.get('Adjustable') else 'No'
            )
        self.__console.print(table)

    # ── Exports ──────────────────────────────────────────────────

    def export_instances(self, *args) -> None:
        filename = args[0] if args else self.__prompt.ask(':floppy_disk: [bold cyan]Filename[/bold cyan]')
        if not filename:
            filename = 'instances_export'

        with self.__console.status("[bold green]Fetching instances..."):
            result = self._call_ec2('describe_instances')

        if not result['status']:
            print_error(self.__console, result['response'])
            return

        data = result['response']
        filepath = save_json(data, filename)
        print_success(self.__console, f"Exported to [bold]{filepath}[/bold]")

    def export_images(self, *args) -> None:
        filename = args[0] if args else self.__prompt.ask(':floppy_disk: [bold cyan]Filename[/bold cyan]')
        if not filename:
            filename = 'images_export'

        with self.__console.status("[bold green]Fetching images..."):
            result = self._call_ec2('describe_images')

        if not result['status']:
            print_error(self.__console, result['response'])
            return

        data = result['response']
        filepath = save_json(data, filename)
        print_success(self.__console, f"Exported to [bold]{filepath}[/bold]")
