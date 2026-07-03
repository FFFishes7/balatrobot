# Play Helpers

Two interfaces on top of the BalatroBot JSON-RPC API:

- **Friendly subcommands** (default) — positional args, no JSON to quote.
- **JSON envelope** (`state` / `exec` / `query` / `know`) — machine-readable, for advanced use.

## Workflow

1. **One-time:** install Lovely + Steamodded, link this repo into `%AppData%\Balatro\Mods\balatrobot\`, run `make install`, copy `serve.example.ps1` → `serve.ps1`.
2. **Launch:** `.\tools\play\serve.ps1` — starts Balatro with the mod and the API on port 12346.
3. **Play:** in another terminal, use `.\tools\play\bot.ps1 ...`.

See the root [README](../../README.md#local-play) and [`PLAY.md`](../../PLAY.md) for the full play guide.

## Commands

```powershell
.\tools\play\bot.ps1 glance              # compact multi-line state summary
.\tools\play\bot.ps1 state               # full JSON envelope
.\tools\play\bot.ps1 know preflight      # verified joker/boss/stake/tag facts
.\tools\play\bot.ps1 query hands         # poker hand level table (base chips/mult)
.\tools\play\bot.ps1 help                # state-aware command list
```

### Friendly action subcommands

No JSON, no quoting — `bot.ps1` forwards these to `act.py`, which parses positional args via `commands.build_params` and prints the new state as a compact summary. Append `--json` to any of them to print the raw envelope instead.

| Command | Args | Notes |
|---|---|---|
| `start` | `DECK STAKE [SEED]` | e.g. `start RED WHITE` |
| `select` | — | select current blind |
| `skip` | — | skip current blind (Small/Big only) — collects the skip tag |
| `play` | `CARD_IDX...` | e.g. `play 0 1 2 3 4` (max 5, 0-based) |
| `discard` | `CARD_IDX...` | e.g. `discard 0 1` |
| `sort` | `MODE` | `rank` / `rank-desc` / `rank-asc` / `suit` / `suit-desc` / `suit-asc` (aliases: `r`,`s`,`rd`,...) |
| `rearrange` | `hand\|jokers\|consumables FULL_ORDER` | e.g. `rearrange hand 2 0 1 3` |
| `buy` | `card\|voucher\|pack IDX` | e.g. `buy card 0`, `buy pack 0` |
| `sell` | `joker\|consumable IDX` | e.g. `sell joker 0` |
| `reroll` | — | reroll shop |
| `cash_out` | — | collect round rewards |
| `next_round` | — | leave shop for blind select |
| `pack` | `IDX [TARGET_IDX...]` or `skip` | e.g. `pack 0`, `pack 0 1 2` (targets for Tarot/Spectral), `pack skip` |
| `use` | `CONSUMABLE_IDX [CARD_IDX...]` | e.g. `use 0`, `use 0 1 2` |
| `death` | `CONSUMABLE SOURCE TARGET` | special: reorders hand then uses Death |
| `menu` | — | return to main menu |
| `save` / `load` / `screenshot` | `PATH` | |

### JSON / advanced

```powershell
.\tools\play\bot.ps1 state                       # full play envelope (gamestate + actions + queries)
.\tools\play\bot.ps1 exec '{\"command\":\"play\",\"params\":{\"cards\":[0,1,2,3,4]}}'
.\tools\play\bot.ps1 query deck | query hands | query blinds | query used_vouchers | query seed
```

> **PowerShell quoting:** `exec` takes a JSON string argument. PowerShell strips
> unescaped double quotes when passing to native exes, so you must escape them
> as `\"` (as shown above). Prefer the friendly subcommands — they avoid this
> entirely.

## AI loop

1. `glance` → compact state + `actions:` line (valid next commands)
2. `know preflight` → verified joker/boss/stake/tag effects (before non-trivial decisions)
3. (optional) `query hands` / `query deck` / …
4. friendly action subcommand → prints the new compact state automatically
5. Repeat until `state == GAME_OVER`, then `menu` + `start`

Every `glance` / action output ends with an `actions:` line listing the
commands valid in the current state. The full envelope (from `state` /
`exec` / `<action> --json`) includes an `actions[]` array with `example`
payloads for each.

## Files

- `bot.ps1` — entry point (`glance` / `state` / `query` / `know` / `exec` / `help` + friendly action subcommands)
- `view.py` — compact summary formatter + `glance` command (`card_label`, `print_summary`)
- `act.py` — friendly action dispatcher (`build_params` → `execute` → compact summary, `--json` for envelope)
- `state.py` — full JSON gamestate envelope
- `query.py` — Layer 2 queries
- `exec.py` — raw JSON-RPC action, returns envelope
- `know.py` — knowledge base lookups (JSON)
- `commands.py` — friendly-command → RPC params parser
- `actions.py` — state-aware action list builder
- `layers.py`, `envelope.py`, `start_options.py`, `bot_client.py` — core logic
- `serve.example.ps1` — copy to `serve.ps1` and set your Balatro Steam path (`serve.ps1` is gitignored)
