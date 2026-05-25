# AWS Tools

A command-line interface (CLI) for managing AWS resources using Python. Built with [Rich](https://github.com/Textualize/rich) for an enhanced terminal experience.

## Prerequisites

- Python 3.8 or later
- AWS credentials (Access Key ID & Secret Access Key)

## Installation

1. Clone the repository:

   ```sh
   git clone https://github.com/faizdotid/aws-tools
   cd aws-tools
   ```

2. Install dependencies:

   ```sh
   pip install -r requirements.txt
   ```

## Usage

Run the CLI:

```sh
python3 main.py
```

Type `help` inside the CLI to see all available commands.

## Available Commands

### Configuration
| Command | Description |
|---------|-------------|
| `configure <key> <secret> <region>` | Configure AWS credentials |
| `change region <region>` | Change AWS region |
| `show regions` | List supported AWS regions |

### EC2 Instances
| Command | Description |
|---------|-------------|
| `show instances <id>` | Show EC2 instances |
| `show instance types <type>` | Show instance types |
| `create instance` | Create a new EC2 instance (interactive) |
| `start instance <id>` | Start a stopped instance |
| `stop instance <id>` | Stop a running instance |
| `reboot instance <id>` | Reboot an instance |
| `terminate instance <id>` | Terminate an instance |

### AMIs
| Command | Description |
|---------|-------------|
| `show images <name>` | Show Amazon Machine Images |

### Key Pairs
| Command | Description |
|---------|-------------|
| `show keypairs <name>` | Show EC2 key pairs |
| `create keypair <name>` | Create a new key pair |

### Security Groups
| Command | Description |
|---------|-------------|
| `show security groups <name>` | Show security groups |
| `create security group <name> <desc>` | Create a security group |
| `authorize security group <id>` | Authorize all traffic (0.0.0.0/0) |

### VPC & Networking
| Command | Description |
|---------|-------------|
| `show vpcs` | List all VPCs |
| `show subnets <vpc_id>` | List subnets |

### S3
| Command | Description |
|---------|-------------|
| `show buckets` | List S3 buckets |
| `show objects <bucket>` | List objects in a bucket |

### Service Quotas
| Command | Description |
|---------|-------------|
| `show service quotas <code>` | Show service quotas (e.g. `ec2`) |

### Export
| Command | Description |
|---------|-------------|
| `export instances <file>` | Export instances to JSON |
| `export images <file>` | Export images to JSON |

### CLI
| Command | Description |
|---------|-------------|
| `help` | Show available commands |
| `clear` | Clear screen |
| `exit` | Quit the CLI |

## Project Structure

```
app/
├── __init__.py           # Package exports
├── config.py             # AWS configuration & region definitions
├── utils.py              # Utility functions & Rich helpers
├── session.py            # AWS session manager (replaces base.py)
├── boto3_base.py         # Base client with unified error handling
├── ec2.py                # EC2 service client
├── s3.py                 # S3 service client
├── service_quotas.py     # Service Quotas client
├── client.py             # Business logic & Rich UI
└── command.py            # CLI loop & command parser
```

## Features

- **Rich UI**: Styled tables, panels, trees, spinners, and progress indicators
- **Error Handling**: Unified error wrapping with credential auto-reset
- **Interactive Prompts**: Guided instance creation with validation
- **Export**: JSON export for instances and images
- **Auto-complete Suggestions**: Similar command suggestions on typo
- **Safe Defaults**: Confirmation prompts for destructive actions
