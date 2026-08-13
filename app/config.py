"""Centralized configuration for AWS Tools."""

from typing import List, Dict

__all__ = ["RegionConfig"]


class RegionConfig:
    """AWS region definitions and validation."""

    REGIONS: List[Dict[str, str]] = [
        {"name": "us-east-1", "description": "US East (N. Virginia)"},
        {"name": "us-east-2", "description": "US East (Ohio)"},
        {"name": "us-west-1", "description": "US West (N. California)"},
        {"name": "us-west-2", "description": "US West (Oregon)"},
        {"name": "af-south-1", "description": "Africa (Cape Town)"},
        {"name": "ap-east-1", "description": "Asia Pacific (Hong Kong)"},
        {"name": "ap-south-1", "description": "Asia Pacific (Mumbai)"},
        {"name": "ap-south-2", "description": "Asia Pacific (Hyderabad)"},
        {"name": "ap-southeast-1", "description": "Asia Pacific (Singapore)"},
        {"name": "ap-southeast-2", "description": "Asia Pacific (Sydney)"},
        {"name": "ap-southeast-3", "description": "Asia Pacific (Jakarta)"},
        {"name": "ap-southeast-4", "description": "Asia Pacific (Melbourne)"},
        {"name": "ap-southeast-5", "description": "Asia Pacific (Malaysia)"},
        {"name": "ap-southeast-7", "description": "Asia Pacific (Thailand)"},
        {"name": "ap-northeast-1", "description": "Asia Pacific (Tokyo)"},
        {"name": "ap-northeast-2", "description": "Asia Pacific (Seoul)"},
        {"name": "ap-northeast-3", "description": "Asia Pacific (Osaka-Local)"},
        {"name": "ca-central-1", "description": "Canada (Central)"},
        {"name": "ca-west-1", "description": "Canada West (Calgary)"},
        {"name": "eu-central-1", "description": "Europe (Frankfurt)"},
        {"name": "eu-central-2", "description": "Europe (Zurich)"},
        {"name": "eu-north-1", "description": "Europe (Stockholm)"},
        {"name": "eu-south-1", "description": "Europe (Milan)"},
        {"name": "eu-south-2", "description": "Europe (Spain)"},
        {"name": "eu-west-1", "description": "Europe (Ireland)"},
        {"name": "eu-west-2", "description": "Europe (London)"},
        {"name": "eu-west-3", "description": "Europe (Paris)"},
        {"name": "il-central-1", "description": "Israel (Tel Aviv)"},
        {"name": "me-central-1", "description": "Middle East (UAE)"},
        {"name": "me-south-1", "description": "Middle East (Bahrain)"},
        {"name": "mx-central-1", "description": "Mexico (Central)"},
        {"name": "sa-east-1", "description": "South America (São Paulo)"},
    ]

    @classmethod
    def get_region_names(cls) -> List[str]:
        """Return list of valid region names."""
        return [r["name"] for r in cls.REGIONS]

    @classmethod
    def validate(cls, region_name: str) -> bool:
        """Check if region is supported."""
        return region_name in cls.get_region_names()
