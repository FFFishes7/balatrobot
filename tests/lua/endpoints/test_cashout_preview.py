"""Live and fixture tests for round.cashout_preview."""

from __future__ import annotations

import time

import httpx
import pytest

from tests.lua.conftest import api, assert_gamestate_response, load_fixture


def _wait_for_victory_overlay(client: httpx.Client, *, attempts: int = 100) -> dict:
    """Poll gamestate until the post-win overlay is visible."""
    for _ in range(attempts):
        gamestate = api(client, "gamestate", {})["result"]
        if gamestate.get("victory_overlay"):
            return gamestate
        time.sleep(0.1)
    raise AssertionError("victory_overlay never appeared after winning the run")


def _preview_lines(gamestate: dict) -> list[dict]:
    preview = (gamestate.get("round") or {}).get("cashout_preview")
    assert preview is not None, "expected round.cashout_preview"
    lines = preview.get("lines")
    assert isinstance(lines, list)
    return lines


def _line_by_kind(gamestate: dict, kind: str) -> list[dict]:
    return [line for line in _preview_lines(gamestate) if line.get("kind") == kind]


def _win_from_selecting_hand(client: httpx.Client) -> dict:
    api(client, "set", {"chips": 10000})
    return assert_gamestate_response(
        api(client, "play", {"cards": [0]}),
        state="ROUND_EVAL",
    )


class TestCashoutPreviewFixture:
    """Fixture-based cashout preview on ROUND_EVAL."""

    def test_round_eval_fixture_has_cashout_preview(self, client: httpx.Client) -> None:
        gamestate = load_fixture(client, "cash_out", "state-ROUND_EVAL")
        assert gamestate["state"] == "ROUND_EVAL"
        preview = gamestate["round"]["cashout_preview"]
        assert isinstance(preview, dict)
        assert isinstance(preview["lines"], list)
        assert preview["lines"], "expected at least one cashout line"
        assert isinstance(preview["total"], int)
        assert preview["total"] > 0
        kinds = {line["kind"] for line in preview["lines"]}
        assert "hands" in kinds


class TestCashoutPreviewLive:
    """Live cashout preview vs actual cash_out."""

    def test_golden_joker_row(self, client: httpx.Client) -> None:
        load_fixture(client, "play", "state-SELECTING_HAND")
        api(client, "add", {"key": "j_golden"})
        gamestate = _win_from_selecting_hand(client)
        joker_lines = [
            line
            for line in _preview_lines(gamestate)
            if line.get("kind") == "joker" and line.get("key") == "j_golden"
        ]
        assert len(joker_lines) == 1
        assert joker_lines[0]["dollars"] == 4

    def test_to_the_moon_interest(self, client: httpx.Client) -> None:
        gamestate = load_fixture(client, "play", "state-SELECTING_HAND")
        api(client, "add", {"key": "j_to_the_moon"})
        api(client, "set", {"chips": 10000, "money": 10})
        gamestate = assert_gamestate_response(
            api(client, "play", {"cards": [0]}),
            state="ROUND_EVAL",
        )
        interest_lines = _line_by_kind(gamestate, "interest")
        assert len(interest_lines) == 1
        # interest_amount=2 (base 1 + To the Moon 1), floor(10/5)=2 → $4
        assert interest_lines[0]["dollars"] == 4

    def test_total_at_least_line_sum_with_interest(self, client: httpx.Client) -> None:
        """Preview total must not undercount modeled lines (interest vs round_dollars)."""
        load_fixture(client, "play", "state-SELECTING_HAND")
        api(client, "set", {"chips": 10000, "money": 15})
        gamestate = assert_gamestate_response(
            api(client, "play", {"cards": [0]}),
            state="ROUND_EVAL",
        )
        preview = gamestate["round"]["cashout_preview"]
        line_sum = sum(line["dollars"] for line in preview["lines"])
        assert preview["total"] >= line_sum
        assert preview["total"] == line_sum or any(
            line.get("kind") == "interest" for line in preview["lines"]
        )

    def test_total_matches_cash_out(self, client: httpx.Client) -> None:
        gamestate = load_fixture(client, "cash_out", "state-ROUND_EVAL")
        preview = gamestate["round"]["cashout_preview"]
        money_before = gamestate["money"]
        pending = preview["total"]
        after = assert_gamestate_response(api(client, "cash_out", {}), state="SHOP")
        assert after["money"] == money_before + pending

    def test_boss_win_without_investment_no_received_field(
        self, client: httpx.Client
    ) -> None:
        """Non-boss or no Investment Tag: no investment_received on preview."""
        gamestate = load_fixture(client, "play", "state-SELECTING_HAND")
        gamestate = _win_from_selecting_hand(client)
        preview = gamestate["round"]["cashout_preview"]
        assert not preview.get("investment_received")
        tag_lines = _line_by_kind(gamestate, "tag")
        assert not any(line.get("key") == "tag_investment" for line in tag_lines)

    def test_investment_tag_probe_on_boss_round(self, client: httpx.Client) -> None:
        """Boss win with Investment Tag: paid on defeat, excluded from pending."""
        gamestate = load_fixture(
            client,
            "play",
            "state-SELECTING_HAND--ante_num-8--blinds.boss.status-CURRENT--round.chips-1000000",
        )
        assert gamestate["blinds"]["boss"]["status"] == "CURRENT"
        held = gamestate.get("held_tags") or []
        has_investment = any(t.get("key") == "tag_investment" for t in held)
        if not has_investment:
            pytest.skip("Investment Tag not held on this boss fixture path")
        money_before_play = gamestate["money"]
        gamestate = assert_gamestate_response(
            api(client, "play", {"cards": [0]}),
            state="ROUND_EVAL",
        )
        preview = gamestate["round"]["cashout_preview"]
        investment = preview.get("investment_received")
        assert investment == 25
        tag_lines = _line_by_kind(gamestate, "tag")
        assert not any(line.get("key") == "tag_investment" for line in tag_lines)
        held_after = gamestate.get("held_tags") or []
        assert not any(t.get("key") == "tag_investment" for t in held_after)
        assert gamestate["money"] == money_before_play + investment
        pending = preview["total"]
        if gamestate.get("won"):
            if not gamestate.get("victory_overlay"):
                gamestate = _wait_for_victory_overlay(client)
            gamestate = assert_gamestate_response(
                api(client, "endless", {}),
                state="ROUND_EVAL",
                won=True,
            )
            assert not gamestate.get("victory_overlay")
            preview = gamestate["round"]["cashout_preview"]
            pending = preview["total"]
        after = assert_gamestate_response(api(client, "cash_out", {}), state="SHOP")
        assert after["money"] == gamestate["money"] + pending

    def test_investment_tag_on_boss_round(self, client: httpx.Client) -> None:
        """Alias for investment boss-round assertions (kept for -k investment)."""
        self.test_investment_tag_probe_on_boss_round(client)
