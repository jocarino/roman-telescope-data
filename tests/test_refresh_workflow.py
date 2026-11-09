"""Run refresh workflow shell steps against fake GitHub/Telegram boundaries."""

from __future__ import annotations

import io
import json
import os
import subprocess
from pathlib import Path
from textwrap import dedent
from urllib.error import HTTPError

import pytest

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github/workflows/catalogue.yml"


def _script(step_prefix, workflow=WORKFLOW):
    text = workflow.read_text()
    section = next(s for s in text.split("      - name: ")[1:] if s.startswith(step_prefix))
    body = []
    for line in section.split("        run: |\n", 1)[1].splitlines():
        if line.strip() and not line.startswith("          "):
            break
        body.append(line)
    return dedent("\n".join(body))


def _run(script, tmp_path, monkeypatch, gh_body):
    gh = tmp_path / "gh"
    gh.write_text("#!/usr/bin/env python3\n" + gh_body)
    gh.chmod(0o755)
    monkeypatch.setenv("PATH", str(tmp_path) + os.pathsep + os.environ["PATH"])
    monkeypatch.setenv("GITHUB_ENV", str(tmp_path / "env"))
    (tmp_path / "data").mkdir(exist_ok=True)
    (tmp_path / "data/RELEASE").write_text("data-pinned\n")
    return subprocess.run(["bash", "-e", "-o", "pipefail", "-c", script],
                          cwd=tmp_path, capture_output=True, text=True)


@pytest.mark.parametrize("step,directory", [
    ("Fetch the baseline manifest", "baseline"),
    ("Fetch the previous release", "prev"),
])
def test_workflow_downloads_deployed_pin_not_unapproved_latest(
    tmp_path, monkeypatch, step, directory,
):
    result = _run(_script(step), tmp_path, monkeypatch, """import json, pathlib, sys
args = sys.argv[1:]
tag = args[2]
directory = pathlib.Path(args[args.index('--dir') + 1])
directory.mkdir(exist_ok=True)
name = args[args.index('--pattern') + 1]
(directory / name).write_text(json.dumps({'selected': tag}))
""")
    assert result.returncode == 0, result.stderr
    assert json.loads((tmp_path / directory / "manifest.json").read_text()) == {
        "selected": "data-pinned",
    }


@pytest.mark.parametrize("step", ["Fetch the baseline manifest", "Fetch the previous release"])
def test_workflow_aborts_when_baseline_download_fails(tmp_path, monkeypatch, step):
    result = _run(_script(step), tmp_path, monkeypatch, "raise SystemExit(1)\n")
    assert result.returncode != 0


def test_missing_manifest_cannot_disable_shrink_guard(tmp_path, monkeypatch):
    (tmp_path / "data").mkdir()
    (tmp_path / "data/planets.json").write_text(json.dumps({"planets": [{}, {}]}))
    result = _run(_script("Sanity gate"), tmp_path, monkeypatch, "raise SystemExit(1)\n")
    assert result.returncode != 0


@pytest.mark.parametrize("count,accepted", [(0, False), (98, False), (99, True), (100, True)])
def test_shrink_guard_boundary(tmp_path, monkeypatch, count, accepted):
    (tmp_path / "data").mkdir()
    (tmp_path / "data/planets.json").write_text(json.dumps({"planets": [{}] * count}))
    (tmp_path / "prev").mkdir()
    (tmp_path / "prev/manifest.json").write_text(json.dumps({"catalogue": {"planets": 100}}))
    result = _run(_script("Sanity gate"), tmp_path, monkeypatch, "raise SystemExit(1)\n")
    assert (result.returncode == 0) is accepted


def test_probe_failure_has_an_actionable_notification_step(tmp_path, monkeypatch):
    script = _script("Alert on probe failure")
    (tmp_path / "scripts").mkdir()
    (tmp_path / "scripts/send_telegram.py").write_text(
        "import pathlib, sys\npathlib.Path('message').write_text(sys.stdin.read())\n"
    )
    monkeypatch.setenv("RUN_URL", "https://github.com/example/repo/actions/runs/123")
    result = _run(script, tmp_path, monkeypatch, "raise SystemExit(1)\n")
    assert result.returncode == 0, result.stderr
    message = (tmp_path / "message").read_text()
    assert "probe" in message.lower() and "failed" in message.lower()
    assert "https://github.com/example/repo/actions/runs/123" in message


@pytest.mark.parametrize("response", [{"ok": False, "description": "Bad Request"}, {}])
def test_telegram_rejection_never_logs_delivery(monkeypatch, capsys, response):
    from scripts import send_telegram

    monkeypatch.setenv("TG_TOKEN", "test-token")
    monkeypatch.setenv("TG_CHAT", "test-chat")
    monkeypatch.setattr("sys.stdin", io.StringIO("Test message"))
    monkeypatch.setattr(send_telegram.urllib.request, "urlopen",
                        lambda *a, **kw: io.BytesIO(json.dumps(response).encode()))
    with pytest.raises(SystemExit):
        send_telegram.main()
    assert "Pinged" not in capsys.readouterr().out


def test_telegram_http_error_does_not_leak_token(monkeypatch, capsys):
    from scripts import send_telegram

    monkeypatch.setenv("TG_TOKEN", "private-test-token")
    monkeypatch.setenv("TG_CHAT", "test-chat")
    monkeypatch.setattr("sys.stdin", io.StringIO("Test message"))

    def reject(request, **kwargs):
        raise HTTPError(request.full_url, 400, "Bad Request", {}, None)

    monkeypatch.setattr(send_telegram.urllib.request, "urlopen", reject)
    with pytest.raises(SystemExit) as exc:
        send_telegram.main()
    output = capsys.readouterr()
    assert "private-test-token" not in str(exc.value) + output.out + output.err
    assert "Pinged" not in output.out


def test_telegram_success_requires_api_confirmation(monkeypatch, capsys):
    from scripts import send_telegram

    monkeypatch.setenv("TG_TOKEN", "test-token")
    monkeypatch.setenv("TG_CHAT", "test-chat")
    monkeypatch.setattr("sys.stdin", io.StringIO("Test message"))
    monkeypatch.setattr(send_telegram.urllib.request, "urlopen",
                        lambda *a, **kw: io.BytesIO(b'{"ok":true,"result":{"message_id":1}}'))
    send_telegram.main()
    assert "Pinged Telegram." in capsys.readouterr().out


def test_missing_telegram_credentials_never_claim_delivery(monkeypatch, capsys):
    from scripts import send_telegram

    monkeypatch.delenv("TG_TOKEN", raising=False)
    monkeypatch.delenv("TG_CHAT", raising=False)
    send_telegram.main()
    output = capsys.readouterr().out
    assert "no ping sent" in output and "Pinged" not in output


@pytest.mark.parametrize("workflow,outcome,expected", [
    (WORKFLOW, "success", "ready to approve"),
    (WORKFLOW, "failure", "Refresh did not complete"),
    (ROOT / ".github/workflows/data-release-check.yml", "failure", "Do not merge #71"),
])
def test_workflow_message_reaches_validated_sender(
    tmp_path, monkeypatch, workflow, outcome, expected,
):
    (tmp_path / "scripts").mkdir()
    (tmp_path / "scripts/send_telegram.py").write_text(
        "import pathlib, sys\npathlib.Path('message').write_text(sys.stdin.read())\n"
    )
    for key, value in {"OUTCOME": outcome, "TAG": "data-test", "HEADLINE": "New planets",
                       "MOVED": "Changed colours", "PR_URL": "https://example.com/pull/71",
                       "RUN_URL": "https://example.com/run/123", "PR_NUM": "71",
                       "PR_TITLE": "Data update", "REASON": "Download failed"}.items():
        monkeypatch.setenv(key, value)
    result = _run(
        _script("Tell Telegram", workflow), tmp_path, monkeypatch, "raise SystemExit(1)\n",
    )
    assert result.returncode == 0, result.stderr
    assert expected in (tmp_path / "message").read_text()
