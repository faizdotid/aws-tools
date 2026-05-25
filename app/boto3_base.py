"""Base client with unified error handling for boto3 services."""

from typing import Any, Callable, Dict
from functools import wraps

from boto3 import client as boto3_client
from botocore.exceptions import ClientError


class BaseClient:
    """Base AWS client wrapper with automatic error handling."""

    def __init__(self) -> None:
        self.__client: boto3_client = None  # type: ignore

    @property
    def client(self) -> boto3_client:
        """Get the underlying boto3 client."""
        return self.__client

    @client.setter
    def client(self, value: boto3_client) -> None:
        """Set the underlying boto3 client."""
        self.__client = value

    def call(self, method: Callable, *args, **kwargs) -> Dict[str, Any]:
        """Execute a boto3 method with unified error handling.
        
        Args:
            method: The boto3 client method to call
            *args, **kwargs: Arguments to pass to the method
            
        Returns:
            Dict with 'status' (bool) and 'response' (Any or error message)
        """
        try:
            response = method(*args, **kwargs)
            return {"status": True, "response": response}
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "Unknown")
            if error_code in ("InvalidClientTokenId", "AuthFailure"):
                self.__client = None
                return {
                    "status": False,
                    "response": "Invalid credentials. Please configure again."
                }
            return {
                "status": False,
                "response": e.response.get("Error", {}).get("Message", str(e))
            }
        except Exception as e:
            return {"status": False, "response": str(e)}
