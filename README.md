# Surge (formerly Brain Loader v4)

Surge is the fourth iteration of the AI Build Engine. It introduces wave-based parallel dispatch across multiple LLM backends. A surge is simultaneous and forceful — tasks are distributed across all available providers at once, with results integrated automatically.

## What's New in Surge

- **Wave-Based Dispatch**: Tasks are sent in parallel waves across all providers
- **Multi-Backend Support**: Simultaneous use of Anthropic, OpenAI, Gemini, MLX, and Ollama
- **Cost Tracking**: Per-project budget monitoring with alerts
- **Intelligent Routing**: Automatic provider selection based on cost and availability
- **TUI Interface**: Interactive terminal UI for monitoring and control

## Hardware

MacBook Pro M1 Max 32GB (25GB allocated to Surge)

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt  # Cloud mode
# OR
pip install -r requirements_local.txt  # With local MLX + Ollama

# Set up config
cp config.yaml.example config.yaml
# Edit config.yaml with your tokens

# Run
python main.py "Build a React Native fitness app with AI meal planner"
```

## Architecture

Surge uses a wave-based dispatch pattern where tasks are distributed across multiple LLM providers simultaneously.

```
┌─────────────┐     ┌─────────────────┐     ┌──────────────┐
│   Request   │────▶│  Wave Engine    │────▶│  Provider A  │
│  (App Idea) │     │                 │     │  (DeepSeek)  │
└─────────────┘     │  ┌───────────┐  │────▶│  Provider B  │
                    │  │  Router   │  │     │  (Mistral)   │
                    │  │           │  │────▶│  Provider C  │
                    │  │ Cost-Aware│  │     │  (Claude)    │
                    │  │  Routing  │  │────▶│  Provider D  │
                    │  └───────────┘  │     │  (Together)  │
                    │                 │────▶│  Provider E  │
                    │  ┌───────────┐  │     │  (Local MLX) │
                    │  │  Tracker  │  │────▶│  Provider F  │
                    │  │  (Budget) │  │     │  (Ollama)    │
                    │  └───────────┘  │     └──────────────┘
                    └─────────────────┘
```

### Key Components

- **Wave Engine** (`core/wave_engine.py`) — Dispatches tasks in parallel waves
- **Model Router** (`core/router.py`) — Routes to optimal providers
- **Cost Tracker** (`core/cost_tracker.py`) — Monitors API spending
- **Provider Implementations** (`core/providers/`) — Pluggable LLM backends:
  - `anthropic_provider.py` — Claude API
  - `openai_provider.py` — OpenAI-compatible APIs (DeepSeek, Mistral, Together)
  - `gemini_provider.py` — Google Gemini
  - `mlx_provider.py` — Local MLX models (Apple Silicon)
  - `ollama_provider.py` — Local Ollama server
- **TUI REPL** (`tui/repl.py`) — Interactive terminal interface

### Workflow

1. Surge receives a build request
2. Planning wave — dispatched to all providers simultaneously
3. Best plan is selected, decomposed into tasks
4. Execution waves — tasks dispatched in parallel
5. Results are collected and integrated
6. Cost tracking ensures budget compliance

## Provider Configuration

```yaml
providers:
  deepseek:
    api_key: "YOUR_KEY"
    model: "deepseek-chat"
    endpoint: "https://api.deepseek.com/v1"
    priority: 1

  anthropic:
    api_key: "YOUR_KEY"
    model: "claude-sonnet-4-20250514"
    endpoint: "https://api.anthropic.com/v1"
    priority: 2

  local_mlx:
    type: "local"
    path: "./models/surge-q4.gguf"
    priority: 0  # Always try local first
```

## Cost Tracking

Surge tracks every API call and enforces budget limits:

```python
# Automatic cost tracking
tracker = CostTracker(budget_limit=10.0, alert_threshold=0.8)
tracker.record_call("deepseek", "deepseek-chat", 1000, 500, 0.01)

if tracker.is_near_budget():
    logger.warning("Approaching budget limit!")
```

## TUI Interface

Launch the interactive TUI:

```bash
python -c "from tui.repl import SurgeREPL; SurgeREPL().cmdloop()"
```

Commands:
- `start <description>` — Start a new build
- `status` — Show build status
- `providers` — List provider health
- `cost` — Show cost summary
- `quit` — Exit

## Logs

All logs are written to `./logs/`. Check `logs/surge_*.log` for detailed execution traces.

## License

MIT
