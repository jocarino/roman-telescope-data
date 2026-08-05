"""Guard the nginx compression settings the deployed site depends on.

`gzip_proxied any` is the one worth pinning. nginx defaults it to "off", which means it
SKIPS compression for any request carrying a Via header — i.e. one forwarded by a reverse
proxy.

Measured 2026-08-05 with Traefik v3.3 terminating TLS in front of this exact config:
Traefik forwards X-Forwarded-Proto/For but no Via, so the default would still compress
today — the risk is conditional, not live. It is worth pinning anyway, because the same
run showed the failure is total and silent: with the default, adding a single Via header
sent a 1.3 MB response out raw, Traefik passed the uncompressed body straight through
without compressing on nginx's behalf, and nothing in the site's own output looked wrong.
At production size that is the ~2.8 MB planet index instead of ~0.5 MB.

The file explains this in a comment; this test makes deleting the comment insufficient to
delete the behaviour. Note the limit: it reads the file, not the wire. It cannot see a
platform-level override, and TLS is none of its business — Traefik terminates HTTPS and
nginx only ever listens on plain :80.
"""

from __future__ import annotations

import re
from pathlib import Path

NGINX_CONF = Path(__file__).resolve().parents[1] / "nginx.conf"


def _directives() -> dict[str, str]:
    """Map directive name -> value for the top-level `gzip*` lines, comments stripped."""
    found: dict[str, str] = {}
    for line in NGINX_CONF.read_text().splitlines():
        line = line.strip()
        if line.startswith("#"):
            continue
        m = re.match(r"^(gzip[a-z_]*)\s+(.+?);", line)
        if m:
            found[m.group(1)] = m.group(2).strip()
    return found


def test_gzip_is_on():
    assert _directives().get("gzip") == "on", "compression disabled in nginx.conf"


def test_gzip_proxied_any_survives():
    value = _directives().get("gzip_proxied")
    assert value == "any", (
        "nginx.conf must keep `gzip_proxied any`: the default ('off') skips compression "
        "for proxied requests, and production is served through Traefik — so the whole "
        f"site would go out uncompressed. Found: {value!r}"
    )


def test_json_and_js_are_compressed():
    """The index is JSON and the front end is JS — the two biggest wins."""
    types = _directives().get("gzip_types", "").split()
    for wanted in ("application/json", "application/javascript", "text/css"):
        assert wanted in types, f"{wanted} missing from gzip_types: {types}"


def test_text_html_is_not_listed():
    """nginx always compresses text/html; listing it emits a duplicate-MIME warning."""
    assert "text/html" not in _directives().get("gzip_types", "").split()


def test_gzip_vary_is_set():
    """Without `Vary: Accept-Encoding`, a proxy can cache a gzipped body for a client
    that did not ask for one."""
    assert _directives().get("gzip_vary") == "on"


def test_the_reason_is_written_down():
    """The comment is the thing that stops a human deleting the line in the first place."""
    text = NGINX_CONF.read_text()
    assert "gzip_proxied" in text
    assert "Via" in text and "proxy" in text.lower(), (
        "keep the comment in nginx.conf explaining why gzip_proxied is not the default"
    )
