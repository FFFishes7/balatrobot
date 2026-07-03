"""Layer-2 query commands."""

from __future__ import annotations

import json
import sys

from bot_client import APIError, rpc
from envelope import QUERY_FORMAT, build_error_envelope, build_query_envelope
from layers import QUERY_EXTRACTORS, available_queries, extract_query, poll_until_stable


def main() -> int:
    if len(sys.argv) < 2:
        print(
            json.dumps(
                build_error_envelope(
                    "BAD_REQUEST",
                    "usage: query.py deck|hands|blinds|used_vouchers|seed",
                    fmt=QUERY_FORMAT,
                ),
                ensure_ascii=False,
            )
        )
        return 2

    name = sys.argv[1].lower()
    if name not in QUERY_EXTRACTORS:
        print(
            json.dumps(
                build_error_envelope("BAD_REQUEST", f"unknown query: {name}", fmt=QUERY_FORMAT),
                ensure_ascii=False,
            )
        )
        return 2

    try:
        raw = poll_until_stable(lambda: rpc("gamestate"))
        state = raw.get("state", "UNKNOWN")
        allowed = {q["name"] for q in available_queries(state)}
        if name not in allowed:
            print(
                json.dumps(
                    build_error_envelope(
                        "INVALID_STATE",
                        f"query {name!r} not available in state {state!r}",
                        fmt=QUERY_FORMAT,
                    ),
                    ensure_ascii=False,
                )
            )
            return 1
        data = extract_query(raw, name)
        print(json.dumps(build_query_envelope(name, data), ensure_ascii=False))
        return 0
    except APIError as e:
        print(
            json.dumps(build_error_envelope(e.name, e.message, fmt=QUERY_FORMAT), ensure_ascii=False)
        )
        return 1
    except TimeoutError as e:
        print(
            json.dumps(build_error_envelope("TIMEOUT", str(e), fmt=QUERY_FORMAT), ensure_ascii=False)
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
