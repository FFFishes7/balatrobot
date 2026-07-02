# Play Helpers

These scripts are a convenience layer on top of the BalatroBot JSON-RPC API. They are not required by the core BalatroBot package; they make manual/LLM-assisted play easier.

## Main entry point

```powershell
.\tools\play\bot.ps1 state
.\tools\play\bot.ps1 know preflight
.\tools\play\bot.ps1 play 0 1
.\tools\play\bot.ps1 pack skip
.\tools\play\bot.ps1 sort rank
```

## Files

- `bot.ps1`: PowerShell wrapper for the helper scripts.
- `act.py`: action dispatcher for play/discard/shop/pack/use/rearrange/sort helpers.
- `view.py`: compact human-readable gamestate display.
- `know.py`: lookup/preflight checks against `knowledge/balatro`.
- `bot_client.py` and `rpc.py`: thin JSON-RPC client helpers.
- `serve.example.ps1`: copy to `serve.ps1` and adjust your local Balatro install path.

`serve.ps1` is intentionally ignored because it usually contains machine-specific paths.
