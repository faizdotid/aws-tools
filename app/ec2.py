"""EC2 service client with AWS API wrappers."""

import datetime
from typing import Any, Dict, List, Optional

from .boto3_base import BaseClient


class EC2Client(BaseClient):
    """Client for AWS EC2 operations."""

    def __init__(self) -> None:
        super().__init__()

    # ── Instance Types ───────────────────────────────────────────

    def describe_instance_types(self, instance_type: str = '') -> List[Dict[str, Any]]:
        """Describe EC2 instance types."""
        filters = [{'Name': 'instance-type', 'Values': [instance_type]}] if instance_type else []
        response = self.client.describe_instance_types(Filters=filters)
        return sorted(response['InstanceTypes'], key=lambda item: item['VCpuInfo']['DefaultVCpus'])

    # ── Instances ────────────────────────────────────────────────

    def describe_instances(self, instance_id: str = '') -> List[Dict[str, Any]]:
        """Describe EC2 instances."""
        filters = [{'Name': 'instance-id', 'Values': [instance_id]}] if instance_id else []
        response = self.client.describe_instances(Filters=filters)
        return sorted(response['Reservations'], key=lambda item: item['Instances'][0]['LaunchTime'])

    def run_instance(
        self,
        image_id: str,
        instance_type: str,
        key_name: str,
        volume_size: int,
        security_group: str
    ) -> Dict[str, Any]:
        """Launch a new EC2 instance."""
        return self.client.run_instances(
            BlockDeviceMappings=[
                {
                    'DeviceName': '/dev/sda1',
                    'Ebs': {'VolumeSize': volume_size}
                }
            ],
            ImageId=image_id,
            InstanceType=instance_type,
            KeyName=key_name,
            MinCount=1,
            MaxCount=1,
            DisableApiTermination=True,
            SecurityGroups=[security_group]
        )

    def start_instances(self, instance_ids: List[str]) -> Dict[str, Any]:
        """Start stopped instances."""
        return self.client.start_instances(InstanceIds=instance_ids)

    def stop_instances(self, instance_ids: List[str]) -> Dict[str, Any]:
        """Stop running instances."""
        return self.client.stop_instances(InstanceIds=instance_ids)

    def reboot_instances(self, instance_ids: List[str]) -> Dict[str, Any]:
        """Reboot instances."""
        return self.client.reboot_instances(InstanceIds=instance_ids)

    def terminate_instance(self, instance_id: str) -> Dict[str, Any]:
        """Terminate an instance (disables API termination protection first)."""
        try:
            self.client.modify_instance_attribute(
                InstanceId=instance_id,
                DisableApiTermination={'Value': False}
            )
        except Exception:
            pass
        return self.client.terminate_instances(InstanceIds=[instance_id])

    def get_password_data(self, instance_id: str) -> Dict[str, Any]:
        """Get Windows instance password data."""
        return self.client.get_password_data(InstanceId=instance_id)

    # ── Images (AMIs) ────────────────────────────────────────────

    def describe_images(self, image_name: str = '') -> List[Dict[str, Any]]:
        """Describe available Amazon machine images."""
        filters = []
        if image_name:
            filters.append({'Name': 'name', 'Values': [image_name]})
        filters.extend([
            {'Name': 'state', 'Values': ['available']},
            {'Name': 'image-type', 'Values': ['machine']},
            {'Name': 'creation-date', 'Values': [f'{datetime.datetime.now().year}*']},
        ])
        response = self.client.describe_images(Filters=filters, Owners=['amazon'])
        return sorted(response['Images'], key=lambda item: item['CreationDate'])

    # ── Key Pairs ────────────────────────────────────────────────

    def describe_key_pairs(self, key_name: str = '') -> List[Dict[str, Any]]:
        """Describe EC2 key pairs."""
        filters = [{'Name': 'key-name', 'Values': [key_name]}] if key_name else []
        response = self.client.describe_key_pairs(Filters=filters)
        return sorted(response['KeyPairs'], key=lambda item: item['KeyName'])

    def create_key_pair(self, key_name: str) -> Dict[str, Any]:
        """Create a new key pair."""
        return self.client.create_key_pair(KeyName=key_name)

    # ── Security Groups ──────────────────────────────────────────

    def describe_security_groups(self, group_name: str = '') -> List[Dict[str, Any]]:
        """Describe security groups."""
        filters = [{'Name': 'group-name', 'Values': [group_name]}] if group_name else []
        response = self.client.describe_security_groups(Filters=filters)
        return sorted(response['SecurityGroups'], key=lambda item: item['GroupName'])

    def create_security_group(self, group_name: str, description: str) -> Dict[str, Any]:
        """Create a security group."""
        return self.client.create_security_group(
            Description=description,
            GroupName=group_name
        )

    def authorize_all_traffic(self, group_id: str) -> None:
        """Authorize all inbound/outbound traffic (0.0.0.0/0)."""
        ip_permissions = [
            {
                'IpProtocol': '-1',
                'IpRanges': [{'CidrIp': '0.0.0.0/0'}]
            }
        ]
        for action in [
            self.client.authorize_security_group_ingress,
            self.client.authorize_security_group_egress,
            self.client.update_security_group_rule_descriptions_ingress,
            self.client.update_security_group_rule_descriptions_egress,
        ]:
            try:
                action(GroupId=group_id, IpPermissions=ip_permissions)
            except Exception:
                pass

    # ── VPC & Networking ─────────────────────────────────────────

    def describe_vpcs(self) -> List[Dict[str, Any]]:
        """Describe all VPCs."""
        response = self.client.describe_vpcs()
        return sorted(response['Vpcs'], key=lambda item: item['VpcId'])

    def describe_subnets(self, vpc_id: str = '') -> List[Dict[str, Any]]:
        """Describe subnets, optionally filtered by VPC."""
        kwargs = {'Filters': [{'Name': 'vpc-id', 'Values': [vpc_id]}]} if vpc_id else {}
        response = self.client.describe_subnets(**kwargs)
        return sorted(response['Subnets'], key=lambda item: item['SubnetId'])
