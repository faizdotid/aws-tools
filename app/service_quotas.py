"""Service Quotas client with AWS API wrappers."""

from typing import Any, Dict, List

from .boto3_base import BaseClient

__all__ = ["ServiceQuotasClient"]


class ServiceQuotasClient(BaseClient):
    """Client for AWS Service Quotas operations."""

    def __init__(self) -> None:
        super().__init__()

    def list_service_quotas(self, service_code: str) -> List[Dict[str, Any]]:
        """List all service quotas for a given service code with pagination.

        Args:
            service_code: AWS service code (e.g., 'ec2', 's3').

        Returns:
            List of quota dictionaries sorted by quota name.

        Raises:
            ValueError: If service_code is empty.
        """
        if not service_code:
            raise ValueError("Service code is required")

        results: List[Dict[str, Any]] = []
        kwargs: Dict[str, Any] = {"ServiceCode": service_code}

        while True:
            response = self.client.list_service_quotas(**kwargs)
            results.extend(response.get("Quotas", []))
            next_token = response.get("NextToken")
            if not next_token:
                break
            kwargs["NextToken"] = next_token

        return sorted(results, key=lambda item: item["QuotaName"])
