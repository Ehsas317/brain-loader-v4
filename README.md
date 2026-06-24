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

1. **Wave Engine** replaces the task loop. The Brain plans a *wave* of 2–5 parallel tasks instead of a sequential list of 30–80.
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
| `