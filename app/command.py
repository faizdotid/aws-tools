from .client import Client
from rich.console import Console
from rich.prompt import Prompt
from rich.progress import Progress

import os
from typing import List

class Command:

    def __init__(self):
        self._console = Console()
        self._prompt = Prompt()
        self._progress = Progress()
        self._client = Client(
            console=self._console,
            prompt=self._prompt,
            progress=self._progress
        )
        self._client._console.print(
                ':sparkles: [bold cyan]Welcome to the AWS CLI[/bold cyan] :sparkles:\n'
                '[bold cyan]Type \'help\' to see available commands[/bold cyan]'
            )
        self.init_folder()

    def init_folder(self):
        if not os.path.exists('results'):
            os.makedirs('results')
        if not os.path.exists('results/keypairs'):
            os.makedirs('results/keypairs')

    def extract_command(self, command: str, skip: int) -> List[str]:
        return command.split()[skip:]

    def execute_command(self, command: str, method_name: str, skip: int) -> None:
        args = self.extract_command(command, skip)
        if self._client._ec2_client.client is None:
            if method_name.startswith('configure'):
                self._client.configure(*args)
                return
            self._client._console.print(
                ':exclamation: [bold red]Please configure first[/bold red] :exclamation:')
            self._client.configure()
        else:
            getattr(self._client, method_name)(*args)

    def start(self):
        try:
            '''Main CLI loop'''
            command_list = [
                {
                    "command": "configure",
                    "description": "Configure AWS credentials",
                    "skip": 1,
                    "method_name": "configure",
                    "args": [
                        "aws_access_key_id",
                        "aws_secret_access_key",
                        "region_name"
                    ]
                },
                {
                    "command": "show instance types",
                    "description": "Show instance types",
                    "skip": 3,
                    "method_name": "show_instance_types",
                    "args": [
                        "instance_type"
                    ]
                },
                {
                    "command": "show instances",
                    "description": "Show instances",
                    "skip": 2,
                    "method_name": "show_instances",
                    "args": [
                        "instance_id"
                    ]
                },
                {
                    "command": "create instance",
                    "description": "Create instance",
                    "skip": 2,
                    "method_name": "create_instance",
                    "args": []
                },
                {
                    "command": "show images",
                    "description": "Show images",
                    "skip": 2,
                    "method_name": "show_images",
                    "args": [
                        "image_description"
                    ]
                },
                {
                    "command": "show keypairs",
                    "description": "Show key pairs",
                    "skip": 2,
                    "method_name": "show_key_pairs",
                    "args": [
                        "key_name"
                    ]
                },
                {
                    "command": "create keypair",
                    "description": "Create key pair",
                    "skip": 2,
                    "method_name": "create_key_pair",
                    "args": [
                        "key_name"
                    ]
                },
                {
                    "command": "change region",
                    "description": "Change region",
                    "skip": 2,
                    "method_name": "change_region",
                    "args": [
                        "region_name"
                    ]
                },
                {
                    "command": "show security groups",
                    "description": "Show security groups",
                    "skip": 3,
                    "method_name": "show_security_groups",
                    "args": [
                        "group_name"
                    ]
                },
                {
                    "command": "authorize security group",
                    "description": "Authorize security group",
                    "skip": 3,
                    "method_name": "authorize_all_traffic",
                    "args": [
                        "group_id"
                    ]
                },
                {
                    "command": "create security group",
                    "description": "Create security group",
                    "skip": 3,
                    "method_name": "create_security_group",
                    "args": [
                        "group_name",
                        "description"
                    ]
                },
                {
                    "command": "show service quotas",
                    "description": "Show service quotas",
                    "skip": 3,
                    "method_name": "show_service_quotas",
                    "args": [
                        "service_code"
                    ]
                },
                {
                    "command": "terminate instance",
                    "description": "Terminate instance",
                    "skip": 2,
                    "method_name": "terminate_instance",
                    "args": [
                        "instance_id"
                    ]
                },
                {
                    "command": "show regions",
                    "description": "Show regions",
                    "skip": 2,
                    "method_name": "show_regions",
                    "args": []
                }
            ]

            while True:
                input_command = self._client._prompt.ask(
                    ':keyboard: [bold cyan]Enter command[/bold cyan] :keyboard:'
                )
                if input_command == 'exit':
                    self._client._console.print(
                        ':wave: [bold cyan]Goodbye![/bold cyan] :wave:')
                    break
                elif input_command == 'help':
                    self._client._console.print(':information_source: [bold cyan]Available Commands:[/bold cyan] :information_source:')
                    for command in sorted(command_list, key=lambda x: x['command']):
                        args = ' '.join([f'[bold green]<{arg}>[/bold green]' for arg in command.get("args", [])])
                        self._client._console.print(
                            f':gear: [bold yellow]{command["command"]}[/bold yellow]: {command["description"]} {args}'
                        )
                elif input_command == 'clear':
                    os.system('clear')
                else:
                    for command in command_list:
                        if input_command.startswith(command['command']):
                            self.execute_command(
                                command=input_command,
                                method_name=command['method_name'],
                                skip=command['skip']
                            )
                            break
                    else:
                        self._client._console.print(
                            ':exclamation: [bold red]Command not found. Type \'help\' to see available commands[/bold red] :exclamation:')
        except KeyboardInterrupt:
            if self._prompt.ask('\n[bold red]Are you sure you want to exit?[/bold red] (y/n)') == 'y':
                self._console.print(
                    ':wave: [bold cyan]Goodbye![/bold cyan] :wave:')
                exit(0)
            self.start()