# Infra

Infrastructure notes and future Terraform for:

- private Cloudflare R2 source mirror
- Postgres provider configuration
- deployment configuration
- backup and restore documentation
- secret store wiring

The scaffold intentionally avoids checked-in credentials, state files, or environment
specific `.tfvars`.
