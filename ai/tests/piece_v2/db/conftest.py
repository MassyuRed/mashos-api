"""Disposable-only boundary for Piece DB tests; no connection or DDL at import.

The frozen test retains its own missing-database NONCREDIT result. When a URL
is explicitly supplied, reject a remote/ambiguous target before test setup.
This guard neither mocks psycopg nor substitutes another database engine.
"""
from __future__ import annotations

import os
import re
from urllib.parse import parse_qsl, unquote, urlparse

import pytest

_ACK = "I_ACKNOWLEDGE_DISPOSABLE_DATABASE"


def validate_disposable_database_url(url: str, acknowledgement: str) -> str:
    """Validate without echoing credentials or contacting the destination."""
    try:
        parsed = urlparse(url)
        database = unquote(parsed.path.removeprefix("/"))
        items = parse_qsl(parsed.query, keep_blank_values=True, strict_parsing=True)
        query = dict(items)
        if (acknowledgement != _ACK or parsed.scheme not in {"postgres", "postgresql"}
                or parsed.fragment or not re.fullmatch(r"piece_v2_test[A-Za-z0-9_]*", database)
                or len(items) != len(query)
                or set(query) - {"host", "sslmode", "connect_timeout", "application_name"}):
            raise ValueError
        host = parsed.hostname
        if host is None:
            socket_dir = query.get("host", "")
            if not socket_dir.startswith("/") or "," in socket_dir or "\x00" in socket_dir:
                raise ValueError
        elif host not in {"127.0.0.1", "::1"} or "host" in query:
            raise ValueError
        if parsed.port is not None and not 1 <= parsed.port <= 65535:
            raise ValueError
        if "connect_timeout" in query and not re.fullmatch(r"[1-9][0-9]?", query["connect_timeout"]):
            raise ValueError
    except (TypeError, ValueError, UnicodeError):
        raise pytest.UsageError("PRODUCTION_DATABASE_PROHIBITED: use an acknowledged local piece_v2_test database") from None
    return url


def pytest_configure(config: pytest.Config) -> None:
    url = os.environ.get("PIECE_V2_TEST_DATABASE_URL", "").strip()
    acknowledgement = os.environ.get("PIECE_V2_TEST_DATABASE_DISPOSABLE_ACK", "").strip()
    if url or acknowledgement:
        validate_disposable_database_url(url, acknowledgement)
