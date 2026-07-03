# IAC-Ansible

Primary component in GitOps Infrastructure as Code for my servers. Supported by additional repositories for CD resources, Grafana provisioning files, CI resources, and the Ansible vault (encrypted).

## Components

The Ansible strategy is broken up into three components: configuration, deployment, and maintenance

### Configuration

Configuration of OS and system before applications are run

- Installing system services (Crowdsec Bouncer, DDClient Grafana Alloy, Docker, Warp)
- Managing SSH Keys
- Installing required packages
- Initializing cron jobs

### Deployment

Deployment of all target applications and supporting applications

- Operations (Traefik, CloudFlared)
- Monitoring (Crowdsec, Grafana, Loki, Mimir)
- Storage (MongoDB)
- Media (Radarr, Sonarr, etc.)
- Applications (Mostly my websites)

### Maintenance

Tasks like cleaning, updating, and reporting that are run more often than other rules

- Cleaning (JournalCTL vacuum, old images, old packages)
- Updating OS

### Utility

Shared functions across the main components

## Playbooks

| File                      | Trigger      | Description                                   |
| ------------------------- | ------------ | --------------------------------------------- |
| `playbooks/configure.yml` | Ansible pull | Reconciles the server configuration           |
| `playbooks/deploy.yml`    | Ansible pull | Deploys configured services                   |
| `playbooks/maintain.yml`  | Ansible pull | Updates and cleans the system                 |

## Standards

### Storage

| Tag          | Directory  | Description                                             |
| ------------ | ---------- | ------------------------------------------------------- |
| `STATIC_DIR` | `/var/lib` | Databases and other non backed up items                 |
| `DATA_DIR`   | `/srv`     | Service and served data that is backed up               |
| `CONFIG_DIR` | `/etc`     | Compose resources, configuration and provisioning files |

### Automation

- Maintenance and reconciliation are handled with Cron synced Ansible-Pull
- CI is handled with GitHub actions triggered Ansible-Pull

### Security

- Passwords and secrets are stored in Bitwarden so they can be generated on the fly and pulled later from a source of truth

### User Accounts

Servers use a small set of accounts with separate responsibilities:

| Account type            | Purpose                                                                                                                                          |
| ----------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------ |
| Initial/Ansible user    | Cloud or image-provided account used by Ansible to bootstrap and reconcile the server. This also acts as the break-glass administrative account. |
| Login user              | Personal interactive account used for normal SSH sessions.                                                                                       |
| Alloy service account   | Non-login service account used by Grafana Alloy.                                                                                                 |
| Actions service account | Restricted service account used by automation to trigger ansible-pull systemd units.                                                             |

### Backups

- Defined data directory is synced to S3
- Database is synced to S3

## Using Ansible

### Installation

Ansible can be installed on Ubuntu (recommended WSL) with

```bash
sudo apt update
sudo apt install software-properties-common
sudo add-apt-repository --yes --update ppa:ansible/ansible
sudo apt install ansible
```

### Compose Commands

#### Start a single service

```bash
docker compose -f compose.monitoring.yml up grafana
```

#### Take down a service and it's data volume

```bash
docker compose -f compose.monitoring.yml down grafana -v
```
