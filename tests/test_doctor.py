from pathlib import Path
import sqlite3
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
    check_cf_pages_project,
    check_d1_database,
    check_pipeline_db,
    check_listmonk,
    check_stripe,
    run_with_deps,
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


def make_pipeline_db(path, city_count: int):
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


def test_run_returns_zero_when_all_pass(tmp_path, capsys):
    def handler(req):
        if req.url.path == "/client/v4/user/tokens/verify":
            return httpx.Response(200, json={"success": True, "result": {"status": "active"}})
        if req.url.path == "/user":
            return httpx.Response(200, json={"login": "nickedpalm"})
        if req.url.path == "/v1/messages":
            return httpx.Response(200, json={"id": "msg_1", "content": [{"type": "text", "text": "ok"}]})
        if req.url.host == "api.perplexity.ai":
            return httpx.Response(200, json={"choices": [{"message": {"content": "hi"}}]})
        if "places.googleapis.com" in req.url.host:
            return httpx.Response(200, json={"places": []})
        return httpx.Response(404)

    def run_cmd(cmd):
        versions = {
            "node": "v20.11.1\n", "python3": "Python 3.11.7\n",
            "npm": "10.2.4\n", "wrangler": "wrangler 3.78.0\n",
        }
        return subprocess.CompletedProcess(cmd, 0, stdout=versions.get(cmd[0], ""), stderr="")

    # No configs directory → discover_verticals returns empty list
    (tmp_path / "configs").mkdir()
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


def test_run_returns_one_on_failure(tmp_path, capsys):
    def handler(req):
        return httpx.Response(401)  # everything fails
    deps = DoctorDeps(
        http=mock_http(handler),
        run_cmd=lambda c: subprocess.CompletedProcess(c, 127, stdout="", stderr=""),
        env={},  # all env missing → shared-env check fails
        project_root=tmp_path,
    )
    (tmp_path / "configs").mkdir()
    rc = run_with_deps(deps, verticals=None, include_optional=False)
    assert rc == 1


def test_run_google_places_gated_by_optional(tmp_path, capsys):
    """Google Places live probe should NOT run unless --optional is passed."""
    places_calls = []

    def handler(req):
        if "places.googleapis.com" in req.url.host:
            places_calls.append(req)
            return httpx.Response(200, json={"places": []})
        if req.url.path == "/client/v4/user/tokens/verify":
            return httpx.Response(200, json={"success": True, "result": {"status": "active"}})
        if req.url.path == "/user":
            return httpx.Response(200, json={"login": "nickedpalm"})
        if req.url.path == "/v1/messages":
            return httpx.Response(200, json={"id": "msg_1", "content": [{"type": "text", "text": "ok"}]})
        if req.url.host == "api.perplexity.ai":
            return httpx.Response(200, json={"choices": [{"message": {"content": "hi"}}]})
        return httpx.Response(404)

    def run_cmd(cmd):
        versions = {"node": "v20.0.0\n", "python3": "Python 3.11.0\n", "npm": "10.0.0\n", "wrangler": "wrangler 3.0.0\n"}
        return subprocess.CompletedProcess(cmd, 0, stdout=versions.get(cmd[0], ""), stderr="")

    (tmp_path / "configs").mkdir()
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
    # Without --optional
    run_with_deps(deps, verticals=None, include_optional=False)
    assert len(places_calls) == 0, "Google Places must not be probed without --optional"
    # With --optional
    run_with_deps(deps, verticals=None, include_optional=True)
    assert len(places_calls) == 1, "Google Places should be probed once when --optional is set"
