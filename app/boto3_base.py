"""Base client with unified error handling for boto3 services."""

from typing import Any, Callable, Dict, Optional

from botocore.exceptions import ClientError

__all__ = ["BaseClient"]

_AUTH_ERROR_CODES = (
    "InvalidClientTokenId",
    "AuthFailure",
    "ExpiredToken",
    "InvalidAccessKeyId",
    "UnrecognizedClient",
)


class BaseClient:
    """Base AWS client wrapper with automatic error handling."""

    def __init__(self) -> None:
        self.__client: Optional[Any] = None

    @property
    def client(self) -> Optional[Any]:
        """Get the underlying boto3 client."""
        return self.__client

    @client.setter
    def client(self, value: Any) -> None:
        """Set the underlying boto3 client."""
        self.__client = value

    def call(self, method: Callable, *args, **kwargs) -> Dict[str, Any]:
        """Execute a boto3 method with unified error handling.

        Args:
            method: The boto3 client method to call.
            *args: Positional arguments for the method.
            **kwargs: Keyword arguments for the method.

        Returns:
            Dictionary with 'status' (bool), 'response' (result or error message),
            and optionally 'auth_error' (True when credentials are invalid).
        """
        try:
            response = method(*args, **kwargs)
            return {"status": True, "response": response}
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "Unknown")
            if error_code in _AUTH_ERROR_CODES:
                self.__client = None
                return {
                    "status": False,
                    "response": "Invalid credentials. Please configure again.",
                    "auth_error": True,
                }
            return {
                "status": False,
                "response": e.response.get("Error", {}).get("Message", str(e)),
            }
        except Exception as e:
            return {"status": False, "response": str(e)}
