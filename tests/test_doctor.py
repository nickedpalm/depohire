from pathlib import Path
import subprocess
import httpx
from scripts.doctor import (
    CheckResult,
    DoctorDeps,
    Status,
    check_shared_env_presence,
    check_cloudflare_token,
    check_github_token,
    check_anthropic_key,
    check_perplexity_key,
    check_google_places_key,
    check_local_tooling,
)


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


def test_github_token_missing():
    deps = make_deps(env={})
    r = check_github_token(deps)
    assert r.status is Status.FAIL
    assert "not set" in r.message.lower()


def test_cloudflare_token_network_error():
    def handler(req):
        raise httpx.ConnectError("boom")
    deps = make_deps(env={"CLOUDFLARE_API_TOKEN": "cf-abc"}, http=mock_http(handler))
    r = check_cloudflare_token(deps)
    assert r.status is Status.FAIL
    assert "network error" in r.message.lower()


def test_github_token_network_error():
    def handler(req):
        raise httpx.ConnectError("boom")
    deps = make_deps(env={"GITHUB_TOKEN": "gh-abc"}, http=mock_http(handler))
    r = check_github_token(deps)
    assert r.status is Status.FAIL
    assert "network error" in r.message.lower()


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


def test_anthropic_key_missing():
    deps = make_deps(env={})
    r = check_anthropic_key(deps)
    assert r.status is Status.FAIL
    assert "not set" in r.message.lower()


def test_anthropic_key_network_error():
    def handler(req):
        raise httpx.ConnectError("boom")
    deps = make_deps(env={"ANTHROPIC_API_KEY": "sk-ant-abc"}, http=mock_http(handler))
    r = check_anthropic_key(deps)
    assert r.status is Status.FAIL
    assert "network error" in r.message.lower()


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


def test_perplexity_key_missing():
    deps = make_deps(env={})
    r = check_perplexity_key(deps)
    assert r.status is Status.FAIL
    assert "not set" in r.message.lower()


def test_perplexity_key_network_error():
    def handler(req):
        raise httpx.ConnectError("boom")
    deps = make_deps(env={"PERPLEXITY_API_KEY": "p-abc"}, http=mock_http(handler))
    r = check_perplexity_key(deps)
    assert r.status is Status.FAIL
    assert "network error" in r.message.lower()


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


def test_google_places_key_missing():
    deps = make_deps(env={})
    r = check_google_places_key(deps)
    assert r.status is Status.FAIL
    assert "not set" in r.message.lower()


def test_google_places_key_network_error():
    def handler(req):
        raise httpx.ConnectError("boom")
    deps = make_deps(env={"GOOGLE_MAPS_API_KEY": "g-abc"}, http=mock_http(handler))
    r = check_google_places_key(deps)
    assert r.status is Status.FAIL
    assert "network error" in r.message.lower()


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
