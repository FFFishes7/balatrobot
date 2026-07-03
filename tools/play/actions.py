"""Build state-aware exec actions from a raw gamestate."""

from __future__ import annotations

from typing import Any

from envelope import detect_save_path
from start_options import build_decks, build_stakes


def _example(command: str, params: dict | None = None) -> dict:
    return {"command": command, "params": params or {}}


def _action(
    command: str,
    description: str,
    *,
    params: dict | None = None,
    example_params: dict | None = None,
) -> dict[str, Any]:
    return {
        "command": command,
        "description": description,
        "params": params or {},
        "example": _example(command, example_params or {}),
    }


def _deck_stake_enums() -> tuple[list[str], list[str]]:
    decks = [d["id"] for d in build_decks()]
    stakes = [s["id"] for s in build_stakes()]
    return decks, stakes


def _visible_cards(area: dict | None) -> list[dict]:
    if not area:
        return []
    return [c for c in area.get("cards", []) if not c.get("state", {}).get("hidden")]


def _consumable_needs_hand(card: dict) -> bool:
    effect = (card.get("value") or {}).get("effect") or ""
    # Fallback: Death and tarots that mention "hand" in effect text need targets.
    key = card.get("key") or ""
    if key == "c_death":
        return True
    return "select" in effect.lower() and "hand" in effect.lower()


def _menu_actions() -> list[dict[str, Any]]:
    decks, stakes = _deck_stake_enums()
    actions = [
        _action(
            "start",
            "Start a new run",
            params={
                "deck": {"type": "string", "required": True, "enum": decks},
                "stake": {"type": "string", "required": True, "enum": stakes},
                "seed": {"type": "string", "required": False},
            },
            example_params={"deck": "RED", "stake": "WHITE"},
        )
    ]
    save_path = detect_save_path()
    if save_path:
        actions.append(
            _action(
                "load",
                "Continue saved run",
                params={"path": {"type": "string", "required": True}},
                example_params={"path": save_path},
            )
        )
    return actions


def _sell_actions(state: dict[str, Any]) -> list[dict[str, Any]]:
    actions: list[dict[str, Any]] = []
    for idx, _card in enumerate(state.get("jokers", {}).get("cards", [])):
        actions.append(
            _action(
                "sell",
                f"Sell joker at index {idx}",
                example_params={"joker": idx},
            )
        )
    for idx, _card in enumerate(state.get("consumables", {}).get("cards", [])):
        actions.append(
            _action(
                "sell",
                f"Sell consumable at index {idx}",
                example_params={"consumable": idx},
            )
        )
    return actions


def _use_actions(state: dict[str, Any]) -> list[dict[str, Any]]:
    actions: list[dict[str, Any]] = []
    hand_cards = _visible_cards(state.get("hand"))
    for idx, card in enumerate(state.get("consumables", {}).get("cards", [])):
        needs_hand = _consumable_needs_hand(card)
        if needs_hand and not hand_cards:
            continue
        params: dict[str, Any] = {"consumable": idx}
        if needs_hand:
            params["cards"] = [0]
        actions.append(
            _action(
                "use",
                f"Use consumable at index {idx}",
                example_params=params,
            )
        )
    return actions


def _shop_actions(state: dict[str, Any]) -> list[dict[str, Any]]:
    actions: list[dict[str, Any]] = []
    for idx, _item in enumerate(state.get("shop", {}).get("cards", [])):
        actions.append(
            _action("buy", f"Buy shop card {idx}", example_params={"card": idx})
        )
    for idx, _item in enumerate(state.get("vouchers", {}).get("cards", [])):
        actions.append(
            _action("buy", f"Buy voucher {idx}", example_params={"voucher": idx})
        )
    for idx, _item in enumerate(state.get("packs", {}).get("cards", [])):
        actions.append(
            _action("buy", f"Buy booster pack {idx}", example_params={"pack": idx})
        )
    actions.extend(_sell_actions(state))
    money = state.get("money", 0)
    reroll_cost = (state.get("round") or {}).get("reroll_cost", 0)
    reroll = _action("reroll", "Reroll shop offers", example_params={})
    if reroll_cost > money:
        reroll["affordable"] = False
    actions.append(reroll)
    actions.append(
        _action("next_round", "Leave shop for blind select", example_params={})
    )
    actions.extend(_use_actions(state))
    return actions


def _pack_actions(state: dict[str, Any]) -> list[dict[str, Any]]:
    actions: list[dict[str, Any]] = []
    for idx, _card in enumerate(state.get("pack", {}).get("cards", [])):
        actions.append(
            _action("pack", f"Select pack card {idx}", example_params={"card": idx})
        )
    actions.append(_action("pack", "Skip pack", example_params={"skip": True}))
    actions.extend(_sell_actions(state))
    actions.extend(_use_actions(state))
    return actions


def _selecting_hand_actions(state: dict[str, Any]) -> list[dict[str, Any]]:
    actions = [
        _action(
            "play",
            "Play selected hand cards",
            example_params={"cards": [0, 1, 2, 3, 4]},
        ),
        _action(
            "discard", "Discard selected hand cards", example_params={"cards": [0, 1]}
        ),
        _action("sort", "Sort hand by rank", example_params={"mode": "rank"}),
    ]
    actions.extend(_use_actions(state))
    for idx, card in enumerate(state.get("consumables", {}).get("cards", [])):
        if card.get("key") == "c_death":
            actions.append(
                _action(
                    "death",
                    "Use Death consumable (reorders hand automatically)",
                    example_params={"consumable": idx, "source": 0, "target": 1},
                )
            )
    hand_cards = state.get("hand", {}).get("cards", [])
    if len(hand_cards) >= 2:
        actions.append(
            _action(
                "rearrange",
                "Reorder hand cards",
                example_params={"hand": list(range(len(hand_cards)))},
            )
        )
    if len(state.get("jokers", {}).get("cards", [])) >= 2:
        actions.append(
            _action(
                "rearrange",
                "Reorder jokers",
                example_params={"jokers": [0, 1]},
            )
        )
    actions.extend(_sell_actions(state))
    return actions


def build_actions(state: dict[str, Any]) -> list[dict[str, Any]]:
    name = state.get("state", "UNKNOWN")
    if name == "MENU":
        return _menu_actions()
    if name == "BLIND_SELECT":
        actions = [
            _action("select", "Select current blind", example_params={}),
        ]
        current = None
        for blind in state.get("blinds", {}).values():
            if blind.get("status") in ("CURRENT", "SELECT"):
                current = blind
                break
        if current and current.get("type") in ("SMALL", "BIG"):
            actions.append(_action("skip", "Skip current blind", example_params={}))
        actions.extend(_sell_actions(state))
        actions.extend(_use_actions(state))
        return actions
    if name == "SELECTING_HAND":
        return _selecting_hand_actions(state)
    if name == "ROUND_EVAL":
        actions = [_action("cash_out", "Cash out round rewards", example_params={})]
        actions.extend(_sell_actions(state))
        actions.extend(_use_actions(state))
        return actions
    if name == "SHOP":
        return _shop_actions(state)
    if name == "SMODS_BOOSTER_OPENED":
        return _pack_actions(state)
    if name == "GAME_OVER":
        return [
            _action("menu", "Return to main menu title screen", example_params={}),
        ]
    return []
