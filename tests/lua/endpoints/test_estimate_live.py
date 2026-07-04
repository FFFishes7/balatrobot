"""Live estimate vs play scoring — validates estimate.py against real Balatro."""

from __future__ import annotations

import httpx
import pytest

from tests.lua.endpoints.estimate_live_recipes import all_live_recipes
from tests.lua.endpoints.estimate_live_runner import run_live_recipe

_ALL_RECIPES = all_live_recipes()
_SCORING_IDS = [r.recipe_id for r in _ALL_RECIPES if r.check_unmodeled]
_BUFF_IDS = [r.recipe_id for r in _ALL_RECIPES if not r.check_unmodeled]


class TestEstimateLiveScoring:
    """Each deterministic scoring joker: estimate must match play delta."""

    @pytest.mark.parametrize(
        "recipe_id",
        _SCORING_IDS,
        ids=_SCORING_IDS,
    )
    def test_scoring_joker_matches_play(self, client: httpx.Client, recipe_id: str) -> None:
        recipe = next(r for r in _ALL_RECIPES if r.recipe_id == recipe_id)
        run_live_recipe(client, recipe)


class TestEstimateLiveCardBuffs:
    """Deterministic card buffs: estimate must match play delta."""

    @pytest.mark.parametrize(
        "recipe_id",
        _BUFF_IDS,
        ids=_BUFF_IDS,
    )
    def test_card_buff_matches_play(self, client: httpx.Client, recipe_id: str) -> None:
        recipe = next(r for r in _ALL_RECIPES if r.recipe_id == recipe_id)
        run_live_recipe(client, recipe)

    def test_scoring_joker_count(self) -> None:
        assert len(_SCORING_IDS) == 99

    def test_buff_recipe_count(self) -> None:
        assert len(_BUFF_IDS) == 9
