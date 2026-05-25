"""AWS Session management."""

from typing import List, Dict, Optional

from boto3 import Session
from boto3.session import Session as BotoSession

from .config import RegionConfig

__all__ = ["SessionManager"]


class SessionManager:
    """Manages AWS boto3 session lifecycle."""

    __session: Optional[BotoSession] = None

    @classmethod
    def configure(
        cls,
        aws_access_key_id: str,
        aws_secret_access_key: str,
        region_name: str,
    ) -> None:
        """Configure AWS session with credentials.

        Args:
            aws_access_key_id: AWS access key ID.
            aws_secret_access_key: AWS secret access key.
            region_name: AWS region name.
        """
        cls.__session = Session(
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            region_name=region_name,
        )

    @classmethod
    def get_client(cls, service_name: str, region_name: str):
        """Get a boto3 client for the specified service and region.

        Args:
            service_name: AWS service name (e.g., 'ec2', 's3').
            region_name: AWS region name.

        Returns:
            Boto3 service client.

        Raises:
            RuntimeError: If session has not been configured.
        """
        if cls.__session is None:
            raise RuntimeError("Session not configured. Call configure() first.")
        return cls.__session.client(service_name, region_name=region_name)

    @classmethod
    def is_configured(cls) -> bool:
        """Check if session has been configured."""
        return cls.__session is not None

    @classmethod
    def get_session(cls) -> Optional[BotoSession]:
        """Get the current boto3 session."""
        return cls.__session

    @classmethod
    def regions(cls) -> List[Dict[str, str]]:
        """Get list of supported regions."""
        return RegionConfig.REGIONS
