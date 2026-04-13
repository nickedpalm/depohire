"""Read-only health check for the directory factory pipeline.

Usage: python3 factory.py doctor [--vertical SLUG] [--optional]

Checks shared env (API keys, tooling), and per-vertical DNS/CF/GitHub/DB state.
All checks are pure and dependency-injected for testability.
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Callable

import httpx


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
