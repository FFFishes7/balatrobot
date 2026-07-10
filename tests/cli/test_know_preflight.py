"""Tests for phase-aware know preflight."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

PLAY_ROOT = Path(__file__).resolve().parents[2] / "tools" / "play"
sys.path.insert(0, str(PLAY_ROOT))

from know import (  # noqa: E402  # type: ignore[unresolved-import]
    _format_preflight,
    check_kind,
    cmd_preflight,
)
from know import (  # noqa: E402  # type: ignore[unresolved-import]
    main as know_main,
)
from know_lib import (  # noqa: E402  # type: ignore[unresolved-import]
    collect_preflight_checks,
    load_library,
    preflight_phase,
)


def _boss_blinds(name: str = "The Eye", status: str = "UPCOMING") -> dict:
    return {
        "small": {"type": "SMALL", "status": "SELECT", "tag_name": "Economy Tag"},
        "big": {"type": "BIG", "status": "UPCOMING", "tag_name": ""},
        "boss": {"type": "BOSS", "name": name, "status": status},
    }


def _owned_joker(label: str = "Baron") -> dict:
    return {"cards": [{"label": label, "set": "JOKER"}]}


def _owned_consumable(label: str, card_set: str) -> dict:
    return {"cards": [{"label": label, "set": card_set}]}


@pytest.mark.parametrize(
    ("state", "expected_kinds"),
    [
        ({"state": "MENU"}, []),
        ({"state": "HAND_PLAYED", "deck": "RED", "stake": "WHITE"}, []),
        (
            {
                "state": "BLIND_SELECT",
                "deck": "RED",
                "stake": "RED",
                "ante_num": 2,
                "money": 8,
                "jokers": _owned_joker("Baron"),
                "consumables": _owned_consumable("The Hermit", "TAROT"),
                "blinds": _boss_blinds(),
            },
            ["deck", "stake", "joker", "tarot", "boss", "tag"],
        ),
        (
            {
                "state": "SELECTING_HAND",
                "deck": "PLASMA",
                "stake": "RED",
                "jokers": _owned_joker(),
                "consumables": _owned_consumable("Pluto", "PLANET"),
                "blinds": _boss_blinds(status="CURRENT"),
            },
            ["deck", "stake", "joker", "planet", "boss"],
        ),
        (
            {
                "state": "SHOP",
                "deck": "RED",
                "stake": "RED",
                "jokers": _owned_joker(),
                "consumables": {"cards": []},
                "blinds": _boss_blinds(),
            },
            ["deck", "stake", "joker", "boss"],
        ),
        (
            {
                "state": "SMODS_BOOSTER_OPENED",
                "deck": "RED",
                "stake": "RED",
                "jokers": _owned_joker(),
                "consumables": {"cards": []},
                "blinds": _boss_blinds(),
            },
            ["deck", "stake", "joker", "boss"],
        ),
        (
            {
                "state": "ROUND_EVAL",
                "deck": "BLUE",
                "stake": "WHITE",
                "jokers": _owned_joker(),
                "consumables": _owned_consumable("Ankh", "SPECTRAL"),
                "blinds": _boss_blinds(),
            },
            ["deck", "stake", "joker", "spectral", "boss"],
        ),
        (
            {
                "state": "GAME_OVER",
                "deck": "RED",
                "stake": "RED",
                "jokers": _owned_joker(),
            },
            ["deck", "stake"],
        ),
    ],
)
def test_preflight_checks_by_phase(state: dict, expected_kinds: list[str]) -> None:
    checks, passed, phase = collect_preflight_checks(state, check_kind=check_kind)
    assert [c["kind"] for c in checks] == expected_kinds
    assert passed is True
    if expected_kinds:
        assert phase == preflight_phase(state)
    text = _format_preflight(
        {
            "preflight": {
                "passed": passed,
                "context": {
                    "state": state.get("state"),
                    "ante_num": state.get("ante_num"),
                    "deck": (state.get("deck") or "RED").upper(),
                    "stake": (state.get("stake") or "WHITE").upper(),
                    "money": state.get("money"),
                },
                "checks": checks,
            }
        }
    )
    if not expected_kinds:
        assert text == ""
    else:
        assert "kind      name" in text
        assert checks[0]["kind"] == "deck"


@pytest.mark.parametrize(
    ("phase", "expected_kinds"),
    [
        ("BLIND_SELECT", ["challenge", "joker", "tarot", "boss", "tag"]),
        ("SELECTING_HAND", ["challenge", "joker", "tarot", "boss"]),
        ("SHOP", ["challenge", "joker", "tarot", "boss"]),
        ("SMODS_BOOSTER_OPENED", ["challenge", "joker", "tarot", "boss"]),
        ("ROUND_EVAL", ["challenge", "joker", "tarot", "boss"]),
        ("GAME_OVER", []),
    ],
)
def test_preflight_challenge_omits_deck_and_stake(
    phase: str, expected_kinds: list[str]
) -> None:
    state = {
        "state": phase,
        "deck": "RED",
        "stake": "WHITE",
        "challenge": {"id": "c_omelette_1", "name": "The Omelette"},
        "jokers": _owned_joker(),
        "consumables": _owned_consumable("The Hermit", "TAROT"),
        "blinds": _boss_blinds(),
    }
    checks, passed, resolved_phase = collect_preflight_checks(
        state, check_kind=check_kind
    )
    assert [check["kind"] for check in checks] == expected_kinds
    assert passed is True
    assert resolved_phase == phase


def test_cmd_preflight_challenge_context_omits_deck_and_stake(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    state = {
        "state": "BLIND_SELECT",
        "ante_num": 2,
        "money": 8,
        "deck": "RED",
        "stake": "WHITE",
        "challenge": {"id": "c_omelette_1", "name": "The Omelette"},
        "jokers": {"cards": []},
        "consumables": {"cards": []},
        "blinds": _boss_blinds(),
    }
    monkeypatch.setattr("know.rpc", lambda _: state)

    payload = cmd_preflight()["preflight"]
    context = payload["context"]

    assert context["challenge"] == "The Omelette"
    assert "deck" not in context
    assert "stake" not in context
    text = _format_preflight({"preflight": payload})
    assert "challenge=The Omelette" in text.splitlines()[0]
    assert "deck=" not in text
    assert "stake=" not in text
    challenge_row = payload["checks"][0]
    assert challenge_row["kind"] == "challenge"
    assert challenge_row["passed"] is True
    assert challenge_row["entry"]["name"] == "The Omelette"
    assert "start with 5 Egg Jokers" in text


def test_cmd_preflight_challenge_game_over_is_empty(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "know.rpc",
        lambda _: {
            "state": "GAME_OVER",
            "deck": "RED",
            "stake": "WHITE",
            "challenge": {"id": "c_omelette_1", "name": "The Omelette"},
        },
    )
    assert _format_preflight(cmd_preflight()) == ""


def test_preflight_unknown_joker_fails() -> None:
    state = {
        "state": "SELECTING_HAND",
        "deck": "RED",
        "stake": "RED",
        "jokers": _owned_joker("Totally Fake Joker"),
        "consumables": {"cards": []},
        "blinds": _boss_blinds(),
    }
    checks, passed, _ = collect_preflight_checks(state, check_kind=check_kind)
    assert passed is False
    joker_row = next(c for c in checks if c["kind"] == "joker")
    assert joker_row["passed"] is False
    assert joker_row["entry"] is None


def test_preflight_header_and_full_effect() -> None:
    checks, passed, _ = collect_preflight_checks(
        {
            "state": "GAME_OVER",
            "deck": "RED",
            "stake": "RED",
        },
        check_kind=check_kind,
    )
    text = _format_preflight(
        {
            "preflight": {
                "passed": passed,
                "context": {
                    "state": "GAME_OVER",
                    "ante_num": 5,
                    "deck": "RED",
                    "stake": "RED",
                    "money": 0,
                },
                "checks": checks,
            }
        }
    )
    assert "passed=" not in text.splitlines()[0]
    assert "ante=5 deck=RED stake=RED" in text.splitlines()[0]
    stake_row = next(c for c in checks if c["kind"] == "stake")
    assert stake_row["entry"]["effect"] in text
    assert "still pay." in text

    ok, entry = check_kind("deck", "RED")
    assert ok is True
    assert entry is not None
    assert "+1 discard" in entry["effect"]


def test_list_deck_alias() -> None:
    from know import cmd_list  # type: ignore[unresolved-import]

    names = cmd_list("deck")["names"]
    assert "RED" in names
    assert "PLASMA" in names


def test_challenge_catalog_and_aliases() -> None:
    catalog = load_library("challenge")
    assert len(catalog) == 20
    assert set(catalog) == {
        "c_omelette_1",
        "c_city_1",
        "c_rich_1",
        "c_knife_1",
        "c_xray_1",
        "c_mad_world_1",
        "c_luxury_1",
        "c_non_perishable_1",
        "c_medusa_1",
        "c_double_nothing_1",
        "c_typecast_1",
        "c_inflation_1",
        "c_bram_poker_1",
        "c_fragile_1",
        "c_monolith_1",
        "c_blast_off_1",
        "c_five_card_1",
        "c_golden_needle_1",
        "c_cruelty_1",
        "c_jokerless_1",
    }
    for challenge_id, entry in catalog.items():
        assert challenge_id.startswith("c_")
        assert set(entry) == {
            "name",
            "name_zh",
            "stake",
            "effect",
            "deck",
            "jokers",
            "consumables",
            "vouchers",
            "rules",
            "restrictions",
            "wiki",
        }
        assert entry["stake"] == "WHITE"
        assert entry["wiki"].startswith("https://balatrowiki.org/w/Challenge_Decks/")

    for name in ("c_omelette_1", "The Omelette", "煎蛋卷"):
        ok, entry = check_kind("challenge", name)
        assert ok is True
        assert entry is not None
        assert entry["name"] == "The Omelette"

    ok, entry = check_kind("challenge", "not a real challenge")
    assert ok is False
    assert entry is None


def test_direct_challenge_command_accepts_chinese_name(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(sys, "argv", ["know.py", "challenge", "煎蛋卷"])
    assert know_main() == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["kind"] == "challenge"
    assert payload["name"] == "The Omelette"
    assert payload["name_zh"] == "煎蛋卷"


def test_knowledge_dir_env_override(monkeypatch: pytest.MonkeyPatch) -> None:
    from know import cmd_stats  # type: ignore[unresolved-import]
    from know_lib import load_library  # type: ignore[unresolved-import]

    fixture_dir = Path(__file__).parents[1] / "fixtures" / "knowledge_override"
    deck_data = {"RED": {"effect": "+1 discard each round", "source": []}}
    monkeypatch.setenv("BALATROBOT_KNOWLEDGE_DIR", str(fixture_dir))

    loaded = load_library("deck")
    assert loaded == deck_data

    stats = cmd_stats()
    assert stats["dir"] == str(fixture_dir.resolve())
    assert stats["libraries"]["deck"]["count"] == 1
