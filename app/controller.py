"""AWS Controller facade with caching and unified data access."""

import logging
import time
from typing import Any, Dict, List, Optional

from .config import RegionConfig
from .ec2 import EC2Client
from .s3 import S3Client
from .service_quotas import ServiceQuotasClient
from .session import SessionManager
from .utils import ensure_results_dir, save_json

__all__ = ["AWSController"]

_logging_configured = False


def _setup_logging() -> None:
    """Configure file logging exactly once."""
    global _logging_configured
    if _logging_configured:
        return
    logging.basicConfig(
        filename="client.log",
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
    )
    _logging_configured = True


class _Cache:
    """Simple TTL cache for AWS API responses."""

    def __init__(self, ttl: int = 30) -> None:
        self._ttl = ttl
        self._store: Dict[str, tuple] = {}

    def get(self, key: str) -> Any:
        """Get cached value if not expired."""
        if key not in self._store:
            return None
        value, timestamp = self._store[key]
        if time.time() - timestamp > self._ttl:
            del self._store[key]
            return None
        return value

    def set(self, key: str, value: Any) -> None:
        """Store value with current timestamp."""
        self._store[key] = (value, time.time())

    def invalidate(self, key: Optional[str] = None) -> None:
        """Invalidate cache entry or all entries."""
        if key is None:
            self._store.clear()
        elif key in self._store:
            del self._store[key]


class AWSController:
    """Facade for all AWS service clients with caching."""

    def __init__(self) -> None:
        _setup_logging()
        self._ec2 = EC2Client()
        self._s3 = S3Client()
        self._quotas = ServiceQuotasClient()
        self._cache = _Cache(ttl=30)
        self._last_error: Optional[str] = None
        ensure_results_dir()

    # ── Properties ───────────────────────────────────────────────

    @property
    def is_configured(self) -> bool:
        """Check if AWS session is configured."""
        return SessionManager.is_configured()

    @property
    def last_error(self) -> Optional[str]:
        """Get last error message."""
        return self._last_error

    # ── Logging ──────────────────────────────────────────────────

    def log(self, message: str) -> None:
        """Write an entry to the activity log."""
        logging.info(message)

    # ── Internal helpers ─────────────────────────────────────────

    def _call(self, client: Any, method, *args) -> Dict[str, Any]:
        """Execute a boto3 call and centralize auth-error handling.

        Args:
            client: BaseClient wrapper instance.
            method: The wrapper method to invoke.
            *args: Positional arguments for the method.

        Returns:
            Status dictionary from BaseClient.call.
        """
        self._last_error = None
        result = client.call(method, *args)
        if result.get("auth_error"):
            self._handle_auth_error()
        if not result["status"]:
            self._last_error = result["response"]
        return result

    def _handle_auth_error(self) -> None:
        """Reset session state after an invalid-credentials error."""
        SessionManager.reset()
        self._ec2.client = None
        self._s3.client = None
        self._quotas.client = None
        self._cache.invalidate()
        self._last_error = "Invalid credentials. Please configure again."

    # ── Configuration ────────────────────────────────────────────

    def configure(
        self, access_key: str, secret_key: str, region: str
    ) -> Dict[str, Any]:
        """Configure AWS credentials and initialize clients.

        Args:
            access_key: AWS access key ID.
            secret_key: AWS secret access key.
            region: AWS region name.

        Returns:
            Status dictionary.
        """
        if not RegionConfig.validate(region):
            self._last_error = f"Region {region} is not supported."
            return {"status": False, "response": self._last_error}

        try:
            SessionManager.configure(access_key, secret_key, region)
            self._ec2.client = SessionManager.get_client("ec2", region)
            self._s3.client = SessionManager.get_client("s3", region)
            self._quotas.client = SessionManager.get_client("service-quotas", region)
            self._cache.invalidate()
            self.log(f"Configured for region {region}")
            self._last_error = None
            return {"status": True, "response": f"Configured for {region}"}
        except Exception as exc:
            self._last_error = str(exc)
            logging.error(f"Configuration failed: {exc}")
            return {"status": False, "response": str(exc)}

    def change_region(self, region: str) -> Dict[str, Any]:
        """Change AWS region without re-configuring credentials.

        Args:
            region: AWS region name.

        Returns:
            Status dictionary.
        """
        if not RegionConfig.validate(region):
            self._last_error = f"Region {region} is not supported."
            return {"status": False, "response": self._last_error}

        try:
            SessionManager.update_region(region)
            self._ec2.client = SessionManager.get_client("ec2", region)
            self._s3.client = SessionManager.get_client("s3", region)
            self._quotas.client = SessionManager.get_client("service-quotas", region)
            self._cache.invalidate()
            self.log(f"Region changed to {region}")
            self._last_error = None
            return {"status": True, "response": f"Region changed to {region}"}
        except Exception as exc:
            self._last_error = str(exc)
            logging.error(f"Region change failed: {exc}")
            return {"status": False, "response": str(exc)}

    # ── EC2: Instances ───────────────────────────────────────────

    def get_instances(self, instance_id: str = "") -> List[Dict[str, Any]]:
        """Get EC2 instances with caching."""
        cache_key = f"instances:{instance_id or 'all'}"
        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached

        result = self._call(self._ec2, self._ec2.describe_instances, instance_id)
        if not result["status"]:
            return []

        data = result["response"]
        self._cache.set(cache_key, data)
        return data

    def get_instance_types(self, instance_type: str = "") -> List[Dict[str, Any]]:
        """Get EC2 instance types with caching."""
        cache_key = f"instance_types:{instance_type or 'all'}"
        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached

        result = self._call(self._ec2, self._ec2.describe_instance_types, instance_type)
        if not result["status"]:
            return []

        data = result["response"]
        self._cache.set(cache_key, data)
        return data

    def start_instance(self, instance_id: str) -> bool:
        """Start a stopped instance."""
        result = self._call(self._ec2, self._ec2.start_instances, [instance_id])
        if result["status"]:
            self.log(f"Started instance {instance_id}")
            self._cache.invalidate("instances:all")
            return True
        return False

    def stop_instance(self, instance_id: str) -> bool:
        """Stop a running instance."""
        result = self._call(self._ec2, self._ec2.stop_instances, [instance_id])
        if result["status"]:
            self.log(f"Stopped instance {instance_id}")
            self._cache.invalidate("instances:all")
            return True
        return False

    def reboot_instance(self, instance_id: str) -> bool:
        """Reboot an instance."""
        result = self._call(self._ec2, self._ec2.reboot_instances, [instance_id])
        if result["status"]:
            self.log(f"Rebooted instance {instance_id}")
            return True
        return False

    def terminate_instance(self, instance_id: str) -> bool:
        """Terminate an instance."""
        result = self._call(self._ec2, self._ec2.terminate_instance, instance_id)
        if result["status"]:
            self.log(f"Terminated instance {instance_id}")
            self._cache.invalidate("instances:all")
            return True
        return False

    def create_instance(
        self,
        image_id: str,
        instance_type: str,
        key_name: str,
        volume_size: int,
        security_group: str,
        root_device: str = "/dev/sda1",
        disable_api_termination: bool = False,
    ) -> Optional[str]:
        """Create a new EC2 instance.

        Returns:
            Instance ID if successful, None otherwise.
        """
        result = self._call(
            self._ec2,
            self._ec2.run_instance,
            image_id,
            instance_type,
            key_name,
            volume_size,
            security_group,
            root_device,
            disable_api_termination,
        )
        if result["status"]:
            instance_id = result["response"]["Instances"][0]["InstanceId"]
            self.log(f"Created instance {instance_id}")
            self._cache.invalidate("instances:all")
            return instance_id
        return None

    # ── EC2: Images ──────────────────────────────────────────────

    def get_images(self, image_name: str = "") -> List[Dict[str, Any]]:
        """Get public AMIs with caching."""
        cache_key = f"images:{image_name or 'all'}"
        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached

        result = self._call(self._ec2, self._ec2.describe_images, image_name)
        if not result["status"]:
            return []

        data = result["response"]
        self._cache.set(cache_key, data)
        return data

    # ── EC2: Key Pairs ───────────────────────────────────────────

    def get_key_pairs(self, key_name: str = "") -> List[Dict[str, Any]]:
        """Get EC2 key pairs with caching."""
        cache_key = f"keypairs:{key_name or 'all'}"
        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached

        result = self._call(self._ec2, self._ec2.describe_key_pairs, key_name)
        if not result["status"]:
            return []

        data = result["response"]
        self._cache.set(cache_key, data)
        return data

    def create_key_pair(self, key_name: str) -> Optional[Dict[str, Any]]:
        """Create a new key pair.

        Returns:
            Response dict if successful, None otherwise.
        """
        result = self._call(self._ec2, self._ec2.create_key_pair, key_name)
        if result["status"]:
            self.log(f"Created key pair {key_name}")
            self._cache.invalidate("keypairs:all")
            return result["response"]
        return None

    # ── EC2: Security Groups ─────────────────────────────────────

    def get_security_groups(self, group_name: str = "") -> List[Dict[str, Any]]:
        """Get security groups with caching."""
        cache_key = f"security_groups:{group_name or 'all'}"
        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached

        result = self._call(self._ec2, self._ec2.describe_security_groups, group_name)
        if not result["status"]:
            return []

        data = result["response"]
        self._cache.set(cache_key, data)
        return data

    def create_security_group(self, name: str, description: str) -> Optional[str]:
        """Create a security group.

        Returns:
            Group ID if successful, None otherwise.
        """
        result = self._call(
            self._ec2, self._ec2.create_security_group, name, description
        )
        if result["status"]:
            group_id = result["response"]["GroupId"]
            self.log(f"Created security group {name} ({group_id})")
            self._cache.invalidate("security_groups:all")
            return group_id
        return None

    def authorize_security_group(self, group_id: str) -> bool:
        """Authorize all inbound traffic for a security group."""
        result = self._call(self._ec2, self._ec2.authorize_all_traffic, group_id)
        if result["status"]:
            self.log(f"Authorized all traffic for {group_id}")
            return True
        return False

    # ── EC2: VPCs ────────────────────────────────────────────────

    def get_vpcs(self) -> List[Dict[str, Any]]:
        """Get VPCs with caching."""
        cache_key = "vpcs:all"
        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached

        result = self._call(self._ec2, self._ec2.describe_vpcs)
        if not result["status"]:
            return []

        data = result["response"]
        self._cache.set(cache_key, data)
        return data

    def get_subnets(self, vpc_id: str = "") -> List[Dict[str, Any]]:
        """Get subnets with caching."""
        cache_key = f"subnets:{vpc_id or 'all'}"
        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached

        result = self._call(self._ec2, self._ec2.describe_subnets, vpc_id)
        if not result["status"]:
            return []

        data = result["response"]
        self._cache.set(cache_key, data)
        return data

    # ── S3 ───────────────────────────────────────────────────────

    def get_buckets(self) -> List[Dict[str, Any]]:
        """Get S3 buckets with caching."""
        cache_key = "buckets:all"
        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached

        result = self._call(self._s3, self._s3.list_buckets)
        if not result["status"]:
            return []

        data = result["response"]
        self._cache.set(cache_key, data)
        return data

    def get_objects(self, bucket: str) -> List[Dict[str, Any]]:
        """Get S3 objects."""
        result = self._call(self._s3, self._s3.list_objects, bucket)
        if not result["status"]:
            return []
        return result["response"]

    # ── Service Quotas ───────────────────────────────────────────

    def get_service_quotas(self, service_code: str) -> List[Dict[str, Any]]:
        """Get service quotas with caching."""
        cache_key = f"quotas:{service_code}"
        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached

        result = self._call(
            self._quotas, self._quotas.list_service_quotas, service_code
        )
        if not result["status"]:
            return []

        data = result["response"]
        self._cache.set(cache_key, data)
        return data

    # ── Export ───────────────────────────────────────────────────

    def export_instances(self, filename: str) -> Optional[str]:
        """Export instances to JSON.

        Returns:
            File path if successful, None otherwise.
        """
        data = self.get_instances()
        if not data:
            return None
        filepath = save_json(data, filename)
        self.log(f"Exported instances to {filepath}")
        return filepath

    def export_images(self, filename: str, image_name: str = "") -> Optional[str]:
        """Export images to JSON.

        Returns:
            File path if successful, None otherwise.
        """
        data = self.get_images(image_name)
        if not data:
            return None
        filepath = save_json(data, filename)
        self.log(f"Exported images to {filepath}")
        return filepath
