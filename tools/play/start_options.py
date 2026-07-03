"""MENU deck/stake option lists for Play Helper envelope."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OPENRPC = ROOT / "src" / "lua" / "utils" / "openrpc.json"
STAKES_VERIFIED = ROOT / "knowledge" / "balatro" / "balatro-stakes-verified.json"


def _load_openrpc() -> dict:
    return json.loads(OPENRPC.read_text(encoding="utf-8"))


def _enum_descriptions(schema_name: str) -> dict[str, str]:
    spec = _load_openrpc()
    schema = spec["components"]["schemas"][schema_name]
    out: dict[str, str] = {}
    for entry in schema.get("oneOf", []):
        const = entry.get("const")
        if const:
            out[const] = entry.get("description", "")
    return out


def build_decks() -> list[dict[str, str]]:
    descriptions = _enum_descriptions("Deck")
    return [
        {"id": deck_id, "description": descriptions.get(deck_id, "")}
        for deck_id in sorted(descriptions)
    ]


def build_stakes() -> list[dict[str, str]]:
    descriptions = _enum_descriptions("Stake")
    if STAKES_VERIFIED.is_file():
        verified = json.loads(STAKES_VERIFIED.read_text(encoding="utf-8"))
        for stake_id, entry in verified.items():
            effect = entry.get("effect")
            if effect:
                descriptions[stake_id] = effect
    return [
        {"id": stake_id, "description": descriptions.get(stake_id, "")}
        for stake_id in sorted(descriptions)
    ]
