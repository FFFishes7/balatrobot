"""Look up wiki-verified Balatro facts (JSON envelope output)."""

from __future__ import annotations

import json
import sys
from difflib import get_close_matches
from pathlib import Path

from bot_client import APIError, rpc
from envelope import KNOW_FORMAT, build_error_envelope, build_know_envelope
from know_lib import (
    ALIASES,
    KNOWLEDGE_DIR,
    LIBRARIES,
    load_library,
    relevant_boss,
    resolve_name,
    upcoming_tags,
)


def check_kind(kind: str, name: str, library: dict | None = None) -> tuple[bool, dict | None]:
    library = library or load_library(kind)
    resolved = resolve_name(kind, name, library, quiet=True)
    if not resolved:
        return False, None
    return True, {"name": resolved, **library[resolved]}


def cmd_list(kind: str, substring: str | None = None) -> dict:
    library = load_library(kind)
    names = sorted(library)
    if substring:
        sub = substring.lower()
        names = [n for n in names if sub in n.lower()]
    return {"kind": kind, "names": names}


def cmd_stats() -> dict:
    libraries: dict[str, dict] = {}
    for kind, fname in LIBRARIES.items():
        path = KNOWLEDGE_DIR / fname
        if path.is_file():
            libraries[kind] = {"count": len(json.loads(path.read_text(encoding="utf-8"))), "file": fname}
        else:
            libraries[kind] = {"count": 0, "file": fname, "missing": True}
    return {"dir": str(KNOWLEDGE_DIR), "libraries": libraries}


def cmd_preflight() -> dict:
    state = rpc("gamestate")
    checks: list[dict] = []
    passed = True

    stake = (state.get("stake") or "WHITE").upper()
    ok, entry = check_kind("stake", stake)
    checks.append({"kind": "stake", "name": stake, "passed": ok, "entry": entry})
    passed = passed and ok

    joker_lib = load_library("joker")
    jokers = [c["label"] for c in state.get("jokers", {}).get("cards", [])]
    for label in jokers:
        ok, entry = check_kind("joker", label, joker_lib)
        checks.append({"kind": "joker", "name": label, "passed": ok, "entry": entry})
        passed = passed and ok

    boss = relevant_boss(state)
    if boss:
        ok, entry = check_kind("boss", boss)
        checks.append({"kind": "boss", "name": boss, "passed": ok, "entry": entry})
        passed = passed and ok

    tag_lib = load_library("tag")
    for slot, tag in upcoming_tags(state):
        ok, entry = check_kind("tag", tag, tag_lib)
        checks.append({"kind": "tag", "name": tag, "slot": slot, "passed": ok, "entry": entry})
        passed = passed and ok

    return {
        "preflight": {
            "passed": passed,
            "context": {
                "state": state.get("state"),
                "ante_num": state.get("ante_num"),
                "stake": stake,
                "money": state.get("money"),
            },
            "checks": checks,
        }
    }


def main() -> int:
    if len(sys.argv) < 2:
        print(
            json.dumps(
                build_error_envelope(
                    "BAD_REQUEST",
                    "usage: know.py preflight|check|list|stats ...",
                    fmt=KNOW_FORMAT,
                ),
                ensure_ascii=False,
            )
        )
        return 2

    cmd = sys.argv[1]
    try:
        if cmd == "preflight":
            payload = cmd_preflight()
            print(json.dumps(build_know_envelope(payload), ensure_ascii=False))
            return 0 if payload["preflight"]["passed"] else 1
        if cmd == "stats":
            print(json.dumps(build_know_envelope(cmd_stats()), ensure_ascii=False))
            return 0
        if cmd == "list":
            if len(sys.argv) < 3:
                raise ValueError("list needs a library kind")
            kind = ALIASES.get(sys.argv[2].lower())
            if not kind:
                raise ValueError(f"unknown library: {sys.argv[2]}")
            substring = sys.argv[3] if len(sys.argv) > 3 else None
            print(json.dumps(build_know_envelope(cmd_list(kind, substring)), ensure_ascii=False))
            return 0
        if cmd == "check":
            if len(sys.argv) < 4:
                raise ValueError('check needs kind and name, e.g. check joker "Mad Joker"')
            kind = ALIASES.get(sys.argv[2].lower(), sys.argv[2].lower())
            if kind not in LIBRARIES:
                raise ValueError(f"unknown kind: {sys.argv[2]}")
            name = " ".join(sys.argv[3:])
            ok, entry = check_kind(kind, name)
            if not ok:
                print(
                    json.dumps(
                        build_know_envelope({"kind": kind, "name": name, "entry": None}),
                        ensure_ascii=False,
                    )
                )
                return 1
            print(json.dumps(build_know_envelope({"kind": kind, **entry}), ensure_ascii=False))
            return 0
        raise ValueError(f"unknown command: {cmd}")
    except APIError as e:
        print(json.dumps(build_error_envelope(e.name, e.message, fmt=KNOW_FORMAT), ensure_ascii=False))
        return 1
    except (ValueError, FileNotFoundError) as e:
        print(json.dumps(build_error_envelope("BAD_REQUEST", str(e), fmt=KNOW_FORMAT), ensure_ascii=False))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
