# Dashboards

## Host

`/host` and `/host/neo` expose administration, deployment, security, federation, evaluation and configuration.

## Agent

`/agent` and `/agent/neo` expose contribution, Skill routing, research planning and knowledge discovery. They intentionally do not expose Host-only operations.

## User

`/user` and `/user/neo` expose Marketplace and public Knowledge discovery. They cannot enter the Host or Agent consoles without their own principal credentials.

## Machine-to-machine

Agents should prefer the HTTP API or SDKs instead of scraping dashboards.
