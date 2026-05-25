"""AWS Session management."""

from boto3 import Session
from boto3.session import Session as BotoSession

from .config import RegionConfig


class SessionManager:
    """Manages AWS boto3 session lifecycle."""

    __session: BotoSession = None  # type: ignore

    @classmethod
    def configure(
        cls,
        aws_access_key_id: str,
        aws_secret_access_key: str,
        region_name: str,
    ) -> None:
        """Configure AWS session with credentials."""
        cls.__session = Session(
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            region_name=region_name
        )

    @classmethod
    def get_client(cls, service_name: str, region_name: str):
        """Get a boto3 client for the specified service and region."""
        if cls.__session is None:
            raise RuntimeError("Session not configured. Call configure() first.")
        return cls.__session.client(service_name, region_name=region_name)

    @classmethod
    def is_configured(cls) -> bool:
        """Check if session has been configured."""
        return cls.__session is not None

    @classmethod
    def get_session(cls) -> BotoSession:
        """Get the current boto3 session."""
        return cls.__session

    @classmethod
    def regions(cls):
        """Get list of supported regions."""
        return RegionConfig.REGIONS
