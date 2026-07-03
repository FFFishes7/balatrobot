"""Shared knowledge library helpers for know.py."""

from __future__ import annotations

import json
import sys
from difflib import get_close_matches
from pathlib import Path

KNOWLEDGE_DIR = Path(__file__).resolve().parents[2] / "knowledge" / "balatro"

LIBRARIES = {
    "joker": "balatro-jokers-verified.json",
    "boss": "balatro-bosses-verified.json",
    "tag": "balatro-tags-verified.json",
    "stake": "balatro-stakes-verified.json",
    "planet": "balatro-planets-verified.json",
    "tarot": "balatro-tarots-verified.json",
    "voucher": "balatro-vouchers-verified.json",
    "spectral": "balatro-spectrals-verified.json",
    "rule": "balatro-rules-verified.json",
}

ALIASES = {
    "jokers": "joker",
    "bosses": "boss",
    "tags": "tag",
    "stakes": "stake",
    "planets": "planet",
    "tarots": "tarot",
    "vouchers": "voucher",
    "spectrals": "spectral",
    "rules": "rule",
}


def load_library(kind: str) -> dict:
    path = KNOWLEDGE_DIR / LIBRARIES[kind]
    if not path.is_file():
        raise FileNotFoundError(f"Missing library: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def resolve_name(
    kind: str, name: str, library: dict, quiet: bool = False
) -> str | None:
    key = name.strip()
    if key in library:
        return key
    lower_map = {k.lower(): k for k in library}
    if key.lower() in lower_map:
        return lower_map[key.lower()]
    matches = get_close_matches(key, library.keys(), n=3, cutoff=0.6)
    if len(matches) == 1:
        if not quiet:
            print(f"  (matched '{matches[0]}')", file=sys.stderr)
        return matches[0]
    if matches and not quiet:
        print(f"  ambiguous — did you mean: {', '.join(matches)}?", file=sys.stderr)
    return None


def relevant_boss(state: dict) -> str | None:
    for blind in state.get("blinds", {}).values():
        if blind.get("type") == "BOSS" and blind.get("status") in (
            "CURRENT",
            "SELECT",
            "UPCOMING",
        ):
            return blind.get("name")
    return None


def upcoming_tags(state: dict) -> list[tuple[str, str]]:
    out = []
    for slot, blind in state.get("blinds", {}).items():
        tag = blind.get("tag_name") or ""
        if tag and blind.get("status") in ("SELECT", "UPCOMING"):
            out.append((slot, tag))
    return out
