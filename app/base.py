from boto3 import Session, client

class BaseClient:

    _session: Session = None

    _regions = [        {
            'name': 'us-east-1',
            'description': 'US East (N. Virginia)'
        },
        {
            'name': 'us-east-2',
            'description': 'US East (Ohio)'
        },
        {
            'name': 'us-west-1',
            'description': 'US West (N. California)'
        },
        {
            'name': 'us-west-2',
            'description': 'US West (Oregon)'
        },
        {
            'name': 'ap-south-1',
            'description': 'Asia Pacific (Mumbai)'
        },
        {
            'name': 'ap-southeast-1',
            'description': 'Asia Pacific (Singapore)'
        },
        {
            'name': 'ap-southeast-2',
            'description': 'Asia Pacific (Sydney)'
        },
        {
            'name': 'ap-northeast-1',
            'description': 'Asia Pacific (Tokyo)'
        },
        {
            'name': 'ap-northeast-2',
            'description': 'Asia Pacific (Seoul)'
        },
        {
            'name': 'ap-northeast-3',
            'description': 'Asia Pacific (Osaka-Local)'
        },
        {
            'name': 'ca-central-1',
            'description': 'Canada (Central)'
        },
        {
            'name': 'eu-south-1',
            'description': 'Europe (Milan)'
        },
        {
            'name': 'eu-central-1',
            'description': 'Europe (Frankfurt)'
        },
        {
            'name': 'eu-north-1',
            'description': 'Europe (Stockholm)'
        },
        {
            'name': 'eu-west-1',
            'description': 'Europe (Ireland)'
        },
        {
            'name': 'eu-west-2',
            'description': 'Europe (London)'
        },
        {
            'name': 'eu-west-3',
            'description': 'Europe (Paris)'
        },
        {
            'name': 'sa-east-1',
            'description': 'South America (São Paulo)'
        },
        {
            'name': 'me-south-1',
            'description': 'Middle East (Bahrain)'
        }
    ]

    def __init__(self):
        pass

    @classmethod
    def configure(
        cls,
        aws_access_key_id: str,
        aws_secret_access_key: str,
        region_name: str,
    ) -> None:
        cls._session = Session(
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            region_name=region_name
        )

    @classmethod
    def get_client(cls, service_name: str, region_name: str) -> client:
        return cls._session.client(service_name, region_name=region_name)
    
    @property
    def regions(self):
        return self._regions