"""Exercise the data-only automatic-merge boundary without GitHub writes."""

from __future__ import annotations

import json
import os
import subprocess
import sys

import pytest
from test_refresh_workflow import ROOT, _run, _script


def _pr(**changes):
    pr = {"state": "OPEN", "author": {"login": "app/github-actions"},
          "baseRefName": "main", "headRefName": "data/refresh-test", "headRefOid": "abc123",
          "isCrossRepository": False, "files": [{"path": "data/RELEASE"}],
          "url": "https://github.com/example/repo/pull/71"}
    return {**pr, **changes}


def _check(pr, tmp_path, monkeypatch, sha="abc123"):
    gh = tmp_path / "gh"
    gh.write_text("#!/usr/bin/env python3\nprint(" + repr(json.dumps(pr)) + ")\n")
    gh.chmod(0o755)
    monkeypatch.setenv("PATH", str(tmp_path) + os.pathsep + os.environ["PATH"])
    return subprocess.run([sys.executable, str(ROOT / "scripts/check_data_pr.py"),
                           "data/refresh-test", sha], capture_output=True, text=True)


def test_only_verified_data_pr_can_be_automatically_merged(tmp_path, monkeypatch):
    result = _check(_pr(), tmp_path, monkeypatch)
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "https://github.com/example/repo/pull/71"


@pytest.mark.parametrize("changes", [
    {"state": "CLOSED"}, {"state": "MERGED"}, {"isCrossRepository": True},
    {"baseRefName": "other"}, {"headRefName": "feature/test"},
    {"author": {"login": "someone-else"}}, {"files": []},
    {"files": [{"path": "data/RELEASE"}, {"path": "pipeline/cli.py"}]},
    {"files": [{"path": ".github/workflows/catalogue.yml"}]}, {"headRefOid": "new-head"},
])
def test_code_forks_or_untested_heads_cannot_auto_merge(tmp_path, monkeypatch, changes):
    result = _check(_pr(**changes), tmp_path, monkeypatch)
    assert result.returncode != 0 and "Refusing automation" in result.stderr


def test_existing_data_pr_is_updated_and_checks_dispatched(tmp_path, monkeypatch):
    (tmp_path / "scripts").mkdir()
    (tmp_path / "scripts/check_data_pr.py").write_text("print('https://example.com/pull/71')\n")
    monkeypatch.setenv("GITHUB_OUTPUT", str(tmp_path / "output"))
    result = _run(_script("Is a data PR already open?"), tmp_path, monkeypatch,
                  """import json, pathlib, sys
args = sys.argv[1:]
with pathlib.Path('commands').open('a') as out:
    out.write(json.dumps(args) + '\\n')
if args[:2] == ['pr', 'list']:
    print('data/refresh-test')
""")
    assert result.returncode == 0, result.stderr
    commands = [json.loads(line) for line in (tmp_path / "commands").read_text().splitlines()]
    assert ["pr", "update-branch", "data/refresh-test"] in commands
    assert ["workflow", "run", "data-release-check.yml", "--ref", "data/refresh-test"] in commands
    assert "pr_open=true" in (tmp_path / "output").read_text()


def test_merge_matches_tested_head_without_admin_bypass(tmp_path, monkeypatch):
    (tmp_path / "scripts").mkdir()
    (tmp_path / "scripts/check_data_pr.py").write_text("print('https://example.com/pull/71')\n")
    monkeypatch.setenv("PR_REF", "data/refresh-test")
    monkeypatch.setenv("HEAD_SHA", "tested-head")
    body = _script("Merge the tested data PR", ROOT / ".github/workflows/data-release-check.yml")
    result = _run(body, tmp_path, monkeypatch, """import json, pathlib, sys
pathlib.Path('command').write_text(json.dumps(sys.argv[1:]))
""")
    assert result.returncode == 0, result.stderr
    assert json.loads((tmp_path / "command").read_text()) == [
        "pr", "merge", "https://example.com/pull/71", "--merge",
        "--match-head-commit", "tested-head",
    ]


@pytest.mark.parametrize("outcome", ["success", "failure"])
def test_dispatched_validation_reports_required_check_through_api(tmp_path, monkeypatch, outcome):
    workflow = ROOT / ".github/workflows/data-release-check.yml"
    monkeypatch.setenv("GITHUB_REPOSITORY", "example/repo")
    monkeypatch.setenv("HEAD_SHA", "tested-head")
    monkeypatch.setenv("RUN_URL", "https://example.com/run/123")
    monkeypatch.setenv("GITHUB_OUTPUT", str(tmp_path / "output"))
    fake = """import json, pathlib, sys
with pathlib.Path('commands').open('a') as out:
    out.write(json.dumps(sys.argv[1:]) + '\\n')
print('314')
"""
    started = _run(_script("Start required data check", workflow), tmp_path, monkeypatch, fake)
    assert started.returncode == 0, started.stderr
    assert "id=314" in (tmp_path / "output").read_text()
    monkeypatch.setenv("CHECK_ID", "314")
    monkeypatch.setenv("OUTCOME", outcome)
    completed = _run(_script("Complete required data check", workflow), tmp_path, monkeypatch, fake)
    assert completed.returncode == 0, completed.stderr
    commands = [json.loads(line) for line in (tmp_path / "commands").read_text().splitlines()]
    assert commands[0][:4] == ["api", "--method", "POST", "repos/example/repo/check-runs"]
    assert "head_sha=tested-head" in commands[0]
    assert "name=data/RELEASE names a fetchable release" in commands[0]
    assert "status=in_progress" in commands[0]
    assert commands[1][:4] == ["api", "--method", "PATCH", "repos/example/repo/check-runs/314"]
    assert "status=completed" in commands[1] and f"conclusion={outcome}" in commands[1]
