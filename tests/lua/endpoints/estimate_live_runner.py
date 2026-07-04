"""Run live estimate recipes against Balatro."""

from __future__ import annotations

import sys
from pathlib import Path

import httpx
import pytest

PLAY_ROOT = Path(__file__).resolve().parents[3] / "tools" / "play"
sys.path.insert(0, str(PLAY_ROOT))

import estimate  # noqa: E402  # type: ignore[unresolved-import]

from tests.lua.endpoints.estimate_live_recipes import CardAdd, LiveRecipe, PAIR_5  # noqa: E402
from tests.lua.conftest import api, load_fixture  # noqa: E402


def _ranks_equal(a: str | None, b: str) -> bool:
    if a is None:
        return False
    if a == b:
        return True
    return {a, b} == {"T", "10"}


def _card_key_parts(key: str) -> tuple[str, str]:
    suit, rank = key.split("_", 1)
    return suit, rank


def _hand_rank(gs: dict, idx: int) -> str | None:
    cards = (gs.get("hand") or {}).get("cards") or []
    if idx >= len(cards):
        return None
    return (cards[idx].get("value") or {}).get("rank")


def _hand_suit(gs: dict, idx: int) -> str | None:
    cards = (gs.get("hand") or {}).get("cards") or []
    if idx >= len(cards):
        return None
    return (cards[idx].get("value") or {}).get("suit")


def _card_matches_add(gs: dict, idx: int, want: CardAdd) -> bool:
    cards = (gs.get("hand") or {}).get("cards") or []
    if idx >= len(cards):
        return False
    c = cards[idx]
    val = c.get("value") or {}
    mod = c.get("modifier") or {}
    ws, wr = _card_key_parts(want.key)
    if not _ranks_equal(val.get("rank"), wr) or val.get("suit") != ws:
        return False
    if want.enhancement and mod.get("enhancement") != want.enhancement:
        return False
    if want.edition and mod.get("edition") != want.edition:
        return False
    if want.seal and mod.get("seal") != want.seal:
        return False
    return True


def _indices_for_cards(gs: dict, wants: tuple[CardAdd, ...]) -> list[int]:
    used: set[int] = set()
    indices: list[int] = []
    for want in wants:
        found = False
        for i in range((gs.get("hand") or {}).get("count", 0)):
            if i in used:
                continue
            if _card_matches_add(gs, i, want):
                indices.append(i)
                used.add(i)
                found = True
                break
        if not found:
            raise AssertionError(f"card not found in hand: {want.key} enh={want.enhancement}")
    return indices


def _indices_for_rank(gs: dict, rank: str, count: int = 2) -> list[int]:
    found = [
        i
        for i in range((gs.get("hand") or {}).get("count", 0))
        if _hand_rank(gs, i) == rank
    ]
    if len(found) < count:
        raise AssertionError(f"need {count} cards rank {rank}, found {len(found)}")
    return found[:count]


def _play_delta(client: httpx.Client, gs: dict, indices: list[int]) -> int:
    chips_before = gs["round"]["chips"]
    gs_after = api(client, "play", {"cards": indices})["result"]
    return gs_after["round"]["chips"] - chips_before


def _add_cards(client: httpx.Client, gs: dict, cards: tuple[CardAdd, ...]) -> dict:
    for card in cards:
        gs = api(client, "add", card.to_add_params())["result"]
    return gs


def setup_recipe(client: httpx.Client, recipe: LiveRecipe) -> dict:
    gs = load_fixture(client, "gamestate", "state-SELECTING_HAND")
    for key in recipe.joker_keys:
        gs = api(client, "add", {"key": key})["result"]
    gs = _add_cards(client, gs, recipe.cards)
    if recipe.set_state:
        gs = api(client, "set", recipe.set_state)["result"]
    if recipe.require_loyalty_active:
        loyalty_ok = False
        for j in (gs.get("jokers") or {}).get("cards") or []:
            if j.get("key") != "j_loyalty_card":
                continue
            stats = (j.get("value") or {}).get("stats") or {}
            every = stats.get("loyalty_every")
            remaining = stats.get("loyalty_remaining")
            if every is not None and remaining is not None and int(remaining) == int(every):
                loyalty_ok = True
                break
        if not loyalty_ok:
            pytest.skip("Loyalty Card countdown not active for ×Mult proc")
    if recipe.pre_play_pair:
        idx = _indices_for_rank(gs, "5", 2)
        api(client, "play", {"cards": idx})
        gs = api(client, "gamestate")["result"]
        gs = _add_cards(client, gs, PAIR_5)
    gs = _maybe_add_round_target_cards(client, gs, recipe)
    return gs


def _maybe_add_round_target_cards(client: httpx.Client, gs: dict, recipe: LiveRecipe) -> dict:
    if recipe.pick == "ancient":
        suit = (gs.get("round") or {}).get("ancient_suit")
        if not suit:
            pytest.skip("round.ancient_suit not set in fixture")
        have = sum(
            1
            for i in range((gs.get("hand") or {}).get("count", 0))
            if _hand_suit(gs, i) == suit
        )
        if have < 2:
            gs = _add_cards(client, gs, (CardAdd(f"{suit}_5"), CardAdd(f"{suit}_6")))
        return gs
    if recipe.pick == "idol":
        rnd = gs.get("round") or {}
        rank = rnd.get("idol_rank")
        suit = rnd.get("idol_suit")
        if not rank or not suit:
            pytest.skip("round.idol_rank/idol_suit not set in fixture")
        have_idol = any(
            _hand_rank(gs, i) == rank and _hand_suit(gs, i) == suit
            for i in range((gs.get("hand") or {}).get("count", 0))
        )
        if not have_idol:
            gs = api(client, "add", {"key": f"{suit}_{rank}"})["result"]
        have_five = _indices_for_rank(gs, "5", 1)
        if not have_five:
            gs = api(client, "add", {"key": "S_5"})["result"]
        return gs
    return gs


def pick_indices(gs: dict, recipe: LiveRecipe) -> list[int]:
    pick = recipe.pick
    if pick == "top":
        est = estimate.estimate(gs)
        return est["estimate"]["top"][0]["indices"]
    if pick == "play_added":
        return _indices_for_cards(gs, recipe.cards)
    if pick == "pair_5s":
        return _indices_for_rank(gs, "5", 2)
    if pick == "pair_rank":
        rank = _card_key_parts(recipe.cards[0].key)[1]
        return _indices_for_rank(gs, rank, 2)
    if pick == "pair_suit":
        suit = _card_key_parts(recipe.cards[0].key)[0]
        found = [
            i
            for i in range((gs.get("hand") or {}).get("count", 0))
            if _hand_suit(gs, i) == suit
        ][:2]
        if len(found) < 2:
            raise AssertionError(f"need 2 cards suit {suit}, found {len(found)}")
        return found
    if pick == "three_k":
        return _indices_for_rank(gs, "K", 3)
    if pick == "two_pair":
        return _indices_for_rank(gs, "K", 2) + _indices_for_rank(gs, "5", 2)
    if pick == "straight_5":
        return _indices_for_cards(gs, recipe.cards)
    if pick == "flush_5d":
        return _indices_for_cards(gs, recipe.cards)
    if pick == "four_k":
        return _indices_for_cards(gs, recipe.cards[:4])
    if pick == "four_flush":
        return _indices_for_cards(gs, recipe.cards)
    if pick == "flower_pot":
        return _indices_for_cards(gs, recipe.cards)
    if pick == "seeing_double":
        return _indices_for_cards(gs, recipe.cards)
    if pick == "blackboard":
        return _indices_for_cards(gs, recipe.cards[:2])
    if pick == "baron_hold":
        return _indices_for_rank(gs, "5", 2)
    if pick == "shoot_hold":
        return _indices_for_rank(gs, "5", 2)
    if pick == "raised_fist_hold":
        return _indices_for_rank(gs, "5", 2)
    if pick == "mime_steel":
        return _indices_for_rank(gs, "5", 2)
    if pick == "high_stone":
        return _indices_for_cards(gs, recipe.cards)
    if pick == "ancient":
        suit = (gs.get("round") or {}).get("ancient_suit")
        if not suit:
            pytest.skip("round.ancient_suit not set")
        found = [
            i
            for i in range((gs.get("hand") or {}).get("count", 0))
            if _hand_suit(gs, i) == suit
        ]
        if len(found) < 2:
            raise AssertionError(f"need 2 cards suit {suit}")
        return found[:2]
    if pick == "idol":
        rnd = gs.get("round") or {}
        rank = rnd.get("idol_rank")
        suit = rnd.get("idol_suit")
        if not rank or not suit:
            pytest.skip("round.idol_rank/idol_suit not set")
        idol_idx = next(
            i
            for i in range((gs.get("hand") or {}).get("count", 0))
            if _hand_rank(gs, i) == rank and _hand_suit(gs, i) == suit
        )
        five_idx = _indices_for_rank(gs, "5", 1)[0]
        if five_idx == idol_idx:
            five_idx = _indices_for_rank(gs, "5", 2)[1]
        return [idol_idx, five_idx]
    raise ValueError(f"unknown pick strategy: {pick}")


def assert_estimate_matches_play(
    client: httpx.Client,
    gs: dict,
    indices: list[int],
    *,
    check_unmodeled: bool = True,
) -> None:
    est_full = estimate.estimate(gs)
    if check_unmodeled:
        assert not est_full["estimate"]["unmodeled_jokers"], (
            f"unexpected unmodeled: {est_full['estimate']['unmodeled_jokers']}"
        )
    est_line = estimate.score_hand_indices(gs, indices)
    delta = _play_delta(client, gs, indices)
    assert delta == est_line["score"], (
        f"estimate={est_line['score']} actual={delta} "
        f"hand={est_line['hand_type']} idx={indices}"
    )


def run_live_recipe(client: httpx.Client, recipe: LiveRecipe) -> None:
    gs = setup_recipe(client, recipe)
    indices = pick_indices(gs, recipe)
    assert_estimate_matches_play(
        client, gs, indices, check_unmodeled=recipe.check_unmodeled
    )
