"""Tests for debuff endpoint (debug / estimate testing)."""

from __future__ import annotations

import httpx

from tests.lua.conftest import api, assert_error_response, load_fixture


class TestDebuffEndpoint:
    """Set and clear debuff on hand cards."""

    def test_debuff_hand_card(self, client: httpx.Client) -> None:
        gs = load_fixture(client, "gamestate", "state-SELECTING_HAND")
        gs = api(client, "add", {"key": "H_K", "enhancement": "WILD"})["result"]
        wild_idx = next(
            i
            for i, c in enumerate(gs["hand"]["cards"])
            if (c.get("modifier") or {}).get("enhancement") == "WILD"
        )
        gs = api(client, "debuff", {"cards": [wild_idx], "debuff": True})["result"]
        card = gs["hand"]["cards"][wild_idx]
        assert card.get("state", {}).get("debuff") is True

    def test_clear_debuff(self, client: httpx.Client) -> None:
        gs = load_fixture(client, "gamestate", "state-SELECTING_HAND")
        gs = api(client, "add", {"key": "D_5"})["result"]
        idx = gs["hand"]["count"] - 1
        gs = api(client, "debuff", {"cards": [idx], "debuff": True})["result"]
        assert gs["hand"]["cards"][idx].get("state", {}).get("debuff") is True
        gs = api(client, "debuff", {"cards": [idx], "debuff": False})["result"]
        assert not gs["hand"]["cards"][idx].get("state", {}).get("debuff")

    def test_debuff_invalid_index(self, client: httpx.Client) -> None:
        load_fixture(client, "gamestate", "state-SELECTING_HAND")
        assert_error_response(
            api(client, "debuff", {"cards": [999], "debuff": True}),
            "BAD_REQUEST",
            "Invalid card index: 999",
        )
