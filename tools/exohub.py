#!/usr/bin/env python3
"""exohub — see, label, and run the per-worktree preview servers in one place.

The problem this solves: several Claude Code sessions each `python -m http.server`
their own `dist/` on whatever port, and you can't tell which port is which
worktree. exohub gives every worktree a *stable* port, stamps a branch badge onto
every served page (so the browser itself tells you which one you're looking at),
and shows a live table of what's running.

Subcommands
    serve   Serve this worktree's dist/ on its stable port, badge injected.
    dash    Print a live table of every preview server now listening.
    ports   Print the stable port for every worktree (what serve would pick).
    mprocs  Write mprocs.yaml (one labelled serve pane per worktree) and run it.

No third-party deps — stdlib only, so it runs under any of the repo venvs or bare
python3.
"""
from __future__ import annotations

import argparse
import http.server
import io
import os
import re
import subprocess
import sys
import zlib
from dataclasses import dataclass
from pathlib import Path
from shutil import which

# --- port policy -----------------------------------------------------------
# main always gets the README's canonical port; every other worktree hashes its
# branch name into a stable slot so a given worktree keeps its port run to run.
MAIN_PORT = 8799
POOL_START = 8800
POOL_SIZE = 90  # 8800..8889


@dataclass
class Worktree:
    path: Path
    branch: str

    @property
    def label(self) -> str:
        # "worktree-planet-render-controls" -> "planet-render-controls"; "main" stays "main"
        return re.sub(r"^worktree-", "", self.branch)


def _run(cmd: list[str], cwd: Path | None = None) -> str:
    return subprocess.run(
        cmd, cwd=cwd, capture_output=True, text=True, check=True
    ).stdout


def repo_root() -> Path:
    out = _run(["git", "rev-parse", "--path-format=absolute", "--git-common-dir"])
    # git-common-dir points at the shared .git; its parent is the main checkout
    return Path(out.strip()).parent


def worktrees() -> list[Worktree]:
    """Every worktree, main first, then the rest sorted by branch for stability."""
    out = _run(["git", "worktree", "list", "--porcelain"], cwd=repo_root())
    trees: list[Worktree] = []
    path: Path | None = None
    for line in out.splitlines():
        if line.startswith("worktree "):
            path = Path(line[len("worktree ") :])
        elif line.startswith("branch "):
            branch = line[len("branch ") :].replace("refs/heads/", "")
            if path is not None:
                trees.append(Worktree(path, branch))
                path = None
        elif line.startswith("detached") and path is not None:
            trees.append(Worktree(path, "detached"))
            path = None
    main = [t for t in trees if t.branch in ("main", "master")]
    rest = sorted((t for t in trees if t not in main), key=lambda t: t.branch)
    return main + rest


def port_for(branch: str, taken: set[int]) -> int:
    if branch in ("main", "master"):
        return MAIN_PORT
    base = POOL_START + (zlib.crc32(branch.encode()) % POOL_SIZE)
    port = base
    while port in taken:  # deterministic linear probe on the rare hash collision
        port = POOL_START + ((port - POOL_START + 1) % POOL_SIZE)
    return port


def assign_ports() -> dict[str, int]:
    """branch -> stable port, resolving collisions deterministically."""
    taken: set[int] = set()
    out: dict[str, int] = {}
    for t in worktrees():
        p = port_for(t.branch, taken)
        taken.add(p)
        out[t.branch] = p
    return out


# --- live scan -------------------------------------------------------------
def _listening() -> list[tuple[int, int]]:
    """(pid, port) for every LISTENing TCP socket owned by this user."""
    try:
        out = subprocess.run(
            ["lsof", "-nP", "-iTCP", "-sTCP:LISTEN", "-Fpn"],
            capture_output=True, text=True, check=False,
        ).stdout
    except FileNotFoundError:
        return []
    rows: list[tuple[int, int]] = []
    pid = 0
    for line in out.splitlines():
        if line.startswith("p"):
            pid = int(line[1:])
        elif line.startswith("n"):
            m = re.search(r":(\d+)$", line)
            if m:
                rows.append((pid, int(m.group(1))))
    return rows


def _cwd_of(pid: int) -> Path | None:
    out = subprocess.run(
        ["lsof", "-a", "-p", str(pid), "-d", "cwd", "-Fn"],
        capture_output=True, text=True, check=False,
    ).stdout
    for line in out.splitlines():
        if line.startswith("n"):
            return Path(line[1:])
    return None


def live_servers() -> list[dict]:
    """Preview servers currently up, matched back to their worktree."""
    trees = worktrees()
    dists = {t.path.resolve() / "dist": t for t in trees}
    roots = {t.path.resolve(): t for t in trees}
    found: list[dict] = []
    seen: set[int] = set()
    for pid, port in _listening():
        if port in seen:
            continue
        cwd = _cwd_of(pid)
        if cwd is None:
            continue
        cwd = cwd.resolve()
        tree = dists.get(cwd) or roots.get(cwd) or roots.get(cwd.parent)
        if tree is None:
            continue
        seen.add(port)
        found.append({"port": port, "pid": pid, "tree": tree})
    return sorted(found, key=lambda r: r["port"])


# --- serve -----------------------------------------------------------------
BADGE_TMPL = (
    '<div id="__exohub_badge" style="position:fixed;left:8px;bottom:8px;'
    "z-index:2147483647;font:600 11px/1.4 ui-monospace,SFMono-Regular,Menlo,"
    "monospace;color:#0b0b0b;background:{color};padding:4px 8px;"
    "border:2px solid #0b0b0b;box-shadow:3px 3px 0 rgba(0,0,0,.55);"
    'letter-spacing:.04em;user-select:none;cursor:pointer" '
    'title="worktree / branch of this preview — click to hide" '
    "onclick=\"this.remove()\">▟ {label} :{port}</div>"
)

# accent per label so two open tabs never look alike (retro palette)
_BADGE_COLORS = ["#7cf5c8", "#8fd0ff", "#ffd166", "#ff8fab", "#c9a7ff", "#a0f0a0"]


def _color(label: str) -> str:
    return _BADGE_COLORS[zlib.crc32(label.encode()) % len(_BADGE_COLORS)]


def _badge(label: str, port: int) -> bytes:
    return BADGE_TMPL.format(color=_color(label), label=label, port=port).encode()


def make_handler(directory: Path, label: str, port: int):
    badge = _badge(label, port)

    class Handler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *a, **kw):
            super().__init__(*a, directory=str(directory), **kw)

        def log_message(self, fmt, *args):  # concise one-liner per request
            sys.stderr.write(f"[{label}] {self.address_string()} {fmt % args}\n")

        def send_head(self):
            path = self.translate_path(self.path)
            # Clean URLs: /foo -> /foo.html, /foo -> /foo/index.html. Mirrors the production
            # nginx `try_files $uri $uri.html $uri/index.html` so local preview matches deploy.
            if not os.path.exists(path):
                if os.path.isfile(path + ".html"):
                    return self._serve_html(path + ".html")
                idx = os.path.join(path, "index.html")
                if os.path.isfile(idx):
                    return self._serve_html(idx)
            if os.path.isdir(path):
                for idx in ("index.html", "index.htm"):
                    if os.path.exists(os.path.join(path, idx)):
                        path = os.path.join(path, idx)
                        break
            if path.endswith((".html", ".htm")) and os.path.isfile(path):
                return self._serve_html(path)
            return super().send_head()

        def _serve_html(self, path: str):
            try:
                body = Path(path).read_bytes()
            except OSError:
                self.send_error(404)
                return None
            if b"</body>" in body:
                body = body.replace(b"</body>", badge + b"</body>", 1)
            else:
                body += badge
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            if self.command == "HEAD":
                return None
            return io.BytesIO(body)

    return Handler


def _tree_for_cwd() -> Worktree | None:
    here = Path.cwd().resolve()
    trees = worktrees()
    exact = next((t for t in trees if t.path.resolve() == here), None)
    if exact:
        return exact
    # nested somewhere under a worktree: pick the longest matching root
    candidates = [t for t in trees if str(here).startswith(str(t.path.resolve()))]
    return max(candidates, key=lambda t: len(str(t.path)), default=None)


def cmd_serve(args) -> int:
    tree = _tree_for_cwd()
    if tree is None:
        here = Path.cwd().resolve()
        print("! not inside a known git worktree; serving cwd with no label",
              file=sys.stderr)
        label, branch, root = here.name, "", here
    else:
        label, branch, root = tree.label, tree.branch, tree.path

    port = args.port or (assign_ports().get(branch) if branch else None) or MAIN_PORT
    dist = root / "dist"

    if args.build:
        print(f"[{label}] building dist/ …", file=sys.stderr)
        subprocess.run([sys.executable, "-m", "web.build", "--out", "dist"],
                       cwd=root, check=True)
    if not dist.is_dir():
        print(f"! {dist} does not exist — run with --build first", file=sys.stderr)
        return 1

    handler = make_handler(dist, label, port)
    try:
        httpd = http.server.ThreadingHTTPServer(("", port), handler)
    except OSError as e:
        print(f"! port {port} busy ({e}). Already serving {label}? Try "
              f"`python tools/exohub.py dash`.", file=sys.stderr)
        return 1
    bar = "─" * 46
    print(f"\n┌{bar}┐")
    print(f"│  ▟ EXOHUB  {label:<32}│")
    print(f"│    http://localhost:{port:<25}│")
    print(f"│    serving {str(dist):<30.30}│")
    print(f"└{bar}┘  (Ctrl-C to stop)\n")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print(f"\n[{label}] stopped.", file=sys.stderr)
    return 0


# --- dash / ports ----------------------------------------------------------
def cmd_dash(args) -> int:
    servers = live_servers()
    assigned = assign_ports()
    trees = {t.branch: t for t in worktrees()}
    print("\n  ▟ EXOHUB — live preview servers\n")
    hdr = f"  {'PORT':<6}{'WORKTREE':<26}{'PID':<8}{'URL'}"
    print(hdr)
    print("  " + "─" * (len(hdr) - 2))
    if not servers:
        print("  (nothing listening that maps to a worktree)")
    up_branches = set()
    for s in servers:
        t: Worktree = s["tree"]
        up_branches.add(t.branch)
        stray = "" if assigned.get(t.branch) == s["port"] else "  ⚠ off-slot"
        print(f"  {s['port']:<6}{t.label:<26}{s['pid']:<8}"
              f"http://localhost:{s['port']}{stray}")
    down = [b for b in assigned if b not in up_branches]
    if down:
        print()
        for b in down:
            print(f"  {assigned[b]:<6}{trees[b].label:<26}{'—':<8}"
                  "(not running)")
    print()
    return 0


def cmd_ports(args) -> int:
    for branch, port in assign_ports().items():
        label = re.sub(r"^worktree-", "", branch)
        print(f"{port}\t{label}\t{branch}")
    return 0


# --- mprocs ----------------------------------------------------------------
def cmd_mprocs(args) -> int:
    root = repo_root()
    script = Path(__file__).resolve()
    trees = worktrees()
    assigned = assign_ports()
    py = sys.executable or "python3"  # this machine may only have `python3`
    lines = [
        "# generated by `python3 tools/exohub.py mprocs` — one pane per worktree",
        "procs:",
        '  "▟ dash":',
        f'    shell: "while true; do clear; {py} {script} dash; sleep 3; done"',
    ]
    for t in trees:
        port = assigned[t.branch]
        lines += [
            f'  "{t.label} :{port}":',
            f'    shell: "{py} {script} serve"',
            f'    cwd: "{t.path}"',
        ]
    cfg = root / "mprocs.yaml"
    cfg.write_text("\n".join(lines) + "\n")
    print(f"wrote {cfg}", file=sys.stderr)
    if args.no_run:
        return 0
    if which("mprocs") is None:
        print("mprocs not on PATH — `brew install mprocs`, then `mprocs`.",
              file=sys.stderr)
        return 0
    return subprocess.run(["mprocs", "--config", str(cfg)]).returncode


def main() -> int:
    p = argparse.ArgumentParser(
        prog="exohub", description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd")

    ps = sub.add_parser("serve", help="serve this worktree's dist on its stable port")
    ps.add_argument("--port", type=int, help="override the stable port")
    ps.add_argument("--build", action="store_true", help="run web.build first")
    ps.set_defaults(fn=cmd_serve)

    sub.add_parser("dash", help="live table of running preview servers").set_defaults(
        fn=cmd_dash)
    sub.add_parser("ports", help="stable port per worktree").set_defaults(fn=cmd_ports)

    pm = sub.add_parser("mprocs", help="write mprocs.yaml and launch mprocs")
    pm.add_argument("--no-run", action="store_true", help="just write the config")
    pm.set_defaults(fn=cmd_mprocs)

    args = p.parse_args()
    if not getattr(args, "fn", None):
        p.print_help()
        return 0
    return args.fn(args)


if __name__ == "__main__":
    raise SystemExit(main())
