from .boto3_base import BaseClient

from typing import List, Dict, Any, Text

class ServiceQuotasClient(BaseClient):

    def __init__(self) -> None:
        super().__init__()
    
    def _show_service_quotas(self, service_code, results: List[Dict[str, Any]], **kwargs) -> List[Dict[str, Any]]:
        if not bool(service_code):
            raise ValueError('Service code is required')
        response = self._client.list_service_quotas(
            ServiceCode=service_code,
            **kwargs
        )
        if 'NextToken' in response:
            results.extend(response['Quotas'])
            return self._show_service_quotas(
                service_code,
                results,
                NextToken=response['NextToken']
            )
        results.extend(response['Quotas'])
        return sorted(
            results,
            key=lambda item: item['QuotaName']
        )