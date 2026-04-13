# Directory Factory

Template-once, deploy-many directory sites for underserved professional niches.

See `CLAUDE.md` for tech stack, setup, and key commands.

## Health Check

Before deploying, verify your environment is sane:

    python3 factory.py doctor

This validates all required API keys, local tooling, DNS records, Cloudflare resources, and per-vertical state. See `scripts/doctor.py` for the full check list.
