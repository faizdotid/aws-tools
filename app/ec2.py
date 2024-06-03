from .boto3_base import BaseClient
import datetime
from typing import List, Dict, Any

class EC2Client(BaseClient):

    def __init__(self) -> None:
        super().__init__()

    def _show_instance_types(self, instance_type: str = '') -> List[Dict[str, Any]]:
        if bool(instance_type):
            filters = [
                {
                    'Name': 'instance-type',
                    'Values': [instance_type]
                }
            ]
        else:
            filters = []
        response = self._client.describe_instance_types(
            Filters=filters
        )['InstanceTypes']
        return sorted(
            response,
            key=lambda item: item['VCpuInfo']['DefaultVCpus']
        )

    def _show_instances(self, instance_id: str = '') -> List[Dict[str, Any]]:
        if bool(instance_id):
            filters = [
                {
                    'Name': 'instance-id',
                    'Values': [instance_id]
                }
            ]
        else:
            filters = []
        response = self._client.describe_instances(
            Filters=filters
        )['Reservations']
        return sorted(
            response,
            key=lambda item: item['Instances'][0]['LaunchTime']
        )

    def _show_images(self, image_name: str = '') -> List[Dict[str, Any]]:
        if bool(image_name):
            filters = [
                {
                    'Name': 'name',
                    'Values': [image_name]
                }
            ]
        else:
            filters = []
        filters.extend([
            {
                'Name': 'state',
                'Values': ['available']
            },
            {
                'Name': 'image-type',
                'Values': ['machine']
            },
            {
                'Name': 'creation-date',
                'Values': [f'{datetime.datetime.now().year}*']
            }
        ])
        response = self._client.describe_images(
            Filters=filters,
            Owners=['amazon']
        )['Images']
        return sorted(
            response,
            key=lambda item: item['CreationDate']
        )

    def _show_key_pairs(self, key_name: str = '') -> List[Dict[str, Any]]:
        if bool(key_name):
            filters = [
                {
                    'Name': 'key-name',
                    'Values': [key_name]
                }
            ]
        else:
            filters = []
        response = self._client.describe_key_pairs(
            Filters=filters
        )['KeyPairs']
        return sorted(
            response,
            key=lambda item: item['KeyName']
        )

    def _create_key_pair(self, key_name: str) -> Dict[str, Any]:
        response = self._client.create_key_pair(
            KeyName=key_name
        )
        return response
    
    def _create_instance(self, image_id: str, instance_type: str, key_name: str, volume_size: int, security_group: str) -> Dict[str, Any]:

        response = self._client.run_instances(
            BlockDeviceMappings=[

                {
                    'DeviceName': '/dev/sda1',
                    'Ebs': {
                        'VolumeSize': volume_size
                    }
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
        return response

    def _show_security_groups(self, group_name: str = '') -> List[Dict[str, Any]]:
        if bool(group_name):
            filters = [
                {
                    'Name': 'group-name',
                    'Values': [group_name]
                }
            ]
        else:
            filters = []
        response = self._client.describe_security_groups(
            Filters=filters
        )['SecurityGroups']
        return sorted(
            response,
            key=lambda item: item['GroupName']
        )
    
    def _create_security_group(self, group_name: str, description: str) -> Dict[str, Any]:
        response = self._client.create_security_group(
            Description=description,
            GroupName=group_name
        )
        return response

    def _authorize_all_traffic(self, group_id: str) -> Dict[str, Any]:
        try:
            self._client.authorize_security_group_ingress(
                GroupId=group_id,
                IpPermissions=[
                    {
                        'IpProtocol': '-1',
                        'IpRanges': [{'CidrIp': '0.0.0.0/0'}]
                    }
                ]
            )
        except Exception:
            pass
        try:
            self._client.authorize_security_group_egress(
                GroupId=group_id,
                IpPermissions=[
                    {
                        'IpProtocol': '-1',
                        'IpRanges': [{'CidrIp': '0.0.0.0/0'}]
                    }
                ]
            )
        except Exception:
            pass
        try:
            self._client.update_security_group_rule_descriptions_ingress(
                GroupId=group_id,
                IpPermissions=[
                    {
                        'IpProtocol': '-1',
                        'IpRanges': [{'CidrIp': '0.0.0.0/0'}]
                    }
                ]
            )
        except Exception:
            pass
        try:
            self._client.update_security_group_rule_descriptions_egress(
                GroupId=group_id,
                IpPermissions=[
                    {
                        'IpProtocol': '-1',
                        'IpRanges': [{'CidrIp': '0.0.0.0/0'}]
                    }
                ]
            )
        except Exception:
            pass
        finally:
            return {
                "status": True,
                "response": "All traffic authorized"
            }
    
    def _terminate_instance(self, instance_id: str) -> Dict[str, Any]:
        try:
            self._client.modify_instance_attribute(
                InstanceId=instance_id,
                DisableApiTermination={
                    'Value': False
                }
            )
        except Exception:
            pass
        response = self._client.terminate_instances(
            InstanceIds=[instance_id]
        )
        return response
    
    def _show_password_data(self, instance_id: str) -> Dict[str, Any]:
        response = self._client.get_password_data(
            InstanceId=instance_id
        )
        return response