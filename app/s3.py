"""S3 service client with AWS API wrappers."""

from typing import Any, Dict, List

from .boto3_base import BaseClient

__all__ = ["S3Client"]


class S3Client(BaseClient):
    """Client for AWS S3 operations."""

    def __init__(self) -> None:
        super().__init__()

    def list_buckets(self) -> List[Dict[str, Any]]:
        """List all S3 buckets.

        Returns:
            List of bucket dictionaries.
        """
        response = self.client.list_buckets()
        return response.get("Buckets", [])

    def list_objects(self, bucket: str, prefix: str = "") -> List[Dict[str, Any]]:
        """List objects in a bucket.

        Args:
            bucket: Bucket name.
            prefix: Object key prefix filter (optional).

        Returns:
            List of object dictionaries.
        """
        kwargs = {"Bucket": bucket}
        if prefix:
            kwargs["Prefix"] = prefix
        response = self.client.list_objects_v2(**kwargs)
        return response.get("Contents", [])

    def get_bucket_location(self, bucket: str) -> str:
        """Get bucket region.

        Args:
            bucket: Bucket name.

        Returns:
            Region name (returns 'us-east-1' if empty).
        """
        response = self.client.get_bucket_location(Bucket=bucket)
        loc = response.get("LocationConstraint")
        return loc if loc else "us-east-1"

    def get_bucket_info(self, bucket: str) -> Dict[str, Any]:
        """Get combined bucket info.

        Args:
            bucket: Bucket name.

        Returns:
            Dictionary with region, object count, and total size.
        """
        location = self.get_bucket_location(bucket)
        objects = self.list_objects(bucket)
        total_size = sum(obj.get("Size", 0) for obj in objects)
        return {
            "Bucket": bucket,
            "Region": location,
            "ObjectCount": len(objects),
            "TotalSizeBytes": total_size,
        }
