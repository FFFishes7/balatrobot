"""Look up wiki-verified Balatro facts.

Default output for ``preflight`` is a compact table; ``check``/``list``/``stats``
and ``--json`` print the raw JSON envelope.
"""

from __future__ import annotations

import json
import sys

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

JSON_FLAG = "--json"


def check_kind(
    kind: str, name: str, library: dict | None = None
) -> tuple[bool, dict | None]:
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
            libraries[kind] = {
                "count": len(json.loads(path.read_text(encoding="utf-8"))),
                "file": fname,
            }
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
        checks.append(
            {"kind": "tag", "name": tag, "slot": slot, "passed": ok, "entry": entry}
        )
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


def _format_preflight(payload: dict) -> str:
    pre = payload.get("preflight") or {}
    ctx = pre.get("context") or {}
    lines = [
        f"preflight passed={pre.get('passed')} "
        f"state={ctx.get('state')} ante={ctx.get('ante_num')} stake={ctx.get('stake')} money={ctx.get('money')}"
    ]
    lines.append("kind     name                     passed  effect")
    for c in pre.get("checks") or []:
        entry = c.get("entry") or {}
        effect = (entry.get("effect") or "")[:60]
        lines.append(
            f"{c.get('kind', ''):<9s}{c.get('name', '')[:24]:<25s}"
            f"{str(c.get('passed')):<8s}{effect}"
        )
    return "\n".join(lines)


def _parse_argv(argv: list[str]) -> tuple[list[str], bool]:
    json_out = False
    rest: list[str] = []
    for arg in argv:
        if arg == JSON_FLAG:
            json_out = True
        else:
            rest.append(arg)
    return rest, json_out


def main() -> int:
    args, json_out = _parse_argv(sys.argv[1:])
    if not args:
        print(
            json.dumps(
                build_error_envelope(
                    "BAD_REQUEST",
                    "usage: know.py preflight|check|list|stats ... [--json]",
                    fmt=KNOW_FORMAT,
                ),
                ensure_ascii=False,
            )
        )
        return 2

    cmd = args[0]
    try:
        if cmd == "preflight":
            payload = cmd_preflight()
            if json_out:
                print(json.dumps(build_know_envelope(payload), ensure_ascii=False))
            else:
                print(_format_preflight(payload))
            return 0 if payload["preflight"]["passed"] else 1
        if cmd == "stats":
            print(json.dumps(build_know_envelope(cmd_stats()), ensure_ascii=False))
            return 0
        if cmd == "list":
            if len(args) < 2:
                raise ValueError("list needs a library kind")
            kind = ALIASES.get(args[1].lower())
            if not kind:
                raise ValueError(f"unknown library: {args[1]}")
            substring = args[2] if len(args) > 2 else None
            print(
                json.dumps(
                    build_know_envelope(cmd_list(kind, substring)), ensure_ascii=False
                )
            )
            return 0
        if cmd == "check":
            if len(args) < 3:
                raise ValueError(
                    'check needs kind and name, e.g. check joker "Mad Joker"'
                )
            kind = ALIASES.get(args[1].lower(), args[1].lower())
            if kind not in LIBRARIES:
                raise ValueError(f"unknown kind: {args[1]}")
            name = " ".join(args[2:])
            ok, entry = check_kind(kind, name)
            if not ok:
                print(
                    json.dumps(
                        build_know_envelope(
                            {"kind": kind, "name": name, "entry": None}
                        ),
                        ensure_ascii=False,
                    )
                )
                return 1
            print(
                json.dumps(
                    build_know_envelope({"kind": kind, **entry}), ensure_ascii=False
                )
            )
            return 0
        raise ValueError(f"unknown command: {cmd}")
    except APIError as e:
        print(
            json.dumps(
                build_error_envelope(e.name, e.message, fmt=KNOW_FORMAT),
                ensure_ascii=False,
            )
        )
        return 1
    except (ValueError, FileNotFoundError) as e:
        print(
            json.dumps(
                build_error_envelope("BAD_REQUEST", str(e), fmt=KNOW_FORMAT),
                ensure_ascii=False,
            )
        )
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
