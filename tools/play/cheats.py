"""Gated debug helpers for add/set/debuff (estimate testing only)."""

from __future__ import annotations

import os
import re

CHEATS_ENV = "BALATROBOT_ALLOW_CHEATS"

# Friendly add: joker/card/consumable only (no voucher/pack — use exec for those).
ADD_KINDS = frozenset({"joker", "card", "consumable"})

# Friendly set: round-scoring knobs only (no money/ante/shop restock).
SET_FIELDS = frozenset({"hands", "discards", "chips"})

SET_FIELD_ALIASES = {
    "hand": "hands",
    "hands_left": "hands",
    "discard": "discards",
    "discards_left": "discards",
    "score": "chips",
    "round_chips": "chips",
}

ADD_CARD_KEY = re.compile(r"^[HDCS]_[2-9TJQKA]$")
ADD_FLAGS = frozenset(
    {"enhancement", "seal", "edition", "eternal", "perishable", "rental"}
)

ENHANCEMENTS = frozenset(
    {"BONUS", "MULT", "WILD", "GLASS", "STEEL", "STONE", "GOLD", "LUCKY"}
)
SEALS = frozenset({"RED", "BLUE", "GOLD", "PURPLE"})
EDITIONS = frozenset({"FOIL", "HOLO", "HOLOGRAPHIC", "POLYCHROME", "NEGATIVE"})


def cheats_enabled() -> bool:
    return os.environ.get(CHEATS_ENV, "").strip().lower() in ("1", "true", "yes")


def require_cheats(method: str) -> None:
    if not cheats_enabled():
        raise ValueError(
            f"{method} is disabled. Set {CHEATS_ENV}=1 to enable debug add/set "
            "(estimate testing only; not for normal play)."
        )


def _parse_flags(args: list[str]) -> dict[str, str]:
    flags: dict[str, str] = {}
    for arg in args:
        if "=" not in arg:
            raise ValueError(f"expected KEY=VALUE flag, got: {arg!r}")
        key, _, value = arg.partition("=")
        key = key.strip().lower()
        value = value.strip()
        if key not in ADD_FLAGS:
            raise ValueError(
                f"unknown flag {key!r}; allowed: {', '.join(sorted(ADD_FLAGS))}"
            )
        flags[key] = value
    return flags


def _normalize_card_key(token: str) -> str:
    if ADD_CARD_KEY.match(token.upper()):
        return token.upper()
    raise ValueError(
        "card key must be SUIT_RANK like D_4 or H_A (suits H/D/C/S, ranks 2-9/T/J/Q/K/A)"
    )


def _apply_add_flags(params: dict, flags: dict[str, str]) -> None:
    for key, value in flags.items():
        if key == "enhancement":
            val = value.upper()
            if val not in ENHANCEMENTS:
                raise ValueError(
                    f"enhancement must be one of: {', '.join(sorted(ENHANCEMENTS))}"
                )
            params["enhancement"] = val
        elif key == "seal":
            val = value.upper()
            if val not in SEALS:
                raise ValueError(f"seal must be one of: {', '.join(sorted(SEALS))}")
            params["seal"] = val
        elif key == "edition":
            val = value.upper()
            if val == "HOLOGRAPHIC":
                val = "HOLO"
            if val not in EDITIONS:
                raise ValueError(
                    f"edition must be one of: {', '.join(sorted(EDITIONS))}"
                )
            params["edition"] = "HOLO" if val == "HOLOGRAPHIC" else val
        elif key == "eternal":
            if value.lower() not in ("1", "true", "yes"):
                raise ValueError("eternal must be true/1/yes")
            params["eternal"] = True
        elif key == "rental":
            if value.lower() not in ("1", "true", "yes"):
                raise ValueError("rental must be true/1/yes")
            params["rental"] = True
        elif key == "perishable":
            params["perishable"] = int(value)
            if params["perishable"] < 1:
                raise ValueError("perishable must be >= 1")


def build_add_params(args: list[str]) -> dict:
    """add joker j_dusk [enhancement=MULT ...] | add card D_4 | add consumable c_fool"""
    require_cheats("add")
    if len(args) < 2:
        raise ValueError(
            "add needs: joker KEY | card SUIT_RANK | consumable KEY "
            "[enhancement=MULT seal=RED edition=FOIL ...]"
        )
    kind = args[0].lower()
    if kind not in ADD_KINDS:
        raise ValueError(
            f"add kind must be joker, card, or consumable (not voucher/pack); got {kind!r}"
        )

    positional, flag_args = [], []
    for arg in args[1:]:
        if "=" in arg:
            flag_args.append(arg)
        else:
            positional.append(arg)
    flags = _parse_flags(flag_args)

    params: dict = {}
    if kind == "joker":
        if len(positional) != 1 or not positional[0].startswith("j_"):
            raise ValueError("add joker needs: joker j_<name> (e.g. add joker j_dusk)")
        params["key"] = positional[0]
    elif kind == "consumable":
        if len(positional) != 1 or not positional[0].startswith("c_"):
            raise ValueError("add consumable needs: consumable c_<name>")
        params["key"] = positional[0]
    else:  # card
        if len(positional) != 1:
            raise ValueError("add card needs: card SUIT_RANK (e.g. add card D_4)")
        params["key"] = _normalize_card_key(positional[0])

    _apply_add_flags(params, flags)
    return params


def build_set_params(args: list[str]) -> dict:
    """set hands 1 | set discards 0 chips 500 (one or more FIELD VALUE pairs)."""
    require_cheats("set")
    if len(args) < 2 or len(args) % 2 != 0:
        raise ValueError(
            "set needs FIELD VALUE pairs, e.g. set hands 1 | set hands 1 discards 0 chips 0"
        )
    params: dict = {}
    for i in range(0, len(args), 2):
        field = SET_FIELD_ALIASES.get(args[i].lower(), args[i].lower())
        if field not in SET_FIELDS:
            raise ValueError(
                f"set field {args[i]!r} not allowed; use: {', '.join(sorted(SET_FIELDS))}"
            )
        params[field] = int(args[i + 1])
    return params


def build_debuff_params(args: list[str]) -> dict:
    """debuff 0 [1 2] | debuff clear 0 [1 2]"""
    require_cheats("debuff")
    if not args:
        raise ValueError("debuff needs card indices, e.g. debuff 0 | debuff clear 0 1")
    clear = False
    if args[0].lower() in ("clear", "off", "false"):
        clear = True
        args = args[1:]
    if not args:
        raise ValueError("debuff needs card indices after clear, e.g. debuff clear 0")
    return {"cards": [int(x) for x in args], "debuff": not clear}
