# Play Helpers

JSON-only interface on top of the BalatroBot JSON-RPC API.

## Workflow

1. **One-time:** install Lovely + Steamodded, link this repo into `%AppData%\Balatro\Mods\balatrobot\`, run `make install`, copy `serve.example.ps1` → `serve.ps1`.
2. **Launch:** `.\tools\play\serve.ps1` — starts Balatro with the mod and the API on port 12346.
3. **Play:** in another terminal, use `.\tools\play\bot.ps1 ...`.

See the root [README](../../README.md#local-play) for the full setup.

## Commands

```powershell
.\tools\play\bot.ps1 state
.\tools\play\bot.ps1 query deck
.\tools\play\bot.ps1 know preflight
.\tools\play\bot.ps1 exec '{"command":"play","params":{"cards":[0,1,2,3,4]}}'
.\tools\play\bot.ps1 help
```

## AI loop

1. `state` → Layer 1 `gamestate` + `actions` + optional `queries`
2. `know preflight` → verified joker/boss/stake facts
3. (optional) `query deck` / `query hands` / …
4. `exec` with an `actions[].example` payload
5. Repeat until `gamestate.state == "GAME_OVER"`

## Files

- `bot.ps1` — entry point (`state` / `query` / `know` / `exec` / `help`)
- `state.py` — fetch stable gamestate envelope
- `query.py` — Layer 2 queries
- `exec.py` — run one RPC action, return envelope
- `know.py` — knowledge base lookups (JSON)
- `help.py` — hidden/debug commands
- `layers.py`, `envelope.py`, `actions.py`, `commands.py`, `start_options.py` — core logic
- `bot_client.py` — JSON-RPC client
- `serve.example.ps1` — copy to `serve.ps1` and set your Balatro Steam path (`serve.ps1` is gitignored)
