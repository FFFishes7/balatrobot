"""Compact human/AI-readable state summary (glance command).

Formats the play envelope into a short multi-line string so the AI can read
the current state at a glance instead of scanning the full JSON envelope.
"""

from __future__ import annotations

import json
from typing import Any

from actions import build_actions
from bot_client import APIError
from envelope import build_error_envelope, build_play_envelope
from state import fetch_stable_gamestate

SUIT_SYMBOL = {"S": "♠", "H": "♥", "D": "♦", "C": "♣"}


def card_label(card: dict[str, Any]) -> str:
    """Format a playing card as e.g. ``K♠`` / ``T♥`` / ``A♦``.

    Hidden cards (boss blinds) return ``??``. Cards missing rank/suit
    (jokers, consumables) fall back to their ``label`` field.
    """
    if card.get("state", {}).get("hidden"):
        return "??"
    value = card.get("value") or {}
    rank = value.get("rank")
    suit = value.get("suit")
    if not rank or not suit:
        return str(card.get("label") or "?")
    return f"{rank}{SUIT_SYMBOL.get(suit, suit)}"


def _joker_line(idx: int, card: dict[str, Any]) -> str:
    name = card.get("label") or "?"
    effect = (card.get("value") or {}).get("effect") or ""
    seal_etc = []
    modifier = card.get("modifier") or {}
    if isinstance(modifier, dict) and modifier.get("edition"):
        seal_etc.append(str(modifier["edition"]))
    if isinstance(modifier, dict) and modifier.get("enhancement"):
        seal_etc.append(str(modifier["enhancement"]))
    prefix = f"[{idx}]"
    if seal_etc:
        prefix = f"[{idx}] {','.join(seal_etc)}"
    return f"{prefix} {name} — {effect}" if effect else f"{prefix} {name}"


def _blind_line(blind: dict[str, Any]) -> str:
    name = blind.get("name") or "?"
    status = blind.get("status") or "?"
    score = blind.get("score")
    effect = blind.get("effect") or ""
    tag_name = blind.get("tag_name") or ""
    tag_effect = blind.get("tag_effect") or ""
    parts = [f"blind={name}", f"target={score}", f"status={status}"]
    if effect:
        parts.append(f"effect={effect}")
    line = " ".join(parts)
    if tag_name or tag_effect:
        line += f"\n  tag={tag_name} ({tag_effect}) [skip reward: only triggers if you skip this blind]"
    return line


def _current_blind(state: dict[str, Any]) -> dict[str, Any] | None:
    for blind in (state.get("blinds") or {}).values():
        if blind.get("status") == "CURRENT":
            return blind
    return None


def _header(state: dict[str, Any]) -> str:
    fields = [
        f"state={state.get('state', 'UNKNOWN')}",
        f"ante={state.get('ante_num')}",
        f"round={state.get('round_num')}",
        f"money={state.get('money')}",
    ]
    if state.get("deck"):
        fields.append(f"deck={state['deck']}")
    if state.get("stake"):
        fields.append(f"stake={state['stake']}")
    return " ".join(fields)


def _round_line(state: dict[str, Any], target: int | None = None) -> str:
    r = state.get("round") or {}
    chips = r.get("chips", 0)
    hands = r.get("hands_left", 0)
    discards = r.get("discards_left", 0)
    score_part = f"score={chips}/{target}" if target is not None else f"score={chips}"
    return f"round: hands={hands} discards={discards} {score_part}"


def _hand_line(state: dict[str, Any]) -> str:
    cards = (state.get("hand") or {}).get("cards") or []
    if not cards:
        return "hand: (empty)"
    return "hand: " + " ".join(f"[{i}] {card_label(c)}" for i, c in enumerate(cards))


def _actions_line(envelope: dict[str, Any]) -> str:
    seen: list[str] = []
    for a in envelope.get("actions") or []:
        cmd = a.get("command")
        if cmd and cmd not in seen:
            seen.append(cmd)
    return "actions: " + (" ".join(seen) if seen else "(none)")


def print_summary(envelope: dict[str, Any]) -> None:
    """Print a compact multi-line summary of a play envelope to stdout."""
    if not envelope.get("ok"):
        err = envelope.get("error") or {}
        print(f"ERROR: {err.get('name', '?')} - {err.get('message', '')}")
        return

    state = envelope.get("gamestate") or {}
    name = state.get("state", "UNKNOWN")
    lines: list[str] = [_header(state)]

    if name == "MENU":
        lines.append("→ start RED WHITE  (or: start RED WHITE SEED)")
    elif name == "BLIND_SELECT":
        blind = _current_blind(state)
        if blind:
            lines.append(_blind_line(blind))
        lines.extend(_joker_lines(state))
        lines.append(_actions_line(envelope))
    elif name == "SELECTING_HAND":
        blind = _current_blind(state)
        target = blind.get("score") if blind else None
        lines.append(_round_line(state, target))
        if blind:
            lines.append(_blind_line(blind))
        lines.extend(_joker_lines(state))
        lines.append(_hand_line(state))
        lines.append(_actions_line(envelope))
    elif name == "ROUND_EVAL":
        r = state.get("round") or {}
        chips = r.get("chips", 0)
        lines.append(f"round won, score={chips}")
        lines.append(_actions_line(envelope))
    elif name == "SHOP":
        lines.append(_shop_block(state))
        lines.extend(_joker_lines(state))
        lines.append(_actions_line(envelope))
    elif name == "SMODS_BOOSTER_OPENED":
        lines.append(_pack_block(state))
        if (state.get("hand") or {}).get("cards"):
            lines.append(_hand_line(state))
        lines.extend(_joker_lines(state))
        lines.append(_actions_line(envelope))
    elif name == "GAME_OVER":
        summary = state.get("run_summary") or {}
        won = state.get("won")
        result = summary.get("result") or ("Victory" if won else "Lost")
        lines.append(f"GAME_OVER: {result}")
        if summary.get("most_played_hand"):
            mp = summary["most_played_hand"]
            lines.append(f"  most_played: {mp.get('name')} x{mp.get('count')}")
        lines.append(_actions_line(envelope))
    else:
        lines.append(_actions_line(envelope))

    print("\n".join(lines))


def _joker_lines(state: dict[str, Any]) -> list[str]:
    jokers = (state.get("jokers") or {}).get("cards") or []
    if not jokers:
        return []
    out = ["jokers: " + "  ".join(_joker_line(i, c) for i, c in enumerate(jokers))]
    consumables = (state.get("consumables") or {}).get("cards") or []
    if consumables:
        out.append(
            "consumables: "
            + "  ".join(_joker_line(i, c) for i, c in enumerate(consumables))
        )
    return out


def _shop_block(state: dict[str, Any]) -> str:
    parts: list[str] = []
    shop = (state.get("shop") or {}).get("cards") or []
    for i, c in enumerate(shop):
        label = c.get("label") or "?"
        cost = (c.get("cost") or {}).get("buy", "?")
        effect = (c.get("value") or {}).get("effect") or ""
        parts.append(f"  shop[{i}] {label} ${cost} — {effect}")
    vouchers = (state.get("vouchers") or {}).get("cards") or []
    for i, c in enumerate(vouchers):
        label = c.get("label") or "?"
        cost = (c.get("cost") or {}).get("buy", "?")
        effect = (c.get("value") or {}).get("effect") or ""
        parts.append(f"  voucher[{i}] {label} ${cost} — {effect}")
    packs = (state.get("packs") or {}).get("cards") or []
    for i, c in enumerate(packs):
        label = c.get("label") or "?"
        cost = (c.get("cost") or {}).get("buy", "?")
        effect = (c.get("value") or {}).get("effect") or ""
        parts.append(f"  pack[{i}] {label} ${cost} — {effect}")
    reroll = (state.get("round") or {}).get("reroll_cost", "?")
    parts.append(f"  reroll=${reroll}")
    return "shop:\n" + "\n".join(parts) if parts else "shop: (empty)"


def _pack_block(state: dict[str, Any]) -> str:
    cards = (state.get("pack") or {}).get("cards") or []
    parts = [f"  pack[{i}] {c.get('label','?')} — {(c.get('value') or {}).get('effect','')}" for i, c in enumerate(cards)]
    return "pack:\n" + "\n".join(parts) if parts else "pack: (empty)"


def main() -> int:
    try:
        raw = fetch_stable_gamestate()
        envelope = build_play_envelope(raw, build_actions(raw))
        print_summary(envelope)
        return 0
    except APIError as e:
        print(json.dumps(build_error_envelope(e.name, e.message), ensure_ascii=False))
        return 1
    except TimeoutError as e:
        print(json.dumps(build_error_envelope("TIMEOUT", str(e)), ensure_ascii=False))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
