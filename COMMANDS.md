# AntiGravity Discord Bot Commands

This file documents all available Discord bot commands and CLI options.

## Discord Commands

| Command | Description | Usage |
|---------|-------------|-------|
| `!ping` | Simple connectivity test | `!ping` |
| `!status` | Check bridge status | `!status` |
| `!screenshot` | Take a screenshot of the desktop | `!screenshot` |
| `!model` | Show available models | `!model` |
| `!model <num>` | Switch to model by number | `!model 3` |
| `!approve` / `!yes` | Approve a pending CLI command | `!approve` |
| `!reject` / `!no` | Reject a pending CLI command | `!reject` |
| `!max [title]` | Maximize a window | `!max AntiGravity` |
| `!min [title]` | Minimize a window | `!min Chrome` |
| `!focus [title]` | Focus a window | `!focus Discord` |
| `!restore [title]` | Restore a minimized window | `!restore` |
| `!windows` | List all open windows | `!windows` |
| `!project <path>` | Open a project in AntiGravity | `!project d:\what-to-do-ai` |

## CLI Options

Run these from the project directory with the virtual environment activated:

```bash
# Activate virtual environment first!
.\venv\Scripts\activate
```

| Option | Description |
|--------|-------------|
| `python bridge.py` | Run the bridge directly |
| `python bridge.py --calibrate` | Calibrate chat input visual anchor |
| `python bridge.py --calibrate-send` | Calibrate send button (arrow icon) |
| `python bridge.py --calibrate-model` | Calibrate model selector anchor |
| `python bridge.py --calibrate-approval` | Calibrate command approval dialog |
| `uvicorn server:app --reload` | Run with hot-reload (recommended) |

## Model Selection

Use `!model` to see available models, or `!model <number>` to switch:

| # | Model | Command |
|---|-------|---------|
| 1 | Gemini 3 Pro (High) | `!model 1` |
| 2 | Gemini 3 Pro (Low) | `!model 2` |
| 3 | Gemini 3 Flash | `!model 3` |
| 4 | Claude Sonnet 4.5 | `!model 4` |
| 5 | Claude Sonnet 4.5 (Thinking) | `!model 5` |
| 6 | Claude Opus 4.5 (Thinking) | `!model 6` |
| 7 | GPT-OSS 120B (Medium) | `!model 7` |

---

*Last Updated: 2026-02-01*
