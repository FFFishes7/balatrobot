"""Integration tests for skip tags that open a booster pack immediately."""

import random
import string

import httpx
import pytest

from tests.lua.conftest import api, assert_gamestate_response

# Only Charm Tag can appear on ante 1; other pack tags need ante 2+ (game.lua min_ante).
CHARM_TAG = "Charm Tag"
NON_PACK_SKIP_TAGS = frozenset(
    {
        "Foil Tag",
        "Economy Tag",
        "Boss Tag",
        "Investment Tag",
        "Coupon Tag",
    }
)

_SEARCH = random.Random(42)


def _random_seed() -> str:
    return "".join(_SEARCH.choices(string.ascii_uppercase + string.digits, k=8))


class TestSkipPackTag:
    """Skip a blind with a pack-granting tag → reported pack-open state."""

    def test_skip_charm_tag_reports_booster_opened(self, client: httpx.Client) -> None:
        for attempt in range(200):
            seed = _random_seed()
            api(client, "menu", {})
            gamestate = assert_gamestate_response(
                api(
                    client,
                    "start",
                    {"deck": "RED", "stake": "WHITE", "seed": seed},
                ),
                state="BLIND_SELECT",
            )
            tag = gamestate["blinds"]["small"]["tag_name"]
            if tag != CHARM_TAG:
                continue

            response = api(client, "skip", {}, timeout=60)
            gamestate = assert_gamestate_response(
                response, state="SMODS_BOOSTER_OPENED"
            )
            pack_cards = (gamestate.get("pack") or {}).get("cards") or []
            assert pack_cards, (
                f"expected open pack cards after skip tag {tag!r} "
                f"(seed={seed!r}, attempt={attempt})"
            )
            return

        pytest.fail("no Charm Tag found in 200 seeded starts (update search)")


class TestSkipNonPackTag:
    """Non-pack skip tags must settle on BLIND_SELECT without waiting for a pack."""

    def test_skip_non_pack_tag_stays_blind_select(self, client: httpx.Client) -> None:
        for attempt in range(200):
            seed = _random_seed()
            api(client, "menu", {})
            gamestate = assert_gamestate_response(
                api(
                    client,
                    "start",
                    {"deck": "RED", "stake": "WHITE", "seed": seed},
                ),
                state="BLIND_SELECT",
            )
            tag = gamestate["blinds"]["small"]["tag_name"]
            if tag not in NON_PACK_SKIP_TAGS:
                continue

            response = api(client, "skip", {}, timeout=15)
            gamestate = assert_gamestate_response(response, state="BLIND_SELECT")
            assert gamestate["blinds"]["small"]["status"] == "SKIPPED"
            pack_cards = (gamestate.get("pack") or {}).get("cards") or []
            assert not pack_cards, (
                f"non-pack tag {tag!r} should not open a pack (seed={seed!r})"
            )
            return

        pytest.fail("no non-pack skip tag found in 200 seeded starts (update search)")
