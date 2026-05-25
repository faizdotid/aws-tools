# AWS Tools

Interactive CLI for managing AWS resources using Python. Features dropdown menus, autocomplete, rich tables, and progress spinners.

## Prerequisites

- Python 3.8+
- AWS credentials (Access Key ID & Secret Access Key)

## Installation

```bash
git clone https://github.com/faizalpratama/aws-tools
cd aws-tools
pip install -r requirements.txt
```

## Usage

```bash
python3 main.py
```

Navigate menus using **arrow keys** and **Enter**.

## Features

- **Interactive Dropdown Menus** — Navigate with arrow keys
- **Autocomplete Inputs** — Quick selection for key pairs, security groups, regions
- **Rich Tables** — Styled output for instances, buckets, VPCs, etc.
- **Progress Spinners** — Visual feedback during API calls
- **Data Caching** — 30-second TTL cache to reduce API calls
- **Export to JSON** — Export instances and images
- **Activity Logging** — Persistent logs to `client.log`

## Menu Structure

```
Main Menu
├── 🖥️ EC2 Management
│   ├── 📋 Show Instances
│   ├── 📦 Show Instance Types
│   ├── 🖼️ Show Images (AMIs)
│   ├── 🔑 Show Key Pairs
│   ├── 🔒 Show Security Groups
│   ├── ➕ Create Instance
│   ├── 🔐 Create Key Pair (.pem auto-saved)
│   ├── 🔓 Create Security Group
│   ├── 🌐 Authorize All Traffic
│   ├── ▶ Start / ⏹ Stop / 🔄 Reboot / 🗑 Terminate
├── 🌐 VPC & Networking
│   ├── 🌐 Show VPCs
│   └── 📡 Show Subnets
├── 🪣 S3
│   ├── 🪣 Show Buckets
│   └── 📁 Show Objects
├── 📊 Service Quotas
├── 📤 Export (JSON)
├── ⚙️ Configuration
│   ├── 🔑 Configure Credentials
│   ├── 🌍 Change Region
│   └── 🗺️ Show Regions
└── 🚪 Exit
```

## Project Structure

```
app/
├── __init__.py          # Package exports
├── config.py            # Region definitions
├── utils.py             # Helpers & validators
├── session.py           # AWS session manager
├── boto3_base.py        # Error handling wrapper
├── ec2.py               # EC2 API wrappers
├── s3.py                # S3 API wrappers
├── service_quotas.py    # Service Quotas API
├── controller.py        # Facade + caching + logging
├── ui.py                # Questionary + Rich helpers
└── cli.py               # Interactive CLI loop
```

## Key Files

- Key pairs saved to `results/keypairs/{name}-{id}.pem`
- JSON exports saved to `results/exports/`
- Logs written to `client.log`
