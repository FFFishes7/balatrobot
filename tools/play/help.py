"""Hidden RPC commands not listed in daily actions."""

from __future__ import annotations

import json
import sys

from envelope import HELP_FORMAT, build_help_envelope
from start_options import build_decks, build_stakes


def hidden_actions() -> list[dict]:
    decks, stakes = [d["id"] for d in build_decks()], [s["id"] for s in build_stakes()]
    return [
        {
            "command": "save",
            "description": "Save current run to a file",
            "params": {"path": {"type": "string", "required": True}},
            "example": {"command": "save", "params": {"path": "run.jkr"}},
        },
        {
            "command": "load",
            "description": "Load a saved run from a file",
            "params": {"path": {"type": "string", "required": True}},
            "example": {"command": "load", "params": {"path": "run.jkr"}},
        },
        {
            "command": "add",
            "description": "Add a card (debug/cheat)",
            "params": {},
            "example": {"command": "add", "params": {"joker": "j_joker"}},
        },
        {
            "command": "set",
            "description": "Set in-game values (debug/cheat)",
            "params": {},
            "example": {"command": "set", "params": {"money": 100}},
        },
        {
            "command": "screenshot",
            "description": "Save a screenshot to disk",
            "params": {"path": {"type": "string", "required": True}},
            "example": {"command": "screenshot", "params": {"path": "shot.png"}},
        },
        {
            "command": "start",
            "description": "Start a new run (also in MENU actions)",
            "params": {
                "deck": {"type": "string", "enum": decks},
                "stake": {"type": "string", "enum": stakes},
            },
            "example": {"command": "start", "params": {"deck": "RED", "stake": "WHITE"}},
        },
    ]


def main() -> int:
    print(json.dumps(build_help_envelope(hidden_actions()), ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
