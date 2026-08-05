"""Crawl a built `dist/` the way a search engine that does not run JavaScript would.

Why this exists: the gallery grid is built client-side from a fetched index and appended in
batches by an IntersectionObserver. A crawler renders but does not scroll, so *none* of those
cards are links as far as the link graph is concerned. For most of this site's life that left
~97% of planet pages reachable only from sitemap.xml — which is itself skipped when the build
has no --base-url, i.e. it did not exist in production at all.

tests/test_share_meta_build.py already asserts every planet id appears in *some* page's HTML.
That is the existence check; this is the shape check, and the two answer different questions:

  - existence: "does a link to this page exist anywhere?"
  - shape:     "starting at /, following only static <a href>, how many clicks away is it,
                and how many distinct pages point at it?"

A page linked only from a page that is itself unreachable passes the first and fails the
second. Depth and in-degree are also what decide whether a crawler bothers: one link from
the middle of a 2,000-anchor tail list is technically not an orphan and practically close to
one.

Link resolution follows nginx.conf's `try_files $uri $uri.html $uri/index.html`, so what is
walked here is what production actually serves.

    python3 tools/link_audit.py --dist dist
    python3 tools/link_audit.py --dist dist --json     # machine-readable, for CI

Stdlib only, so it runs anywhere the build runs.
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from collections import deque
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urldefrag, urlparse

# Crawlable document types. Everything else a page points at (css, js, png, .ase palettes,
# the JSON index) is an asset: fetched, never a node in the link graph.
_DOC_SUFFIXES = {"", ".html"}


class _Anchors(HTMLParser):
    """Every href on a page, in document order. Deliberately only <a href> — a crawler builds
    the graph from anchors, not from <link>, <form> or anything JS attaches later."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.hrefs: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag != "a":
            return
        for name, value in attrs:
            if name == "href" and value:
                self.hrefs.append(value)


def _normalise(href: str, base: str) -> str | None:
    """Resolve one href to a site-root-relative URL path, or None if it leaves the site.

    `base` is the URL of the page the href was found on, so relative links resolve. Fragments
    and query strings are stripped: they address a position within a page, not another page.
    """
    href, _ = urldefrag(href.strip())
    if not href:
        return None
    parts = urlparse(href)
    if parts.scheme or parts.netloc:
        return None  # external, mailto:, tel:
    path = parts.path
    if not path:
        return None
    if not path.startswith("/"):
        # Relative to the *directory* of the current page.
        stem = base.rsplit("/", 1)[0]
        path = f"{stem}/{path}"
    # Collapse . and .. without touching the filesystem.
    out: list[str] = []
    for seg in path.split("/"):
        if seg in ("", "."):
            continue
        if seg == "..":
            if out:
                out.pop()
            continue
        out.append(seg)
    return _key("/" + "/".join(out))


def _key(url: str) -> str:
    """One node per page, whatever form the link took.

    `/tours`, `/tours/` and `/tours/index.html` are the same document — nginx serves all three
    — so they have to collapse to one key or the graph shows phantom orphans next to
    double-counted pages.
    """
    if url.endswith("/index.html"):
        url = url[: -len("index.html")]
    elif url.endswith(".html"):
        url = url[: -len(".html")]
    return url.rstrip("/") or "/"


def _resolve(dist: Path, url: str) -> Path | None:
    """URL path -> file on disk, following nginx's `try_files $uri $uri.html $uri/index.html`."""
    rel = url.lstrip("/")
    if not rel:
        candidate = dist / "index.html"
        return candidate if candidate.is_file() else None
    for candidate in (dist / rel, dist / f"{rel}.html", dist / rel / "index.html"):
        if candidate.is_file():
            return candidate
    return None


def _is_document(url: str) -> bool:
    return Path(url).suffix.lower() in _DOC_SUFFIXES


def crawl(dist: Path, start: str = "/") -> dict:
    """Breadth-first walk from `start`. Returns depth and in-degree for every page reached."""
    depth: dict[str, int] = {start: 0}
    inbound: dict[str, set[str]] = {}
    outdegree: dict[str, int] = {}
    broken: dict[str, set[str]] = {}
    queue: deque[str] = deque([start])

    while queue:
        url = queue.popleft()
        path = _resolve(dist, url)
        if path is None:
            continue
        parser = _Anchors()
        parser.feed(path.read_text(encoding="utf-8", errors="replace"))
        targets = []
        for href in parser.hrefs:
            target = _normalise(href, url)
            if target is None or not _is_document(target):
                continue
            targets.append(target)
        outdegree[url] = len(targets)
        for target in targets:
            if _resolve(dist, target) is None:
                broken.setdefault(target, set()).add(url)
                continue
            if target != url:
                inbound.setdefault(target, set()).add(url)
            if target not in depth:
                depth[target] = depth[url] + 1
                queue.append(target)

    return {"depth": depth, "inbound": inbound, "outdegree": outdegree, "broken": broken}


def _canonical(dist: Path, path: Path) -> str:
    """The URL form the site links to: root-relative and extensionless (`/planet/earth`)."""
    return _key("/" + path.relative_to(dist).as_posix())


def audit(dist: Path) -> dict:
    graph = crawl(dist)
    depth, inbound = graph["depth"], graph["inbound"]

    built = {
        _canonical(dist, p)
        for p in dist.rglob("*.html")
        # Peek fragments are headless partials fetched by the long-press UI, robots-excluded
        # by design (see robots.txt). They are not pages and must not count as orphans.
        if "fragments" not in p.relative_to(dist).parts and p.name != "404.html"
    }
    planets = {u for u in built if u.startswith("/planet/")}
    reachable = set(depth)

    def _stats(urls: set[str]) -> dict:
        found = sorted(urls & reachable)
        degrees = [len(inbound.get(u, ())) for u in found]
        depths = [depth[u] for u in found]
        return {
            "built": len(urls),
            "reachable": len(found),
            "orphans": sorted(urls - reachable)[:20],
            "orphan_count": len(urls - reachable),
            "depth_histogram": {d: depths.count(d) for d in sorted(set(depths))},
            "inbound_min": min(degrees, default=0),
            "inbound_median": statistics.median(degrees) if degrees else 0,
            "inbound_max": max(degrees, default=0),
            "single_inbound": sum(1 for d in degrees if d == 1),
        }

    return {
        "pages_crawled": len(reachable),
        "all_pages": _stats(built),
        "planet_pages": _stats(planets),
        "widest_pages": sorted(
            graph["outdegree"].items(), key=lambda kv: kv[1], reverse=True
        )[:8],
        "broken_links": {t: sorted(s)[:3] for t, s in sorted(graph["broken"].items())[:20]},
        "broken_count": len(graph["broken"]),
    }


def _report(result: dict) -> None:
    planets, everything = result["planet_pages"], result["all_pages"]
    print(f"crawled {result['pages_crawled']} pages from /  (static <a href> only, no JS)\n")
    for label, s in (("all pages", everything), ("planet pages", planets)):
        pct = 100.0 * s["reachable"] / s["built"] if s["built"] else 0.0
        print(f"{label}: {s['reachable']}/{s['built']} reachable ({pct:.1f}%)")
        if s["orphan_count"]:
            print(f"  ORPHANS: {s['orphan_count']} — e.g. {', '.join(s['orphans'][:5])}")
        print(f"  depth from /: {s['depth_histogram']}")
        print(
            f"  inbound links: min {s['inbound_min']}, median {s['inbound_median']:g}, "
            f"max {s['inbound_max']}  ({s['single_inbound']} pages have exactly one)\n"
        )
    print("widest pages (outbound links):")
    for url, n in result["widest_pages"]:
        print(f"  {n:>5}  {url}")
    if result["broken_count"]:
        print(f"\nBROKEN LINKS: {result['broken_count']}")
        for target, sources in list(result["broken_links"].items())[:10]:
            print(f"  {target}  <- {', '.join(sources)}")


def main() -> int:
    parser = argparse.ArgumentParser(prog="link_audit")
    parser.add_argument("--dist", type=Path, default=Path("dist"))
    parser.add_argument("--json", action="store_true", help="machine-readable output")
    parser.add_argument(
        "--fail-on-orphans",
        action="store_true",
        help="exit 1 if any built page is unreachable from / by static links",
    )
    args = parser.parse_args()
    if not (args.dist / "index.html").is_file():
        sys.exit(f"{args.dist} has no index.html — build the site first.")
    result = audit(args.dist)
    print(json.dumps(result, indent=2, default=list)) if args.json else _report(result)
    return 1 if args.fail_on_orphans and result["all_pages"]["orphan_count"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
