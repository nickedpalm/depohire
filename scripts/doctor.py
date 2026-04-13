"""Read-only health check for the directory factory pipeline.

Usage: python3 factory.py doctor [--vertical SLUG] [--optional]

Checks shared env (API keys, tooling), and per-vertical DNS/CF/GitHub/DB state.
All checks are pure and dependency-injected for testability.
"""

from __future__ import annotations

import re
import socket
import subprocess
import sys
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Callable

import httpx
import yaml


class Status(Enum):
    OK = "ok"
    FAIL = "fail"
    WARN = "warn"
    SKIP = "skip"


@dataclass
class CheckResult:
    status: Status
    name: str
    message: str
    remediation: str | None

    def is_blocking(self) -> bool:
        return self.status is Status.FAIL


@dataclass
class DoctorDeps:
    http: httpx.Client
    run_cmd: Callable[[list[str]], subprocess.CompletedProcess]
    env: dict[str, str]
    project_root: Path


REQUIRED_SHARED_ENV = [
    "PERPLEXITY_API_KEY",
    "ANTHROPIC_API_KEY",
    "GOOGLE_MAPS_API_KEY",
    "CLOUDFLARE_API_TOKEN",
    "GITHUB_TOKEN",
]


def check_shared_env_presence(deps: DoctorDeps) -> CheckResult:
    missing = [k for k in REQUIRED_SHARED_ENV if not deps.env.get(k)]
    if not missing:
        return CheckResult(Status.OK, "shared-env", "all 5 required keys present", None)
    return CheckResult(
        status=Status.FAIL,
        name="shared-env",
        message=f"missing or empty: {', '.join(missing)}",
        remediation="Export each in your shell profile (~/.bashrc) or your .env loader. "
                    "See docs/BOOTSTRAP.md for where to obtain each key.",
    )


def check_cloudflare_token(deps: DoctorDeps) -> CheckResult:
    token = deps.env.get("CLOUDFLARE_API_TOKEN", "")
    if not token:
        return CheckResult(Status.FAIL, "cloudflare-token", "not set", "Export CLOUDFLARE_API_TOKEN.")
    try:
        r = deps.http.get(
            "https://api.cloudflare.com/client/v4/user/tokens/verify",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10,
        )
    except httpx.HTTPError as e:
        return CheckResult(Status.FAIL, "cloudflare-token", f"network error: {e}", None)
    if r.status_code == 200 and r.json().get("success"):
        return CheckResult(Status.OK, "cloudflare-token", "active", None)
    return CheckResult(
        status=Status.FAIL,
        name="cloudflare-token",
        message=f"verify failed: {r.status_code} {r.text[:120]}",
        remediation="Regenerate token at dash.cloudflare.com → My Profile → API Tokens. "
                    "Required scopes: Account:Cloudflare Pages:Edit, Zone:DNS:Edit, Zone:Zone:Read.",
    )


def check_github_token(deps: DoctorDeps) -> CheckResult:
    token = deps.env.get("GITHUB_TOKEN", "")
    if not token:
        return CheckResult(Status.FAIL, "github-token", "not set", "Export GITHUB_TOKEN.")
    try:
        r = deps.http.get(
            "https://api.github.com/user",
            headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"},
            timeout=10,
        )
    except httpx.HTTPError as e:
        return CheckResult(Status.FAIL, "github-token", f"network error: {e}", None)
    if r.status_code == 200:
        return CheckResult(Status.OK, "github-token", f"authenticated as {r.json().get('login')}", None)
    return CheckResult(
        status=Status.FAIL,
        name="github-token",
        message=f"verify failed: {r.status_code}",
        remediation="Generate a new PAT at github.com/settings/tokens. Required scopes: repo.",
    )


def check_anthropic_key(deps: DoctorDeps) -> CheckResult:
    key = deps.env.get("ANTHROPIC_API_KEY", "")
    if not key:
        return CheckResult(Status.FAIL, "anthropic-key", "not set", "Export ANTHROPIC_API_KEY.")
    try:
        r = deps.http.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": "claude-haiku-4-5-20251001",
                "max_tokens": 1,
                "messages": [{"role": "user", "content": "hi"}],
            },
            timeout=15,
        )
    except httpx.HTTPError as e:
        return CheckResult(Status.FAIL, "anthropic-key", f"network error: {e}", None)
    if r.status_code == 200:
        return CheckResult(Status.OK, "anthropic-key", "responded", None)
    return CheckResult(
        status=Status.FAIL,
        name="anthropic-key",
        message=f"{r.status_code}: {r.text[:120]}",
        remediation="Regenerate at console.anthropic.com → API Keys. Set a monthly spend cap while there.",
    )


def check_perplexity_key(deps: DoctorDeps) -> CheckResult:
    key = deps.env.get("PERPLEXITY_API_KEY", "")
    if not key:
        return CheckResult(Status.FAIL, "perplexity-key", "not set", "Export PERPLEXITY_API_KEY.")
    try:
        r = deps.http.post(
            "https://api.perplexity.ai/chat/completions",
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            json={
                "model": "sonar",
                "max_tokens": 1,
                "messages": [{"role": "user", "content": "hi"}],
            },
            timeout=15,
        )
    except httpx.HTTPError as e:
        return CheckResult(Status.FAIL, "perplexity-key", f"network error: {e}", None)
    if r.status_code == 200:
        return CheckResult(Status.OK, "perplexity-key", "responded", None)
    return CheckResult(
        status=Status.FAIL,
        name="perplexity-key",
        message=f"{r.status_code}: {r.text[:120]}",
        remediation="Regenerate at perplexity.ai/settings/api. Top up credits if depleted.",
    )


def check_google_places_key(deps: DoctorDeps) -> CheckResult:
    key = deps.env.get("GOOGLE_MAPS_API_KEY", "")
    if not key:
        return CheckResult(Status.FAIL, "google-places-key", "not set", "Export GOOGLE_MAPS_API_KEY.")
    try:
        r = deps.http.post(
            "https://places.googleapis.com/v1/places:searchText",
            headers={
                "X-Goog-Api-Key": key,
                "X-Goog-FieldMask": "places.displayName",
                "Content-Type": "application/json",
            },
            json={"textQuery": "coffee shop san francisco", "pageSize": 1},
            timeout=10,
        )
    except httpx.HTTPError as e:
        return CheckResult(Status.FAIL, "google-places-key", f"network error: {e}", None)
    if r.status_code == 200:
        return CheckResult(Status.OK, "google-places-key", "responded", None)
    return CheckResult(
        status=Status.FAIL,
        name="google-places-key",
        message=f"{r.status_code}: {r.text[:160]}",
        remediation="Check GCP Console → APIs & Services → Credentials. Ensure Places API (New) is enabled "
                    "and billing is active. Free tier covers ~$200/mo of calls.",
    )


TOOLING_MINIMA = [
    ("node", ["node", "--version"], re.compile(r"v(\d+)\.(\d+)\.(\d+)"), (20, 0, 0)),
    ("python3", ["python3", "--version"], re.compile(r"Python (\d+)\.(\d+)\.(\d+)"), (3, 11, 0)),
    ("npm", ["npm", "--version"], re.compile(r"(\d+)\.(\d+)\.(\d+)"), (10, 0, 0)),
    ("wrangler", ["wrangler", "--version"], re.compile(r"(?:wrangler\s+)(\d+)\.(\d+)\.(\d+)"), (3, 0, 0)),
]


def check_local_tooling(deps: DoctorDeps) -> CheckResult:
    problems = []
    for name, cmd, pattern, minimum in TOOLING_MINIMA:
        result = deps.run_cmd(cmd)
        if result.returncode != 0:
            problems.append(f"{name} not found (run `{cmd[0]} --version` to confirm)")
            continue
        combined_output = result.stdout + (result.stderr or "")
        m = pattern.search(combined_output)
        if not m:
            problems.append(f"{name} version unparsable: {combined_output.strip()[:40]}")
            continue
        got = tuple(int(x) for x in m.groups())
        if got < minimum:
            problems.append(f"{name} {'.'.join(map(str, got))} < required {'.'.join(map(str, minimum))}")
    if not problems:
        return CheckResult(Status.OK, "local-tooling", "node, python3, npm, wrangler all present at required versions", None)
    return CheckResult(
        status=Status.FAIL,
        name="local-tooling",
        message="; ".join(problems),
        remediation="Install missing tools: node≥20 (nvm install 20), wrangler (npm i -g wrangler), "
                    "python≥3.11 (system package manager).",
    )


REQUIRED_YAML_FIELDS = ["name", "slug", "domain", "brand_name", "primary_keyword"]


def discover_verticals(deps: DoctorDeps, only: str | None) -> list[str]:
    configs_dir = deps.project_root / "configs"
    slugs = sorted(p.stem for p in configs_dir.glob("*.yaml"))
    if only is None:
        return slugs
    if only not in slugs:
        print(f"error: no config for vertical '{only}'. Found: {slugs}", file=sys.stderr)
        raise SystemExit(2)
    return [only]


def check_vertical_yaml(deps: DoctorDeps, slug: str) -> CheckResult:
    path = deps.project_root / "configs" / f"{slug}.yaml"
    try:
        raw = path.read_text()
    except FileNotFoundError:
        return CheckResult(Status.FAIL, f"{slug}:yaml", f"config file not found: {path}",
                           f"Create configs/{slug}.yaml. See docs/VERTICAL-PLAYBOOK.md §2.")
    try:
        config = yaml.safe_load(raw)
    except yaml.YAMLError as e:
        return CheckResult(Status.FAIL, f"{slug}:yaml", f"parse error: {e}", "Validate YAML at yamlchecker.com.")
    if not isinstance(config, dict):
        return CheckResult(Status.FAIL, f"{slug}:yaml", "yaml is empty or not a mapping",
                           "Top-level yaml must be a mapping of keys to values.")
    missing = [k for k in REQUIRED_YAML_FIELDS if not config.get(k)]
    if missing:
        return CheckResult(
            status=Status.FAIL,
            name=f"{slug}:yaml",
            message=f"missing required fields: {', '.join(missing)}",
            remediation="See docs/VERTICAL-PLAYBOOK.md §2 for the full yaml template.",
        )
    return CheckResult(Status.OK, f"{slug}:yaml", f"{len(config)} fields parsed", None)


def _load_vertical_config(deps: DoctorDeps, slug: str) -> dict:
    path = deps.project_root / "configs" / f"{slug}.yaml"
    return yaml.safe_load(path.read_text()) or {}


def check_domain_dns(deps: DoctorDeps, slug: str) -> CheckResult:
    config = _load_vertical_config(deps, slug)
    domain = config.get("domain", "")
    if not domain:
        return CheckResult(Status.FAIL, f"{slug}:dns", "no domain in config", None)
    try:
        ip = socket.gethostbyname(domain)
    except socket.gaierror as e:
        return CheckResult(
            status=Status.FAIL,
            name=f"{slug}:dns",
            message=f"{domain} does not resolve: {e}",
            remediation=f"In Cloudflare dashboard, add a CNAME for {domain} → <project>.pages.dev.",
        )
    return CheckResult(Status.OK, f"{slug}:dns", f"{domain} → {ip}", None)


def check_github_repo(deps: DoctorDeps, slug: str) -> CheckResult:
    token = deps.env.get("GITHUB_TOKEN", "")
    if not token:
        return CheckResult(Status.SKIP, f"{slug}:github", "GITHUB_TOKEN not set (checked separately)", None)
    try:
        r = deps.http.get(
            f"https://api.github.com/repos/nickedpalm/{slug}",
            headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"},
            timeout=10,
        )
    except httpx.HTTPError as e:
        return CheckResult(Status.FAIL, f"{slug}:github", f"network error: {e}", None)
    if r.status_code == 200:
        return CheckResult(Status.OK, f"{slug}:github", f"nickedpalm/{slug} exists", None)
    if r.status_code == 404:
        return CheckResult(
            status=Status.FAIL,
            name=f"{slug}:github",
            message=f"nickedpalm/{slug} not found",
            remediation=f"gh repo create nickedpalm/{slug} --public --source=verticals/{slug} --push",
        )
    return CheckResult(Status.FAIL, f"{slug}:github", f"unexpected {r.status_code}", None)
