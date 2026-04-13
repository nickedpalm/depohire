from pathlib import Path
import httpx
from scripts.doctor import CheckResult, DoctorDeps, Status, check_shared_env_presence


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
