"""EC2 service client with AWS API wrappers."""

import logging
from typing import Any, Dict, List

from botocore.exceptions import ClientError

from .boto3_base import BaseClient

__all__ = ["EC2Client"]

logger = logging.getLogger(__name__)


class EC2Client(BaseClient):
    """Client for AWS EC2 operations."""

    def __init__(self) -> None:
        super().__init__()

    # ── Instance Types ───────────────────────────────────────────

    def describe_instance_types(self, instance_type: str = "") -> List[Dict[str, Any]]:
        """Describe EC2 instance types.

        Args:
            instance_type: Filter by specific instance type (optional).

        Returns:
            List of instance type dictionaries sorted by vCPU count.
        """
        kwargs: Dict[str, Any] = {}
        if instance_type:
            kwargs["Filters"] = [{"Name": "instance-type", "Values": [instance_type]}]
        results: List[Dict[str, Any]] = []
        while True:
            response = self.client.describe_instance_types(**kwargs)
            results.extend(response.get("InstanceTypes", []))
            next_token = response.get("NextToken")
            if not next_token:
                break
            kwargs["NextToken"] = next_token
        return sorted(results, key=lambda item: item["VCpuInfo"]["DefaultVCpus"])

    # ── Instances ────────────────────────────────────────────────

    def describe_instances(self, instance_id: str = "") -> List[Dict[str, Any]]:
        """Describe EC2 instances.

        Args:
            instance_id: Filter by specific instance ID (optional).

        Returns:
            List of reservation dictionaries sorted by launch time.
        """
        kwargs: Dict[str, Any] = {}
        if instance_id:
            kwargs["Filters"] = [{"Name": "instance-id", "Values": [instance_id]}]
        results: List[Dict[str, Any]] = []
        while True:
            response = self.client.describe_instances(**kwargs)
            results.extend(response.get("Reservations", []))
            next_token = response.get("NextToken")
            if not next_token:
                break
            kwargs["NextToken"] = next_token
        results = [r for r in results if r.get("Instances")]
        return sorted(results, key=lambda item: item["Instances"][0]["LaunchTime"])

    def run_instance(
        self,
        image_id: str,
        instance_type: str,
        key_name: str,
        volume_size: int,
        security_group: str,
        root_device: str = "/dev/sda1",
        disable_api_termination: bool = False,
    ) -> Dict[str, Any]:
        """Launch a new EC2 instance.

        Args:
            image_id: AMI ID.
            instance_type: Instance type (e.g., 't2.micro').
            key_name: Key pair name.
            volume_size: Root volume size in GB.
            security_group: Security group name.
            root_device: Root device name (e.g., '/dev/sda1').
            disable_api_termination: Enable API termination protection.

        Returns:
            Run instances response dictionary.
        """
        return self.client.run_instances(
            BlockDeviceMappings=[
                {"DeviceName": root_device, "Ebs": {"VolumeSize": volume_size}}
            ],
            ImageId=image_id,
            InstanceType=instance_type,
            KeyName=key_name,
            MinCount=1,
            MaxCount=1,
            DisableApiTermination=disable_api_termination,
            SecurityGroups=[security_group],
        )

    def start_instances(self, instance_ids: List[str]) -> Dict[str, Any]:
        """Start stopped instances.

        Args:
            instance_ids: List of instance IDs.

        Returns:
            Start instances response dictionary.
        """
        return self.client.start_instances(InstanceIds=instance_ids)

    def stop_instances(self, instance_ids: List[str]) -> Dict[str, Any]:
        """Stop running instances.

        Args:
            instance_ids: List of instance IDs.

        Returns:
            Stop instances response dictionary.
        """
        return self.client.stop_instances(InstanceIds=instance_ids)

    def reboot_instances(self, instance_ids: List[str]) -> Dict[str, Any]:
        """Reboot instances.

        Args:
            instance_ids: List of instance IDs.

        Returns:
            Reboot instances response dictionary.
        """
        return self.client.reboot_instances(InstanceIds=instance_ids)

    def terminate_instance(self, instance_id: str) -> Dict[str, Any]:
        """Terminate an instance.

        Disables API termination protection before terminating.

        Args:
            instance_id: Instance ID to terminate.

        Returns:
            Terminate instances response dictionary.
        """
        try:
            self.client.modify_instance_attribute(
                InstanceId=instance_id, DisableApiTermination={"Value": False}
            )
        except ClientError as exc:
            logger.warning(
                "Failed to disable termination protection for %s: %s",
                instance_id,
                exc,
            )
        return self.client.terminate_instances(InstanceIds=[instance_id])

    # ── Images (AMIs) ────────────────────────────────────────────

    def describe_images(self, image_name: str = "") -> List[Dict[str, Any]]:
        """Describe publicly available machine images.

        Args:
            image_name: Filter by image name (e.g., 'ubuntu/images/hvm-ssd/*').

        Returns:
            List of image dictionaries sorted by creation date.
        """
        filters = [
            {"Name": "state", "Values": ["available"]},
            {"Name": "image-type", "Values": ["machine"]},
        ]
        if image_name:
            filters.append({"Name": "name", "Values": [image_name]})
        kwargs: Dict[str, Any] = {"Filters": filters}
        results: List[Dict[str, Any]] = []
        while True:
            response = self.client.describe_images(**kwargs)
            results.extend(response.get("Images", []))
            next_token = response.get("NextToken")
            if not next_token:
                break
            kwargs["NextToken"] = next_token
        return sorted(results, key=lambda item: item["CreationDate"])

    # ── Key Pairs ────────────────────────────────────────────────

    def describe_key_pairs(self, key_name: str = "") -> List[Dict[str, Any]]:
        """Describe EC2 key pairs.

        Args:
            key_name: Filter by key name (optional).

        Returns:
            List of key pair dictionaries sorted by name.
        """
        kwargs: Dict[str, Any] = {}
        if key_name:
            kwargs["Filters"] = [{"Name": "key-name", "Values": [key_name]}]
        results: List[Dict[str, Any]] = []
        while True:
            response = self.client.describe_key_pairs(**kwargs)
            results.extend(response.get("KeyPairs", []))
            next_token = response.get("NextToken")
            if not next_token:
                break
            kwargs["NextToken"] = next_token
        return sorted(results, key=lambda item: item["KeyName"])

    def create_key_pair(self, key_name: str) -> Dict[str, Any]:
        """Create a new key pair.

        Args:
            key_name: Name for the new key pair.

        Returns:
            Create key pair response dictionary.
        """
        return self.client.create_key_pair(KeyName=key_name)

    # ── Security Groups ──────────────────────────────────────────

    def describe_security_groups(self, group_name: str = "") -> List[Dict[str, Any]]:
        """Describe security groups.

        Args:
            group_name: Filter by group name (optional).

        Returns:
            List of security group dictionaries sorted by name.
        """
        kwargs: Dict[str, Any] = {}
        if group_name:
            kwargs["Filters"] = [{"Name": "group-name", "Values": [group_name]}]
        results: List[Dict[str, Any]] = []
        while True:
            response = self.client.describe_security_groups(**kwargs)
            results.extend(response.get("SecurityGroups", []))
            next_token = response.get("NextToken")
            if not next_token:
                break
            kwargs["NextToken"] = next_token
        return sorted(results, key=lambda item: item["GroupName"])

    def create_security_group(
        self, group_name: str, description: str
    ) -> Dict[str, Any]:
        """Create a security group.

        Args:
            group_name: Security group name.
            description: Security group description.

        Returns:
            Create security group response dictionary.
        """
        return self.client.create_security_group(
            Description=description, GroupName=group_name
        )

    def authorize_all_traffic(self, group_id: str) -> None:
        """Authorize all inbound traffic (0.0.0.0/0, all protocols).

        Raises:
            ClientError: If authorization fails.
        """
        ip_permissions = [{"IpProtocol": "-1", "IpRanges": [{"CidrIp": "0.0.0.0/0"}]}]
        self.client.authorize_security_group_ingress(
            GroupId=group_id, IpPermissions=ip_permissions
        )

    # ── VPC & Networking ─────────────────────────────────────────

    def describe_vpcs(self) -> List[Dict[str, Any]]:
        """Describe all VPCs.

        Returns:
            List of VPC dictionaries sorted by ID.
        """
        kwargs: Dict[str, Any] = {}
        results: List[Dict[str, Any]] = []
        while True:
            response = self.client.describe_vpcs(**kwargs)
            results.extend(response.get("Vpcs", []))
            next_token = response.get("NextToken")
            if not next_token:
                break
            kwargs["NextToken"] = next_token
        return sorted(results, key=lambda item: item["VpcId"])

    def describe_subnets(self, vpc_id: str = "") -> List[Dict[str, Any]]:
        """Describe subnets.

        Args:
            vpc_id: Filter by VPC ID (optional).

        Returns:
            List of subnet dictionaries sorted by ID.
        """
        kwargs: Dict[str, Any] = {}
        if vpc_id:
            kwargs["Filters"] = [{"Name": "vpc-id", "Values": [vpc_id]}]
        results: List[Dict[str, Any]] = []
        while True:
            response = self.client.describe_subnets(**kwargs)
            results.extend(response.get("Subnets", []))
            next_token = response.get("NextToken")
            if not next_token:
                break
            kwargs["NextToken"] = next_token
        return sorted(results, key=lambda item: item["SubnetId"])
