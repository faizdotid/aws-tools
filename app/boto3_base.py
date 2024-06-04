from boto3 import client
from botocore.exceptions import ClientError

from typing import List, \
    Dict, Any


class BaseClient:

    __client: client = None

    def __init__(self) -> None:
        pass

    @property
    def client(self) -> client:
        return self.__client

    @client.setter
    def client(self, value: client) -> None:
        self._client = value

    def _execute(
        self, function_name: str,
        *args
    ) -> Dict[str, Any]:
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
