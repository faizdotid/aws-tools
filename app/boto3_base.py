from boto3 import client
from botocore.exceptions import ClientError

from typing import List, Dict, Any

class BaseClient:

    _client: client = None

    _regions: List[str] = [
        "us-east-1", "us-east-2", "us-west-1",
        "us-west-2", "ap-south-1", "ap-southeast-1",
        "ap-southeast-2", "ap-northeast-1", "ap-northeast-2",
        "ap-northeast-3", "ca-central-1", "eu-south-1",
        "eu-central-1", "eu-north-1", "eu-west-1",
        "eu-west-2", "eu-west-3", "sa-east-1",
        "me-south-1",
    ]

    def __init__(self) -> None:
        pass

    @property
    def client(self) -> client:
        return self._client
    
    @property
    def regions(self) -> List[str]:
        return self._regions
    
    @client.setter
    def client(self, value: client) -> None:
        self._client = value
    
    def _execute(self, function_name: str, *args) -> Dict[str, Any]:
        try:
            response = getattr(self, function_name)(*args)
            return {
                "status": True,
                "response": response
            }
        except ClientError as e:
            if e.response["Error"]["Code"] == "InvalidClientTokenId":
                self._client = None
                return {
                    "status": False,
                    "response": "Invalid credentials. Please configure again."
                }
            if e.response["Error"]["Code"] == "AuthFailure":
                self._client = None
                return {
                    "status": False,
                    "response": "Invalid credentials. Please configure again."
                }
            return {
                "status": False,
                "response": e.response["Error"]["Message"]
            }
        except Exception as e:
            return {
                "status": False,
                "response": str(e)
            }