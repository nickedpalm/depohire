# Factory Doctor Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add `python3 factory.py doctor` — a read-only health check that validates every API key, local tool, DNS record, Cloudflare resource, and per-vertical artifact the factory pipeline depends on. Output a color-coded report, exit 0 if healthy, 1 otherwise. No side effects (read-only, no auto-fix).

**Architecture:** A single `scripts/doctor.py` module exposing `run(verticals: list[str] | None, include_optional: bool) -> int`. Check functions are pure: they take injected dependencies (httpx client, config dict, subprocess runner) and return `CheckResult(status, name, message, remediation)`. This keeps them unit-testable with `httpx.MockTransport` and `subprocess` monkeypatching — no real network or shell calls in tests. `factory.py` gets a new `doctor` subparser that calls `scripts.doctor.run(...)` and returns its exit code.

**Tech Stack:** Python 3.11+, `httpx` (sync), `pyyaml`, stdlib `tomllib` (for wrangler.toml), stdlib `subprocess`, stdlib `socket` (DNS), `pytest` + `httpx.MockTransport` for tests. No new runtime dependencies.

---

## File Structure

- **Create:** `scripts/doctor.py` — all check functions + runner. One file, ~400 lines. Split by section comments: shared-env checks, tooling checks, per-vertical checks, optional checks, runner + formatter.
- **Create:** `scripts/doctor_checks/__init__.py` — NOT NEEDED. Single file is fine; promoting to a package is YAGNI until the check list exceeds ~30.
- **Create:** `tests/__init__.py` (empty) — tests directory marker if it doesn't already exist.
- **Create:** `tests/test_doctor.py` — unit tests per check, parametrized where shape is identical.
- **Modify:** `factory.py` — add `doctor` subparser (~15 lines near the bottom of argparse setup, plus one new `cmd_doctor(args)` function delegating to `scripts.doctor.run`).
- **Modify:** `requirements.txt` — add `httpx>=0.27`, `pyyaml>=6.0`, `pytest>=8.0` (confirm each is actually missing first; current file only has `Pillow>=10.0.0`, but scripts clearly use httpx/pyyaml so they're installed somehow — probably via venv drift; this plan makes them explicit).
- **Modify:** `CLAUDE.md` — add `python3 factory.py doctor` to Key Commands section, document exit codes and cost (~$0.001 per run).
- **Modify:** `README.md` — one-paragraph doctor section with example output.

---

## Testing Conventions

All check functions follow this signature:

```python
def check_<name>(deps: DoctorDeps) -> CheckResult: ...
```

Where `DoctorDeps` is a dataclass holding `http: httpx.Client`, `run_cmd: Callable[[list[str]], subprocess.CompletedProcess]`, `env: dict[str, str]`, `project_root: Path`. Tests construct `DoctorDeps` with mocks; production code builds it once in `run()`.

Commit after each task passes its test. Commit messages: `feat(doctor): <what>`.

---

## Task 1: Scaffold module, data types, and test harness

**Files:**
- Create: `scripts/doctor.py`
- Create: `tests/__init__.py`
- Create: `tests/test_doctor.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_doctor.py
from pathlib import Path
import httpx
from scripts.doctor import CheckResult, DoctorDeps, Status


def make_deps(**overrides) -> DoctorDeps:
    defaults = dict(
        http=httpx.Client(transport=httpx.MockTransport(lambda r: httpx.Response(200))),
        run_cmd=lambda cmd: None,
        env={},
        project_root=Path("/tmp"),
    )
    defaults.update(overrides)
    return DoctorDeps(**defaults)


def test_check_result_constructs():
    r = CheckResult(status=Status.OK, name="x", message="fine", remediation=None)
    assert r.status is Status.OK
    assert r.is_blocking() is False


def test_check_result_fail_is_blocking():
    r = CheckResult(status=Status.FAIL, name="x", message="bad", remediation="fix it")
    assert r.is_blocking() is True


def test_check_result_skip_is_not_blocking():
    r = CheckResult(status=Status.SKIP, name="x", message="n/a", remediation=None)
    assert r.is_blocking() is False


def test_deps_builds():
    deps = make_deps()
    assert deps.env == {}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd ~/tools/directory-factory && python3 -m pytest tests/test_doctor.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'scripts.doctor'` (or similar import error).

- [ ] **Step 3: Write minimal implementation**

```python
# scripts/doctor.py
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
```

Also create empty `tests/__init__.py`.

- [ ] **Step 4: Run test to verify it passes**

Run: `cd ~/tools/directory-factory && python3 -m pytest tests/test_doctor.py -v`
Expected: 4 passed.

- [ ] **Step 5: Commit**

```bash
cd ~/tools/directory-factory
git add scripts/doctor.py tests/__init__.py tests/test_doctor.py
git commit -m "feat(doctor): scaffold module, CheckResult, DoctorDeps"
```

---

## Task 2: Shared-env presence check (no network)

Validates that required env vars are set and non-empty. Runs before any live API check so the rest can assume presence.

**Files:**
- Modify: `scripts/doctor.py` — add `check_shared_env_presence`
- Modify: `tests/test_doctor.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_doctor.py (add)
from scripts.doctor import check_shared_env_presence, Status


def test_shared_env_presence_all_ok():
    deps = make_deps(env={
        "PERPLEXITY_API_KEY": "p-xxx",
        "ANTHROPIC_API_KEY": "sk-ant-xxx",
        "GOOGLE_MAPS_API_KEY": "g-xxx",
        "CLOUDFLARE_API_TOKEN": "cf-xxx",
        "GITHUB_TOKEN": "gh-xxx",
    })
    result = check_shared_env_presence(deps)
    assert result.status is Status.OK


def test_shared_env_presence_missing_one():
    deps = make_deps(env={
        "PERPLEXITY_API_KEY": "p-xxx",
        "ANTHROPIC_API_KEY": "sk-ant-xxx",
        "GOOGLE_MAPS_API_KEY": "g-xxx",
        "CLOUDFLARE_API_TOKEN": "",
        "GITHUB_TOKEN": "gh-xxx",
    })
    result = check_shared_env_presence(deps)
    assert result.status is Status.FAIL
    assert "CLOUDFLARE_API_TOKEN" in result.message
    assert result.remediation is not None


def test_shared_env_presence_all_missing():
    deps = make_deps(env={})
    result = check_shared_env_presence(deps)
    assert result.status is Status.FAIL
    for key in ["PERPLEXITY_API_KEY", "ANTHROPIC_API_KEY", "GOOGLE_MAPS_API_KEY",
                "CLOUDFLARE_API_TOKEN", "GITHUB_TOKEN"]:
        assert key in result.message
```

- [ ] **Step 2: Run to verify failure**

Run: `python3 -m pytest tests/test_doctor.py::test_shared_env_presence_all_ok -v`
Expected: FAIL with `ImportError: cannot import name 'check_shared_env_presence'`.

- [ ] **Step 3: Implement**

```python
# scripts/doctor.py (append)
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
```

- [ ] **Step 4: Run tests**

Run: `python3 -m pytest tests/test_doctor.py -v`
Expected: 7 passed.

- [ ] **Step 5: Commit**

```bash
git add scripts/doctor.py tests/test_doctor.py
git commit -m "feat(doctor): check shared env var presence"
```

---

## Task 3: Live API checks (Cloudflare, GitHub)

These two have free, dedicated auth-verify endpoints. Do them together because the test shape is identical.

**Files:**
- Modify: `scripts/doctor.py`
- Modify: `tests/test_doctor.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_doctor.py (add)
from scripts.doctor import check_cloudflare_token, check_github_token


def mock_http(handler) -> httpx.Client:
    return httpx.Client(transport=httpx.MockTransport(handler))


def test_cloudflare_token_valid():
    def handler(req):
        assert req.url.path == "/client/v4/user/tokens/verify"
        assert req.headers["authorization"] == "Bearer cf-abc"
        return httpx.Response(200, json={"success": True, "result": {"status": "active"}})
    deps = make_deps(env={"CLOUDFLARE_API_TOKEN": "cf-abc"}, http=mock_http(handler))
    assert check_cloudflare_token(deps).status is Status.OK


def test_cloudflare_token_invalid():
    def handler(req):
        return httpx.Response(401, json={"success": False, "errors": [{"message": "invalid"}]})
    deps = make_deps(env={"CLOUDFLARE_API_TOKEN": "cf-bad"}, http=mock_http(handler))
    r = check_cloudflare_token(deps)
    assert r.status is Status.FAIL
    assert "invalid" in r.message.lower() or "401" in r.message


def test_cloudflare_token_missing():
    deps = make_deps(env={})
    r = check_cloudflare_token(deps)
    assert r.status is Status.FAIL
    assert "not set" in r.message.lower()


def test_github_token_valid():
    def handler(req):
        assert req.url.path == "/user"
        assert req.headers["authorization"] == "Bearer gh-abc"
        return httpx.Response(200, json={"login": "nickedpalm"})
    deps = make_deps(env={"GITHUB_TOKEN": "gh-abc"}, http=mock_http(handler))
    r = check_github_token(deps)
    assert r.status is Status.OK
    assert "nickedpalm" in r.message


def test_github_token_invalid():
    def handler(req):
        return httpx.Response(401)
    deps = make_deps(env={"GITHUB_TOKEN": "gh-bad"}, http=mock_http(handler))
    assert check_github_token(deps).status is Status.FAIL
```

- [ ] **Step 2: Run to verify failure**

Run: `python3 -m pytest tests/test_doctor.py -v`
Expected: ImportError for `check_cloudflare_token`.

- [ ] **Step 3: Implement**

```python
# scripts/doctor.py (append)
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
```

- [ ] **Step 4: Run tests**

Run: `python3 -m pytest tests/test_doctor.py -v`
Expected: 12 passed.

- [ ] **Step 5: Commit**

```bash
git add scripts/doctor.py tests/test_doctor.py
git commit -m "feat(doctor): live check Cloudflare and GitHub tokens"
```

---

## Task 4: Live API checks (Anthropic, Perplexity, Google Places)

These charge per call. Use the cheapest possible probe: 1-token completion for Anthropic/Perplexity, 1-result Places text search. Document total run cost (<$0.001).

**Files:**
- Modify: `scripts/doctor.py`
- Modify: `tests/test_doctor.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_doctor.py (add)
from scripts.doctor import check_anthropic_key, check_perplexity_key, check_google_places_key


def test_anthropic_key_valid():
    def handler(req):
        assert req.url.path == "/v1/messages"
        assert req.headers["x-api-key"] == "sk-ant-abc"
        return httpx.Response(200, json={"id": "msg_1", "content": [{"type": "text", "text": "ok"}]})
    deps = make_deps(env={"ANTHROPIC_API_KEY": "sk-ant-abc"}, http=mock_http(handler))
    assert check_anthropic_key(deps).status is Status.OK


def test_anthropic_key_invalid():
    def handler(req):
        return httpx.Response(401, json={"error": {"message": "invalid api-key"}})
    deps = make_deps(env={"ANTHROPIC_API_KEY": "sk-bad"}, http=mock_http(handler))
    assert check_anthropic_key(deps).status is Status.FAIL


def test_perplexity_key_valid():
    def handler(req):
        assert req.url.host == "api.perplexity.ai"
        assert req.headers["authorization"] == "Bearer p-abc"
        return httpx.Response(200, json={"choices": [{"message": {"content": "hi"}}]})
    deps = make_deps(env={"PERPLEXITY_API_KEY": "p-abc"}, http=mock_http(handler))
    assert check_perplexity_key(deps).status is Status.OK


def test_perplexity_key_invalid():
    def handler(req):
        return httpx.Response(401)
    deps = make_deps(env={"PERPLEXITY_API_KEY": "p-bad"}, http=mock_http(handler))
    assert check_perplexity_key(deps).status is Status.FAIL


def test_google_places_key_valid():
    def handler(req):
        assert "places.googleapis.com" in req.url.host
        assert req.headers["x-goog-api-key"] == "g-abc"
        return httpx.Response(200, json={"places": [{"displayName": {"text": "A Cafe"}}]})
    deps = make_deps(env={"GOOGLE_MAPS_API_KEY": "g-abc"}, http=mock_http(handler))
    assert check_google_places_key(deps).status is Status.OK


def test_google_places_key_invalid():
    def handler(req):
        return httpx.Response(403, json={"error": {"message": "API key not valid"}})
    deps = make_deps(env={"GOOGLE_MAPS_API_KEY": "g-bad"}, http=mock_http(handler))
    r = check_google_places_key(deps)
    assert r.status is Status.FAIL
    assert "not valid" in r.message.lower() or "403" in r.message
```

- [ ] **Step 2: Run to verify failure**

Run: `python3 -m pytest tests/test_doctor.py -v`
Expected: ImportError for the three new functions.

- [ ] **Step 3: Implement**

```python
# scripts/doctor.py (append)
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
```

- [ ] **Step 4: Run tests**

Run: `python3 -m pytest tests/test_doctor.py -v`
Expected: 18 passed.

- [ ] **Step 5: Commit**

```bash
git add scripts/doctor.py tests/test_doctor.py
git commit -m "feat(doctor): live check Anthropic, Perplexity, Google Places keys"
```

---

## Task 5: Local tooling checks (node, python, wrangler, npm)

Uses `deps.run_cmd` for testability. Parses `--version` output and compares to minima.

**Files:**
- Modify: `scripts/doctor.py`
- Modify: `tests/test_doctor.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_doctor.py (add)
from scripts.doctor import check_local_tooling
import subprocess


def fake_run(responses: dict[str, tuple[int, str]]):
    def run(cmd: list[str]) -> subprocess.CompletedProcess:
        key = " ".join(cmd)
        rc, out = responses.get(key, (127, ""))
        return subprocess.CompletedProcess(cmd, rc, stdout=out, stderr="")
    return run


def test_local_tooling_all_ok():
    deps = make_deps(run_cmd=fake_run({
        "node --version": (0, "v20.11.1\n"),
        "python3 --version": (0, "Python 3.11.7\n"),
        "npm --version": (0, "10.2.4\n"),
        "wrangler --version": (0, " ⛅️ wrangler 3.78.0\n"),
    }))
    r = check_local_tooling(deps)
    assert r.status is Status.OK


def test_local_tooling_node_too_old():
    deps = make_deps(run_cmd=fake_run({
        "node --version": (0, "v18.0.0\n"),
        "python3 --version": (0, "Python 3.11.7\n"),
        "npm --version": (0, "10.2.4\n"),
        "wrangler --version": (0, "wrangler 3.78.0\n"),
    }))
    r = check_local_tooling(deps)
    assert r.status is Status.FAIL
    assert "node" in r.message.lower()


def test_local_tooling_wrangler_missing():
    deps = make_deps(run_cmd=fake_run({
        "node --version": (0, "v20.11.1\n"),
        "python3 --version": (0, "Python 3.11.7\n"),
        "npm --version": (0, "10.2.4\n"),
        "wrangler --version": (127, ""),
    }))
    r = check_local_tooling(deps)
    assert r.status is Status.FAIL
    assert "wrangler" in r.message.lower()
```

- [ ] **Step 2: Run to verify failure**

Run: `python3 -m pytest tests/test_doctor.py -v`
Expected: ImportError for `check_local_tooling`.

- [ ] **Step 3: Implement**

```python
# scripts/doctor.py (append)
import re

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
        m = pattern.search(result.stdout)
        if not m:
            problems.append(f"{name} version unparsable: {result.stdout.strip()[:40]}")
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
```

- [ ] **Step 4: Run tests**

Run: `python3 -m pytest tests/test_doctor.py -v`
Expected: 21 passed.

- [ ] **Step 5: Commit**

```bash
git add scripts/doctor.py tests/test_doctor.py
git commit -m "feat(doctor): check local tooling versions"
```

---

## Task 6: Vertical discovery + yaml validation

Enumerates `configs/*.yaml` (and optionally filters to a single slug), validates each parses and has the required fields: `name`, `slug`, `domain`, `brand_name`, `primary_keyword`.

**Files:**
- Modify: `scripts/doctor.py`
- Modify: `tests/test_doctor.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_doctor.py (add)
import tempfile
from pathlib import Path
from scripts.doctor import discover_verticals, check_vertical_yaml


def test_discover_verticals_finds_all(tmp_path):
    (tmp_path / "configs").mkdir()
    (tmp_path / "configs" / "a.yaml").write_text("slug: a\n")
    (tmp_path / "configs" / "b.yaml").write_text("slug: b\n")
    (tmp_path / "configs" / "voice-guide.md").write_text("# ignored")
    deps = make_deps(project_root=tmp_path)
    assert sorted(discover_verticals(deps, None)) == ["a", "b"]


def test_discover_verticals_filters_to_one(tmp_path):
    (tmp_path / "configs").mkdir()
    (tmp_path / "configs" / "a.yaml").write_text("slug: a\n")
    (tmp_path / "configs" / "b.yaml").write_text("slug: b\n")
    deps = make_deps(project_root=tmp_path)
    assert discover_verticals(deps, "a") == ["a"]


def test_discover_verticals_missing_slug_raises(tmp_path):
    (tmp_path / "configs").mkdir()
    (tmp_path / "configs" / "a.yaml").write_text("slug: a\n")
    deps = make_deps(project_root=tmp_path)
    import pytest
    with pytest.raises(SystemExit):
        discover_verticals(deps, "nope")


def test_vertical_yaml_valid(tmp_path):
    (tmp_path / "configs").mkdir()
    (tmp_path / "configs" / "x.yaml").write_text(
        "name: X\nslug: x\ndomain: x.com\nbrand_name: X\nprimary_keyword: x\n"
    )
    deps = make_deps(project_root=tmp_path)
    r = check_vertical_yaml(deps, "x")
    assert r.status is Status.OK


def test_vertical_yaml_missing_field(tmp_path):
    (tmp_path / "configs").mkdir()
    (tmp_path / "configs" / "x.yaml").write_text("slug: x\n")
    deps = make_deps(project_root=tmp_path)
    r = check_vertical_yaml(deps, "x")
    assert r.status is Status.FAIL
    assert "name" in r.message
```

- [ ] **Step 2: Run to verify failure**

Run: `python3 -m pytest tests/test_doctor.py -v`
Expected: ImportError for `discover_verticals`.

- [ ] **Step 3: Implement**

```python
# scripts/doctor.py (append)
import sys
import yaml

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
        config = yaml.safe_load(path.read_text())
    except yaml.YAMLError as e:
        return CheckResult(Status.FAIL, f"{slug}:yaml", f"parse error: {e}", "Validate YAML at yamlchecker.com.")
    missing = [k for k in REQUIRED_YAML_FIELDS if not config.get(k)]
    if missing:
        return CheckResult(
            status=Status.FAIL,
            name=f"{slug}:yaml",
            message=f"missing required fields: {', '.join(missing)}",
            remediation="See docs/VERTICAL-PLAYBOOK.md §2 for the full yaml template.",
        )
    return CheckResult(Status.OK, f"{slug}:yaml", f"{len(config)} fields parsed", None)
```

- [ ] **Step 4: Run tests**

Run: `python3 -m pytest tests/test_doctor.py -v`
Expected: 26 passed.

- [ ] **Step 5: Commit**

```bash
git add scripts/doctor.py tests/test_doctor.py
git commit -m "feat(doctor): discover verticals and validate yaml"
```

---

## Task 7: DNS + GitHub repo checks per vertical

For each vertical, check the domain resolves (socket, no network cost) and the GitHub repo `nickedpalm/<slug>` exists.

**Files:**
- Modify: `scripts/doctor.py`
- Modify: `tests/test_doctor.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_doctor.py (add)
from scripts.doctor import check_domain_dns, check_github_repo
from unittest.mock import patch


def test_domain_dns_resolves(tmp_path):
    (tmp_path / "configs").mkdir()
    (tmp_path / "configs" / "x.yaml").write_text("slug: x\ndomain: stenoscout.com\n")
    deps = make_deps(project_root=tmp_path)
    with patch("socket.gethostbyname", return_value="172.67.1.1"):
        r = check_domain_dns(deps, "x")
    assert r.status is Status.OK


def test_domain_dns_nxdomain(tmp_path):
    import socket
    (tmp_path / "configs").mkdir()
    (tmp_path / "configs" / "x.yaml").write_text("slug: x\ndomain: nonexistent-xyz-abc.invalid\n")
    deps = make_deps(project_root=tmp_path)
    with patch("socket.gethostbyname", side_effect=socket.gaierror("nxdomain")):
        r = check_domain_dns(deps, "x")
    assert r.status is Status.FAIL
    assert "resolve" in r.message.lower() or "dns" in r.message.lower()


def test_github_repo_exists(tmp_path):
    (tmp_path / "configs").mkdir()
    (tmp_path / "configs" / "x.yaml").write_text("slug: x\ndomain: x.com\n")
    def handler(req):
        assert req.url.path == "/repos/nickedpalm/x"
        return httpx.Response(200, json={"full_name": "nickedpalm/x"})
    deps = make_deps(
        project_root=tmp_path,
        env={"GITHUB_TOKEN": "gh-abc"},
        http=mock_http(handler),
    )
    assert check_github_repo(deps, "x").status is Status.OK


def test_github_repo_missing(tmp_path):
    (tmp_path / "configs").mkdir()
    (tmp_path / "configs" / "x.yaml").write_text("slug: x\ndomain: x.com\n")
    def handler(req):
        return httpx.Response(404)
    deps = make_deps(
        project_root=tmp_path,
        env={"GITHUB_TOKEN": "gh-abc"},
        http=mock_http(handler),
    )
    r = check_github_repo(deps, "x")
    assert r.status is Status.FAIL
    assert "not found" in r.message.lower() or "404" in r.message
```

- [ ] **Step 2: Run to verify failure**

Run: `python3 -m pytest tests/test_doctor.py -v`
Expected: ImportError for `check_domain_dns`.

- [ ] **Step 3: Implement**

```python
# scripts/doctor.py (append)
import socket


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
```

- [ ] **Step 4: Run tests**

Run: `python3 -m pytest tests/test_doctor.py -v`
Expected: 30 passed.

- [ ] **Step 5: Commit**

```bash
git add scripts/doctor.py tests/test_doctor.py
git commit -m "feat(doctor): check per-vertical DNS and GitHub repo"
```

---

## Task 8: Cloudflare Pages project + last deploy status

Looks up the Pages project by name (slug) under the CF account, checks that a production deployment exists and its status is `success`.

**Files:**
- Modify: `scripts/doctor.py`
- Modify: `tests/test_doctor.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_doctor.py (add)
from scripts.doctor import check_cf_pages_project


def test_cf_pages_project_healthy(tmp_path):
    (tmp_path / "configs").mkdir()
    (tmp_path / "configs" / "x.yaml").write_text("slug: x\ndomain: x.com\n")

    def handler(req):
        if req.url.path == "/client/v4/accounts":
            return httpx.Response(200, json={"success": True, "result": [{"id": "acc-1"}]})
        if req.url.path == "/client/v4/accounts/acc-1/pages/projects/x":
            return httpx.Response(200, json={"success": True, "result": {
                "name": "x",
                "latest_deployment": {"latest_stage": {"name": "deploy", "status": "success"}},
            }})
        return httpx.Response(404)

    deps = make_deps(
        project_root=tmp_path,
        env={"CLOUDFLARE_API_TOKEN": "cf-abc"},
        http=mock_http(handler),
    )
    assert check_cf_pages_project(deps, "x").status is Status.OK


def test_cf_pages_project_missing(tmp_path):
    (tmp_path / "configs").mkdir()
    (tmp_path / "configs" / "x.yaml").write_text("slug: x\ndomain: x.com\n")

    def handler(req):
        if req.url.path == "/client/v4/accounts":
            return httpx.Response(200, json={"success": True, "result": [{"id": "acc-1"}]})
        return httpx.Response(404, json={"success": False})

    deps = make_deps(
        project_root=tmp_path,
        env={"CLOUDFLARE_API_TOKEN": "cf-abc"},
        http=mock_http(handler),
    )
    r = check_cf_pages_project(deps, "x")
    assert r.status is Status.FAIL
    assert "not found" in r.message.lower() or "404" in r.message


def test_cf_pages_project_last_deploy_failed(tmp_path):
    (tmp_path / "configs").mkdir()
    (tmp_path / "configs" / "x.yaml").write_text("slug: x\ndomain: x.com\n")

    def handler(req):
        if req.url.path == "/client/v4/accounts":
            return httpx.Response(200, json={"success": True, "result": [{"id": "acc-1"}]})
        return httpx.Response(200, json={"success": True, "result": {
            "name": "x",
            "latest_deployment": {"latest_stage": {"name": "deploy", "status": "failure"}},
        }})

    deps = make_deps(
        project_root=tmp_path,
        env={"CLOUDFLARE_API_TOKEN": "cf-abc"},
        http=mock_http(handler),
    )
    r = check_cf_pages_project(deps, "x")
    assert r.status is Status.WARN
    assert "failure" in r.message.lower()
```

- [ ] **Step 2: Run to verify failure**

Run: `python3 -m pytest tests/test_doctor.py -v`
Expected: ImportError for `check_cf_pages_project`.

- [ ] **Step 3: Implement**

```python
# scripts/doctor.py (append)
def _cf_account_id(deps: DoctorDeps) -> str | None:
    token = deps.env.get("CLOUDFLARE_API_TOKEN", "")
    if not token:
        return None
    r = deps.http.get(
        "https://api.cloudflare.com/client/v4/accounts",
        headers={"Authorization": f"Bearer {token}"},
        timeout=10,
    )
    if r.status_code != 200:
        return None
    results = r.json().get("result") or []
    return results[0]["id"] if results else None


def check_cf_pages_project(deps: DoctorDeps, slug: str) -> CheckResult:
    token = deps.env.get("CLOUDFLARE_API_TOKEN", "")
    if not token:
        return CheckResult(Status.SKIP, f"{slug}:cf-pages", "CLOUDFLARE_API_TOKEN not set", None)
    account_id = _cf_account_id(deps)
    if not account_id:
        return CheckResult(Status.FAIL, f"{slug}:cf-pages", "could not resolve CF account", None)
    try:
        r = deps.http.get(
            f"https://api.cloudflare.com/client/v4/accounts/{account_id}/pages/projects/{slug}",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10,
        )
    except httpx.HTTPError as e:
        return CheckResult(Status.FAIL, f"{slug}:cf-pages", f"network error: {e}", None)
    if r.status_code == 404:
        return CheckResult(
            status=Status.FAIL,
            name=f"{slug}:cf-pages",
            message=f"Pages project '{slug}' not found",
            remediation=f"Create at dash.cloudflare.com → Pages → Create project, name it '{slug}'.",
        )
    if r.status_code != 200:
        return CheckResult(Status.FAIL, f"{slug}:cf-pages", f"unexpected {r.status_code}", None)
    project = r.json().get("result") or {}
    latest = (project.get("latest_deployment") or {}).get("latest_stage") or {}
    status = latest.get("status", "unknown")
    if status == "success":
        return CheckResult(Status.OK, f"{slug}:cf-pages", f"last deploy: success", None)
    if status in {"failure", "canceled"}:
        return CheckResult(
            status=Status.WARN,
            name=f"{slug}:cf-pages",
            message=f"last deploy: {status}",
            remediation="Check build logs at dash.cloudflare.com → Pages → {slug} → Deployments.",
        )
    return CheckResult(Status.WARN, f"{slug}:cf-pages", f"last deploy: {status}", None)
```

- [ ] **Step 4: Run tests**

Run: `python3 -m pytest tests/test_doctor.py -v`
Expected: 33 passed.

- [ ] **Step 5: Commit**

```bash
git add scripts/doctor.py tests/test_doctor.py
git commit -m "feat(doctor): check CF Pages project existence and deploy status"
```

---

## Task 9: D1 database check from wrangler.toml

Parses `verticals/<slug>/wrangler.toml`, pulls the `[[d1_databases]]` block if present, and verifies the DB exists via CF API.

**Files:**
- Modify: `scripts/doctor.py`
- Modify: `tests/test_doctor.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_doctor.py (add)
from scripts.doctor import check_d1_database


def test_d1_database_exists(tmp_path):
    (tmp_path / "configs").mkdir()
    (tmp_path / "configs" / "x.yaml").write_text("slug: x\ndomain: x.com\n")
    vdir = tmp_path / "verticals" / "x"
    vdir.mkdir(parents=True)
    (vdir / "wrangler.toml").write_text(
        'name = "x"\n'
        'compatibility_date = "2024-09-23"\n'
        '[[d1_databases]]\n'
        'binding = "LEADS_DB"\n'
        'database_name = "x-db"\n'
        'database_id = "abc-123"\n'
    )

    def handler(req):
        if req.url.path == "/client/v4/accounts":
            return httpx.Response(200, json={"success": True, "result": [{"id": "acc-1"}]})
        if req.url.path == "/client/v4/accounts/acc-1/d1/database/abc-123":
            return httpx.Response(200, json={"success": True, "result": {"uuid": "abc-123", "name": "x-db"}})
        return httpx.Response(404)

    deps = make_deps(
        project_root=tmp_path,
        env={"CLOUDFLARE_API_TOKEN": "cf-abc"},
        http=mock_http(handler),
    )
    assert check_d1_database(deps, "x").status is Status.OK


def test_d1_database_no_wrangler(tmp_path):
    (tmp_path / "configs").mkdir()
    (tmp_path / "configs" / "x.yaml").write_text("slug: x\ndomain: x.com\n")
    (tmp_path / "verticals" / "x").mkdir(parents=True)
    deps = make_deps(project_root=tmp_path, env={"CLOUDFLARE_API_TOKEN": "cf-abc"})
    r = check_d1_database(deps, "x")
    assert r.status is Status.SKIP


def test_d1_database_missing(tmp_path):
    (tmp_path / "configs").mkdir()
    (tmp_path / "configs" / "x.yaml").write_text("slug: x\ndomain: x.com\n")
    vdir = tmp_path / "verticals" / "x"
    vdir.mkdir(parents=True)
    (vdir / "wrangler.toml").write_text(
        '[[d1_databases]]\nbinding = "LEADS_DB"\ndatabase_name = "x-db"\ndatabase_id = "bad-id"\n'
    )

    def handler(req):
        if req.url.path == "/client/v4/accounts":
            return httpx.Response(200, json={"success": True, "result": [{"id": "acc-1"}]})
        return httpx.Response(404, json={"success": False})

    deps = make_deps(
        project_root=tmp_path,
        env={"CLOUDFLARE_API_TOKEN": "cf-abc"},
        http=mock_http(handler),
    )
    r = check_d1_database(deps, "x")
    assert r.status is Status.FAIL
```

- [ ] **Step 2: Run to verify failure**

Run: `python3 -m pytest tests/test_doctor.py -v`
Expected: ImportError for `check_d1_database`.

- [ ] **Step 3: Implement**

```python
# scripts/doctor.py (append)
import tomllib


def check_d1_database(deps: DoctorDeps, slug: str) -> CheckResult:
    wrangler_path = deps.project_root / "verticals" / slug / "wrangler.toml"
    if not wrangler_path.exists():
        return CheckResult(Status.SKIP, f"{slug}:d1", "no wrangler.toml", None)
    try:
        cfg = tomllib.loads(wrangler_path.read_text())
    except tomllib.TOMLDecodeError as e:
        return CheckResult(Status.FAIL, f"{slug}:d1", f"wrangler.toml parse error: {e}", None)
    dbs = cfg.get("d1_databases") or []
    if not dbs:
        return CheckResult(Status.SKIP, f"{slug}:d1", "no [[d1_databases]] binding", None)
    token = deps.env.get("CLOUDFLARE_API_TOKEN", "")
    if not token:
        return CheckResult(Status.SKIP, f"{slug}:d1", "CLOUDFLARE_API_TOKEN not set", None)
    account_id = _cf_account_id(deps)
    if not account_id:
        return CheckResult(Status.FAIL, f"{slug}:d1", "could not resolve CF account", None)

    missing = []
    for db in dbs:
        db_id = db.get("database_id", "")
        if not db_id:
            missing.append(f"{db.get('binding', '?')}:no-id")
            continue
        r = deps.http.get(
            f"https://api.cloudflare.com/client/v4/accounts/{account_id}/d1/database/{db_id}",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10,
        )
        if r.status_code != 200:
            missing.append(f"{db.get('database_name', db_id)} ({r.status_code})")
    if missing:
        return CheckResult(
            status=Status.FAIL,
            name=f"{slug}:d1",
            message=f"D1 DBs unreachable: {', '.join(missing)}",
            remediation="Create with `wrangler d1 create <name>` and paste the ID into wrangler.toml.",
        )
    return CheckResult(Status.OK, f"{slug}:d1", f"{len(dbs)} D1 DB(s) reachable", None)
```

- [ ] **Step 4: Run tests**

Run: `python3 -m pytest tests/test_doctor.py -v`
Expected: 36 passed.

- [ ] **Step 5: Commit**

```bash
git add scripts/doctor.py tests/test_doctor.py
git commit -m "feat(doctor): check D1 databases referenced in wrangler.toml"
```

---

## Task 10: Pipeline DB integrity + listing sanity

Per-vertical `pipeline.db` (sqlite) — runs `PRAGMA integrity_check` and counts listings across cities. Warns if <3 cities with listings (site is probably broken).

**Files:**
- Modify: `scripts/doctor.py`
- Modify: `tests/test_doctor.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_doctor.py (add)
import sqlite3
from scripts.doctor import check_pipeline_db


def make_pipeline_db(path: Path, city_count: int):
    conn = sqlite3.connect(path)
    conn.execute("CREATE TABLE listings (id INTEGER PRIMARY KEY, city TEXT NOT NULL)")
    for i in range(city_count):
        conn.execute("INSERT INTO listings (city) VALUES (?)", (f"city-{i}",))
    conn.commit()
    conn.close()


def test_pipeline_db_healthy(tmp_path):
    (tmp_path / "configs").mkdir()
    (tmp_path / "configs" / "x.yaml").write_text("slug: x\n")
    vdir = tmp_path / "verticals" / "x"
    vdir.mkdir(parents=True)
    make_pipeline_db(vdir / "pipeline.db", city_count=15)
    deps = make_deps(project_root=tmp_path)
    r = check_pipeline_db(deps, "x")
    assert r.status is Status.OK
    assert "15" in r.message


def test_pipeline_db_missing(tmp_path):
    (tmp_path / "configs").mkdir()
    (tmp_path / "configs" / "x.yaml").write_text("slug: x\n")
    (tmp_path / "verticals" / "x").mkdir(parents=True)
    deps = make_deps(project_root=tmp_path)
    r = check_pipeline_db(deps, "x")
    assert r.status is Status.SKIP


def test_pipeline_db_too_few_cities(tmp_path):
    (tmp_path / "configs").mkdir()
    (tmp_path / "configs" / "x.yaml").write_text("slug: x\n")
    vdir = tmp_path / "verticals" / "x"
    vdir.mkdir(parents=True)
    make_pipeline_db(vdir / "pipeline.db", city_count=1)
    deps = make_deps(project_root=tmp_path)
    r = check_pipeline_db(deps, "x")
    assert r.status is Status.WARN
```

- [ ] **Step 2: Run to verify failure**

Run: `python3 -m pytest tests/test_doctor.py -v`
Expected: ImportError for `check_pipeline_db`.

- [ ] **Step 3: Implement**

```python
# scripts/doctor.py (append)
import sqlite3


def check_pipeline_db(deps: DoctorDeps, slug: str) -> CheckResult:
    db_path = deps.project_root / "verticals" / slug / "pipeline.db"
    if not db_path.exists():
        return CheckResult(Status.SKIP, f"{slug}:pipeline-db", "pipeline.db not present (pre-scrape)", None)
    try:
        conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
        integrity = conn.execute("PRAGMA integrity_check").fetchone()[0]
        if integrity != "ok":
            conn.close()
            return CheckResult(Status.FAIL, f"{slug}:pipeline-db", f"integrity_check: {integrity}",
                               "Re-run the scrape pipeline to regenerate.")
        try:
            count = conn.execute("SELECT COUNT(DISTINCT city) FROM listings").fetchone()[0]
        except sqlite3.OperationalError:
            count = 0
        conn.close()
    except sqlite3.DatabaseError as e:
        return CheckResult(Status.FAIL, f"{slug}:pipeline-db", f"sqlite error: {e}", None)
    if count == 0:
        return CheckResult(Status.WARN, f"{slug}:pipeline-db", "no listings in any city",
                           "Run `python3 factory.py scrape --vertical " + slug + "`.")
    if count < 3:
        return CheckResult(Status.WARN, f"{slug}:pipeline-db", f"only {count} cities with listings",
                           "Expected 20-35 cities for a healthy vertical.")
    return CheckResult(Status.OK, f"{slug}:pipeline-db", f"{count} cities with listings", None)
```

- [ ] **Step 4: Run tests**

Run: `python3 -m pytest tests/test_doctor.py -v`
Expected: 39 passed.

- [ ] **Step 5: Commit**

```bash
git add scripts/doctor.py tests/test_doctor.py
git commit -m "feat(doctor): check pipeline.db integrity and listing sanity"
```

---

## Task 11: Optional checks (Listmonk + Stripe), gated behind --optional

Listmonk and Stripe are optional per vertical. Default run skips them; `--optional` turns them on. Listmonk env vars: `LISTMONK_URL`, `LISTMONK_USERNAME`, `LISTMONK_PASSWORD` (per CLAUDE.md). Stripe: `STRIPE_SECRET_KEY` in CF Pages env, so we can only check if user has exported it locally.

**Files:**
- Modify: `scripts/doctor.py`
- Modify: `tests/test_doctor.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_doctor.py (add)
from scripts.doctor import check_listmonk, check_stripe


def test_listmonk_healthy():
    def handler(req):
        assert req.url.path == "/api/health"
        return httpx.Response(200, json={"data": True})
    deps = make_deps(
        env={"LISTMONK_URL": "https://mail.firestick.io", "LISTMONK_USERNAME": "u", "LISTMONK_PASSWORD": "p"},
        http=mock_http(handler),
    )
    assert check_listmonk(deps).status is Status.OK


def test_listmonk_not_configured():
    deps = make_deps(env={})
    assert check_listmonk(deps).status is Status.SKIP


def test_listmonk_unreachable():
    def handler(req):
        return httpx.Response(503)
    deps = make_deps(
        env={"LISTMONK_URL": "https://mail.firestick.io", "LISTMONK_USERNAME": "u", "LISTMONK_PASSWORD": "p"},
        http=mock_http(handler),
    )
    assert check_listmonk(deps).status is Status.FAIL


def test_stripe_valid():
    def handler(req):
        assert req.url.path == "/v1/balance"
        assert req.headers["authorization"] == "Bearer sk_test_abc"
        return httpx.Response(200, json={"object": "balance"})
    deps = make_deps(env={"STRIPE_SECRET_KEY": "sk_test_abc"}, http=mock_http(handler))
    assert check_stripe(deps).status is Status.OK


def test_stripe_not_configured():
    deps = make_deps(env={})
    assert check_stripe(deps).status is Status.SKIP


def test_stripe_invalid():
    def handler(req):
        return httpx.Response(401)
    deps = make_deps(env={"STRIPE_SECRET_KEY": "sk_bad"}, http=mock_http(handler))
    assert check_stripe(deps).status is Status.FAIL
```

- [ ] **Step 2: Run to verify failure**

Run: `python3 -m pytest tests/test_doctor.py -v`
Expected: ImportError for `check_listmonk`.

- [ ] **Step 3: Implement**

```python
# scripts/doctor.py (append)
def check_listmonk(deps: DoctorDeps) -> CheckResult:
    url = deps.env.get("LISTMONK_URL", "")
    user = deps.env.get("LISTMONK_USERNAME", "")
    pw = deps.env.get("LISTMONK_PASSWORD", "")
    if not (url and user and pw):
        return CheckResult(Status.SKIP, "listmonk", "LISTMONK_* not configured (optional)", None)
    try:
        r = deps.http.get(f"{url.rstrip('/')}/api/health", auth=(user, pw), timeout=10)
    except httpx.HTTPError as e:
        return CheckResult(Status.FAIL, "listmonk", f"network error: {e}", None)
    if r.status_code == 200:
        return CheckResult(Status.OK, "listmonk", "reachable", None)
    return CheckResult(
        status=Status.FAIL,
        name="listmonk",
        message=f"{r.status_code}: {r.text[:80]}",
        remediation="Verify LISTMONK_URL, LISTMONK_USERNAME, LISTMONK_PASSWORD. "
                    "v6 API users need password_login=true in DB and plaintext password.",
    )


def check_stripe(deps: DoctorDeps) -> CheckResult:
    key = deps.env.get("STRIPE_SECRET_KEY", "")
    if not key:
        return CheckResult(Status.SKIP, "stripe", "STRIPE_SECRET_KEY not set (optional)", None)
    try:
        r = deps.http.get(
            "https://api.stripe.com/v1/balance",
            headers={"Authorization": f"Bearer {key}"},
            timeout=10,
        )
    except httpx.HTTPError as e:
        return CheckResult(Status.FAIL, "stripe", f"network error: {e}", None)
    if r.status_code == 200:
        return CheckResult(Status.OK, "stripe", "key valid", None)
    return CheckResult(
        status=Status.FAIL,
        name="stripe",
        message=f"{r.status_code}: {r.text[:80]}",
        remediation="Regenerate at dashboard.stripe.com → Developers → API keys.",
    )
```

- [ ] **Step 4: Run tests**

Run: `python3 -m pytest tests/test_doctor.py -v`
Expected: 45 passed.

- [ ] **Step 5: Commit**

```bash
git add scripts/doctor.py tests/test_doctor.py
git commit -m "feat(doctor): optional Listmonk and Stripe checks"
```

---

## Task 12: Runner + formatted output

The `run()` function composes all checks, prints a color-coded table, and returns an exit code (0 = no FAILs, 1 = any FAIL). WARNs are yellow but non-blocking. SKIPs are dim.

**Files:**
- Modify: `scripts/doctor.py`
- Modify: `tests/test_doctor.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_doctor.py (add)
import io
from scripts.doctor import run_with_deps


def test_run_returns_zero_when_all_pass(tmp_path, capsys):
    (tmp_path / "configs").mkdir()
    # No verticals, no optional — only shared checks run.
    # Mock every external call to succeed.
    def handler(req):
        # CF verify
        if req.url.path == "/client/v4/user/tokens/verify":
            return httpx.Response(200, json={"success": True, "result": {"status": "active"}})
        # GitHub user
        if req.url.path == "/user":
            return httpx.Response(200, json={"login": "nickedpalm"})
        # Anthropic
        if req.url.path == "/v1/messages":
            return httpx.Response(200, json={"id": "msg_1", "content": [{"type": "text", "text": "ok"}]})
        # Perplexity
        if req.url.host == "api.perplexity.ai":
            return httpx.Response(200, json={"choices": [{"message": {"content": "hi"}}]})
        # Google Places
        if "places.googleapis.com" in req.url.host:
            return httpx.Response(200, json={"places": []})
        return httpx.Response(404)

    def run_cmd(cmd):
        versions = {
            "node": "v20.11.1\n", "python3": "Python 3.11.7\n",
            "npm": "10.2.4\n", "wrangler": "wrangler 3.78.0\n",
        }
        return subprocess.CompletedProcess(cmd, 0, stdout=versions.get(cmd[0], ""), stderr="")

    deps = DoctorDeps(
        http=mock_http(handler),
        run_cmd=run_cmd,
        env={
            "PERPLEXITY_API_KEY": "p", "ANTHROPIC_API_KEY": "a",
            "GOOGLE_MAPS_API_KEY": "g", "CLOUDFLARE_API_TOKEN": "c",
            "GITHUB_TOKEN": "gh",
        },
        project_root=tmp_path,
    )
    rc = run_with_deps(deps, verticals=None, include_optional=False)
    out = capsys.readouterr().out
    assert rc == 0
    assert "shared-env" in out
    assert "OK" in out or "ok" in out.lower()


def test_run_returns_one_on_failure(tmp_path, capsys):
    def handler(req):
        return httpx.Response(401)  # everything fails
    deps = DoctorDeps(
        http=mock_http(handler),
        run_cmd=lambda c: subprocess.CompletedProcess(c, 127, stdout="", stderr=""),
        env={},
        project_root=tmp_path,
    )
    (tmp_path / "configs").mkdir()
    rc = run_with_deps(deps, verticals=None, include_optional=False)
    assert rc == 1
```

- [ ] **Step 2: Run to verify failure**

Run: `python3 -m pytest tests/test_doctor.py -v`
Expected: ImportError for `run_with_deps`.

- [ ] **Step 3: Implement**

```python
# scripts/doctor.py (append)
import os

COLOR = {
    Status.OK: "\033[32m",   # green
    Status.FAIL: "\033[31m",  # red
    Status.WARN: "\033[33m",  # yellow
    Status.SKIP: "\033[2m",   # dim
}
RESET = "\033[0m"


def _fmt(r: CheckResult) -> str:
    color = COLOR[r.status] if os.isatty(1) else ""
    reset = RESET if os.isatty(1) else ""
    label = {Status.OK: "OK  ", Status.FAIL: "FAIL", Status.WARN: "WARN", Status.SKIP: "SKIP"}[r.status]
    line = f"{color}{label}{reset}  {r.name:<32} {r.message}"
    if r.remediation and r.status in {Status.FAIL, Status.WARN}:
        line += f"\n      → {r.remediation}"
    return line


def run_with_deps(deps: DoctorDeps, verticals: list[str] | None, include_optional: bool) -> int:
    results: list[CheckResult] = []

    # Shared checks
    results.append(check_shared_env_presence(deps))
    if deps.env.get("CLOUDFLARE_API_TOKEN"):
        results.append(check_cloudflare_token(deps))
    if deps.env.get("GITHUB_TOKEN"):
        results.append(check_github_token(deps))
    if deps.env.get("ANTHROPIC_API_KEY"):
        results.append(check_anthropic_key(deps))
    if deps.env.get("PERPLEXITY_API_KEY"):
        results.append(check_perplexity_key(deps))
    if deps.env.get("GOOGLE_MAPS_API_KEY"):
        results.append(check_google_places_key(deps))
    results.append(check_local_tooling(deps))

    # Per-vertical checks
    slugs = discover_verticals(deps, verticals[0] if verticals and len(verticals) == 1 else None) \
        if verticals else discover_verticals(deps, None)
    for slug in slugs:
        results.append(check_vertical_yaml(deps, slug))
        results.append(check_domain_dns(deps, slug))
        results.append(check_github_repo(deps, slug))
        results.append(check_cf_pages_project(deps, slug))
        results.append(check_d1_database(deps, slug))
        results.append(check_pipeline_db(deps, slug))

    # Optional
    if include_optional:
        results.append(check_listmonk(deps))
        results.append(check_stripe(deps))

    # Print
    print("\n=== Directory Factory Doctor ===\n")
    for r in results:
        print(_fmt(r))
    ok = sum(1 for r in results if r.status is Status.OK)
    fail = sum(1 for r in results if r.status is Status.FAIL)
    warn = sum(1 for r in results if r.status is Status.WARN)
    skip = sum(1 for r in results if r.status is Status.SKIP)
    print(f"\n{ok} OK · {fail} FAIL · {warn} WARN · {skip} SKIP\n")
    return 1 if fail > 0 else 0


def run(verticals: list[str] | None, include_optional: bool) -> int:
    import os
    deps = DoctorDeps(
        http=httpx.Client(),
        run_cmd=lambda cmd: subprocess.run(cmd, capture_output=True, text=True),
        env=dict(os.environ),
        project_root=Path(__file__).parent.parent,
    )
    try:
        return run_with_deps(deps, verticals, include_optional)
    finally:
        deps.http.close()
```

- [ ] **Step 4: Run tests**

Run: `python3 -m pytest tests/test_doctor.py -v`
Expected: 47 passed.

- [ ] **Step 5: Commit**

```bash
git add scripts/doctor.py tests/test_doctor.py
git commit -m "feat(doctor): runner, formatted output, exit codes"
```

---

## Task 13: Wire up `factory.py doctor` subcommand

**Files:**
- Modify: `factory.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_doctor.py (add)
def test_factory_doctor_subcommand_exists():
    result = subprocess.run(
        ["python3", "factory.py", "doctor", "--help"],
        capture_output=True, text=True, cwd=Path(__file__).parent.parent,
    )
    assert result.returncode == 0
    assert "--vertical" in result.stdout
    assert "--optional" in result.stdout
```

- [ ] **Step 2: Run to verify failure**

Run: `python3 -m pytest tests/test_doctor.py::test_factory_doctor_subcommand_exists -v`
Expected: FAIL — `doctor` subcommand doesn't exist yet.

- [ ] **Step 3: Implement**

Add to `factory.py`. First, add the command handler (near other `cmd_*` functions):

```python
def cmd_doctor(args):
    from scripts.doctor import run as doctor_run
    verticals = [args.vertical] if args.vertical else None
    sys.exit(doctor_run(verticals=verticals, include_optional=args.optional))
```

Then add to the argparse setup (in `main()` or wherever subparsers are defined — match existing style):

```python
    p_doctor = subparsers.add_parser("doctor", help="Run health checks against env, APIs, and verticals.")
    p_doctor.add_argument("--vertical", help="Check only this vertical slug (default: all).")
    p_doctor.add_argument("--optional", action="store_true", help="Also run optional checks (Listmonk, Stripe).")
    p_doctor.set_defaults(func=cmd_doctor)
```

- [ ] **Step 4: Run the test**

Run: `python3 -m pytest tests/test_doctor.py::test_factory_doctor_subcommand_exists -v`
Expected: PASS.

Also smoke-test manually:

```bash
cd ~/tools/directory-factory
source .venv/bin/activate
python3 factory.py doctor --help
python3 factory.py doctor --vertical court-reporters
```

Expected: help text matches, then real doctor runs against the live env and produces a color-coded report.

- [ ] **Step 5: Commit**

```bash
git add factory.py tests/test_doctor.py
git commit -m "feat(doctor): add `factory.py doctor` subcommand"
```

---

## Task 14: Documentation

**Files:**
- Modify: `CLAUDE.md`
- Modify: `README.md`

- [ ] **Step 1: Update `CLAUDE.md` Key Commands section**

Add this line under the existing commands:

```
python3 factory.py doctor [--vertical <slug>] [--optional]  # health check, read-only
```

Add a new section after Env Vars:

```markdown
## Doctor

`factory.py doctor` runs ~15 read-only health checks: env var presence, live API validation (CF, GitHub, Anthropic, Perplexity, Google Places), local tooling versions, and per-vertical DNS / GitHub repo / CF Pages / D1 / pipeline.db state. Exit 0 if healthy, 1 if any blocking FAIL.

Cost per full run: ~$0.001 (one 1-token Anthropic + one 1-token Perplexity + one free Places search).

Use `--optional` to also check Listmonk and Stripe.
```

- [ ] **Step 2: Update `README.md`**

Add a section:

```markdown
## Health Check

Before deploying, verify your environment is sane:

    python3 factory.py doctor

This validates all required API keys, local tooling, DNS records, Cloudflare resources, and per-vertical state. See `scripts/doctor.py` for the full check list.
```

- [ ] **Step 3: Commit**

```bash
git add CLAUDE.md README.md
git commit -m "docs(doctor): document doctor command and exit codes"
```

---

## Task 15: End-to-end verification

Run doctor against the live environment, fix anything it flags, then verify a clean run.

- [ ] **Step 1: Run doctor against all verticals**

```bash
cd ~/tools/directory-factory
source .venv/bin/activate
python3 factory.py doctor
```

- [ ] **Step 2: Review output**

Expected: every shared-env check passes, local tooling passes, per-vertical checks show current state honestly. Any FAIL is a real problem to investigate (not a bug in doctor).

- [ ] **Step 3: Fix findings or document as known issues**

For each FAIL: either remediate (regenerate key, create missing resource) or open a GitHub issue on the vertical's repo describing the gap.

- [ ] **Step 4: Re-run to confirm green**

```bash
python3 factory.py doctor
echo "exit code: $?"
```

Expected: `exit code: 0`, no FAIL in output.

- [ ] **Step 5: Run with --optional to stress-test**

```bash
python3 factory.py doctor --optional
```

Expected: Listmonk and Stripe checks either pass or SKIP cleanly; no crashes.

No commit for this task — it's verification of the real environment, not code changes.

---

## Self-Review Notes

**Spec coverage (checked against conversation):**
- ✓ API key validation (all 5 shared)
- ✓ DNS resolution
- ✓ CF Pages project health
- ✓ D1 database existence
- ✓ GitHub repo presence
- ✓ Pipeline DB integrity + listing sanity
- ✓ Local tooling versions
- ✓ Optional Listmonk/Stripe (gated)
- ✓ Exit code contract
- ✓ Cost disclosure
- ✗ **Not yet covered** (deferred to future plans): CF Web Analytics script injection, GSC verification state, email routing MX check, SES domain verification status, sitemap ping state. These belong in the post-deploy hooks plan (plan #5 in the roadmap).

**Placeholder scan:** No "TBD", no "similar to Task N", no "add validation", every code block complete.

**Type consistency:** `CheckResult`, `DoctorDeps`, `Status` used consistently across all 15 tasks. `check_*` naming convention uniform. `deps.env`, `deps.http`, `deps.run_cmd`, `deps.project_root` referenced identically everywhere. `_cf_account_id` defined in Task 8, reused in Task 9.
