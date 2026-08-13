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
        kwargs: Dict[str, Any] = {"Bucket": bucket}
        if prefix:
            kwargs["Prefix"] = prefix
        results: List[Dict[str, Any]] = []
        while True:
            response = self.client.list_objects_v2(**kwargs)
            results.extend(response.get("Contents", []))
            if not response.get("IsTruncated"):
                break
            kwargs["ContinuationToken"] = response.get("NextContinuationToken")
        return results
