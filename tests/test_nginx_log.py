"""The access log has to outlive the container that wrote it.

Crawlers and the assistants that quote this site never run JavaScript, so PostHog cannot see
them: a request line is the only evidence they were here. nginx's default log goes to
container stdout, which Docker discards when the container is replaced -- every deploy wiped
the only record of who fetched what. These assertions are cheap text checks, but each one
guards a failure that is invisible until you go looking for data that was never kept:

* logging only to stdout, or to a path the nginx image has symlinked back to stdout;
* logging $remote_addr behind Traefik, which makes every line the proxy's address;
* logging a full client address, which turns a bot-counting log into personal data;
* dropping the user-agent, which is the field that separates GPTBot from a person.
"""

from __future__ import annotations

import re
from pathlib import Path

NGINX_CONF = Path("nginx.conf").read_text()
DOCKERFILE = Path("Dockerfile").read_text()

LOG_DIR = "/var/log/site"
ACCESS_LOGS = re.findall(r"^\s*access_log\s+(\S+)\s+(\S+?);", NGINX_CONF, re.M)


def _log_format(name: str) -> str:
    """The body of `log_format <name> ...;`, joined across its continuation lines."""
    match = re.search(rf"log_format\s+{name}\s+(.*?);", NGINX_CONF, re.S)
    assert match, f"nginx.conf defines no log_format named {name!r}"
    return match.group(1)


def test_access_log_is_written_to_a_file_as_well_as_stdout():
    targets = {path for path, _ in ACCESS_LOGS}
    assert f"{LOG_DIR}/access.log" in targets, (
        f"no durable access_log: {targets or 'none at all'}. Logging only to stdout means the "
        "record dies with the container on the next deploy."
    )
    assert "/dev/stdout" in targets, "keep the stdout sink too, or `docker logs` goes quiet"


def test_the_durable_path_is_not_under_var_log_nginx():
    """nginx:alpine symlinks /var/log/nginx/access.log -> /dev/stdout. A file written there
    silently goes back to the container log, and the mount looks fine while collecting
    nothing."""
    for path, _ in ACCESS_LOGS:
        assert not path.startswith("/var/log/nginx/"), (
            f"{path} is inside the image's symlinked log dir; use {LOG_DIR}"
        )


def test_the_image_creates_the_log_directory():
    assert re.search(rf"mkdir -p {LOG_DIR}\b", DOCKERFILE), (
        f"the Dockerfile must create {LOG_DIR}; nginx will not start if it cannot open its log"
    )


def test_the_logged_address_comes_from_the_forwarded_header_and_is_truncated():
    fmt = _log_format("site")
    assert "$client_net" in fmt, "log the truncated network, not a raw address"
    for raw in ("$remote_addr", "$client_addr", "$http_x_forwarded_for"):
        assert raw not in fmt, f"{raw} in the log format defeats the truncation map"

    # $client_addr reads the first X-Forwarded-For entry; $client_net truncates that.
    assert re.search(r"map\s+\$http_x_forwarded_for\s+\$client_addr", NGINX_CONF), (
        "behind Traefik $remote_addr is the proxy -- derive the client from X-Forwarded-For"
    )
    assert re.search(r"map\s+\$client_addr\s+\$client_net", NGINX_CONF)


def test_the_format_keeps_the_fields_the_log_exists_for():
    fmt = _log_format("site")
    for field in ("$time_iso8601", "$request", "$status", "$http_user_agent", "$http_referer"):
        assert field in fmt, f"{field} missing from the access log format"


def test_the_server_uses_that_format():
    for path, fmt in ACCESS_LOGS:
        assert fmt == "site", f"{path} logs with {fmt!r}, not the site format"
