# Card Key Reference

Card keys identify playing cards, Jokers, consumables, vouchers, and booster
packs in the BlindDeck API. They appear in `Card.key` and are accepted by debug
methods such as [`add`](api.md#add).

## Canonical sources

Use the source that matches the task:

| Need                              | Source                                                                 |
| --------------------------------- | ---------------------------------------------------------------------- |
| Validate an API request           | [`openrpc.json`](../src/lua/utils/openrpc.json), schema `CardKey`      |
| Update runtime-supported keys     | [`enums.lua`](../src/lua/utils/enums.lua)                              |
| Read verified names and effects   | [`knowledge/balatro/`](../knowledge/balatro/README.md)                 |
| Inspect cards in the current game | `bot.ps1 state --json`, `query`, or the relevant `gamestate` card area |

`openrpc.json` is the API contract. Do not maintain another exhaustive key
list in Markdown; duplicated lists drift when Balatro or BlindDeck changes.

## Key families

| Family                  | Format or examples                          |
| ----------------------- | ------------------------------------------- |
| Playing cards           | `{Suit}_{Rank}`, such as `H_A` or `S_T`     |
| Tarot, Planet, Spectral | `c_...`, such as `c_fool` or `c_black_hole` |
| Jokers                  | `j_...`, such as `j_joker` or `j_blueprint` |
| Vouchers                | `v_...`, such as `v_grabber`                |
| Booster packs           | `p_...`, such as `p_arcana_normal_1`        |

Consumable families share the `c_` prefix. Use the card's `set` field
(`TAROT`, `PLANET`, or `SPECTRAL`) when the family matters.

### Playing-card format

- Suits: `H` (Hearts), `D` (Diamonds), `C` (Clubs), `S` (Spades).
- Ranks: `2`–`9`, `T`, `J`, `Q`, `K`, `A`.

Examples: `H_A` is the Ace of Hearts; `D_T` is the Ten of Diamonds.

## Human-friendly lookup

For verified effects and localized names, prefer the play-helper knowledge
commands instead of searching a static Markdown table:

```powershell
.\tools\play\bot.ps1 know check joker j_blueprint
.\tools\play\bot.ps1 know list joker
```

For the exact machine-readable enum, inspect `components.schemas.CardKey` in
`src/lua/utils/openrpc.json` or call `rpc.discover` on a running game.
