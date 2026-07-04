"""Hidden RPC commands not listed in daily actions."""

from __future__ import annotations

import json

from envelope import build_help_envelope
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
            "description": "Add joker/card/consumable (debug; requires BALATROBOT_ALLOW_CHEATS=1)",
            "params": {},
            "example": {"command": "add", "params": {"key": "j_dusk"}},
        },
        {
            "command": "set",
            "description": "Set hands/discards/chips (debug; requires BALATROBOT_ALLOW_CHEATS=1)",
            "params": {},
            "example": {"command": "set", "params": {"hands": 1, "chips": 0}},
        },
        {
            "command": "debuff",
            "description": "Debuff/clear hand cards by index (debug; requires BALATROBOT_ALLOW_CHEATS=1)",
            "params": {},
            "example": {"command": "debuff", "params": {"cards": [0], "debuff": True}},
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
            "example": {
                "command": "start",
                "params": {"deck": "RED", "stake": "WHITE"},
            },
        },
    ]


def main() -> int:
    print(json.dumps(build_help_envelope(hidden_actions()), ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
