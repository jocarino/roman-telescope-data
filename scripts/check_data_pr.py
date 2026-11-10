"""Allow automation only for an open, same-repository bot PR changing the data pin."""

from __future__ import annotations

import json
import subprocess
import sys


def main() -> None:
    fields = "state,author,baseRefName,headRefName,headRefOid,isCrossRepository,files,url"
    pr = json.loads(subprocess.check_output(
        ["gh", "pr", "view", sys.argv[1], "--json", fields], text=True,
    ))
    if not (
        pr["state"] == "OPEN" and pr["author"]["login"] == "app/github-actions"
        and pr["baseRefName"] == "main" and pr["isCrossRepository"] is False
        and pr["headRefName"].startswith("data/refresh-")
        and [f["path"] for f in pr["files"]] == ["data/RELEASE"]
    ):
        sys.exit("Refusing automation: expected an open bot PR changing only data/RELEASE.")
    if len(sys.argv) > 2 and pr["headRefOid"] != sys.argv[2]:
        sys.exit("Refusing automation: the PR head no longer matches the tested commit.")
    print(pr["url"])


if __name__ == "__main__":
    main()
