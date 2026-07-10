# Balatro Knowledge Library

This directory contains the local, machine-readable Balatro knowledge used by the play helpers.

## Files

- `balatro-*-verified.json`: lookup tables used by `tools/play/know.py` (jokers, bosses, tags, stakes, **decks**, challenges, tarots, planets, spectrals, vouchers). Each entry pairs a card effect with a `balatrowiki.org` URL. These are hand-maintained data files.
- `balatro-rules-verified.json`: hand-curated universal mechanics rules with source references. Prefer this for scoring/order/capacity rules that are not tied to one card name.

## Challenge catalog

`balatro-challenges-verified.json` contains the 20 native Challenge Decks. Entries
use the stable native challenge ID as the key and provide English and Simplified
Chinese names, the White Stake, a compact effect, starting deck/items, custom
rules, restrictions, and the individual `balatrowiki.org` page. Use
`bot.ps1 know challenge ID_OR_NAME` (or `know check challenge ...`) to query it.

This static catalog is intentionally separate from `bot.ps1 challenges`: the API
command returns profile-dependent unlock/completion state and the live game's
serialized setup, while this file supplies stable Wiki-backed facts and citations.

The play helper defaults to this directory, but it can be overridden with `BALATROBOT_KNOWLEDGE_DIR`.

## Rule Sources

The generic rule file (`balatro-rules-verified.json`) is source-backed exclusively by public Balatro Wiki pages on `https://balatrowiki.org/` — each rule's `source` array cites only wiki URLs (no `Balatro.exe` line references, no Fandom/Wikipedia/Steam guides). This keeps citations stable across game patches and consistent with the joker/boss/tag/stake libraries, which also cite `balatrowiki.org`.

Exact mechanic values (chip amounts, seal payouts, edition/enhancement numbers, poker-hand base values) are cross-verified against the installed game Lua bundled in `Balatro.exe` during maintenance, but that verification is used to correct the rule text rather than as a published citation. When a wiki page and the game source disagree, fix the rule to match the game and note the wiki lag in the rule text if it matters for play.
