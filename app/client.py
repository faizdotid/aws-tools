from .base import BaseSession
from .ec2 import EC2Client
from .service_quotas import ServiceQuotasClient

from rich.table import Table
from rich.console import Console
from rich.prompt import Prompt
from rich.progress import Progress, \
    SpinnerColumn, BarColumn, \
    TextColumn
from boto3.session import Session

import os
import datetime
import logging
import time
from typing import Tuple, Union


class Client:
    '''
    Client for handling command
    '''

    def __init__(
            self, console: Console,
            prompt: Prompt
        ) -> None:
        self.__base_session = BaseSession()
        self.__ec2_client = EC2Client()
        self.__service_quotas_client = ServiceQuotasClient()
        self.__console = console
        self.__prompt = prompt
        logging.basicConfig(filename='client.log', level=logging.INFO,
                            format='%(asctime)s:%(levelname)s:%(message)s')

    @property
    def _base_session_session(self) -> Union[Session, None]:
        return self.__base_session.session
    
    @staticmethod
    def mb_to_gb(mb: int) -> int:
        return mb // 1024
    
    def __print_error(self, message: str) -> None:
        self.__console.print(f':x: [bold red]{message}[/bold red]')
        logging.error(message)

    def validate_configure(self, *args) -> Tuple[str, str, str]:
        if len(args) < 2:
            aws_access_key_id = self.__prompt.ask(':key: [bold cyan]AWS Access Key ID ? [/bold cyan]')
            aws_secret_access_key = self.__prompt.ask(':lock: [bold cyan]AWS Secret Access Key ? [/bold cyan]')
            region_name = self.__prompt.ask(':globe_with_meridians: [bold cyan]Region Name ?[/bold cyan]', default='us-east-1')
            self.__console.print(f':warning: [bold yellow]Region Name not provided. Defaulting to {region_name}[/bold yellow]')
        else:
            aws_access_key_id = args[0]
            aws_secret_access_key = args[1]
            region_name = args[2] if len(args) > 2 else 'us-east-1'
        return aws_access_key_id, aws_secret_access_key, region_name

    def configure(self, *args):
        aws_access_key_id, aws_secret_access_key, region_name = self.validate_configure(*args)
        try:
            self.__base_session.configure(
                aws_access_key_id, aws_secret_access_key,
                region_name
            )
            self.__ec2_client.client = self.__base_session.get_client('ec2', region_name)
            self.__service_quotas_client.client = self.__base_session.get_client('service-quotas', region_name)
            self.__console.print(':white_check_mark: [bold green]Configured successfully[/bold green]')
            logging.info('AWS configured successfully.')
        except Exception as e:
            self.__console.print(f':x: [bold red]Configuration failed: {str(e)}[/bold red]')
            logging.error(f'Configuration failed: {str(e)}')

    # NOTE: This method is not used
    # def validate_args(
    #     self, questions: List[str],
    #     args: List[Any]) -> List[Any]:
    #     new_args = []
    #     for question, arg in zip(questions, args):
    #         if not bool(arg):
    #             new_args.append(self.__console.ask(question))
    #         else:
    #             new_args.append(arg)
    #     return new_args

    def change_region(self, *args) -> None:
        if len(args) < 1:
            region_name = self.__prompt.ask(':globe_with_meridians: [bold cyan]Region Name ? [/bold cyan]', default='us-east-1')
        else:
            region_name = args[0]
        regions = map(lambda region: region['name'], self.__base_session.regions)
        if region_name not in regions:
            self.__console.print(f':x: [bold red]Region {region_name} not supported[/bold red]')
            return
        self.__ec2_client.client = self.__base_session.get_client('ec2', region_name)
        self.__service_quotas_client.client = self.__base_session.get_client('service-quotas', region_name)
        self.__console.print(f':white_check_mark: [bold green]Region changed to {region_name} successfully[/bold green]')
        logging.info(f'Region changed to {region_name} successfully.')

    def show_regions(self) -> None:
        table = Table(title=':globe_with_meridians: Supported Regions')
        table.add_column('Region Name', style='cyan')
        table.add_column('Description', style='magenta')
        for region in self._base_client.regions:
            table.add_row(region['name'], region['description'])
        self.__console.print(table)

    def show_instance_types(self, *args) -> None:
        response = self.__ec2_client._execute('_show_instance_types', *args)
        if not response['status']:
            self.__print_error(response['response'])
            return
        response = response['response']
        table = Table(title=':package: Instance Types')
        table.add_column('Instance Type', style='cyan')
        table.add_column('VCPU', style='magenta')
        table.add_column('Memory', style='green')
        table.add_column('Architecture', style='yellow')
        table.add_column('Storage', style='blue')
        table.add_column('Network Performance', style='purple')
        for instance_type in response:
            table.add_row(
                instance_type['InstanceType'],
                str(instance_type['VCpuInfo']['DefaultVCpus']),
                str(self.mb_to_gb(instance_type['MemoryInfo']['SizeInMiB'])) + ' GB',
                ', '.join(instance_type['ProcessorInfo']['SupportedArchitectures']),
                'EBS-Only' if not instance_type['InstanceStorageSupported'] else str(instance_type['InstanceStorageInfo']['TotalSizeInGB']) + ' GB',
                str(instance_type['NetworkInfo']['NetworkPerformance'])
            )
        self.__console.print(table)

    def show_instances(self, *args) -> None:
        response = self.__ec2_client._execute('_show_instances', *args)
        if not response['status']:
            self.__print_error(response['response'])
            return
        response = response['response']
        table = Table(title=':computer: Instances')
        table.add_column('Instance ID', style='cyan')
        table.add_column('Instance Type', style='magenta')
        table.add_column('State', style='green')
        table.add_column('Public IP', style='blue')
        table.add_column('Public Key', style='purple')
        table.add_column('Launch Time', style='yellow')
        for reservation in response:
            for instance in reservation['Instances']:
                table.add_row(
                    instance['InstanceId'],
                    instance['InstanceType'],
                    instance['State']['Name'],
                    instance.get('PublicIpAddress', 'N/A'),
                    instance['KeyName'] if 'KeyName' in instance.keys() else 'N/A',
                    datetime.datetime.strftime(instance['LaunchTime'], '%Y-%m-%d %H:%M:%S')
                )
        self.__console.print(table)

    def show_images(self, *args) -> None:
        image_name = ' '.join(args) if args else ''
        response = self.__ec2_client._execute('_show_images', image_name)
        if not response['status']:
            self.__print_error(response['response'])
            return
        response = response['response']
        table = Table(title=':frame_with_picture: Images')
        table.add_column('Image ID', style='cyan')
        table.add_column('Name', style='magenta')
        table.add_column('Architecture', style='yellow')
        table.add_column('State', style='green')
        table.add_column('Creation Date', style='blue')
        for image in response:
            table.add_row(
                image['ImageId'],
                image['Name'],
                image['Architecture'],
                image['State'],
                image['CreationDate']
            )
        self.__console.print(table)

    def show_key_pairs(self, *args) -> None:
        response = self.__ec2_client._execute('_show_key_pairs', *args)
        if not response['status']:
            self.__print_error(response['response'])
            return
        response = response['response']
        table = Table(title=':key: Key Pairs')
        table.add_column('Key Name', style='cyan')
        table.add_column('Key ID', style='green')
        table.add_column('Creation Date', style='magenta')
        for key_pair in response:
            table.add_row(
                key_pair['KeyName'],
                key_pair['KeyPairId'],
                datetime.datetime.strftime(key_pair['CreateTime'], '%Y-%m-%d %H:%M:%S')
            )
        self.__console.print(table)

    def show_security_groups(self, *args) -> None:
        response = self.__ec2_client._execute('_show_security_groups', *args)
        if not response['status']:
            self.__print_error(response['response'])
            return
        response = response['response']
        table = Table(title=':lock: Security Groups')
        table.add_column('Group Name', style='cyan')
        table.add_column('Description', style='magenta')
        table.add_column('Group ID', style='green')
        for security_group in response:
            table.add_row(
                security_group['GroupName'],
                security_group['Description'],
                security_group['GroupId']
            )
        self.__console.print(table)

    def create_instance(self):
        instance_type = self.__prompt.ask(':package: [bold cyan]Instance Type [/bold cyan][bold yellow](e.g. t2.micro)[/bold yellow]')
        image_id = self.__prompt.ask(':frame_with_picture: [bold cyan]Image ID[/bold cyan]')
        key_pairs = self.__ec2_client._execute('_show_key_pairs')
        if not key_pairs['status']:
            self.__print_error(key_pairs['response'])
            return
        if len(key_pairs['response']) == 0:
            self.__console.print(':warning: [bold yellow]No key pairs found. Create a key pair first[/bold yellow]')
            self.create_key_pair()
            key_pairs = self.__ec2_client._execute('_show_key_pairs')
        self.__console.print(
            ':key: [bold cyan]Available Key Pairs: [green]'
            + ', '.join([f'{key_pair['KeyName']}:{key_pair['KeyPairId']}' for key_pair in key_pairs['response']])
            + '[/green][/bold cyan]'
        )
        key_name = self.__prompt.ask(':key: [bold cyan]Key Name[/bold cyan]',)
        if key_name not in [key_pair['KeyName'] for key_pair in key_pairs['response']]:
            self.__console.print(':x: [bold red]Key pair not found. Please create a key pair first.[/bold red]')
            key_name, key_pair_id = self.create_key_pair()
        else:
            key_pair_id = list(
                filter(
                    lambda key_pair: key_pair['KeyName'] == key_name, key_pairs['response']
                )
            )[0]['KeyPairId']
        security_groups = self.__ec2_client._execute('_show_security_groups')
        if len(security_groups['response']) == 0:
            self.__console.print(':warning: [bold yellow]No security groups found. Creating a default security group.[/bold yellow]')
            security_group = self.__ec2_client._execute(
                '_create_security_group', 'default',
                'Default security group'
            )
            self.__ec2_client._execute('_authorize_all_traffic', 'default')
        else:
            self.__console.print(
                ':lock: [bold cyan]Available Security Groups: [green]'
                + ', '.join([security_group['GroupName'] for security_group in security_groups['response']])
                + '[/green][/bold cyan]'
            )
            security_group = self.__prompt.ask(':lock: [bold cyan]Security Group[/bold cyan]', default='default')
            if security_group not in [security_group['GroupName'] for security_group in security_groups['response']]:
                self.__console.print(':x: [bold red]Security group not found. Creating a default security group.[/bold red]')
                security_group = self.__ec2_client._execute(
                    '_create_security_group', 'default',
                    'Default security group'
                )
        storage_size = self.__prompt.ask(':floppy_disk: [bold cyan]Storage Size (GB)[/bold cyan]', default='8')
        response = self.__ec2_client._execute(
            '_create_instance', image_id,
            instance_type, key_name,
            int(storage_size), security_group
        )
        if not response['status']:
            self.__print_error(response['response'])
            return
        self.__console.print(':white_check_mark: [bold green]Instance created successfully[/bold green]')
        with Progress(
            SpinnerColumn(),
            BarColumn(),
            TextColumn('[progress.percentage]{task.percentage:>3.0f}%'),
            TextColumn('{task.description}'),
            transient=True,
        ) as progress:
            task = progress.add_task('[cyan]Waiting for instance to be ready...', total=60)
            for _ in range(60):
                progress.update(task, advance=1)
                time.sleep(1)

        instance = self.__ec2_client._execute('_show_instances', response['response']['Instances'][0]['InstanceId'])
        if not instance['status']:
            self.__console.print(instance['response'])
            return
        instance = instance['response'][0]['Instances'][0]
        self.__console.print(f':information_source: [bold cyan]Instance ID[/bold cyan]: {instance['InstanceId']}')
        self.__console.print(f':information_source: [bold cyan]Public IP[/bold cyan]: {instance.get('PublicIpAddress', 'N/A')}')
        self.__console.print(f':information_source: [bold cyan]Public Key[/bold cyan]: {instance['KeyName']}')
        self.__console.print(f':information_source: [bold cyan]Public Key File[/bold cyan]: results/keypairs/{key_name}-{key_pair_id}.pem')
        with open(f'results/instances.txt', 'a') as instance_file:
            instance_file.write(f'Instance ID: {instance['InstanceId']}\n')
            instance_file.write(f'Public IP: {instance.get('PublicIpAddress', 'N/A')}\n')
            instance_file.write(f'Public Key: {instance['KeyName']}\n')
            instance_file.write(f'Public Key File: results/keypairs/{key_name}-{key_pair_id}.pem\n')
            instance_file.write('-' * 50 + '\n')

    def create_key_pair(self, *args) -> Tuple[str, str]:
        if len(args) < 1:
            key_name = self.__prompt.ask(':key: [bold cyan]Key Name[/bold cyan]')
        else:
            key_name = args[0]
        response = self.__ec2_client._execute('_create_key_pair', key_name)
        if not response['status']:
            self.__print_error(response['response'])
            return
        outfile = f'results/keypairs/{response['response']['KeyName']}-{response['response']['KeyPairId']}.pem'
        with os.fdopen(
            os.open(outfile, os.O_WRONLY | os.O_CREAT, 0o600), 'w'
        ) as key_file:
            key_file.write(response['response']['KeyMaterial'])
        self.__console.print(
            f':white_check_mark: [bold green]Key pair saved into {outfile}[/bold green]'
        )
        return key_name, response['response']['KeyPairId']

    def create_security_group(self, *args) -> None:
        if len(args) < 2:
            security_group = self.__prompt.ask(':lock: [bold cyan]Security Group Name[/bold cyan]')
            description = self.__prompt.ask(':lock: [bold cyan]Description[/bold cyan]')
        else:
            security_group = args[0]
            description = ' '.join(args[1:])
        response = self.__ec2_client._execute(
            '_create_security_group', security_group,
            description
        )
        if not response['status']:
            self.__print_error(response['response'])
            return
        self.__console.print(
            ':white_check_mark: [bold green]Successfully created security group '
            + security_group
            + '[/bold green]'
        )
        self.__console.print(
            ':information_source: [bold cyan]Security Group ID[/bold cyan]: '
            + response['response']['GroupId']
        )

    def authorize_all_traffic(self, *args) -> None:
        security_group_id = args[0] if len(args) > 0 else self.__prompt.ask(':lock: [bold cyan]Security Group ID[/bold cyan]')
        response = self.__ec2_client._execute(
            '_authorize_all_traffic', security_group_id
        )
        if not response['status']:
            self.__print_error(response['response'])
            return
        self.__console.print(
            ':white_check_mark: [bold green]Successfully authorized all traffic for '
            + security_group_id
            + '[/bold green]'
        )

    def show_service_quotas(self, *args) -> None:
        service_code = ' '.join(args) if args else self.__prompt.ask(':chart_with_upwards_trend: [bold cyan]Service Code[/bold cyan]')
        response = self.__service_quotas_client._execute(
            '_show_service_quotas', service_code,
            []
        )
        if not response['status']:
            self.__print_error(response['response'])
            return
        response = response['response']
        table = Table(title=':chart_with_upwards_trend: Service Quotas')
        table.add_column('Service Name', style='cyan')
        table.add_column('Quota Name', style='magenta')
        table.add_column('Value', style='green')
        table.add_column('Unit', style='blue')
        for quota in response:
            table.add_row(
                quota['ServiceName'],
                quota['QuotaName'],
                str(quota['Value']),
                quota['Unit']
            )
        self.__console.print(table)

    def terminate_instance(self, *args) -> None:
        instance_id = args[0] if len(args) > 0 else self.__prompt.ask(':warning: [bold cyan]Instance ID[/bold cyan]')
        second_ask = self.__prompt.ask(':warning: [bold yellow]Are you sure you want to terminate this instance? (yes/no)[/bold yellow]')
        if not second_ask.lower().startswith('y'):
            return
        response = self.__ec2_client._execute(
            '_terminate_instance', instance_id
        )
        if not response['status']:
            self.__print_error(response['response'])
            return
        self.__console.print(':white_check_mark: [bold green]Instance terminated successfully[/bold green]')

    # NOTE: Still development
    # def show_password(self, *args) -> None:
    #     instance_id = args[0] if len(args) > 0 else self.__prompt.ask(':warning: [bold cyan]Instance ID[/bold cyan]')
    #     response = self.__ec2_client._execute(
    #         '_show_password_data', instance_id
    #     )
    #     print(response)
    #     if not response['status']:
    #         self.__print_error(response['response'])
    #         return
    #     if response['response']['PasswordData'] is '':
    #         self.__console.print(':warning: [bold yellow]Password not available for this instance[/bold yellow]')
    #         return
