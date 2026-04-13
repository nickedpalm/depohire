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
