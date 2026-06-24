# Brain Loader v4

**Multi-Backend Agentic AI Orchestrator**

Local MLX · Local Ollama · Cloud API · Hybrid Parallel Execution · Auto-Failover · Terminal-Native REPL · Cost Tracking

> **Evolution from v3:** v4 replaces the sequential single-model architecture with a **wave-based parallel dispatch** system, adds **7+ cloud providers**, introduces **automatic provider failover chains**, and ships with a **Rich-powered terminal REPL**. Where v3 hot-swapped one local model at a time, v4 orchestrates multiple backends simultaneously — routing each task to the best available provider.

---

## Table of Contents

- [What's New in v4](#whats-new-in-v4)
- [Architecture Overview](#architecture-overview)
- [Execution Modes](#execution-modes)
- [Supported Providers](#supported-providers)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [Terminal REPL Commands](#terminal-repl-commands)
- [Role-Based Routing](#role-based-routing)
- [Cost Tracking & Budgets](#cost-tracking--budgets)
- [Circuit Breaker & Failover](#circuit-breaker--failover)
- [File Structure](#file-structure)
- [Migrating from v3](#migrating-from-v3)
- [Troubleshooting](#troubleshooting)

---

## What's New in v4

| Feature | v3 | v4 |
|---|---|---|
| **Execution model** | Sequential (one task at a time) | Wave-based parallel dispatch |
| **Max parallelism** | 1 task | Configurable batch (default 5) |
| **Backends** | MLX (Apple) + Ollama (any) | MLX + Ollama + 6 cloud providers |
| **Provider failover** | None | Per-role provider chains with auto-fallback |
| **Circuit breaker** | None | Automatic failure detection & recovery |
| **Cost tracking** | None | Per-session cost with budget limits |
| **User interface** | CLI arguments only | Rich terminal REPL with live tables |
| **Human approval** | None | HITL (Human-in-the-Loop) wave approval |
| **Memory model** | Structured markdown file | Rolling context window |
| **Hot-swap** | Yes (one model in RAM) | N/A (stateless API calls + local locks) |
| **Async architecture** | Synchronous | Fully async (`asyncio`) |
| **Cloud API support** | None | Anthropic, OpenAI, OpenRouter, Groq, DeepSeek, Google |

### Key Architectural Changes

1. **Wave Engine** replaces the task loop. The Brain plans a *wave* of 2-5 parallel tasks instead of a sequential list of 30-80.
2. **Universal Router** sends each task to its assigned provider via a priority chain. If the primary fails, it automatically tries the next.
3. **Terminal REPL** (`tui/repl.py`) provides an interactive experience with live task status tables, command interface, and wave approval.
4. **Pure async** — all provider calls are async with `aiohttp`/`asyncio`, enabling true parallelism.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Terminal REPL (Rich)                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────┐  │
│  │ /status      │  │ /memory      │  │ /cost                    │  │
│  │ /mode        │  │ /save        │  │ /exit                    │  │
│  └──────────────┘  └──────────────┘  └──────────────────────────┘  │
└─────────────────────────────┬───────────────────────────────────────┘
                              │
┌─────────────────────────────▼───────────────────────────────────────┐
│                      Wave Engine                                    │
│  1. Plan  → Brain decomposes goal into parallel task wave           │
│  2. Dispatch → Parallel tasks sent to Universal Router              │
│  3. Synthesize → Brain combines all outputs into final answer       │
└─────────────────────────────┬───────────────────────────────────────┘
                              │
┌─────────────────────────────▼───────────────────────────────────────┐
│                    Universal Router                                 │
│  Per-role provider chains:                                          │
│    coder:    [ollama/qwen2.5-coder:32b] → [groq/llama-3.3-70b]    │
│    researcher: [anthropic/claude-3.5-sonnet] → [openai/gpt-4o]    │
│    writer:   [deepseek-chat] → [ollama/qwen3:32b]                 │
│                                                                     │
│  Circuit Breaker: skips failing providers, retries after timeout    │
│  Local locks: mlx and ollama share one slot each (async-safe)       │
└────────────┬──────────────────────┬────────────────────┬────────────┘
             │                      │                    │
    ┌────────▼────────┐  ┌─────────▼─────────┐  ┌──────▼──────┐
    │  Local Backends │  │  Cloud Providers  │  │   Cost      │
    │                 │  │                   │  │   Tracker   │
    │  • MLX          │  │  • Anthropic      │  │             │
    │  • Ollama       │  │  • OpenAI         │  │  $ per      │
    │                 │  │  • OpenRouter     │  │  session    │
    │  (Apple Silicon │  │  • Groq           │  │  with       │
    │   + any system) │  │  • DeepSeek       │  │  budget     │
    │                 │  │  • Google Gemini  │  │  limits     │
    └─────────────────┘  └───────────────────┘  └─────────────┘
```

### Execution Flow (One Wave)

```
User enters goal in REPL
         │
         ▼
┌─────────────────┐     ┌──────────────────────┐
│  Brain plans    │────▶│  Task wave (2-5      │
│  (brain role)   │     │  parallel tasks)     │
└─────────────────┘     └──────────────────────┘
                                 │
                    ┌────────────┼────────────┐
                    ▼            ▼            ▼
              ┌─────────┐  ┌─────────┐  ┌─────────┐
              │ Task T1 │  │ Task T2 │  │ Task T3 │  (parallel_safe=true)
              │ coder   │  │researchr│  │ writer  │
              └────┬────┘  └────┬────┘  └────┬────┘
                   │            │            │
                   └────────────┼────────────┘
                                ▼
                    ┌─────────────────────┐
                    │  Sequential tasks   │  (parallel_safe=false)
                    │  (after parallel    │
                    │   results available)│
                    └─────────────────────┘
                                │
                                ▼
                    ┌─────────────────────┐
                    │  Brain synthesizes  │
                    │  final answer from  │
                    │  all outputs        │
                    └─────────────────────┘
                                │
                                ▼
                    ┌─────────────────────┐
                    │  Save to outputs/   │
                    │  Update memory.md   │
                    │  Telegram notify    │
                    └─────────────────────┘
```

---

## Execution Modes

`config.yaml` → `mode:` controls the global behavior:

| Mode | Behavior | Best For |
|---|---|---|
| `"local"` | 100% local execution. MLX (Apple Silicon) and/or Ollama only. Zero API cost. Sequential dispatch with local locks. | Privacy-sensitive work, no budget, Apple Silicon users |
| `"api"` | 100% cloud execution. Maximum parallelism (all tasks run concurrently). Costs money per call. | Speed priority, complex tasks that need big models |
| `"hybrid"` | **Default.** Tries cloud providers first per role chain, falls back to local. Best balance of speed and cost. | General use — fast cloud where available, local fallback |

### How Hybrid Mode Works

1. Each role has a **provider chain** (priority list) in `config.yaml`
2. Router tries the first provider → if available and circuit breaker is closed, executes
3. If it fails (rate limit, quota, error) → tries the next provider in the chain
4. If all cloud providers fail → falls back to local (Ollama or MLX)
5. Circuit breakers prevent hammering failing providers

---

## Supported Providers

### Cloud Providers (API Key Required)

| Provider | Key File | Models | Rate Limit Handling |
|---|---|---|---|
| **Anthropic** | `providers.anthropic.api_key` | Claude 3.5 Sonnet, Haiku, Opus | Auto-skip on 429 |
| **OpenAI** | `providers.openai.api_key` | GPT-4o, GPT-4-turbo | 2s retry on 429 |
| **OpenRouter** | `providers.openrouter.api_key` | 100+ models via unified API | Auto-skip on 429 |
| **Groq** | `providers.groq.api_key` | Llama 3.3, Mixtral (fast inference) | Auto-skip on 429 |
| **DeepSeek** | `providers.deepseek.api_key` | DeepSeek-V3, DeepSeek-Coder | Auto-skip on 429 |
| **Google** | `providers.google.api_key` | Gemini 1.5 Pro, Flash | Standard HTTP |

### Local Providers (No API Key)

| Provider | Requirements | Best For |
|---|---|---|
| **MLX** | Apple Silicon + `mlx` + `mlx-lm` | Fastest local inference on Mac |
| **Ollama** | `ollama` installed and running | Any system — Linux, macOS, Windows |

### Provider Availability Check

Each provider implements `is_available()`:
- **Cloud**: Returns `true` if API key is configured
- **Ollama**: Probes `http://host:11434/api/tags` with 3s timeout
- **MLX**: Returns `true` if `mlx.core` can be imported

---

## Quick Start

### 1. Install Dependencies

```bash
# Base (required for all modes)
pip install -r requirements.txt

# Apple Silicon — add local MLX support
pip install -r requirements_local.txt
```

### 2. Configure

```bash
# Copy the example config
cp config.yaml config.my.yaml

# Edit — add your API keys for providers you want to use
nano config.my.yaml
```

At minimum, configure **one** provider:

```yaml
# For local-only (free):
providers:
  ollama:
    host: "http://localhost:11434"  # default

# For cloud (add keys for providers you have):
providers:
  anthropic:
    api_key: "sk-ant-your-key-here"
  groq:
    api_key: "gsk-your-key-here"
```

### 3. Set Role Chains

Each role (brain, coder, researcher, writer, math, critic) has a provider chain. The router tries each in order:

```yaml
roles:
  brain:
    max_tokens: 4096
    temperature: 0.6
    chain:
      - provider: ollama
        model: "qwen3:32b"
      # Fallback if Ollama fails:
      - provider: groq
        model: "llama-3.3-70b-versatile"
```

### 4. Run

```bash
# Interactive REPL (recommended)
python main.py

# Headless — single goal, auto-approves the wave
python main.py "Build a FastAPI server with JWT auth"

# Custom config
python main.py --config config.my.yaml "Research quantum computing applications"
```

### First Run Walkthrough

```
┌────────────────────────────────────────────┐
│ Brain Loader v4  —  Terminal Interactive   │
│ Mode: HYBRID                               │
│ Providers: anthropic · ollama · groq · ... │
├────────────────────────────────────────────┤
│ /status   Provider health + token stats    │
│ /memory   Show current memory.md           │
│ /mode     Current mode                     │
│ /cost     Session cost                     │
│ /save     Save output manually             │
│ /exit     Quit                             │
└────────────────────────────────────────────┘

You > Build a REST API for a task management app

🧠 Brain plans your wave...

┌ Brain's Proposed Wave ───────────────────────────────┐
│ ID │ Role      │ Prompt preview        │ Parallel    │
├────┼───────────┼───────────────────────┼─────────────┤
│ T1 │ coder     │ Design the database   │ ✓ Yes       │
│ T2 │ researcher│ Compare Flask vs Fast │ ✓ Yes       │
│ T3 │ writer    │ Write API docs        │ ⏳ After    │
└────┴───────────┴───────────────────────┴─────────────┘

Approve this wave? [y/n]: y

🌊 Dispatching 3 task(s) in HYBRID mode...

ID  │ Role       │ Status          │ Provider / Model        │ Time
────┼────────────┼─────────────────┼─────────────────────────┼──────
T1  │ coder      │ ✓ Done          │ ollama / qwen2.5-coder  │ 12.3s
T2  │ researcher │ ✓ Done          │ anthropic / claude-3.5  │ 8.1s
T3  │ writer     │ 🔄 Running      │ —                       │ —

[Final answer panel appears with synthesized output]

Saved → outputs/output_20260124_143052.md
```

---

## Configuration

### Full `config.yaml` Reference

```yaml
# ═══════════════════════════════════════════════════════════════════
# Execution mode: "local" | "api" | "hybrid"
# ═══════════════════════════════════════════════════════════════════
mode: "hybrid"

project:
  name: "brain_loader_v4"
  outputs_dir: "./outputs"           # Where task outputs are saved
  memory_file: "./memory.md"         # Rolling context window
  state_file: "./state.json"         # Crash recovery
  memory_context_bytes: 3000         # How much history the brain reads
  parallel_batch_size: 5             # Max parallel tasks per wave

# ─────────────────────────────────────────────────────────────────
# Telegram (optional — leave empty to disable)
# ─────────────────────────────────────────────────────────────────
telegram:
  token: ""
  chat_id: ""

# ═════════════════════════════════════════════════════════════════
# Provider Credentials — leave api_key as "" to disable
# ═════════════════════════════════════════════════════════════════
providers:
  anthropic:
    api_key: ""

  openai:
    api_key: ""

  openrouter:
    api_key: ""
    base_url: "https://openrouter.ai/api/v1"

  groq:
    api_key: ""

  deepseek:
    api_key: ""
    base_url: "https://api.deepseek.com/v1"

  google:
    api_key: ""
    base_url: "https://generativelanguage.googleapis.com/v1beta"

  ollama:
    host: "http://localhost:11434"

  mlx:
    enabled: false                    # Set to true on Apple Silicon

# ═════════════════════════════════════════════════════════════════
# Role → Provider Chain Routing
# The router tries each provider in order until one succeeds.
# ═════════════════════════════════════════════════════════════════
roles:
  brain:
    max_tokens: 4096
    temperature: 0.6
    chain:
      - provider: ollama
        model: "qwen3:32b"

  coder:
    max_tokens: 8192
    temperature: 0.2
    chain:
      - provider: ollama
        model: "qwen2.5-coder:32b"

  researcher:
    max_tokens: 6144
    temperature: 0.5
    chain:
      - provider: ollama
        model: "qwen3:32b"

  writer:
    max_tokens: 6144
    temperature: 0.7
    chain:
      - provider: ollama
        model: "qwen3:32b"

  math:
    max_tokens: 4096
    temperature: 0.1
    chain:
      - provider: ollama
        model: "qwen3:32b"

  critic:
    max_tokens: 4096
    temperature: 0.4
    chain:
      - provider: ollama
        model: "qwen3:14b"

# ─────────────────────────────────────────────────────────────────
# Cost Tracking & Budget Limits
# ─────────────────────────────────────────────────────────────────
cost_tracking:
  enabled: true
  warn_threshold: 10.00
  max_cost_per_project: 50.00

# ─────────────────────────────────────────────────────────────────
# Circuit Breaker — auto-disables failing providers
# ─────────────────────────────────────────────────────────────────
circuit_breaker:
  failure_threshold: 5       # Opens after 5 consecutive failures
  recovery_timeout: 60       # Tries again after 60 seconds

# ─────────────────────────────────────────────────────────────────
# Local Fallback
# ─────────────────────────────────────────────────────────────────
local_fallback:
  enabled: true
  ollama_host: "http://localhost:11434"
  fallback_model: "qwen3:32b"
```

---

## Terminal REPL Commands

During an interactive session, type `/` commands:

| Command | Description |
|---|---|
| `/status` | Provider health table + session token/cost stats |
| `/memory` | Display current `memory.md` contents |
| `/mode` | Show current execution mode (local/api/hybrid) |
| `/cost` | Show current session cost in USD |
| `/save` | Manually save the last output to `outputs/` |
| `/exit` | Quit the REPL |

Any input not starting with `/` is treated as a goal and sent to the Brain for planning.

---

## Role-Based Routing

Each **role** maps to a **provider chain** — an ordered list of (provider, model) pairs. The Universal Router walks the chain until a call succeeds.

### Default Role Mapping

| Role | Purpose | Default Provider |
|---|---|---|
| `brain` | Strategic planning, wave decomposition | First in chain |
| `coder` | Code generation, debugging, implementation | First in chain |
| `researcher` | Research, analysis, data gathering | First in chain |
| `writer` | Documentation, synthesis, long-form writing | First in chain |
| `math` | Mathematical reasoning, algorithms | First in chain |
| `critic` | Review, critique, quality assurance | First in chain |

### Custom Role Chains

Example: Use Claude for research, GPT-4o for coding, local Ollama for everything else:

```yaml
roles:
  researcher:
    max_tokens: 8192
    temperature: 0.4
    chain:
      - provider: anthropic
        model: "claude-3-5-sonnet-20241022"
      - provider: groq
        model: "llama-3.3-70b-versatile"
      - provider: ollama
        model: "qwen3:32b"

  coder:
    max_tokens: 16384
    temperature: 0.2
    chain:
      - provider: openai
        model: "gpt-4o"
      - provider: groq
        model: "llama-3.3-70b-versatile"
      - provider: ollama
        model: "qwen2.5-coder:32b"
```

---

## Cost Tracking & Budgets

The router automatically tracks token usage and estimated cost for every API call.

### Pricing Defaults (per 1M tokens)

| Provider | Input | Output |
|---|---|---|
| Anthropic (Sonnet) | $3.00 | $15.00 |
| OpenAI (GPT-4o) | $2.50 | $10.00 |
| OpenRouter | $0.27 | $0.85 |
| Groq | $0.50 | $0.79 |
| DeepSeek | $0.14 | $0.28 |
| Google (Gemini) | $1.25 | $10.00 |
| Local (MLX/Ollama) | $0.00 | $0.00 |

### Budget Alerts

```yaml
cost_tracking:
  enabled: true
  warn_threshold: 10.00       # Warning at $10
  max_cost_per_project: 50.00  # Hard stop at $50
```

Costs are printed after each wave and tracked in the router stats (`/cost` command).

---

## Circuit Breaker & Failover

Each provider has a **circuit breaker** that tracks consecutive failures:

- **Closed** (normal): Requests go through
- **Open** (after `failure_threshold` failures): Requests skip this provider
- **Half-open** (after `recovery_timeout` seconds): One trial request allowed

### Failure Triggers

The router detects and handles:
- **Rate limits** (429): Wait 2s, retry once, then move to next provider
- **Quota/billing errors**: Skip immediately (no retry)
- **Network timeouts**: Record failure, try next provider
- **Generic errors**: Record failure, try next provider

### Local Locks

Local providers (MLX, Ollama) use `asyncio.Lock` to ensure only one task accesses the local model at a time. Cloud providers have no such restriction — they run fully parallel.

---

## File Structure

```
brain-loader-v4/
├── main.py                      # Entry point — async CLI
├── config.yaml                  # Main configuration
├── requirements.txt             # Base dependencies (cloud + core)
├── requirements_local.txt       # + Apple Silicon local backends
├── memory.md                    # Rolling session context (auto-managed)
├── state.json                   # Crash recovery state (auto-managed)
│
├── core/                        # Core engine
│   ├── __init__.py
│   ├── router.py               # UniversalRouter + CircuitBreaker + stats
│   ├── wave_engine.py          # WaveEngine: plan → dispatch → synthesize
│   ├── cost_tracker.py         # Session-level spend monitoring
│   └── providers/              # Provider implementations
│       ├── __init__.py
│       ├── base.py             # BaseProvider + CallResult dataclass
│       ├── anthropic_provider.py
│       ├── openai_provider.py  # OpenAI + OpenRouter + Groq + DeepSeek
│       ├── gemini_provider.py  # Google Gemini
│       ├── ollama_provider.py  # Ollama local
│       └── mlx_provider.py     # MLX (Apple Silicon)
│
├── tui/                         # Terminal UI
│   ├── __init__.py
│   └── repl.py                 # BrainREPL: Rich console interface
│
└── utils/                       # Utilities
    ├── __init__.py
    ├── state_manager.py        # Persistent state (crash recovery)
    └── telegram_notify.py      # Telegram notifications
```

---

## Migrating from v3

### Key Differences

| Aspect | v3 | v4 Change |
|---|---|---|
| **Execution** | Sequential task loop | Wave-based parallel dispatch |
| **Entry point** | `python main.py "goal"` | `python main.py` for REPL, or `python main.py "goal"` for headless |
| **Config** | Separate MLX/Ollama sections | Unified `providers` + `roles` with chains |
| **Memory** | Structured `memory.md` with task list | Rolling context window (last N bytes) |
| **State** | `Coordinator` manages everything | `StateManager` + `WaveEngine` + `UniversalRouter` |
| **Models** | One model in RAM at a time | Stateless — models loaded per-call for locals |
| **Resume** | `--resume` flag | Not yet implemented in v4 (state manager exists) |

### Config Migration Example

**v3 config (Ollama):**
```yaml
backend: "ollama"
ollama_host: "http://localhost:11434"
brain_ollama:
  model_path: "qwen3:32b"
specialists_ollama:
  coder:
    model_path: "qwen2.5-coder:32b"
```

**v4 equivalent:**
```yaml
mode: "local"
providers:
  ollama:
    host: "http://localhost:11434"
roles:
  brain:
    chain:
      - provider: ollama
        model: "qwen3:32b"
  coder:
    chain:
      - provider: ollama
        model: "qwen2.5-coder:32b"
```

### What v3 Features Are Not (Yet) in v4

- `--resume` / checkpoint restoration (state manager exists but wave resume not implemented)
- `--constraints` CLI argument (constraints can be included in the goal prompt)
- `--list-specialists` (use `/status` in REPL instead)
- Task adaptation during execution (v4 replans per wave instead)

---

## Troubleshooting

### "No providers available"

Check `/status` in the REPL. Ensure at least one provider shows `[green]✓ Yes`.

**Cloud providers:** Verify your API key is set in `config.yaml`.
**Ollama:** Run `ollama serve` and check `ollama list` shows pulled models.
**MLX:** Ensure you're on Apple Silicon and `mlx` is installed.

### "All providers in chain failed"

1. Check `/status` — are circuit breakers OPEN? Wait `recovery_timeout` seconds or restart.
2. Check your API keys are valid (not expired or rate-limited).
3. Ensure Ollama is running: `curl http://localhost:11434/api/tags`

### High API costs

- Switch mode to `"local"` for free execution
- Use smaller models in your chains (e.g., `claude-3-5-haiku` instead of `opus`)
- Set `max_cost_per_project` to enforce a hard limit
- Local backends (MLX/Ollama) always cost $0.00

### MLX not loading on Apple Silicon

```bash
pip install -r requirements_local.txt
# Ensure you're using a Python version that supports MLX
python -c "import mlx.core; print('MLX OK')"
```

### Telegram notifications not working

Check that both `token` and `chat_id` are set in `config.yaml`. The bot must have sent at least one message to the chat before notifications work.

---

## License

MIT
