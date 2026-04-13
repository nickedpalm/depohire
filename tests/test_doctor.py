from pathlib import Path
import subprocess
import httpx
import pytest
from unittest.mock import patch
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
    discover_verticals,
    check_vertical_yaml,
    check_domain_dns,
    check_github_repo,
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


def test_vertical_yaml_file_missing(tmp_path):
    (tmp_path / "configs").mkdir()
    deps = make_deps(project_root=tmp_path)
    r = check_vertical_yaml(deps, "ghost")
    assert r.status is Status.FAIL
    assert "not found" in r.message.lower()


def test_vertical_yaml_empty_file(tmp_path):
    (tmp_path / "configs").mkdir()
    (tmp_path / "configs" / "e.yaml").write_text("")
    deps = make_deps(project_root=tmp_path)
    r = check_vertical_yaml(deps, "e")
    assert r.status is Status.FAIL
    assert "empty" in r.message.lower() or "mapping" in r.message.lower()


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
