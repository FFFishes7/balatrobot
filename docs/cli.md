# CLI Reference

Command-line interface for **BlindDeck** (`balatrobot` CLI).

## Usage

```bash
# Start Balatro server
uvx balatrobot serve [OPTIONS]

# Call API on running server
uvx balatrobot api METHOD [PARAMS] [OPTIONS]
```

BlindDeck provides two commands:

- **serve** - Start Balatro with the BlindDeck mod loaded
- **api** - Call API endpoints on a running server

## serve Command

Start Balatro with the BlindDeck mod loaded and API server running.

```bash
uvx balatrobot serve [OPTIONS]
```

### Options

All options can be set via CLI flags or environment variables. CLI flags override environment variables.

| CLI Flag                        | Environment Variable             | Default       | Description                                |
| ------------------------------- | -------------------------------- | ------------- | ------------------------------------------ |
| `--host HOST`                   | `BALATROBOT_HOST`                | `127.0.0.1`   | Server hostname                            |
| `--port PORT`                   | `BALATROBOT_PORT`                | `12346`       | Server port                                |
| `--fast`                        | `BALATROBOT_FAST`                | `0`           | Enable fast mode (10x game speed)          |
| `--headless`                    | `BALATROBOT_HEADLESS`            | `0`           | Enable headless mode (minimal rendering)   |
| `--render-on-api`               | `BALATROBOT_RENDER_ON_API`       | `0`           | Render only on API calls                   |
| `--audio`                       | `BALATROBOT_AUDIO`               | `0`           | Enable audio                               |
| `--debug`                       | `BALATROBOT_DEBUG`               | `0`           | Enable debug mode (requires DebugPlus mod) |
| `--no-shaders`                  | `BALATROBOT_NO_SHADERS`          | `0`           | Disable all shaders                        |
| `--fps-cap FPS_CAP`             | `BALATROBOT_FPS_CAP`             | `60`          | Maximum FPS cap                            |
| `--gamespeed GAMESPEED`         | `BALATROBOT_GAMESPEED`           | `4`           | Game speed multiplier                      |
| `--animation-fps ANIMATION_FPS` | `BALATROBOT_ANIMATION_FPS`       | `10`          | Animation FPS                              |
| `--no-reduced-motion`           | `BALATROBOT_NO_REDUCED_MOTION`   | `0`           | Disable reduced motion                     |
| `--pixel-art-smoothing`         | `BALATROBOT_PIXEL_ART_SMOOTHING` | `0`           | Enable pixel art smoothing                 |
| `--balatro-path BALATRO_PATH`   | `BALATROBOT_BALATRO_PATH`        | auto-detected | Path to Balatro game directory             |
| `--lovely-path LOVELY_PATH`     | `BALATROBOT_LOVELY_PATH`         | auto-detected | Path to lovely library (dll/so/dylib)      |
| `--love-path LOVE_PATH`         | `BALATROBOT_LOVE_PATH`           | auto-detected | Path to game launcher executable           |
| `--platform PLATFORM`           | `BALATROBOT_PLATFORM`            | auto-detected | Platform: darwin, linux, windows, native   |
| `--logs-path LOGS_PATH`         | `BALATROBOT_LOGS_PATH`           | `logs`        | Directory for log files                    |
| `-h, --help`                    | -                                | -             | Show help message and exit                 |

!!! note "Mutually Exclusive Flags"

    `--headless` and `--render-on-api` are mutually exclusive.

**Note:** Boolean flags (`--fast`, `--headless`, etc.) use `1` for enabled and `0` for disabled when set via environment variables.

## api Command

Call an API endpoint on a running BlindDeck server. Returns JSON response to stdout.

```bash
uvx balatrobot api METHOD [PARAMS] [OPTIONS]
```

### Arguments

| Argument | Required | Description                                        |
| -------- | -------- | -------------------------------------------------- |
| `METHOD` | Yes      | API method to call (see available methods below)   |
| `PARAMS` | No       | JSON object with method parameters (default: `{}`) |

### Options

| CLI Flag      | Default     | Description     |
| ------------- | ----------- | --------------- |
| `--host HOST` | `127.0.0.1` | Server hostname |
| `--port PORT` | `12346`     | Server port     |

### Available Methods

`add`, `buy`, `cash_out`, `challenge`, `challenges`, `debuff`, `discard`, `endless`, `gamestate`, `health`, `load`, `menu`, `next_round`, `pack`, `play`, `rearrange`, `reroll`, `reroll_boss`, `rpc.discover`, `save`, `screenshot`, `select`, `sell`, `set`, `skip`, `sort`, `start`, `use`

For detailed method documentation including parameters and schemas, see the [OpenRPC specification](../src/lua/utils/openrpc.json).

### api Examples

```bash
# Health check
uvx balatrobot api health

# Get current game state
uvx balatrobot api gamestate

# Start a new game with Red Deck
uvx balatrobot api start '{"deck": "RED", "stake": "WHITE"}'

# Play cards at indices 0 and 2
uvx balatrobot api play '{"cards": [0, 2]}'

# Connect to server on different port
uvx balatrobot api health --port 8080
```

### Error Handling

On success, prints JSON result to stdout (exit code 0).
On error, prints `Error: NAME - message` to stderr (exit code 1).

## Serve Examples

### Basic Usage

```bash
# Start an interactive session with audio
uvx balatrobot serve --audio

# Start a fast interactive session with audio
uvx balatrobot serve --fast --audio

# Start with debug mode (requires DebugPlus mod)
uvx balatrobot serve --fast --audio --debug

# Start headless for automated testing
uvx balatrobot serve --headless --fast
```

### Custom Port

```bash
# Use a different port
uvx balatrobot serve --port 8080 --audio
```

Platform-specific custom paths are covered below.

## Environment Variable Precedence

**Bash:**

```bash
# Configure via environment variables
export BALATROBOT_PORT=8080
export BALATROBOT_FAST=1
export BALATROBOT_AUDIO=1

# Launch with defaults from env vars
uvx balatrobot serve

# CLI flags override env vars
uvx balatrobot serve --port 9000  # Uses port 9000, not 8080
```

**Windows PowerShell:**

```powershell
$env:BALATROBOT_PORT = "8080"
$env:BALATROBOT_FAST = "1"
$env:BALATROBOT_AUDIO = "1"
uvx balatrobot serve
```

## Process Management

The CLI automatically:

- Logs output to `logs/{timestamp}/{port}.log`
- Sets up the correct environment variables
- Gracefully shuts down on Ctrl+C

## Platform-Specific Details

The launcher selects a platform automatically; override it with `--platform` when
needed.

| Platform       | Game / launcher path                             | Lovely path                                                  | Mods directory                                                                           |
| -------------- | ------------------------------------------------ | ------------------------------------------------------------ | ---------------------------------------------------------------------------------------- |
| Windows        | `...\Steam\steamapps\common\Balatro\Balatro.exe` | `...\Balatro\version.dll`                                    | `%AppData%\Balatro\Mods`                                                                 |
| macOS          | `.../Balatro.app/Contents/MacOS/love`            | `.../Balatro/liblovely.dylib`                                | `~/Library/Application Support/Balatro/Mods`                                             |
| Linux (Proton) | Balatro directory + detected Proton executable   | `<Balatro>/version.dll`                                      | `~/.local/share/Steam/steamapps/compatdata/2379780/pfx/.../AppData/Roaming/Balatro/Mods` |
| Linux (native) | Balatro source directory + `love` from `PATH`    | `/usr/local/lib/liblovely.so` or `~/.local/lib/liblovely.so` | `~/.config/love/Mods`                                                                    |

Common requirements are Balatro, Lovely Injector, and the matching injector
library in the game directory. Additional constraints:

- macOS launches the LOVE runtime directly because launching through Steam is
    unreliable.
- Linux Proton requires `DISPLAY` or `WAYLAND_DISPLAY`; only Valve's standard
    Steam package is tested.
- Native Linux requires a source directory containing `main.lua` and game
    settings under `~/.local/share/love/balatro`.

### Custom path examples

```powershell
# Windows
uvx balatrobot serve --audio `
  --love-path "C:\Custom\Balatro\Balatro.exe" `
  --lovely-path "C:\Custom\Balatro\version.dll"
```

```bash
# macOS
uvx balatrobot serve --audio \
  --love-path "/path/to/Balatro.app/Contents/MacOS/love" \
  --lovely-path "/path/to/Balatro/liblovely.dylib"

# Linux via Proton
uvx balatrobot serve --audio \
  --love-path /path/to/proton \
  --balatro-path /path/to/Balatro

# Native Linux
uvx balatrobot serve --audio --platform native \
  --balatro-path /path/to/balatro/source
```

## Troubleshooting

**Connection refused**: Ensure Balatro is running and the mod loaded successfully. Check logs in `logs/{timestamp}/{port}.log` for errors.

**Mod not loading**: Verify that Lovely Injector and Steamodded are installed correctly.

**Port in use**: Change the port with `--port` or set `BALATROBOT_PORT` to a different value.

**Game crashes**: Try disabling shaders with `--no-shaders` or running in headless mode with `--headless`.

## Play helper environment variables

Used by `tools/play/bot.ps1` helpers (not the `balatrobot serve` launcher itself):

| Variable                   | Default                      | Purpose                                                         |
| -------------------------- | ---------------------------- | --------------------------------------------------------------- |
| `BALATROBOT_KNOWLEDGE_DIR` | `knowledge/balatro/` in repo | Override path for `know` lookup JSON files                      |
| `BALATROBOT_ALLOW_CHEATS`  | unset                        | Set to `1` to enable debug `add` / `set` / `debuff` subcommands |

See [tools/play/README.md](../tools/play/README.md) for cheat gating and [knowledge/balatro/README.md](../knowledge/balatro/README.md) for the knowledge library layout.
