# Project Overview

Single-file map of the whole project: what it is, how the pieces connect, and where to read details for each part. This is the entry point for understanding the repo; it deliberately points outward to the focused docs instead of duplicating them.

---

## 1. What This Project Is

**BlindDeck** is a Balatro play desk for humans and AI agents: a Steamodded mod,
JSON-RPC HTTP API, and command-line helpers so you (or your agent) can **glance**
run state and act one deliberate command at a time.

| Role              | Who                                          |
| ----------------- | -------------------------------------------- |
| **The Game**      | Balatro (running as a normal Windows game)   |
| **The Interface** | This repository — mod + API + helper scripts |
| **The Brain**     | Cursor / Codex (outside this repo)           |

The Python CLI launches Balatro with the mod loaded; after that all control goes through the JSON-RPC API.

---

## 2. High-Level Architecture

```
┌─────────────────────────────────────────────┐
│  Cursor / Codex  (the AI brain, not in repo) │
└────────────────────┬────────────────────────┘
                     │ bot.ps1 / JSON-RPC
┌────────────────────▼────────────────────────┐
│  tools/play/  (Python helper scripts)        │
└────────────────────┬────────────────────────┘
                     │ HTTP JSON-RPC 2.0 → POST http://127.0.0.1:12346
┌────────────────────▼────────────────────────┐
│  Lua mod  (running inside Balatro)           │
│  server.lua · dispatcher.lua · endpoints/   │
└────────────────────┬────────────────────────┘
                     │ Love2D / game engine
┌────────────────────▼────────────────────────┐
│  Balatro.exe  (the game itself)              │
└─────────────────────────────────────────────┘
```

---

## 3. Where to Read What

| Topic                                                                                   | Document                                                                                                          |
| --------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------- |
| **Playing a run** (loop, scoring, state→command, pitfalls)                              | [`PLAY.md` §1–§6](../PLAY.md#1-what-you-are-doing); commands in [`tools/play/README.md`](../tools/play/README.md) |
| **Installing / launching** (one-time setup, `serve.ps1`)                                | [`README.md`](../README.md)                                                                                       |
| **AI dev guidance** (make rules, architecture summary, play quick-start inline)         | [`AGENTS.md`](../AGENTS.md)                                                                                       |
| **API reference** (every method, params, schemas, enums, errors)                        | [`api.md`](api.md)                                                                                                |
| **Card keys** (formats, examples, canonical machine-readable sources)                   | [`card-keys.md`](card-keys.md)                                                                                    |
| **CLI reference** (all `serve` flags, env vars, platform paths, troubleshooting)        | [`cli.md`](cli.md)                                                                                                |
| **Contributing / dev setup** (direnv, Lua LSP, adding an endpoint, tests, CI, PR rules) | [`contributing.md`](contributing.md)                                                                              |
| **Play helpers** (`bot.ps1` commands, compact summary vs detail queries vs JSON)        | [`../tools/play/README.md`](../tools/play/README.md)                                                              |
| **Estimate scoring model** (joker registry, live-test checklist)                        | [`../tools/play/estimate_registry.md`](../tools/play/estimate_registry.md)                                        |
| **Knowledge library** (verified lookup tables, including **deck** and challenge)        | [`../knowledge/balatro/README.md`](../knowledge/balatro/README.md)                                                |

---

## 4. Component Snapshot

These one-line descriptions are enough to orient you; read the linked doc for behavior details.

### Python layer (`src/balatrobot/`)

- **`cli/serve.py`** — `balatrobot serve` launches `Balatro.exe` with the mod, polls `/health`, keeps the process alive.
- **`cli/api.py`** — `balatrobot api METHOD PARAMS` calls one JSON-RPC method on a running server.
- **`manager.py`** — `BalatroInstance` async context manager: starts subprocess, waits for health, logs to `logs/<timestamp>/<port>.log`, tears down on exit.
- **`config.py`** — `Config` dataclass; every field maps to a `BALATROBOT_*` env var. Priority: CLI flag → env var → default.
- **`platforms/`** — per-OS launcher: `validate_paths`, `build_cmd`, `build_env`, `cleanup`.

### Lua layer (`src/lua/`)

- **`core/server.lua`** — single-client HTTP/1.1 server on LuaSocket, max body 64KB, only handles `POST /`.
- **`core/dispatcher.lua`** — routes by `method`; pipeline: protocol check → endpoint lookup → schema validation → game-state check → execute.
- **`core/validator.lua`** — checks params against each endpoint's `schema` table; returns `BAD_REQUEST` on failure.
- **`endpoints/*.lua`** — one module per API method, each exports `name`, `schema`, `requires_state`, `execute`.
- **`utils/gamestate.lua`** — reads `G.*` and produces the JSON-serializable gamestate. Masks face-down cards (boss blinds) so the bot can't cheat.
- **`utils/openrpc.json`** — machine-readable API spec, the source of truth for method signatures.

### Game states

Primary loop states: `MENU`, `BLIND_SELECT`, `SELECTING_HAND`, `ROUND_EVAL`, `SHOP`, `SMODS_BOOSTER_OPENED`, `GAME_OVER`. **Transient** states (`HAND_PLAYED`, `DRAW_TO_HAND`, `NEW_ROUND`, `PLAY_TAROT`) require re-polling with `glance` until stable — see [`PLAY.md` §2](../PLAY.md#2-loop-and-hard-rules) and the transient line in [`tools/play/README.md`](../tools/play/README.md#what-glance-shows). The state→command mapping is in [`PLAY.md` §4](../PLAY.md#4-state--command); the per-method contracts are in [`api.md`](api.md).

### Error codes

`INTERNAL_ERROR` (-32000), `BAD_REQUEST` (-32001), `INVALID_STATE` (-32002), `NOT_ALLOWED` (-32003). See [`api.md`](api.md) for the full error object shape.

---

Development setup, test commands, and quality checks live in
[contributing.md](contributing.md); agent-specific enforcement rules live in
[AGENTS.md](../AGENTS.md).
