# AWS CLI

This project is a command-line interface (CLI) for managing AWS resources using Python. Most of the commands are EC2 and the rest are some other AWS services

## Prerequisites

- Python 3.6 or later
- AWS credentials

## Installation

1. Clone the repository:

    ```sh
    git clone https://github.com/faizdotid/aws-tools
    cd aws-cli
    ```

2. Install the required Python packages:

    ```sh
    pip install -r requirements.txt
    ```

## Usage

Run the CLI:

```sh
python main.py
```

## Availble commands

- `configure` <aws_access_key_id> <aws_secret_access_key> <region_name>: Configure AWS credentials.
- `show instance types` <instance_type>: Show instance types.
- `show instances` <instance_id>: Show instances.
- `create instance`: Create an instance.
- `show images` <image_name>: Show images.
- `show keypairs` <key_name>: Show key pairs.
- `create keypair` <key_name>: Create a key pair.
- `change region` <region_name>: Change the region.
- `show security groups` <group_name>: Show security groups.
- `authorize security group` <group_id>: Authorize security group.
- `create security group` <group_name> <description>: Create a security group.
- `show service quotas` <service_code>: Show service quotas.
- `terminate instance` <instance_id>: Terminate an instance.
- `show regions`: Show regions.