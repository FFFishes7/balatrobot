# BlindDeck API Reference

JSON-RPC 2.0 API for controlling Balatro locally via **BlindDeck**.

## Overview

- **Protocol**: JSON-RPC 2.0 over HTTP/1.1
- **Endpoint**: `http://127.0.0.1:12346` (default)
- **Content-Type**: `application/json`

### Request Format

```json
{
  "jsonrpc": "2.0",
  "method": "method_name",
  "params": { ... },
  "id": 1
}
```

### Response Format

**Success:**

```json
{
  "jsonrpc": "2.0",
  "result": { ... },
  "id": 1
}
```

**Error:**

```json
{
  "jsonrpc": "2.0",
  "error": {
    "code": -32001,
    "message": "Error description",
    "data": { "name": "BAD_REQUEST" }
  },
  "id": 1
}
```

## Quickstart

#### 1. Health Check

```bash
curl -X POST http://127.0.0.1:12346 \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "method": "health", "id": 1}'
```

#### 2. Get Game State

```bash
curl -X POST http://127.0.0.1:12346 \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "method": "gamestate", "id": 1}'
```

#### 3. Start a New Run

```bash
curl -X POST http://127.0.0.1:12346 \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "method": "start", "params": {"deck": "RED", "stake": "WHITE"}, "id": 1}'
```

#### 4. Select Blind and Play Cards

```bash
# Select the blind
curl -X POST http://127.0.0.1:12346 \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "method": "select", "id": 1}'

# Play cards at indices 0, 1, 2
curl -X POST http://127.0.0.1:12346 \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "method": "play", "params": {"cards": [0, 1, 2]}, "id": 1}'
```

## Game States

The game progresses through these states:

```
MENU ──► BLIND_SELECT ──► SELECTING_HAND ──► ROUND_EVAL ──► SHOP ─┐
                ▲                │                                │
                │                ▼                                │
                │            GAME_OVER                            │
                │                                                 │
                └─────────────────────────────────────────────────┘
```

| State                  | Description                                                                       |
| ---------------------- | --------------------------------------------------------------------------------- |
| `MENU`                 | Main menu                                                                         |
| `BLIND_SELECT`         | Choosing which blind to play, skip, or reroll Boss ($10; Director's Cut / Retcon) |
| `SELECTING_HAND`       | Selecting cards to play or discard                                                |
| `ROUND_EVAL`           | Round complete, ready to cash out                                                 |
| `SHOP`                 | Shopping phase                                                                    |
| `SMODS_BOOSTER_OPENED` | Booster pack opened; `pack.choices_remaining` shows picks still required          |
| `GAME_OVER`            | Game ended                                                                        |

---

## Methods

- [`health`](#health) - Health check endpoint
- [`gamestate`](#gamestate) - Get the complete current game state
- [`rpc.discover`](#rpcdiscover) - Returns the OpenRPC specification
- [`start`](#start) - Start a new game run
- [`challenges`](#challenges) - List native challenges and profile availability
- [`challenge`](#challenge) - Start an unlocked native challenge
- [`menu`](#menu) - Return to the main menu
- [`save`](#save) - Save the current run to a file
- [`load`](#load) - Load a saved run from a file
- [`select`](#select) - Select the current blind to begin the round
- [`skip`](#skip) - Skip the current blind (Small or Big only)
- [`buy`](#buy) - Buy a card, voucher, or pack from the shop
- [`pack`](#pack) - Select a card or skip an opened booster pack; Tarot and Spectral cards may require hand targets
- [`sell`](#sell) - Sell a joker or consumable
- [`reroll`](#reroll) - Reroll the shop items
- [`reroll_boss`](#reroll_boss) - Reroll the Boss blind ($10; Director's Cut / Retcon)
- [`cash_out`](#cash_out) - Cash out round rewards and transition to shop
- [`endless`](#endless) - Dismiss victory overlay to continue in endless mode
- [`next_round`](#next_round) - Leave the shop and advance to blind selection
- [`play`](#play) - Play cards from hand
- [`discard`](#discard) - Discard cards from hand
- [`rearrange`](#rearrange) - Rearrange jokers
- [`sort`](#sort) - Sort hand cards using Balatro's native rank or suit sort
- [`use`](#use) - Use a consumable card
- [`add`](#add) - Add a card to the game (debug/testing)
- [`debuff`](#debuff) - Set or clear debuff on hand cards (debug / estimate testing)
- [`screenshot`](#screenshot) - Take a screenshot of the game
- [`set`](#set) - Set in-game values (debug/testing)

---

### `health`

Health check endpoint.

**Returns:** `{ "status": "ok" }`

**Example:**

```bash
curl -X POST http://127.0.0.1:12346 \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "method": "health", "id": 1}'
```

---

### `gamestate`

Get the complete current game state.

**Returns:** [GameState](#gamestate-schema) object

**Example:**

```bash
curl -X POST http://127.0.0.1:12346 \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "method": "gamestate", "id": 1}'
```

---

### `rpc.discover`

Returns the OpenRPC specification for this API.

**Returns:** OpenRPC schema document

**Example:**

```bash
curl -X POST http://127.0.0.1:12346 \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "method": "rpc.discover", "id": 1}'
```

---

### `start`

Start a new game run.

**Parameters:**

| Name    | Type   | Required | Description           |
| ------- | ------ | -------- | --------------------- |
| `deck`  | string | Yes      | [Deck](#deck) to use  |
| `stake` | string | Yes      | [Stake](#stake) level |
| `seed`  | string | No       | Seed for the run      |

**Returns:** [GameState](#gamestate-schema) (state will be `BLIND_SELECT`)

**Errors:** `BAD_REQUEST`, `INVALID_STATE`, `INTERNAL_ERROR`

**Required State:** `MENU`

**Example:**

```bash
curl -X POST http://127.0.0.1:12346 \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "method": "start", "params": {"deck": "BLUE", "stake": "WHITE", "seed": "TEST123"}, "id": 1}'
```

---

### `challenges`

List the 20 native Balatro challenges with their stable IDs, localized names,
profile-specific unlock/completion status, and native setup.

**Returns:** `{ "challenges": Challenge[] }`. Each challenge includes `id`,
`index`, `name`, `unlocked`, `completed`, `deck`, `jokers`, `consumables`,
`vouchers`, `rules`, and `restrictions`.

**Required State:** Any state

**Example:**

```bash
curl -X POST http://127.0.0.1:12346 \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "method": "challenges", "id": 1}'
```

---

### `challenge`

Start an unlocked native challenge by the stable ID returned by
[`challenges`](#challenges). The challenge supplies its own deck, rules,
restrictions, and White Stake; it does not accept deck, stake, or seed overrides.

**Parameters:**

| Name | Type   | Required | Description                              |
| ---- | ------ | -------- | ---------------------------------------- |
| `id` | string | Yes      | Native challenge ID, e.g. `c_omelette_1` |

**Returns:** [GameState](#gamestate-schema) (state will be `BLIND_SELECT`)

**Errors:** `BAD_REQUEST`, `INVALID_STATE`, `NOT_ALLOWED`

**Required State:** `MENU`

**Example:**

```bash
curl -X POST http://127.0.0.1:12346 \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "method": "challenge", "params": {"id": "c_omelette_1"}, "id": 1}'
```

---

### `menu`

Return to the main menu from any state.

**Returns:** [GameState](#gamestate-schema) (state will be `MENU`)

**Example:**

```bash
curl -X POST http://127.0.0.1:12346 \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "method": "menu", "id": 1}'
```

---

### `save`

Save the current run to a file.

On Windows, relative paths are resolved by the Balatro/LÖVE process. For example, `path: "run.jkr"` writes under `C:\Users\<username>\AppData\Roaming\Balatro\`. Use an absolute path to save elsewhere.

**Parameters:**

| Name   | Type   | Required | Description            |
| ------ | ------ | -------- | ---------------------- |
| `path` | string | Yes      | File path for the save |

**Returns:** `{ "success": true, "path": "..." }`

**Errors:** `INVALID_STATE`, `INTERNAL_ERROR`, `NOT_ALLOWED` (victory overlay visible — call [`endless`](#endless) or [`menu`](#menu) first)

**Example:**

```bash
curl -X POST http://127.0.0.1:12346 \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "method": "save", "params": {"path": "/tmp/save.jkr"}, "id": 1}'
```

---

### `load`

Load a saved run from a file.

**Parameters:**

| Name   | Type   | Required | Description           |
| ------ | ------ | -------- | --------------------- |
| `path` | string | Yes      | Path to the save file |

**Returns:** `{ "success": true, "path": "..." }`

**Errors:** `INTERNAL_ERROR`

**Example:**

```bash
curl -X POST http://127.0.0.1:12346 \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "method": "load", "params": {"path": "/tmp/save.jkr"}, "id": 1}'
```

---

### `select`

Select the current blind to begin the round.

**Returns:** [GameState](#gamestate-schema) (state will be `SELECTING_HAND`)

**Errors:** `INVALID_STATE`

**Required State:** `BLIND_SELECT`

**Example:**

```bash
curl -X POST http://127.0.0.1:12346 \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "method": "select", "id": 1}'
```

---

### `skip`

Skip the current blind (Small or Big only).

**Returns:** [GameState](#gamestate-schema)

**Errors:** `INVALID_STATE`, `NOT_ALLOWED`

**Required State:** `BLIND_SELECT`

**Example:**

```bash
curl -X POST http://127.0.0.1:12346 \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "method": "skip", "id": 1}'
```

---

### `reroll_boss`

Reroll the Boss blind for **$10** during blind selection. Requires **Director's Cut** (once per ante) or **Retcon** (unlimited). Same rules as the in-game Reroll Boss button.

**Returns:** [GameState](#gamestate-schema) (state stays `BLIND_SELECT`; boss name/effect update)

**Errors:** `INVALID_STATE`, `NOT_ALLOWED`, `INTERNAL_ERROR`

**Required State:** `BLIND_SELECT` with Boss on deck

**Affordability:** `money - bankrupt_at >= 10`

**Example:**

```bash
curl -X POST http://127.0.0.1:12346 \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "method": "reroll_boss", "id": 1}'
```

---

### `buy`

Buy a card, voucher, or pack from the shop.

**Parameters:** (exactly one required)

| Name      | Type    | Required | Description                     |
| --------- | ------- | -------- | ------------------------------- |
| `card`    | integer | No       | 0-based index of card to buy    |
| `voucher` | integer | No       | 0-based index of voucher to buy |
| `pack`    | integer | No       | 0-based index of pack to buy    |

**Returns:** [GameState](#gamestate-schema)

**Errors:** `BAD_REQUEST`, `NOT_ALLOWED`

**Required State:** `SHOP`

**Affordability:** A purchase succeeds only when `cost <= money - bankrupt_at` (see [`GameState`](#gamestate-schema)). Credit Card and similar jokers raise `bankrupt_at`, so raw `money` can overstate what you can spend.

**Example:**

```bash
# Buy first card in shop
curl -X POST http://127.0.0.1:12346 \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "method": "buy", "params": {"card": 0}, "id": 1}'
```

---

### `pack`

Select a card or skip a pack from an opened booster pack.

After buying a pack with [`buy`](#buy), this method allows you to select a card from the pack or skip the selection. Different pack types behave differently:

- **Buffoon packs**: Selected jokers are added to your joker slots
- **Standard packs**: Selected playing cards are added to your deck
- **Arcana/Celestial/Spectral packs**: Selected consumables are **used immediately**

The returned [GameState](#gamestate-schema) includes `pack.choices_remaining` (from `G.GAME.pack_choices`) while a booster is open — shop normal Arcana usually **1**; **Charm Tag** skip opens Mega Arcana (**2**, then **1** after the first pick). The play helper shows this as `choices remaining: N` in `glance`. **`skip: true`** forfeits all remaining picks in the current pack.

Some Tarot and Spectral cards require you to select target cards from your hand (e.g., The Magician enhances 1-2 cards to Lucky). **Ankh, Hex, and Ectoplasm** (`random_joker_effect` on the card `value`) pick a **random** joker — `targets` only highlight hand cards and do not select a joker slot. See `requires_jokers_min` on Ankh/Hex (at least one joker must be present).

**Parameters:** (exactly one required)

| Name      | Type      | Required | Description                                                              |
| --------- | --------- | -------- | ------------------------------------------------------------------------ |
| `card`    | integer   | No       | 0-based index of card to select from pack                                |
| `targets` | integer[] | No       | 0-based indices of hand cards to target (for consumables that need them) |
| `skip`    | boolean   | No       | Forfeit all remaining picks in the current pack without choosing a card  |

**Returns:** [GameState](#gamestate-schema)

**Errors:** `BAD_REQUEST`, `INVALID_STATE`, `NOT_ALLOWED`

**Required State:** `SMODS_BOOSTER_OPENED`

**Examples:**

```bash
# Select first card from a Buffoon pack (adds joker to slots)
curl -X POST http://127.0.0.1:12346 \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "method": "pack", "params": {"card": 0}, "id": 1}'

# Select a Tarot card requiring targets (e.g., The Magician on 2 hand cards)
curl -X POST http://127.0.0.1:12346 \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "method": "pack", "params": {"card": 0, "targets": [0, 1]}, "id": 1}'

# Skip pack selection
curl -X POST http://127.0.0.1:12346 \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "method": "pack", "params": {"skip": true}, "id": 1}'
```

---

### `sell`

Sell a joker or consumable. This is not available during `ROUND_EVAL`; cash out first.

**Parameters:** (exactly one required)

| Name         | Type    | Required | Description                         |
| ------------ | ------- | -------- | ----------------------------------- |
| `joker`      | integer | No       | 0-based index of joker to sell      |
| `consumable` | integer | No       | 0-based index of consumable to sell |

**Returns:** [GameState](#gamestate-schema)

**Errors:** `BAD_REQUEST`, `INVALID_STATE`, `NOT_ALLOWED` (victory overlay visible — call [`endless`](#endless) or [`menu`](#menu) first)

**Required State:** `BLIND_SELECT`, `SELECTING_HAND`, `SHOP`, or `SMODS_BOOSTER_OPENED`

**Example:**

```bash
# Sell first joker
curl -X POST http://127.0.0.1:12346 \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "method": "sell", "params": {"joker": 0}, "id": 1}'
```

---

### `reroll`

Reroll the shop items (costs money).

**Returns:** [GameState](#gamestate-schema)

**Errors:** `INVALID_STATE`, `NOT_ALLOWED`

**Affordability:** Same as [`buy`](#buy) — reroll cost must be `<= money - bankrupt_at`.

**Required State:** `SHOP`

**Example:**

```bash
curl -X POST http://127.0.0.1:12346 \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "method": "reroll", "id": 1}'
```

---

### `cash_out`

Cash out round rewards and transition to shop. The response waits until the shop
has stable buyable items **and** the pending tag stack is settled (`held_tags_ready`
is true), so shop-entry tags (Foil, Coupon, etc.) can finish applying before the
snapshot is returned.

**Returns:** [GameState](#gamestate-schema) (state will be `SHOP`)

**Errors:** `INVALID_STATE`, `NOT_ALLOWED` (victory overlay visible — call [`endless`](#endless) or [`menu`](#menu) first)

**Required State:** `ROUND_EVAL` without `victory_overlay`

**Example:**

```bash
curl -X POST http://127.0.0.1:12346 \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "method": "cash_out", "id": 1}'
```

---

### `next_round`

Leave the shop and advance to blind selection.

**Returns:** [GameState](#gamestate-schema) (state will be `BLIND_SELECT`)

**Errors:** `INVALID_STATE`

**Required State:** `SHOP`

**Example:**

```bash
curl -X POST http://127.0.0.1:12346 \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "method": "next_round", "id": 1}'
```

---

### `play`

Play cards from hand.

**Parameters:**

| Name    | Type      | Required | Description                                  |
| ------- | --------- | -------- | -------------------------------------------- |
| `cards` | integer[] | Yes      | 0-based indices of cards to play (1-5 cards) |

**Returns:** [GameState](#gamestate-schema)

**Errors:** `BAD_REQUEST`

**Required State:** `SELECTING_HAND`

**Example:**

```bash
# Play cards at positions 0, 2, 4
curl -X POST http://127.0.0.1:12346 \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "method": "play", "params": {"cards": [0, 2, 4]}, "id": 1}'
```

---

### `endless`

Dismiss the post-win victory overlay (same as the in-game **Endless** button) so the run can continue into endless mode (Ante 9+).

**Returns:** [GameState](#gamestate-schema) (state remains `ROUND_EVAL`; `victory_overlay` becomes absent)

**Errors:** `INVALID_STATE`, `NOT_ALLOWED` (run not won, or overlay already dismissed)

**Required State:** `ROUND_EVAL` with `won: true` and `victory_overlay: true`

**Typical flow after beating Ante 8 Boss:** `endless` → [`cash_out`](#cash_out) → shop → [`next_round`](#next_round)

**Example:**

```bash
curl -X POST http://127.0.0.1:12346 \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "method": "endless", "id": 1}'
```

---

### `discard`

Discard cards from hand.

**Parameters:**

| Name    | Type      | Required | Description                         |
| ------- | --------- | -------- | ----------------------------------- |
| `cards` | integer[] | Yes      | 0-based indices of cards to discard |

**Returns:** [GameState](#gamestate-schema)

**Errors:** `BAD_REQUEST`

**Required State:** `SELECTING_HAND`

**Example:**

```bash
# Discard cards at positions 0 and 1
curl -X POST http://127.0.0.1:12346 \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "method": "discard", "params": {"cards": [0, 1]}, "id": 1}'
```

---

### `rearrange`

Rearrange jokers. The supplied indices must be a complete permutation of the
current Joker slots.

**Parameters:**

| Name     | Type      | Required | Description                                            |
| -------- | --------- | -------- | ------------------------------------------------------ |
| `jokers` | integer[] | Yes      | Complete new order of all Jokers using 0-based indices |

**Returns:** [GameState](#gamestate-schema)

**Errors:** `BAD_REQUEST`, `INVALID_STATE`, `NOT_ALLOWED`

**Required State:** `SELECTING_HAND`, `SHOP`, or `SMODS_BOOSTER_OPENED`

**Example:**

```bash
# Put the second Joker before the first
curl -X POST http://127.0.0.1:12346 \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "method": "rearrange", "params": {"jokers": [1, 0]}, "id": 1}'
```

---

### `sort`

Sort hand cards using Balatro's native hand sort logic. This uses the same `CardArea:sort` methods as the in-game Rank and Suit buttons.

**Parameters:**

| Name   | Type   | Required | Description                                                                                                                        |
| ------ | ------ | -------- | ---------------------------------------------------------------------------------------------------------------------------------- |
| `mode` | string | No       | Sort mode: `rank`/`rank-desc`/`value`/`value-desc`, `rank-asc`/`value-asc`, `suit`/`suit-desc`, or `suit-asc`. Defaults to `rank`. |

**Returns:** [GameState](#gamestate-schema)

**Errors:** `BAD_REQUEST`, `NOT_ALLOWED`

**Required State:** `SELECTING_HAND`

**Example:**

```bash
# Sort hand by rank descending (default)
curl -X POST http://127.0.0.1:12346 \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "method": "sort", "id": 1}'

# Sort hand by suit ascending
curl -X POST http://127.0.0.1:12346 \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "method": "sort", "params": {"mode": "suit-asc"}, "id": 1}'
```

---

### `use`

Use a consumable card. This is not available during `ROUND_EVAL`; cash out first.

**Parameters:**

| Name         | Type      | Required | Description                                                              |
| ------------ | --------- | -------- | ------------------------------------------------------------------------ |
| `consumable` | integer   | Yes      | 0-based index of consumable to use                                       |
| `cards`      | integer[] | No       | 0-based indices of target cards (for consumables that require selection) |

**Returns:** [GameState](#gamestate-schema)

**Errors:** `BAD_REQUEST`, `INVALID_STATE`, `NOT_ALLOWED` (victory overlay visible — call [`endless`](#endless) or [`menu`](#menu) first)

**Required State:** `BLIND_SELECT`, `SELECTING_HAND`, `SHOP`, or `SMODS_BOOSTER_OPENED`

**Example:**

```bash
# Use The Magician on cards 0 and 1
curl -X POST http://127.0.0.1:12346 \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "method": "use", "params": {"consumable": 0, "cards": [0, 1]}, "id": 1}'
```

---

### `add`

Add a card to the game (debug/testing). Supports jokers, consumables, vouchers, packs, and playing cards.

!!! note "API vs `bot.ps1`"

    The JSON-RPC `add` method is always callable when the mod is loaded (integration tests use it directly). **`bot.ps1 add`** is gated by `BALATROBOT_ALLOW_CHEATS=1` and only accepts `joker` / `card` / `consumable` — not voucher or pack keys. Use `exec` or `balatrobot api add` for full params.

**Parameters:**

| Name          | Type    | Required | Description                                                                    |
| ------------- | ------- | -------- | ------------------------------------------------------------------------------ |
| `key`         | string  | Yes      | [Card key](#card-keys) (e.g., `j_joker`, `c_fool`, `p_arcana_normal_1`, `H_A`) |
| `seal`        | string  | No       | [Seal](#card-modifier-seal) type (playing cards only)                          |
| `edition`     | string  | No       | [Edition](#card-modifier-edition) type (not vouchers or packs)                 |
| `enhancement` | string  | No       | [Enhancement](#card-modifier-enhancement) type (playing cards only)            |
| `eternal`     | boolean | No       | Cannot be sold/destroyed (jokers only)                                         |
| `perishable`  | integer | No       | Rounds until perish (jokers only)                                              |
| `rental`      | boolean | No       | Adds the rental sticker; runtime fee is returned as `modifier.rental_cost`     |

**Returns:** [GameState](#gamestate-schema)

**Errors:** `BAD_REQUEST`, `INVALID_STATE`, `NOT_ALLOWED`

**Required State:** Vouchers and packs require `SHOP` state. Packs also require available booster slots.

**Examples:**

```bash
# Add a Polychrome Joker
curl -X POST http://127.0.0.1:12346 \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "method": "add", "params": {"key": "j_joker", "edition": "POLYCHROME"}, "id": 1}'

# Add an Arcana Pack to the shop (requires SHOP state)
curl -X POST http://127.0.0.1:12346 \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "method": "add", "params": {"key": "p_arcana_normal_1"}, "id": 1}'
```

---

### `debuff`

Set or clear debuff on hand cards (debug / estimate testing). Uses the game's `Card:set_debuff` — debuffed cards show `(rank♠)` in `glance` and Wild cards revert to their printed suit for scoring.

**Parameters:**

| Name     | Type      | Required | Description                           |
| -------- | --------- | -------- | ------------------------------------- |
| `cards`  | integer[] | Yes      | 0-based hand card indices (non-empty) |
| `debuff` | boolean   | Yes      | `true` to debuff, `false` to clear    |

**Returns:** [GameState](#gamestate-schema)

**Errors:** `BAD_REQUEST`, `INVALID_STATE`

**Required State:** `SELECTING_HAND`

**Example:**

```bash
curl -X POST http://127.0.0.1:12346 \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "method": "debuff", "params": {"cards": [0], "debuff": true}, "id": 1}'
```

Friendly CLI: `bot.ps1 debuff 0` · `bot.ps1 debuff clear 0` (requires `BALATROBOT_ALLOW_CHEATS=1`).

---

### `screenshot`

Take a screenshot of the game.

**Parameters:**

| Name   | Type   | Required | Description                  |
| ------ | ------ | -------- | ---------------------------- |
| `path` | string | Yes      | File path for PNG screenshot |

**Returns:** `{ "success": true, "path": "..." }`

**Errors:** `INTERNAL_ERROR`

**Example:**

```bash
curl -X POST http://127.0.0.1:12346 \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "method": "screenshot", "params": {"path": "/tmp/screenshot.png"}, "id": 1}'
```

---

### `set`

Set in-game values (debug/testing).

!!! note "API vs `bot.ps1`"

    The JSON-RPC `set` method accepts all parameters below. **`bot.ps1 set`** requires `BALATROBOT_ALLOW_CHEATS=1` and only maps `hands`, `discards`, and `chips` (`tools/play/cheats.py`). For `money`, `ante`, `grant_voucher`, `boss_rerolled`, or `shop`, use `exec` or `balatrobot api set`.

**Parameters:** (at least one required)

| Name            | Type    | Required | Description                                                                 |
| --------------- | ------- | -------- | --------------------------------------------------------------------------- |
| `money`         | integer | No       | Set money amount                                                            |
| `chips`         | integer | No       | Set chips scored                                                            |
| `ante`          | integer | No       | Set ante number                                                             |
| `round`         | integer | No       | Set round number                                                            |
| `hands`         | integer | No       | Set hands remaining                                                         |
| `discards`      | integer | No       | Set discards remaining                                                      |
| `shop`          | boolean | No       | Re-stock shop (SHOP state only)                                             |
| `grant_voucher` | string  | No       | Mark a voucher redeemed (debug / integration tests; e.g. `v_directors_cut`) |
| `boss_rerolled` | boolean | No       | Set whether Boss reroll was used this ante (debug / testing)                |

**Returns:** [GameState](#gamestate-schema)

**Errors:** `BAD_REQUEST`, `INVALID_STATE`, `NOT_ALLOWED`

**Example:**

```bash
# Set money to 100 and hands to 5
curl -X POST http://127.0.0.1:12346 \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "method": "set", "params": {"money": 100, "hands": 5}, "id": 1}'
```

---

## Schemas

### GameState Schema

The complete game state returned by most methods.

```json
{
  "state": "SELECTING_HAND",
  "round_num": 1,
  "ante_num": 1,
  "money": 4,
  "bankrupt_at": 0,
  "deck": "RED",
  "stake": "WHITE",
  "challenge": { "id": "c_omelette_1", "name": "The Omelette" },
  "seed": "ABC123",
  "won": false,
  "victory_overlay": false,
  "used_vouchers": {},
  "hands": { ... },
  "round": { ... },
  "blinds": { ... },
  "jokers": { ... },
  "consumables": { ... },
  "cards": { ... },
  "hand": { ... },
  "shop": { ... },
  "vouchers": { ... },
  "packs": { ... },
  "pack": { ... },
  "run": { ... },
  "run_summary": { ... },
  "held_tags": [{ "key": "tag_foil", "name": "Foil Tag", "effect": "A random base Joker in the next shop is free with Foil edition." }],
  "held_tags_ready": true
}
```

`challenge` is present only for a native Challenge Mode run and contains its
stable `id` plus localized `name`. Normal deck/stake runs omit it.

`held_tags` ([HeldTag](#heldtag)) lists **pending untriggered** skip tags (oldest
first). Empty `[]` when none are held. `held_tags_ready: false` means a tag yep or
trigger is still in flight — wait and poll again before trusting the stack. On
**`MENU`**, **`SPLASH`**, and **`GAME_OVER`**, `held_tags_ready` is always **`true`**
(no active tag stack / not shown in play summary).

When **`state`** is **`SMODS_BOOSTER_OPENED`**, **`pack_ready`** and **`pack_hand_ready`**
tell play helpers when to snapshot: `glance` waits until both are true (avoids empty
pack rows or missing `hand:` during Arcana/Spectral deal animations). Omitted in other states.
Skip-reward tags on blinds you have **not** skipped yet remain on
`blinds.{small,big}.tag_key` / `tag_name`, not in `held_tags`. Use **`tag_key`**
and **`held_tags[].key`** for logic (locale-independent); `tag_name` / `name` are
display strings and may be localized.

`run` ([RunCounters](#runcounters)) is present during an active run. Joker cards may include `value.stats` ([JokerStats](#jokerstats)) and `value.rarity` — see [Joker card example](#card).

Outcome fields have distinct meanings:

- `victory_overlay: true` means the post-win screen is visible (`ROUND_EVAL`);
    call [`endless`](#endless) to continue.
- `won: true` means the run defeated the Ante 8 Boss. It remains true during
    endless mode and after a later loss.
- `run_summary` ([RunSummary](#runsummary)) appears on `GAME_OVER`. Read its
    human-readable `result` instead of `won` to distinguish victory from an
    endless-mode death.

| Field         | Type    | Description                                                                                                                                                                              |
| ------------- | ------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `money`       | integer | Current dollars                                                                                                                                                                          |
| `bankrupt_at` | integer | Credit Card and similar effects can make this negative; **buying power** is `money - bankrupt_at` (same check [`buy`](#buy), [`reroll`](#reroll), and [`reroll_boss`](#reroll_boss) use) |

`bankrupt_at` is present during an active run (omitted on `MENU`).

### Area

Represents a card area (hand, jokers, consumables, shop, etc.).

When the area is an open booster (`pack`), optional **`choices_remaining`** is the number of selections still required from this pack (from `G.GAME.pack_choices`; omitted when the pack is closed or 0).

```json
{
  "count": 8,
  "limit": 8,
  "highlighted_limit": 5,
  "choices_remaining": 1,
  "cards": [ ... ]
}
```

(`choices_remaining` appears on open `pack` areas only; other areas omit it.)

### Card

Represents a single card in any area (hand, deck, shop, pack, etc.).

When a card is face down in-game (`state.hidden: true`), the API masks its identity so clients cannot read rank, suit, key, or modifiers before the card is revealed. This prevents cheating on boss blinds like The Wheel, The Mark, and The Psychic.

For hidden cards, only these fields contain reliable information:

- `id` — stable position identifier (`sort_id`)
- `state.hidden` — always `true`
- `state.highlight` — present when the card is highlighted
- `state.forced_selection` — present when a boss blind such as Cerulean Bell forces the card to stay selected
- `cost` — sell/buy values (including booster `free` picks when applicable)

All other fields use placeholder values: empty `key`/`label`, `set: "DEFAULT"`, empty `value`, and empty `modifier`. Do not infer card identity from masked fields.

`state.debuff: true` means the card is debuffed (boss blinds, debug [`debuff`](#debuff), etc.). Debuffed Wild cards count only as their printed suit; debuffed scoring cards lose enhancement bonuses.

`state.forced_selection: true` marks a card forced selected by a boss blind, currently Cerulean Bell. It is distinct from a normal `state.highlight`.

**Visible card example:**

```json
{
  "id": 1,
  "key": "H_A",
  "set": "DEFAULT",
  "label": "Ace of Hearts",
  "value": {
    "suit": "H",
    "rank": "A",
    "effect": "..."
  },
  "modifier": {
    "seal": null,
    "edition": null,
    "enhancement": null,
    "eternal": false,
    "perishable": null,
    "rental": false,
    "pinned": false
  },
  "state": {
    "debuff": false,
    "hidden": false,
    "highlight": false,
    "forced_selection": false
  },
  "cost": {
    "sell": 1,
    "buy": 0
  }
}
```

**Joker card example** (includes locale-independent scoring snapshot):

```json
{
  "id": 0,
  "key": "j_jolly",
  "set": "JOKER",
  "label": "Jolly Joker",
  "value": {
    "effect": "+8 Mult if played hand contains a Pair",
    "stats": {
      "mult": 8
    },
    "rarity": "COMMON"
  },
  "modifier": {
    "edition": "HOLOGRAPHIC",
    "eternal": false,
    "perishable": null,
    "rental": false
  },
  "state": {
    "debuff": false,
    "hidden": false
  },
  "cost": {
    "sell": 2,
    "buy": 0
  }
}
```

`value.stats` fields vary by joker (e.g. `x_mult`, `chips`, `loyalty_remaining`, `caino_xmult`). See [JokerStats](#jokerstats). `value.rarity` is one of `COMMON`, `UNCOMMON`, `RARE`, `LEGENDARY`.

`value.effect` is the card's **mechanism** description (main UI text). For **Jokers**, only `main` ability text is included — edition, perishable, rental, eternal, pinned-left, and profile stake win sticker lines (e.g. “Used this Joker to win on White Stake difficulty”) live in the in-game `info` panel and are **not** appended to `value.effect` (use `modifier` and glance prefix tags for those buffs). **Consumables** still merge `main` + `info`, excluding stake win sticker lines from `info`.

Rental Jokers expose both `modifier.rental: true` and `modifier.rental_cost`.
The latter is the live per-round dollar charge read from Balatro's current run,
so clients must use it instead of assuming a fixed fee. Non-rental cards omit
`rental_cost`.

Jokers with a source-verified deterministic self-destruction event may include `value.self_destructs_on`. Its initial enum value is `SAVES_FROM_GAME_OVER` (Mr. Bones destroys itself after it prevents game over). This machine-readable lifecycle field is intentionally separate from localized `value.effect`. A pinned Joker instead exposes `modifier.pinned: true`, meaning Balatro keeps it in the leftmost Joker position.

Consumables (Tarot/Planet/Spectral) may include `value.target_min` / `value.target_max` (hand cards required when using or selecting from a pack), `value.requires_jokers_min` (must own at least N jokers — Ankh, Hex), and `value.random_joker_effect` (Ankh, Hex, Ectoplasm: picks a random joker; **not** targetable via `pack` indices). Derived from game config — same rules as the [`pack`](#pack) endpoint.

**Hidden (face-down) card example:**

```json
{
  "id": 4,
  "key": "",
  "set": "DEFAULT",
  "label": "",
  "value": {
    "effect": ""
  },
  "modifier": {},
  "state": {
    "hidden": true
  },
  "cost": {
    "sell": 1,
    "buy": 0
  }
}
```

### Round

```json
{
  "hands_left": 4,
  "hands_played": 0,
  "discards_left": 3,
  "discards_used": 0,
  "reroll_cost": 5,
  "boss_reroll_cost": 10,
  "boss_reroll_available": false,
  "boss_rerolled": false,
  "chips": 0,
  "ancient_suit": "S",
  "idol_rank": "7",
  "idol_suit": "D",
  "castle_suit": "H",
  "cashout_preview": {
    "lines": [
      { "kind": "blind", "label": "blind", "dollars": 3 },
      { "kind": "hands", "label": "hands", "dollars": 3 },
      { "kind": "joker", "label": "Golden Joker", "dollars": 4, "key": "j_golden" },
      { "kind": "interest", "label": "interest", "dollars": 1 }
    ],
    "total": 11
  }
}
```

Scoring-target fields (`ancient_suit`, `idol_rank`, `idol_suit`, `castle_suit`) appear when the corresponding joker is owned. Suit values: `H`, `D`, `C`, `S`. Rank values: `A`, `2`–`10`, `J`, `Q`, `K`.

`cashout_preview` appears on a won `ROUND_EVAL`; see
[CashoutPreview](#cashoutpreview) for its fields. Important boundaries:

- `total` is pending [`cash_out`](#cash_out) income and always equals the sum of
    `lines[].dollars`.
- `investment_received` is already included in `money`, so it is excluded from
    `lines`, `total`, and same-round interest.
- A `bonus` line reconciles otherwise unmodeled evaluation income.
- Mid-round economy effects, sell-value changes, rental, and RNG are not
    previewed.

Boss reroll fields (`boss_reroll_cost`, `boss_reroll_available`, `boss_rerolled`) appear in `BLIND_SELECT`. `boss_reroll_available` is true when the Boss blind is on deck, you own Director's Cut (unused this ante) or Retcon, and `money - bankrupt_at >= 10`.

### CashoutPreview

Round-end income preview (`round.cashout_preview` on won `ROUND_EVAL`):

| Field                 | Type            | Description                                                                   |
| --------------------- | --------------- | ----------------------------------------------------------------------------- |
| `lines`               | `CashoutLine[]` | Pending cash_out income rows in cashout order                                 |
| `total`               | integer         | Sum of `lines[].dollars` (pending `cash_out`; excludes `investment_received`) |
| `investment_received` | integer         | Investment Tag paid on boss defeat (in `money`, not in `total`)               |

**CashoutLine:** `kind` (`blind` | `hands` | `discards` | `joker` | `tag` | `interest` | `rental` | `bonus`), `label`, signed `dollars`, optional `key` (joker/tag id). `bonus` reconciles unmodeled eval income so `total` matches `cash_out`.

### RunCounters

Run-level counters on `gamestate.run` (during an active run):

```json
{
  "skips": 1,
  "deck_size": 52,
  "starting_deck_size": 52,
  "tarot_used": 3
}
```

### RunSummary

Run statistics on `gamestate.run_summary` (primarily on `GAME_OVER`; may appear after a win while still in-run). Mirrors the game-over modal.

```json
{
  "best_hand": 12450,
  "most_played_hand": {
    "name": "Pair",
    "count": 42
  },
  "cards_played": 187,
  "cards_discarded": 63,
  "cards_purchased": 28,
  "reroll_count": 5,
  "new_discoveries": 3,
  "result": "Lost to The Flint"
}
```

| Field              | Type    | Description                                                          |
| ------------------ | ------- | -------------------------------------------------------------------- |
| `best_hand`        | integer | Highest single-hand score this run                                   |
| `most_played_hand` | object  | `{ name, count }` — most frequently played poker hand (when tracked) |
| `cards_played`     | integer | Total cards played                                                   |
| `cards_discarded`  | integer | Total cards discarded                                                |
| `cards_purchased`  | integer | Total cards purchased                                                |
| `reroll_count`     | integer | Total shop rerolls                                                   |
| `new_discoveries`  | integer | New discoveries this run                                             |
| `result`           | string  | Human-readable outcome — e.g. `Victory`, `Lost to The Flint`, `Lost` |

Only fields the game tracked are present. **`result`** is the reliable outcome on `GAME_OVER`; pair with `won` when distinguishing endless victory vs endless death.

### JokerStats

Structured scoring snapshot on joker `value.stats` (from `card.ability`, not UI text). Only fields relevant to the joker are present:

| Field                                                    | Meaning                                          |
| -------------------------------------------------------- | ------------------------------------------------ |
| `mult`                                                   | Additive Mult in joker_main                      |
| `chips`                                                  | Additive chips in joker_main                     |
| `x_mult`                                                 | Multiplicative Mult in joker_main                |
| `caino_xmult`                                            | Caino ×Mult (when > 1)                           |
| `seltzer_remaining`                                      | Seltzer retrigger countdown                      |
| `steel_tally` / `stone_tally` / `driver_tally`           | Deck tallies                                     |
| `loyalty_every` / `loyalty_remaining` / `loyalty_x_mult` | Loyalty Card countdown                           |
| `obelisk_step`                                           | Obelisk ×Mult increment per non-dominant hand    |
| `ride_the_bus_step`                                      | Ride the Bus +Mult per hand without scoring face |
| `green_hand_add`                                         | Green Joker +Mult increment per hand played      |

Machine-readable schema: `src/lua/utils/openrpc.json` → `JokerStats`.

### HeldTag

A pending skip tag waiting to trigger (already earned, not yet consumed).

```json
{
  "key": "tag_foil",
  "name": "Foil Tag",
  "effect": "A random base Joker in the next shop is free with Foil edition."
}
```

| Field    | Type   | Description                                        |
| -------- | ------ | -------------------------------------------------- |
| `key`    | string | Stable tag id (e.g. `tag_foil`); **use for logic** |
| `name`   | string | Display name (may be localized)                    |
| `effect` | string | Short effect description                           |

`GameState.held_tags` is an array of HeldTag, oldest first. Omitted or empty when
none are pending. Pair with `held_tags_ready` — when false, the stack snapshot may
change on the next poll.

Machine-readable schema: `src/lua/utils/openrpc.json` → `HeldTag`.

### Blind

```json
{
  "type": "SMALL",
  "status": "SELECT",
  "name": "Small Blind",
  "effect": "No special effect",
  "score": 300,
  "tag_key": "tag_uncommon",
  "tag_name": "Uncommon Tag",
  "tag_effect": "Shop has a free Uncommon Joker"
}
```

Blind skip-reward tags include **`tag_key`** (stable id) and **`tag_name`** (display;
may be localized). Match tags by **`tag_key`**, not `tag_name`.

### Hand (Poker Hand Info)

```json
{
  "order": 1,
  "level": 1,
  "chips": 10,
  "mult": 1,
  "played": 0,
  "played_this_round": 0,
  "example": [["H_A", true], ["H_K", true]]
}
```

---

## Enums

### Deck

| Value       | Description                                                   |
| ----------- | ------------------------------------------------------------- |
| `RED`       | +1 discard every round                                        |
| `BLUE`      | +1 hand every round                                           |
| `YELLOW`    | Start with extra $10                                          |
| `GREEN`     | $2 per remaining Hand, $1 per remaining Discard (no interest) |
| `BLACK`     | +1 Joker slot, -1 hand every round                            |
| `MAGIC`     | Start with Crystal Ball voucher and 2 copies of The Fool      |
| `NEBULA`    | Start with Telescope voucher, -1 consumable slot              |
| `GHOST`     | Spectral cards may appear in shop, start with Hex card        |
| `ABANDONED` | Start with no Face Cards                                      |
| `CHECKERED` | Start with 26 Spades and 26 Hearts                            |
| `ZODIAC`    | Start with Tarot Merchant, Planet Merchant, and Overstock     |
| `PAINTED`   | +2 hand size, -1 Joker slot                                   |
| `ANAGLYPH`  | Gain Double Tag after each Boss Blind                         |
| `PLASMA`    | Balanced Chips/Mult, 2X base Blind size                       |
| `ERRATIC`   | Randomized Ranks and Suits                                    |

### Stake

| Value    | Description                     |
| -------- | ------------------------------- |
| `WHITE`  | Base difficulty                 |
| `RED`    | Small Blind gives no reward     |
| `GREEN`  | Required score scales faster    |
| `BLACK`  | Shop can have Eternal Jokers    |
| `BLUE`   | -1 Discard                      |
| `PURPLE` | Required score scales faster    |
| `ORANGE` | Shop can have Perishable Jokers |
| `GOLD`   | Shop can have Rental Jokers     |

### Card Value Suit

| Value | Description |
| ----- | ----------- |
| `H`   | Hearts      |
| `D`   | Diamonds    |
| `C`   | Clubs       |
| `S`   | Spades      |

### Card Value Rank

| Value | Description |
| ----- | ----------- |
| `2`   | Two         |
| `3`   | Three       |
| `4`   | Four        |
| `5`   | Five        |
| `6`   | Six         |
| `7`   | Seven       |
| `8`   | Eight       |
| `9`   | Nine        |
| `T`   | Ten         |
| `J`   | Jack        |
| `Q`   | Queen       |
| `K`   | King        |
| `A`   | Ace         |

### Card Set

| Value      | Description                   |
| ---------- | ----------------------------- |
| `DEFAULT`  | Playing card                  |
| `ENHANCED` | Playing card with enhancement |
| `JOKER`    | Joker card                    |
| `TAROT`    | Tarot consumable              |
| `PLANET`   | Planet consumable             |
| `SPECTRAL` | Spectral consumable           |
| `VOUCHER`  | Voucher                       |
| `BOOSTER`  | Booster pack                  |

### Card Modifier Seal

| Value    | Description                                |
| -------- | ------------------------------------------ |
| `RED`    | Retrigger card 1 time                      |
| `BLUE`   | Creates Planet card for final hand if held |
| `GOLD`   | Earn $3 when scored                        |
| `PURPLE` | Creates Tarot when discarded               |

### Card Modifier Edition

| Value        | Description                       |
| ------------ | --------------------------------- |
| `FOIL`       | +50 Chips                         |
| `HOLO`       | +10 Mult                          |
| `POLYCHROME` | X1.5 Mult                         |
| `NEGATIVE`   | +1 slot (jokers/consumables only) |

### Card Modifier Enhancement

| Value   | Description                          |
| ------- | ------------------------------------ |
| `BONUS` | +30 Chips when scored                |
| `MULT`  | +4 Mult when scored                  |
| `WILD`  | Counts as every suit                 |
| `GLASS` | X2 Mult when scored                  |
| `STEEL` | X1.5 Mult while held                 |
| `STONE` | +50 Chips (no rank/suit)             |
| `GOLD`  | $3 if held at end of round           |
| `LUCKY` | 1/5 chance +20 Mult, 1/15 chance $20 |

### Blind Type

| Value   | Description                           |
| ------- | ------------------------------------- |
| `SMALL` | Can be skipped for a Tag              |
| `BIG`   | Can be skipped for a Tag              |
| `BOSS`  | Cannot be skipped, has special effect |

### Blind Status

| Value      | Description        |
| ---------- | ------------------ |
| `SELECT`   | Can be selected    |
| `CURRENT`  | Currently active   |
| `UPCOMING` | Future blind       |
| `DEFEATED` | Previously beaten  |
| `SKIPPED`  | Previously skipped |

### Card Keys

Card keys appear in `Card.key` and are accepted by methods such as
[`add`](#add). See the focused [Card Key Reference](card-keys.md) for formats,
examples, lookup commands, and canonical sources.

---

## Error Codes

| Code   | Name             | Description                              |
| ------ | ---------------- | ---------------------------------------- |
| -32000 | `INTERNAL_ERROR` | Server-side failure                      |
| -32001 | `BAD_REQUEST`    | Invalid parameters or protocol error     |
| -32002 | `INVALID_STATE`  | Action not allowed in current game state |
| -32003 | `NOT_ALLOWED`    | Game rules prevent this action           |

---

## OpenRPC Specification

For machine-readable API documentation, use the `rpc.discover` method to retrieve the full OpenRPC specification.
