# IAC-Ansible

Infrastructure as Code for bootstrapping hosts, reconciling host configuration, deploying Compose services, and running recurring maintenance with Ansible Pull.

This repository is the host-side Ansible layer. Service definitions live in `meyersa/iac-cd` and are cloned to the host during deploy.

## Setup

Before running the playbooks against a new host, the host needs two things:

1. An initial admin account that Ansible can SSH into.
2. A Bitwarden Secrets Manager access token file on the host.

### Initial Admin Account

Set `ansible_user` in `inventory.yml` to the cloud or image-provided admin account for the host. That account must be reachable over SSH and able to run `sudo` during the first configure run.

The configure playbook then reconciles the longer-term account model:

| Account | Managed by | Purpose |
| ------- | ---------- | ------- |
| `ansible_user` | Inventory | Bootstrap and break-glass admin account used by Ansible. |
| Login user | Bitwarden item referenced by `LOGIN_USER` | Personal interactive SSH account with sudo access. |
| Login aliases | Bitwarden item referenced by `LOGIN_USER_ALIASES` | Comma-separated SSH usernames that map to the login user UID, home, and shell. |
| `ansible_managed_group` | Inventory | Shared group for Ansible-owned managed resources; includes `ansible_user` and the login user. |
| `alloy` | `roles/configure/tasks/accounts.yml` | Non-login service account for Grafana Alloy. |
| `actions` | `ansible_pull_actions_user` | Restricted automation account that can trigger `ansible-pull` systemd units. |

Compose/CD resources under `/etc/compose` are owned by `ansible_user` and grouped with `ansible_managed_group`, keeping `alloy` and `actions` out of that access path.

### Secrets File

Create the Bitwarden token file at the path configured by `ansible_pull_secrets_file`, currently:

```text
/etc/ansible-pull/bws_access_token
```

The file should contain the Bitwarden Secrets Manager access token used by `bitwarden.secrets.lookup`. The configure playbook enforces root ownership and `0600` permissions, but the file must exist before configure reaches the Ansible Pull setup tasks.

Manual playbook runs also need Bitwarden auth available on the control machine, typically by exporting the same token before running Ansible:

```bash
export BWS_ACCESS_TOKEN=<token>
```

After configure installs the Ansible Pull wrapper, pull-based runs load `BWS_ACCESS_TOKEN` from the host-local secrets file.

### First Run

Install Ansible on the control machine, make sure the target host is listed in `inventory.yml`, then run configure:

```bash
ansible-playbook -i inventory.yml playbooks/configure.yml
```

After configure succeeds, the host has the local accounts, SSH access, packages, Docker, supporting services, and Ansible Pull systemd units needed for ongoing automation.

## Playbooks

| File | Trigger | Scope |
| ---- | ------- | ----- |
| `playbooks/configure.yml` | Manual first run, then Ansible Pull | Reconciles host configuration: accounts, SSH access, packages, hostname, firewall, CrowdSec bouncer, WARP, DDClient, Grafana Alloy, swap, Docker, and Ansible Pull resources. |
| `playbooks/deploy.yml` | Ansible Pull | Clones `meyersa/iac-cd` into `/etc/compose`, renders templates, runs baseline Compose reconciliation for each project, and force-recreates impacted services when service files change. |
| `playbooks/maintain.yml` | Scheduled Ansible Pull | Updates OS packages and cleans system resources, including journal logs, apt cleanup, and Docker pruning. |

The utility role contains shared helper tasks such as Discord webhook notifications.

## Standards

### Storage

| Variable | Directory | Description |
| -------- | --------- | ----------- |
| `CONFIG_DIR` | `/etc` | Host configuration and rendered Compose resources. |
| `STATIC_DIR` | `/var/lib` | Local service state, databases, and other host-bound data. |
| `DATA_DIR` | `/srv` | Service data intended to be served or backed up. |

### Automation

- `configure.yml` bootstraps Ansible Pull and the restricted `actions` account.
- GitHub Actions can SSH as `actions` to start approved `ansible-pull@branch:playbook.service` units.
- Scheduled maintenance is handled by the `ansible-pull@main:maintain.timer` systemd timer.
- `deploy.yml` is the source of truth for Docker Compose reconciliation; manual Compose commands are for inspection, debugging, or targeted intervention.

### Secrets

- Secret values are stored in Bitwarden Secrets Manager.
- Inventory variables store Bitwarden item IDs, not raw secret values.
- Playbooks read secrets with `bitwarden.secrets.lookup`.
- The host-local token file is secured at `ansible_pull_secrets_file`.

### Backups

- Service data under `DATA_DIR` is expected to be backed up.
- Database backup behavior belongs with the service definitions and operational jobs in the Compose/CD layer.

## Using Ansible

### Installation

Ansible can be installed on Ubuntu or WSL with:

```bash
sudo apt update
sudo apt install software-properties-common
sudo add-apt-repository --yes --update ppa:ansible/ansible
sudo apt install ansible
```

### Ansible Pull

Configure installs a wrapper at `/usr/local/bin/ansible-pull-run` and systemd units using this pattern:

```text
ansible-pull@branch:playbook[:downstream-branch].service
```

For example, automation can trigger:

```bash
systemctl start ansible-pull@main:deploy.service
```

Hosts also get a small command wrapper on the system path:

```bash
ap deploy -b main -d feature/branch
ap configure -b main
ap maintain
```

`ap` starts the systemd unit and streams the journal output from that run.

The host also installs a Compose shortcut:

```bash
dc monitoring ps
dc monitoring logs -f grafana
dc monitoring up -d --force-recreate grafana
```

For `deploy`, the optional downstream branch selects the `iac-cd` branch:

```bash
systemctl start ansible-pull@main:deploy:feature-branch.service
```

When triggering through the restricted `actions` SSH command, the wrapper escapes the systemd unit name for you:

```bash
ssh actions@host ansible-pull main:deploy:feature/branch
```

The SSH wrapper also streams the journal output from the triggered run.

For direct `systemctl` calls with branch names that contain `/`, escape the unit instance first:

```bash
systemd-escape --template=ansible-pull@.service 'main:deploy:feature/branch'
```

## Compose Operations

Normal Compose reconciliation is handled by `playbooks/deploy.yml`. Use direct `docker compose` commands only when you need to inspect or intervene on a host.

Compose files are deployed under `/etc/compose` and follow this naming pattern:

```text
/etc/compose/compose.<project>.yml
```

Useful examples:

```bash
dc monitoring ps
dc monitoring logs -f grafana
dc monitoring up -d --force-recreate grafana
dc monitoring stop grafana
dc monitoring rm -f grafana
```

To take down an entire Compose project, including named volumes:

```bash
dc monitoring down -v
```
