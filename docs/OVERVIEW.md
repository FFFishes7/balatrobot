# BalatroBot — Complete Project Overview

This document describes every part of the project: what it is, how it is structured, what each file does, and how all the pieces connect together.

---

## 1. What This Project Is

This is a personal setup for letting an AI (running inside Cursor or Codex) play Balatro autonomously while you watch.

The project has three roles:

| Role | Who |
|---|---|
| **The Game** | Balatro (running as a normal Windows game) |
| **The Interface** | This repository — mod + API + helper scripts |
| **The Brain** | Cursor / Codex (outside this repo) |

You, the human, are the audience. You watch the game window. The AI calls the helper scripts, which call the API, which controls the game.

---

## 2. High-Level Architecture

```
┌─────────────────────────────────────────────┐
│  Cursor / Codex  (the AI brain, not in repo) │
│  calls bot.ps1 commands                      │
└────────────────────┬────────────────────────┘
                     │ runs Python scripts
┌────────────────────▼────────────────────────┐
│  tools/play/  (Python helper scripts)        │
│  state · act · know · view · rpc            │
└────────────────────┬────────────────────────┘
                     │ HTTP JSON-RPC 2.0
                     │ POST http://127.0.0.1:12346
┌────────────────────▼────────────────────────┐
│  Lua mod  (running inside Balatro)           │
│  server.lua · dispatcher.lua · endpoints/   │
└────────────────────┬────────────────────────┘
                     │ Love2D / game engine
┌────────────────────▼────────────────────────┐
│  Balatro.exe  (the game itself)              │
└─────────────────────────────────────────────┘
```

The Python CLI (`balatrobot serve`) is responsible for launching Balatro with the mod loaded and keeping the process alive. After that it does nothing — all actual game control goes through the JSON-RPC API.

---

## 3. Project Directory Structure

```
balatrobot/
│
├── balatrobot.lua          # Mod entry point — loaded by Steamodded at game start
├── balatrobot.json         # Mod metadata (name, version, author)
│
├── src/
│   ├── balatrobot/         # Python package
│   │   ├── cli/            # CLI commands (serve, api)
│   │   ├── platforms/      # Windows / macOS / Linux launchers
│   │   ├── manager.py      # BalatroInstance — starts/stops the game process
│   │   └── config.py       # All configuration fields and env var mapping
│   │
│   └── lua/
│       ├── core/
│       │   ├── server.lua      # HTTP server (accepts connections, parses requests)
│       │   ├── dispatcher.lua  # Routes requests to endpoints, validates everything
│       │   └── validator.lua   # Schema validation for request params
│       ├── endpoints/          # One file per API method
│       ├── utils/
│       │   ├── gamestate.lua   # Reads G.* game state and formats it
│       │   ├── logger.lua      # Debug/info logging
│       │   ├── enums.lua       # Deck/stake/hand type name lists
│       │   ├── types.lua       # Lua type annotations
│       │   └── openrpc.json    # Machine-readable API specification
│       └── settings.lua        # Reads BALATROBOT_* env vars inside the game
│
├── tools/
│   └── play/               # Helper scripts for calling the API
│       ├── bot.ps1         # PowerShell entry point — state/query/know/exec/help
│       ├── state.py        # Layer-1 gamestate JSON envelope
│       ├── query.py        # Layer-2 query commands
│       ├── exec.py         # Execute one JSON-RPC action, return envelope
│       ├── know.py         # Verified Balatro facts (JSON)
│       ├── help.py         # Hidden/debug commands
│       ├── layers.py       # L1/L2/L3 filtering and transition polling
│       ├── envelope.py     # Response envelope builders
│       ├── actions.py      # State-aware action list generation
│       ├── commands.py     # RPC parameter builders
│       ├── start_options.py # MENU deck/stake lists
│       ├── bot_client.py   # Shared HTTP client for all scripts
│       ├── serve.example.ps1  # Template — copy to serve.ps1 and set your game path
│       └── README.md
│
├── knowledge/
│   └── balatro/            # Verified fact tables for the AI to consult
│       ├── balatro-jokers-verified.json
│       ├── balatro-bosses-verified.json
│       ├── balatro-tags-verified.json
│       ├── balatro-stakes-verified.json
│       ├── balatro-planets-verified.json
│       ├── balatro-tarots-verified.json
│       ├── balatro-vouchers-verified.json
│       ├── balatro-spectrals-verified.json
│       ├── balatro-rules-verified.json
│       └── build_knowledge.py  # Script to regenerate the JSON files
│
├── docs/                   # Documentation
├── tests/                  # Python and Lua test suites
├── pyproject.toml          # Python dependencies and tool config
├── Makefile                # make install / test / lint / format / typecheck
└── CLAUDE.md / AGENTS.md   # Instructions for AI assistants working on this repo
```

---

## 4. Setup (Windows)

### 4.1 One-Time Game Setup

These steps only need to be done once.

**Step 1: Install Lovely Injector**

Download `version.dll` from [Lovely Injector](https://github.com/ethangreen-dev/lovely-injector) and place it in the Balatro game folder (same folder as `Balatro.exe`). This allows mods to be loaded.

Default path: `C:\Program Files (x86)\Steam\steamapps\common\Balatro\`

**Step 2: Install Steamodded**

Download [Steamodded](https://github.com/Steamodded/smods) and place the `smods` folder inside:
```
%AppData%\Roaming\Balatro\Mods\smods\
```

**Step 3: Link this repo as a mod**

Run PowerShell as Administrator:
```powershell
New-Item -ItemType SymbolicLink `
  -Path "$env:APPDATA\Balatro\Mods\balatrobot" `
  -Target "D:\Private\balatrobot"
```

This creates a symlink so that Balatro always loads the latest version of the mod from this repo.

### 4.2 One-Time Python Setup

**Step 4: Install Python dependencies**

From the repo root in PowerShell:
```powershell
make install
```

This creates `.venv\` with the `balatrobot` CLI and all dependencies (`httpx`, `typer`, etc.).

**Step 5: Create serve.ps1**

```powershell
Copy-Item tools\play\serve.example.ps1 tools\play\serve.ps1
```

Edit `serve.ps1` only if Balatro is not installed at the default Steam path. The file is gitignored so your machine-specific path is never committed.

---

## 5. Running the Game

### 5.1 Start Balatro + API (Terminal 1)

```powershell
.\tools\play\serve.ps1
```

Or with flags:
```powershell
.\tools\play\serve.ps1 --fast --debug
```

What this does:
1. Sets `BALATROBOT_BALATRO_PATH`, `BALATROBOT_LOVE_PATH`, `BALATROBOT_LOVELY_PATH` in the current shell session.
2. Calls `.venv\Scripts\balatrobot.exe serve`, which launches `Balatro.exe` with the mod loaded.
3. The mod starts an HTTP server inside the game on port 12346.
4. `balatrobot serve` waits for the health endpoint to respond, then prints `Balatro running on port 12346`.

Leave this terminal open. It must stay open for the API to work.

### 5.2 Use the API (Terminal 2)

In a second terminal, use `bot.ps1`:
```powershell
.\tools\play\bot.ps1 state
.\tools\play\bot.ps1 know preflight
.\tools\play\bot.ps1 play 0 1 2 3 4
```

---

## 6. The Python Layer (`src/balatrobot/`)

### 6.1 `config.py` — Configuration

All configuration is expressed as a `Config` dataclass. Every field maps to an environment variable.

| Field | Env Var | Default | Description |
|---|---|---|---|
| `host` | `BALATROBOT_HOST` | `127.0.0.1` | HTTP server host |
| `port` | `BALATROBOT_PORT` | `12346` | HTTP server port |
| `fast` | `BALATROBOT_FAST` | `False` | 10x game speed, unlimited FPS |
| `headless` | `BALATROBOT_HEADLESS` | `False` | Minimize window, disable rendering |
| `render_on_api` | `BALATROBOT_RENDER_ON_API` | `False` | Only render frames when API is called |
| `audio` | `BALATROBOT_AUDIO` | `False` | Enable game audio |
| `debug` | `BALATROBOT_DEBUG` | `False` | Verbose debug logging from mod |
| `gamespeed` | `BALATROBOT_GAMESPEED` | `4` | Speed multiplier (1–10) |
| `animation_fps` | `BALATROBOT_ANIMATION_FPS` | `10` | Animation frame rate |
| `fps_cap` | `BALATROBOT_FPS_CAP` | `60` | Maximum FPS |
| `balatro_path` | `BALATROBOT_BALATRO_PATH` | auto | Path to Balatro install dir |
| `lovely_path` | `BALATROBOT_LOVELY_PATH` | auto | Path to `version.dll` |
| `love_path` | `BALATROBOT_LOVE_PATH` | auto | Path to `Balatro.exe` |
| `platform` | `BALATROBOT_PLATFORM` | auto | `windows`, `darwin`, `linux`, `native` |
| `logs_path` | `BALATROBOT_LOGS_PATH` | `logs` | Directory for log files |

Config is read in priority order: CLI flag → env var → dataclass default.

### 6.2 `manager.py` — BalatroInstance

`BalatroInstance` is an async context manager that:

1. Creates a session log directory (`logs/<timestamp>/`).
2. Calls the platform-specific launcher to start `Balatro.exe` as a subprocess.
3. Polls the `/health` endpoint every 0.5 seconds until the game is ready (timeout: 30s).
4. On exit, terminates the subprocess gracefully (then force-kills after 5s).

Usage in tests:
```python
async with BalatroInstance(port=12347) as instance:
    # game is running and healthy
    pass  # game is stopped
```

### 6.3 `platforms/` — Cross-Platform Launchers

Each platform has a launcher class that provides:

- `validate_paths(config)` — checks that required files exist, fills in defaults.
- `build_cmd(config)` — returns the command list to `subprocess.Popen`.
- `build_env(config)` — returns the environment dict (includes all `BALATROBOT_*` vars).
- `cleanup(config)` — platform-specific teardown (e.g. `wineserver -k` on Linux).

| File | Platform |
|---|---|
| `windows.py` | Windows, Steam install |
| `macos.py` | macOS, Steam install |
| `linux.py` | Linux, Steam + Proton |
| `native.py` | Any platform with native Love2D |

### 6.4 `cli/` — Command Line Interface

The `balatrobot` CLI has two commands:

**`balatrobot serve`** — Starts Balatro. All options mirror the `Config` fields above.

**`balatrobot api METHOD PARAMS`** — Calls one API method on an already-running server.

```powershell
balatrobot api gamestate '{}'
balatrobot api start '{"deck":"RED","stake":"WHITE"}'
```

---

## 7. The Lua Layer (`src/lua/`)

The Lua mod runs inside Balatro's Love2D engine. It is loaded by Steamodded when the game starts.

### 7.1 Entry Point (`balatrobot.lua`)

When Steamodded loads the mod, `balatrobot.lua` runs. It:

1. Loads all endpoint files from `src/lua/endpoints/`.
2. Initializes the HTTP server (`BB_SERVER.init()`).
3. Initializes the dispatcher with all endpoints (`BB_DISPATCHER.init()`).
4. Hooks into `love.update(dt)` to run `BB_SERVER.update()` on every game tick.

The server update loop is called ~60 times per second (or faster in `--fast` mode). It checks if there is an incoming HTTP request, processes it, and sends the response — all within a single game tick.

### 7.2 `core/server.lua` — HTTP Server

A minimal single-client HTTP/1.1 server implemented using LuaSocket.

- Listens on the configured port (default 12346).
- Accepts one connection at a time (serial, not concurrent).
- Only handles `POST /` requests.
- Max request body: 64KB.
- Parses the HTTP request, extracts the JSON body, passes it to the dispatcher.
- Writes the JSON response back over the same connection, then closes it.

### 7.3 `core/dispatcher.lua` — Request Router

Receives parsed JSON from the server and routes it to the correct endpoint.

**Validation pipeline** (in order — fails fast):

1. **Protocol check** — must be JSON-RPC 2.0, must have a string `method` and a valid `id`.
2. **Endpoint lookup** — `method` must match a registered endpoint name.
3. **Schema validation** — request params must match the endpoint's declared schema.
4. **Game state check** — if the endpoint has `requires_state`, the current game state must match.
5. **Execution** — calls `endpoint.execute(params, send_response)`.

### 7.4 `core/validator.lua` — Schema Validation

Each endpoint declares a `schema` table that describes its parameters:

```lua
schema = {
  cards = { type = "array", items = { type = "integer" }, required = true },
  deck  = { type = "string", required = true },
}
```

The validator checks types, required fields, array item types, and enum values. On failure it returns a `BAD_REQUEST` error with a human-readable message.

### 7.5 `utils/gamestate.lua` — Game State Reader

Reads the game's internal global `G.*` tables and returns a structured JSON-serializable Lua table. This is what the `gamestate` endpoint returns.

Key fields in the gamestate response:

| Field | Description |
|---|---|
| `state` | Current game state string (see Section 8) |
| `ante_num` | Current ante number |
| `round_num` | Current round number |
| `money` | Player's money |
| `deck` | Deck name (e.g. `"RED"`) |
| `stake` | Stake name (e.g. `"WHITE"`) |
| `seed` | Run seed |
| `hand` | Hand cards, highlights, discard/hand counts |
| `jokers` | All joker cards in joker slots |
| `consumables` | Tarots, planets, spectrals in hand |
| `shop` | Shop cards, vouchers, packs, reroll cost |
| `blinds` | Small/Big/Boss blind info, score target, effect |
| `round` | Hands remaining, discards remaining, current score |
| `won` | `true` if the run is won (only meaningful in `GAME_OVER`) |

---

## 8. Game States

The game is always in exactly one state. Every endpoint that changes game state documents which states it requires and what state it returns.

| State string | When it occurs | What the AI should do |
|---|---|---|
| `MENU` | Game just started, or returned to main menu | Call `start` to begin a run |
| `BLIND_SELECT` | Between rounds — choose which blind to play | Call `select` or `skip` |
| `SELECTING_HAND` | Playing a round — choose cards to play or discard | Call `play` or `discard` |
| `HAND_PLAYED` | Brief transition after playing cards | Call `gamestate` and wait |
| `ROUND_EVAL` | Round won — scoring screen | Call `cash_out` |
| `SHOP` | Shop is open between antes | Call `buy`, `reroll`, `sell`, `use`, `next_round` |
| `SMODS_BOOSTER_OPENED` | A booster pack is open | Call `pack N` or `pack skip` |
| `GAME_OVER` | Run ended (win or loss) | Call `menu` to go back to start |

---

## 9. API Endpoints

All endpoints use JSON-RPC 2.0. Send `POST http://127.0.0.1:12346` with:
```json
{"jsonrpc": "2.0", "method": "METHOD_NAME", "params": {...}, "id": 1}
```

All indices are **0-based**.

### Query / Utility

| Method | Params | Required State | Description |
|---|---|---|---|
| `health` | none | any | Returns `{"status": "ok"}`. Used to check if the API is up. |
| `gamestate` | none | any | Returns the full current game state. |
| `screenshot` | `path` (string) | any | Saves a PNG screenshot to the given file path. |
| `save` | `path` (string) | any | Saves run state to a file. |
| `load` | `path` (string) | any | Loads run state from a file. |

### Navigation

| Method | Params | Required State | Description |
|---|---|---|---|
| `menu` | none | any | Returns to the main menu. Aborts the current run. |
| `start` | `deck`, `stake`, `seed` (optional) | `MENU` | Starts a new run. |
| `select` | none | `BLIND_SELECT` | Selects the current blind and begins the round. |
| `skip` | none | `BLIND_SELECT` | Skips the current blind (only works for Small or Big blinds). Collects the skip tag reward. |
| `cash_out` | none | `ROUND_EVAL` | Collects round rewards and enters the shop. |
| `next_round` | none | `SHOP` | Leaves the shop and goes to the next blind selection. |

### Hand Play

| Method | Params | Required State | Description |
|---|---|---|---|
| `play` | `cards` (array of int) | `SELECTING_HAND` | Plays the cards at the given hand indices. Triggers scoring. |
| `discard` | `cards` (array of int) | `SELECTING_HAND` | Discards the cards at the given hand indices. Draws replacement cards. |
| `sort` | `mode` (string) | `SELECTING_HAND` | Sorts the hand using Balatro's native sort. Modes: `rank`, `rank-asc`, `rank-desc`, `suit`, `suit-asc`, `suit-desc`. |
| `rearrange` | `hand` or `jokers` or `consumables` (array of int) | `SELECTING_HAND`, `SHOP`, `SMODS_BOOSTER_OPENED` | Reorders cards by supplying the full desired index order. |

### Shop

| Method | Params | Required State | Description |
|---|---|---|---|
| `buy` | `card` or `voucher` or `pack` (int) | `SHOP` | Buys a card, voucher, or booster pack from the shop. |
| `reroll` | none | `SHOP` | Rerolls the shop (costs money). |
| `sell` | `joker` or `consumable` (int) | `SELECTING_HAND`, `SHOP`, `SMODS_BOOSTER_OPENED` | Sells a joker or consumable for money. |

### Booster Pack

| Method | Params | Required State | Description |
|---|---|---|---|
| `pack` | `card` (int), `targets` (array of int, optional), or `skip` (bool) | `SMODS_BOOSTER_OPENED` | Selects a card from an open booster pack. Some cards (e.g. Tarot) need `targets` to specify which hand cards they apply to. `skip: true` closes the pack without picking. |

### Consumables

| Method | Params | Required State | Description |
|---|---|---|---|
| `use` | `consumable` (int), `cards` (array of int, optional) | `SELECTING_HAND`, `SHOP` | Uses a consumable. Some consumables (e.g. Tarot) need `cards` to specify targets. |

### Debug / Cheat

| Method | Params | Required State | Description |
|---|---|---|---|
| `add` | `type`, `key`, and position/area params | any | Adds a card (joker, consumable, voucher, playing card, or booster pack) directly to the game. |
| `set` | `money`, `chips`, `ante`, etc. | any | Sets in-game values directly. Useful for testing. |

---

## 10. Error Handling

When an API call fails, the response contains an `error` object:

```json
{
  "jsonrpc": "2.0",
  "error": {
    "code": -32001,
    "message": "You can only play 5 cards",
    "data": { "name": "BAD_REQUEST" }
  },
  "id": 1
}
```

| Error name | Code | When |
|---|---|---|
| `INTERNAL_ERROR` | -32000 | Unexpected Lua runtime error |
| `BAD_REQUEST` | -32001 | Invalid params (wrong type, out of range, etc.) |
| `INVALID_STATE` | -32002 | Action not allowed in the current game state |
| `NOT_ALLOWED` | -32003 | Action blocked by game rules (e.g. not enough money to reroll) |

---

## 11. `tools/play/` — Helper Scripts

These scripts wrap the raw JSON-RPC API into simple command-line tools that the AI calls via `bot.ps1`.

### `bot.ps1` — Main Entry Point

```powershell
.\tools\play\bot.ps1 COMMAND [args...]
```

`bot.ps1` finds Python in `.venv\Scripts\python.exe` and dispatches:

| Command | Dispatches to |
|---|---|
| `state` | `state.py` |
| `hand` | `hand.py` (alias for `state.py`) |
| `know` | `know.py` |
| `rpc` | `rpc.py` |
| anything else | `act.py COMMAND [args...]` |

### `state.py` / `hand.py` — Current State

Calls `gamestate` and prints a compact summary via `view.py`. Use this before every action to know what state the game is in.

Example output:
```
state=SELECTING_HAND ante=2 round=3 money=12 deck=RED stake=WHITE
blind=The Flint type=Boss status=CURRENT target=2400 effect=The base Chips and Mult of each played hand are halved (rounded up)
round: hands=3 discards=3 score=0/2400
jokers: [0] Joker ($2)  [1] Greedy Joker ($3)
hand: [0] 2♠  [1] 5♥  [2] 7♦  [3] 9♣  [4] Q♠  [5] K♥  [6] A♦  [7] 3♣
hint: python act.py play 0 1 2 3 4  |  discard 0 1  |  use 0 [cards...]  |  sort rank|suit
? .\bot.ps1 help  — full command list (state-aware)
```

### `act.py` — All Game Actions

Executes one game action and prints the resulting state.

Full command reference (run `.\bot.ps1 help` to see state-filtered version):

**Run flow:**
```powershell
.\bot.ps1 start RED WHITE          # start new run (deck, stake)
.\bot.ps1 start RED WHITE ABCDEF   # start with specific seed
.\bot.ps1 menu                     # return to main menu
.\bot.ps1 select                   # select current blind
.\bot.ps1 skip                     # skip current blind
.\bot.ps1 cash_out                 # collect round rewards
.\bot.ps1 next_round               # leave shop
```

**Hand play:**
```powershell
.\bot.ps1 play 0 1 2 3 4           # play cards at indices 0,1,2,3,4
.\bot.ps1 discard 0 1              # discard cards at indices 0,1
.\bot.ps1 sort rank                # sort hand by rank
.\bot.ps1 sort suit                # sort hand by suit
.\bot.ps1 rearrange hand 2 0 1 3   # reorder hand to: card2, card0, card1, card3
.\bot.ps1 rearrange jokers 1 0     # swap joker 0 and joker 1
```

**Shop:**
```powershell
.\bot.ps1 buy card 0               # buy the first shop card
.\bot.ps1 buy voucher 0            # buy the first voucher
.\bot.ps1 buy pack 0               # buy the first booster pack
.\bot.ps1 reroll                   # reroll shop
.\bot.ps1 sell joker 0             # sell joker at index 0
.\bot.ps1 sell consumable 0        # sell consumable at index 0
```

**Booster pack:**
```powershell
.\bot.ps1 pack 0                   # take card 0 from the open pack
.\bot.ps1 pack 0 1 2               # take card 0, targeting hand cards 1,2
.\bot.ps1 pack skip                # skip the pack
```

**Consumables:**
```powershell
.\bot.ps1 use 0                    # use consumable at index 0
.\bot.ps1 use 0 1 2                # use consumable 0 on hand cards 1,2
.\bot.ps1 death 0 3 5              # Death card 0: turn hand card 3 into hand card 5
```

**Query:**
```powershell
.\bot.ps1 state                    # current state summary
.\bot.ps1 help                     # commands valid in current state
.\bot.ps1 help all                 # all commands regardless of state
.\bot.ps1 help SHOP                # commands valid in SHOP state
```

### `know.py` — Knowledge Base Lookups

Queries the verified fact tables in `knowledge/balatro/`. The AI must use this before relying on information about jokers, bosses, tags, or rules — to avoid hallucinating card effects.

```powershell
# Verify stake + all active jokers + current boss + tags before deciding
.\bot.ps1 know preflight

# Look up one specific entry
.\bot.ps1 know check joker "Joker"
.\bot.ps1 know check joker "Fibonacci"
.\bot.ps1 know check boss "The Psychic"
.\bot.ps1 know check tag "Coupon Tag"
.\bot.ps1 know check stake WHITE
.\bot.ps1 know check rule scoring_hand_only

# List all entries of a kind
.\bot.ps1 know list jokers
.\bot.ps1 know list bosses
.\bot.ps1 know list tags

# JSON output (for scripting)
.\bot.ps1 know check joker "Mad Joker" --json
.\bot.ps1 know list jokers --json

# Library summary
.\bot.ps1 know stats
```

`preflight` is the most important command. It reads the current gamestate and looks up every active joker, the current boss blind effect, and any pending tags — printing verified effects so the AI knows what it is dealing with before making decisions.

### `rpc.py` — Raw RPC Call

For calling endpoints that `act.py` does not wrap. Reads JSON params from stdin.

```powershell
# No params
.\bot.ps1 rpc gamestate

# With params via stdin
echo '{"path": "C:\\tmp\\screenshot.png"}' | .\bot.ps1 rpc screenshot
echo '{"deck": "BLACK", "stake": "RED"}' | .\bot.ps1 rpc start
```

### `bot_client.py` — Shared HTTP Client

All helper scripts import `rpc` from `bot_client.py`. It is a thin wrapper around `httpx` that:

- Uses a threading lock (safe for multi-threaded callers, though currently unused).
- Reads `BALATROBOT_URL` (default `http://127.0.0.1:12346`) and `BALATROBOT_TIMEOUT` (default 120s) from env.
- Raises `APIError` (with `name`, `message`, `code`) on JSON-RPC error responses.

### `view.py` — State Formatter

Not called directly. Used by `state.py` and `act.py` to format gamestate into the compact human/AI-readable output. Contains:

- `card_label(card)` — formats a playing card as e.g. `Q♠`, `10♥`.
- `print_summary(state)` — prints the full compact state summary.
- `print_hint(state_name)` — prints the most relevant commands for the current state.
- Chinese-language edition/enhancement labels (e.g. `"箔片:+50筹码"`) for joker/consumable display.

---

## 12. `knowledge/balatro/` — Verified Fact Tables

Nine JSON files containing machine-verified Balatro game data. These exist so the AI can look up accurate card effects instead of guessing.

| File | Contents |
|---|---|
| `balatro-jokers-verified.json` | All jokers: key, effect, trigger, limits, notes |
| `balatro-bosses-verified.json` | All boss blinds: effect, category, min_ante |
| `balatro-tags-verified.json` | All tags: effect, notes |
| `balatro-stakes-verified.json` | All stakes: rules, effects |
| `balatro-planets-verified.json` | All planet cards: hand type upgrade effects |
| `balatro-tarots-verified.json` | All tarot cards: effects, target counts |
| `balatro-vouchers-verified.json` | All vouchers: effects, prerequisites |
| `balatro-spectrals-verified.json` | All spectral cards: effects, limits |
| `balatro-rules-verified.json` | Universal mechanics rules (scoring order, hand limits, etc.) |

`build_knowledge.py` regenerates these files from `docs/api.md` plus hand-written override files (`*-overrides.json`). Run it when updating knowledge:

```powershell
.\.venv\Scripts\python.exe knowledge\balatro\build_knowledge.py
```

---

## 13. Configuration Reference (Complete)

### Serve Flags

Passed to `.\tools\play\serve.ps1` or `balatrobot serve`:

```powershell
.\tools\play\serve.ps1 --fast           # 10x game speed
.\tools\play\serve.ps1 --debug          # verbose mod logging
.\tools\play\serve.ps1 --headless       # minimize window (no rendering)
.\tools\play\serve.ps1 --port 12347     # use a different port
.\tools\play\serve.ps1 --audio          # enable game audio (default: off)
```

### Environment Variables

All config can be set via env vars (useful for permanent settings):

```powershell
$env:BALATROBOT_FAST = "1"
$env:BALATROBOT_GAME_DIR = "D:\Games\Balatro"
$env:BALATROBOT_URL = "http://127.0.0.1:12346"    # used by bot_client.py
$env:BALATROBOT_TIMEOUT = "120"                    # request timeout in seconds
```

---

## 14. Testing

Tests are in `tests/`. They require Balatro to be installed.

```powershell
make test              # run all tests
pytest tests/lua -n 6  # Lua integration tests in parallel (starts real Balatro instances)
pytest tests/cli       # CLI tests
pytest tests/lua/endpoints/test_health.py -v  # one specific test
pytest tests/cli -m "not integration"          # skip tests that need Balatro running
```

Integration tests start Balatro instances on random ports, run API calls, and stop the instances. They take 30–120 seconds each.

---

## 15. Development Commands

```powershell
make install      # install dependencies into .venv
make lint         # check code with ruff
make format       # auto-format with ruff + mdformat
make typecheck    # run type checker (Python: ty, Lua: custom)
make quality      # lint + typecheck + format (all checks)
make test         # run all tests
make all          # quality + test
make fixtures     # regenerate test fixtures
make help         # list all targets
```

---

## 16. How the AI Should Use This Project

This section describes the intended workflow for Cursor or Codex acting as the player.

### The Basic Loop

```
repeat:
  1. .\bot.ps1 state              ← see current game state
  2. .\bot.ps1 know preflight     ← verify joker/boss/tag effects
  3. decide what to do
  4. .\bot.ps1 COMMAND [args]     ← execute one action
  5. read the printed state       ← the action prints the new state automatically
until state == GAME_OVER
```

After `GAME_OVER`:
```
.\bot.ps1 menu    ← return to main menu
```

Then start a new run:
```
.\bot.ps1 start RED WHITE
```

### State-by-State Guide

**`MENU`**
```powershell
.\bot.ps1 start RED WHITE           # begin a new run with Red Deck, White Stake
.\bot.ps1 start RED WHITE ABCDEF    # use a specific seed
```

**`BLIND_SELECT`**
```powershell
.\bot.ps1 know preflight            # check what the boss blind does
.\bot.ps1 select                    # play this blind
.\bot.ps1 skip                      # skip (Small/Big only) — collect tag reward
```

**`SELECTING_HAND`**
```powershell
.\bot.ps1 state                     # see hand, jokers, round info
.\bot.ps1 know preflight            # verify joker effects before playing
.\bot.ps1 sort rank                 # sort hand for easier reading
.\bot.ps1 play 0 1 2 3 4            # play 5 cards
.\bot.ps1 discard 0 1               # or discard to draw new cards
.\bot.ps1 use 0                     # use a consumable if needed
```

**`ROUND_EVAL`**
```powershell
.\bot.ps1 cash_out                  # always — moves to shop
```

**`SHOP`**
```powershell
.\bot.ps1 state                     # see what is in the shop
.\bot.ps1 know check joker "Name"   # look up any joker before buying
.\bot.ps1 buy card 0                # buy it
.\bot.ps1 buy pack 0                # buy a booster pack
.\bot.ps1 reroll                    # reroll if nothing useful (costs money)
.\bot.ps1 next_round                # leave shop when done
```

**`SMODS_BOOSTER_OPENED`**
```powershell
.\bot.ps1 state                     # see what cards are in the pack
.\bot.ps1 pack 0                    # take card 0
.\bot.ps1 pack 0 1 2                # take card 0, applying it to hand cards 1 and 2
.\bot.ps1 pack skip                 # skip the pack
```

### Important Rules

- **Always call `state` first.** Do not guess the current state.
- **Always call `know preflight` before making a decision.** It prevents acting on wrong assumptions about joker or boss effects.
- **All indices are 0-based.** The first card in hand is `0`, not `1`.
- **One action at a time.** The server handles one request at a time. Do not send two commands simultaneously.
- **If the connection fails**, the game is probably still loading. Wait a few seconds and try `state` again.
- **If `act.py` prints an error**, read the message carefully. Common causes: wrong state, index out of range, not enough money.
- **`help` is state-aware.** Running `.\bot.ps1 help` shows only the commands valid in the current state.
