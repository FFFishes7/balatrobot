# Play Helpers

Convenience scripts on top of the BalatroBot JSON-RPC API. Not required by the core package — they make manual and LLM-assisted play easier.

## Workflow

1. **One-time:** install Lovely + Steamodded, link this repo into `%AppData%\Balatro\Mods\balatrobot\`, run `make install`, copy `serve.example.ps1` → `serve.ps1`.
2. **Launch:** `.\tools\play\serve.ps1` — starts Balatro with the mod and the API on port 12346.
3. **Play:** in another terminal, use `.\tools\play\bot.ps1 ...`.

See the root [README](../../README.md#local-play) for the full setup.

## Commands

```powershell
.\tools\play\bot.ps1 state
.\tools\play\bot.ps1 know preflight
.\tools\play\bot.ps1 play 0 1
.\tools\play\bot.ps1 pack skip
.\tools\play\bot.ps1 sort rank
```

## Files

- `bot.ps1` — PowerShell entry point for helper commands
- `act.py` — play / discard / shop / pack / use / rearrange / sort
- `view.py` — compact gamestate display
- `know.py` — lookups against `knowledge/balatro`
- `bot_client.py`, `rpc.py` — JSON-RPC client
- `serve.example.ps1` — copy to `serve.ps1` and set your Balatro Steam path (`serve.ps1` is gitignored)
