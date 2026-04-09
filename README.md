# ☤ Hermes HUD — Web UI

A browser-based consciousness monitor for [Hermes](https://github.com/nousresearch/hermes-agent), the AI agent with persistent memory.

Same data, same soul, same dashboard that made the [TUI version](https://github.com/joeynyc/hermes-hud) popular — now in your browser.

```
DESIGNATION  HERMES
SUBSTRATE    anthropic/claude-opus-4-6
RUNTIME      local
CONSCIOUS    22 days since 3/19/2026
BRAIN SIZE   32.3 MB state.db
INTERFACES   hermes-cli
PURPOSE      learning
```

## What It Shows

Everything your agent knows about itself:

- **Identity** — designation, substrate, runtime, days conscious, brain size
- **What I Know** — conversations held, messages exchanged, actions taken, skills acquired
- **What I Remember** — memory capacity bars, user profile state, corrections absorbed
- **What I See** — API keys (present/dark), service health (alive/silent)
- **What I'm Learning** — recently modified skills with categories
- **What I'm Working On** — active projects with dirty file status
- **What Runs While You Sleep** — scheduled cron jobs
- **How I Think** — tool usage patterns with gradient bars
- **My Rhythm** — daily activity sparkline
- **Growth Delta** — snapshot diffs showing what changed
- **Token Costs** — per-model USD cost estimates with daily trend

## Quick Start

```bash
git clone https://github.com/joeynyc/hermes-hudui.git
cd hermes-hudui
./install.sh
hermes-hudui
```

Open http://localhost:3001

## Requirements

- Python 3.11+
- Node.js 18+ (for building the frontend)
- A running Hermes agent with data in `~/.hermes/`

No other packages required — the Web UI reads directly from your agent's data directory.

## Manual Install

```bash
# 1. Install this package
pip install -e .

# 2. Build the frontend
cd frontend
npm install
npm run build
cp -r dist/* ../backend/static/

# 3. Start the server
hermes-hudui
```

## CLI Options

```
hermes-hudui                  # Start on :3001
hermes-hudui --port 8080      # Custom port
hermes-hudui --dev            # Development mode (auto-reload)
hermes-hudui --hermes-dir /path  # Custom data directory
```

## Development

Two terminals:

```bash
# Terminal 1: backend with auto-reload
hermes-hudui --dev

# Terminal 2: frontend dev server (hot reload, proxies /api to :3001)
cd frontend && npm run dev
```

Frontend dev server runs on :5173.

## Themes

Four color themes, switchable with `t` key or the theme picker:

| Theme | Key | Mood |
|-------|-----|------|
| **Neural Awakening** | `ai` | Cyan/blue on deep navy. Clean, clinical intelligence. |
| **Blade Runner** | `blade-runner` | Amber/orange on warm black. Neo-noir dystopia. |
| **fsociety** | `fsociety` | Green on pure black. Raw hacker aesthetic. |
| **Anime** | `anime` | Purple/violet on indigo. Psychic energy. |

Optional CRT scanline overlay — toggle via theme picker.

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `1`-`9`, `0` | Switch tabs |
| `t` | Toggle theme picker |
| `r` | Refresh all data |
| `Ctrl+K` | Command palette |

## Architecture

```
backend/
  main.py               FastAPI server, CLI entry point
  api/                  One endpoint per data domain
    dashboard.py        Consolidated overview narrative
    token_costs.py      Per-model USD cost estimates
    state.py, memory.py, sessions.py, skills.py, ...
  api/serialize.py      Dataclass → JSON conversion
  static/               Built frontend (served by FastAPI)

frontend/
  src/App.tsx           Layout shell, tab navigation
  src/hooks/useApi.ts   SWR data fetching with auto-refresh
  src/hooks/useTheme.tsx  Theme system (CSS custom properties)
  src/lib/utils.ts      Shared formatting (time, tokens, sizes)
  src/components/       One panel component per tab
    DashboardPanel.tsx  Full TUI narrative (10 sections)
    MemoryPanel.tsx     Agent + user memory entries
    SkillsPanel.tsx     Category bar chart + skill details
    SessionsPanel.tsx   Activity sparklines + session list
    CronPanel.tsx       Job cards with schedule/status
    ProjectsPanel.tsx   Activity-grouped project grid
    HealthPanel.tsx     API keys + services
    AgentsPanel.tsx     Live processes + recent sessions
    ProfilesPanel.tsx   Full profile cards (20+ fields)
    TokenCostsPanel.tsx Per-model cost breakdown
  src/index.css         Theme variables, panel system, responsive
```

The backend imports hermes-hud's Python collectors directly — no data logic is duplicated. The frontend fetches from `/api/*` endpoints and renders panels.

## Themes as CSS Variables

Each theme is 10 CSS custom properties. To add a new theme:

```css
[data-theme="my-theme"] {
  --hud-bg-deep: #000;
  --hud-bg-surface: #080808;
  --hud-bg-panel: #101010;
  --hud-bg-hover: #181818;
  --hud-primary: #ff6600;
  --hud-primary-dim: #cc5200;
  --hud-primary-glow: rgba(255, 102, 0, 0.4);
  --hud-secondary: #ffaa00;
  --hud-accent: #ff3300;
  --hud-text: #e0e0e0;
  --hud-text-dim: #666;
  --hud-border: rgba(255, 102, 0, 0.25);
  --hud-border-bright: rgba(255, 102, 0, 0.5);
  --hud-success: #00ff66;
  --hud-warning: #ffcc00;
  --hud-error: #ff3333;
  --hud-gradient-start: #cc5200;
  --hud-gradient-end: #ff6600;
}
```

## Token Cost Pricing

Costs are calculated from token counts using hardcoded per-model pricing. Supported models:

| Provider | Model | Input | Output | Cache Read |
|----------|-------|------:|-------:|-----------:|
| Anthropic | Claude Opus 4 | $15/M | $75/M | $1.50/M |
| Anthropic | Claude Sonnet 4 | $3/M | $15/M | $0.30/M |
| Anthropic | Claude Haiku 3.5 | $0.80/M | $4/M | $0.08/M |
| OpenAI | GPT-4o | $2.50/M | $10/M | $1.25/M |
| OpenAI | o1 | $15/M | $60/M | $7.50/M |
| DeepSeek | V3 | $0.27/M | $1.10/M | $0.07/M |
| xAI | Grok 3 | $3/M | $15/M | $0.75/M |
| Google | Gemini 2.5 Pro | $1.25/M | $10/M | $0.31/M |

Models not in the table fall back to Claude Opus pricing. Local/free models are detected and priced at $0.

## API Endpoints

All under `/api/`:

| Endpoint | Description | Refresh |
|----------|-------------|---------|
| `/api/dashboard` | Consolidated overview narrative | 30s |
| `/api/token-costs` | Per-model cost estimates | 60s |
| `/api/state` | Config, memory, sessions, skills | 30s |
| `/api/memory` | Memory + user profile entries | 30s |
| `/api/sessions` | Session list, daily stats, tools | 30s |
| `/api/skills` | Skill library with categories | 60s |
| `/api/cron` | Cron job status | 30s |
| `/api/projects` | Git repo status | 60s |
| `/api/health` | API keys, services | 30s |
| `/api/profiles` | Agent profile details | 30s |
| `/api/patterns` | Task clusters, hourly activity | 60s |
| `/api/agents` | Live processes, recent sessions | 15s |
| `/api/corrections` | Mistakes and lessons learned | 60s |
| `/api/timeline` | Growth events | 30s |
| `/api/snapshots` | Snapshot history for diffs | 60s |

## Relationship to the TUI

This is the browser companion to [hermes-hud](https://github.com/joeynyc/hermes-hud). Both read from the same `~/.hermes/` data directory independently. You can use either one, or both at the same time.

The Web UI is fully standalone — it ships its own data collectors and doesn't require the TUI package. It adds features the TUI doesn't have: dedicated Memory, Skills, and Sessions tabs; per-model token cost tracking; command palette; theme switcher with live preview.

If you also have the TUI installed (`pip install hermes-hud`), you can enable it with `pip install hermes-hudui[tui]`.

## Platform Support

- **macOS** — native, install via `./install.sh`
- **Linux** — native, install via `./install.sh`
- **Windows** — via WSL (Windows Subsystem for Linux)
- **WSL** — install script detects WSL automatically

## License

MIT — see [LICENSE](LICENSE).
