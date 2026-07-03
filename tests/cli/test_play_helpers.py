"""Unit tests for Play Helper JSON layer (no Balatro required)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

PLAY_ROOT = Path(__file__).resolve().parents[2] / "tools" / "play"
import sys

sys.path.insert(0, str(PLAY_ROOT))

from actions import build_actions  # noqa: E402
from commands import build_params, normalize_sort_mode  # noqa: E402
from envelope import build_play_envelope  # noqa: E402
from layers import extract_query, filter_layer1  # noqa: E402
from start_options import build_decks, build_stakes  # noqa: E402


@pytest.fixture
def selecting_hand_state() -> dict:
    return {
        "state": "SELECTING_HAND",
        "money": 10,
        "round_num": 1,
        "ante_num": 1,
        "deck": "RED",
        "stake": "WHITE",
        "won": False,
        "seed": "ABC123",
        "round": {"hands_left": 4, "discards_left": 3, "chips": 100, "reroll_cost": 5},
        "blinds": {
            "small": {"status": "DEFEATED", "name": "Small Blind"},
            "big": {"status": "CURRENT", "name": "Big Blind", "type": "BIG"},
            "boss": {"status": "UPCOMING", "name": "The Hook", "type": "BOSS"},
        },
        "hands": {"Pair": {"level": 1, "chips": 10, "mult": 2}},
        "used_vouchers": {"v_overstock": "Shop has more cards"},
        "jokers": {"count": 1, "limit": 5, "cards": [{"label": "Joker", "key": "j_joker"}]},
        "consumables": {"count": 0, "limit": 2, "cards": []},
        "cards": {"count": 44, "limit": 52, "cards": ["hidden"]},
        "hand": {"count": 8, "limit": 8, "cards": [{"label": "Ace of Spades"}]},
        "shop": {"count": 0, "limit": 0, "cards": []},
    }


def test_filter_layer1_selecting_hand_strips_l3(selecting_hand_state: dict) -> None:
    filtered = filter_layer1(selecting_hand_state)
    assert filtered["state"] == "SELECTING_HAND"
    assert "hand" in filtered
    assert "shop" not in filtered
    assert "hands" not in filtered
    assert "seed" not in filtered
    assert filtered["cards"] == {"count": 44, "limit": 52}
    assert list(filtered["blinds"]) == ["big"]


def test_query_deck_extracts_full_cards(selecting_hand_state: dict) -> None:
    data = extract_query(selecting_hand_state, "deck")
    assert data["count"] == 44
    assert data["cards"] == ["hidden"]


def test_menu_envelope_has_decks_stakes() -> None:
    raw = {"state": "MENU", "money": 0, "round_num": 0, "ante_num": 0}
    envelope = build_play_envelope(raw, build_actions(raw))
    assert envelope["format"] == "balatrobot-play-v1"
    assert envelope["gamestate"] == {"state": "MENU"}
    assert "queries" not in envelope
    assert len(envelope["decks"]) == len(build_decks())
    assert len(envelope["stakes"]) == len(build_stakes())
    assert envelope["actions"][0]["command"] == "start"


def test_game_over_envelope(selecting_hand_state: dict) -> None:
    raw = {
        "state": "GAME_OVER",
        "won": False,
        "seed": "3ZF4YT86",
        "ante_num": 5,
        "round_num": 11,
        "run_summary": {
            "best_hand": 11446,
            "result": "Lost to Big Blind",
        },
        "money": 32,
        "jokers": selecting_hand_state["jokers"],
    }
    envelope = build_play_envelope(raw, build_actions(raw))
    gs = envelope["gamestate"]
    assert gs["seed"] == "3ZF4YT86"
    assert gs["run_summary"]["best_hand"] == 11446
    assert "money" not in gs
    assert "queries" not in envelope
    commands = {a["command"] for a in envelope["actions"]}
    assert commands == {"menu"}


def test_build_actions_selecting_hand(selecting_hand_state: dict) -> None:
    actions = build_actions(selecting_hand_state)
    commands = {a["command"] for a in actions}
    assert {"play", "discard", "sort"}.issubset(commands)


def test_start_options_descriptions() -> None:
    decks = build_decks()
    assert any(d["id"] == "RED" and d["description"] for d in decks)
    stakes = build_stakes()
    assert any(s["id"] == "WHITE" and s["description"] for s in stakes)


def test_build_params_sell() -> None:
    assert build_params("sell", ["joker", "0"]) == {"joker": 0}
    assert build_params("sell", ["consumable", "2"]) == {"consumable": 2}


def test_build_params_use() -> None:
    assert build_params("use", ["0"]) == {"consumable": 0}
    assert build_params("use", ["0", "1", "2"]) == {"consumable": 0, "cards": [1, 2]}


def test_build_params_sort() -> None:
    assert build_params("sort", []) == {"mode": "rank"}
    assert build_params("sort", ["suit-desc"]) == {"mode": "suit-desc"}


def test_normalize_sort_mode_aliases() -> None:
    assert normalize_sort_mode("r") == "rank"
    assert normalize_sort_mode("value-desc") == "rank-desc"
    assert normalize_sort_mode("sa") == "suit-asc"


def test_build_params_sell_errors() -> None:
    with pytest.raises(ValueError, match="sell needs"):
        build_params("sell", ["joker"])
    with pytest.raises(ValueError, match="sell kind must be"):
        build_params("sell", ["card", "0"])


def test_build_params_use_errors() -> None:
    with pytest.raises(ValueError, match="use needs"):
        build_params("use", [])


def test_build_params_sort_errors() -> None:
    with pytest.raises(ValueError, match="sort mode must be"):
        normalize_sort_mode("invalid")


def test_build_actions_shop(selecting_hand_state: dict) -> None:
    shop_state = {
        **selecting_hand_state,
        "state": "SHOP",
        "shop": {
            "count": 1,
            "limit": 2,
            "cards": [{"label": "Joker", "key": "j_joker"}],
        },
        "vouchers": {"count": 0, "limit": 1, "cards": []},
        "packs": {"count": 0, "limit": 2, "cards": []},
        "consumables": {
            "count": 1,
            "limit": 2,
            "cards": [{"label": "The Hermit", "key": "c_hermit"}],
        },
    }
    commands = {a["command"] for a in build_actions(shop_state)}
    assert {"buy", "reroll", "next_round", "sell", "use"}.issubset(commands)


def test_build_actions_blind_select(selecting_hand_state: dict) -> None:
    blind_state = {
        **selecting_hand_state,
        "state": "BLIND_SELECT",
        "consumables": {
            "count": 1,
            "limit": 2,
            "cards": [{"label": "The Hermit", "key": "c_hermit"}],
        },
    }
    commands = {a["command"] for a in build_actions(blind_state)}
    assert {"select", "sell", "use"}.issubset(commands)


def test_build_actions_round_eval(selecting_hand_state: dict) -> None:
    round_eval_state = {
        **selecting_hand_state,
        "state": "ROUND_EVAL",
        "consumables": {
            "count": 1,
            "limit": 2,
            "cards": [{"label": "The Hermit", "key": "c_hermit"}],
        },
    }
    commands = {a["command"] for a in build_actions(round_eval_state)}
    assert {"cash_out", "sell", "use"}.issubset(commands)


def test_build_actions_pack_open(selecting_hand_state: dict) -> None:
    pack_state = {
        **selecting_hand_state,
        "state": "SMODS_BOOSTER_OPENED",
        "pack": {
            "count": 3,
            "limit": 3,
            "cards": [{"label": "The Magician", "key": "c_magician"}],
        },
        "consumables": {
            "count": 1,
            "limit": 2,
            "cards": [
                {
                    "label": "The Magician",
                    "key": "c_magician",
                    "value": {"effect": "Select 1-2 cards in hand"},
                }
            ],
        },
    }
    commands = {a["command"] for a in build_actions(pack_state)}
    assert {"pack", "sell", "use"}.issubset(commands)
