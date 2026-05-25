"""Centralized configuration for AWS Tools."""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional


@dataclass(frozen=True)
class AWSConfig:
    """Immutable AWS configuration container."""
    aws_access_key_id: str
    aws_secret_access_key: str
    region_name: str

    @property
    def is_valid(self) -> bool:
        """Check if all required fields are non-empty."""
        return all([
            bool(self.aws_access_key_id),
            bool(self.aws_secret_access_key),
            bool(self.region_name)
        ])


class RegionConfig:
    """AWS region definitions and validation."""

    REGIONS: List[Dict[str, str]] = [
        {'name': 'us-east-1', 'description': 'US East (N. Virginia)'},
        {'name': 'us-east-2', 'description': 'US East (Ohio)'},
        {'name': 'us-west-1', 'description': 'US West (N. California)'},
        {'name': 'us-west-2', 'description': 'US West (Oregon)'},
        {'name': 'ap-south-1', 'description': 'Asia Pacific (Mumbai)'},
        {'name': 'ap-southeast-1', 'description': 'Asia Pacific (Singapore)'},
        {'name': 'ap-southeast-2', 'description': 'Asia Pacific (Sydney)'},
        {'name': 'ap-northeast-1', 'description': 'Asia Pacific (Tokyo)'},
        {'name': 'ap-northeast-2', 'description': 'Asia Pacific (Seoul)'},
        {'name': 'ap-northeast-3', 'description': 'Asia Pacific (Osaka-Local)'},
        {'name': 'ca-central-1', 'description': 'Canada (Central)'},
        {'name': 'eu-south-1', 'description': 'Europe (Milan)'},
        {'name': 'eu-central-1', 'description': 'Europe (Frankfurt)'},
        {'name': 'eu-north-1', 'description': 'Europe (Stockholm)'},
        {'name': 'eu-west-1', 'description': 'Europe (Ireland)'},
        {'name': 'eu-west-2', 'description': 'Europe (London)'},
        {'name': 'eu-west-3', 'description': 'Europe (Paris)'},
        {'name': 'sa-east-1', 'description': 'South America (São Paulo)'},
        {'name': 'me-south-1', 'description': 'Middle East (Bahrain)'},
    ]

    @classmethod
    def get_region_names(cls) -> List[str]:
        """Return list of valid region names."""
        return [r['name'] for r in cls.REGIONS]

    @classmethod
    def validate(cls, region_name: str) -> bool:
        """Check if region is supported."""
        return region_name in cls.get_region_names()

    @classmethod
    def get_description(cls, region_name: str) -> Optional[str]:
        """Get region description by name."""
        for region in cls.REGIONS:
            if region['name'] == region_name:
                return region['description']
        return None
