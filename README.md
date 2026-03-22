# OpenClaw Deterministic Retrieval

> Predictable, debuggable file and memory retrieval for OpenClaw

[![Tests](https://img.shields.io/badge/tests-23%20passing-green)]()
[![Python](https://img.shields.io/badge/python-3.9%2B-blue)]()
[![License](https://img.shields.io/badge/license-MIT-yellow)]()

## Overview

Deterministic Retrieval provides **predictable, path-based file lookup** with optional semantic overlay support. Unlike purely semantic retrieval which can be non-deterministic, this module guarantees exact results for exact paths.

### Why Deterministic Retrieval?

| Semantic Retrieval | Deterministic Retrieval |
|-------------------|------------------------|
| May return similar but wrong files | Returns exactly what you asked for |
| Embedding drift over time | Path-based = immutable |
| Hard to debug "why this result?" | Clear provenance: path → file |
| Non-repeatable | 100% reproducible |

## Installation

```bash
git clone https://github.com/0x-wzw/openclaw-deterministic-retrieval.git
cd openclaw-deterministic-retrieval

# No external dependencies required (stdlib only)
python3 -m pip install -e .  # Optional: install as package
```

## Quick Start

```bash
# Retrieve a specific memory file
openclaw-retrieve --mode deterministic --path memory/2026-03-22.md

# List directory contents
openclaw-retrieve --mode deterministic --path memory/agents

# Search with pattern
openclaw-retrieve --mode hybrid --search --path "memory/*.md"

# JSON output for piping
openclaw-retrieve --mode deterministic --path memory/agents --format json
```

## Modes Explained

### `deterministic` (Default)
Exact path-based lookup. No surprises.

```python
from deterministic_retrieval import DeterministicRetrieval

engine = DeterministicRetrieval(mode="deterministic")
result = engine.retrieve("memory/agents/halloween/config.yaml")
# Returns EXACTLY that file or not-found
```

### `semantic` 
Semantic similarity search (placeholder for embedding integration).

```python
result = engine.retrieve("config for halloween agent")
# Returns files semantically similar to query
```

### `hybrid`
Path-based lookup first, semantic enhancement second.

```python
result = engine.retrieve("memory/agents/halloween")
# Gets exact directory, adds semantic metadata
```

## Mode Comparison

| Feature | Deterministic | Semantic | Hybrid |
|---------|--------------|----------|---------|
| Exact path match | ✅ | ❌ | ✅ |
| Handles typos | ❌ | ✅ | ❌ |
| Reproducible | ✅ | ❌ | ✅ |
| Concept matching | ❌ | ✅ | ✅ |
| Debuggable | ✅ | ❌ | ✅ |
| Speed | ⚡⚡⚡ | ⚡ | ⚡⚡ |

## Python API

```python
from deterministic_retrieval import DeterministicRetrieval, retrieve, retrieve_memory

# Full engine
engine = DeterministicRetrieval(
    base_path="~/.openclaw/workspace",
    mode="hybrid",
    enable_caching=True
)

# Retrieve file
result = engine.retrieve("memory/agents/halloween/SKILL.md")
print(result.content)  # File contents
print(result.exists)   # True/False

# Retrieve directory
result = engine.retrieve("memory/agents")
print(result.content)  # List of files

# Batch retrieval
results = engine.batch_retrieve([
    "memory/2026-03-20.md",
    "memory/2026-03-21.md",
    "memory/2026-03-22.md"
])

# Search with glob
results = engine.search("memory/**/*.md")

# Convenience functions
result = retrieve("memory/test.md", mode="deterministic")
result = retrieve_memory("agents/halloween")  # auto-adds memory/ prefix
```

## Path Resolution

Paths are resolved in order of specificity:

1. **Absolute**: `/etc/hosts` → `/etc/hosts`
2. **Home-relative**: `~/notes.txt` → `/home/user/notes.txt`
3. **Memory-relative**: `memory/agents/halloween` → `~/.openclaw/workspace/memory/agents/halloween`
4. **Workspace-relative**: `skills/weather` → `~/.openclaw/workspace/skills/weather`

## CLI Reference

```
openclaw-retrieve [OPTIONS]

Options:
  -p, --path PATH          Path to retrieve (required)
  -m, --mode MODE          Retrieval mode: deterministic|semantic|hybrid [default: deterministic]
  -b, --base-path PATH     Base path for relative lookups [default: ~/.openclaw/workspace]
  -f, --format FORMAT      Output format: auto|json|raw [default: auto]
  -s, --search             Treat path as glob pattern for search
  -t, --content-type TYPE  Content type hint: text|json|auto [default: auto]
  --no-cache               Disable result caching
  --version                Show version and exit
  -h, --help               Show help message
```

## Episodic Memory Integration

Works with OpenClaw's memory structure:

```
~/.openclaw/workspace/memory/
├── 2026-03-22.md              # Daily notes
├── 2026-03-21.md
├── agents/
│   ├── halloween/             # Agent workspaces
│   │   └── config.yaml
│   └── octoberxin/
└── agent-comm-logs/
    └── 2026-03-22.jsonl       # Communication logs
```

```python
# Access daily notes
result = engine.retrieve("memory/2026-03-22.md")

# Access agent configs
result = engine.retrieve("memory/agents/halloween/config.yaml")

# List agent communication logs
logs = engine.memory_adapter.get_comm_logs("2026-03-22")
```

## Testing

```bash
# Run all tests
python3 test_deterministic.py

# Or with pytest
python3 -m pytest test_deterministic.py -v
```

23 tests covering:
- Path resolution (absolute, relative, home, memory)
- File retrieval (text, JSON, binary)
- Directory listing
- Batch operations
- Search patterns
- Caching
- Mode switching
- Edge cases

## Architecture

```
┌─────────────────────────────────────────┐
│         CLI (cli.py)                    │
│    openclaw-retrieve command            │
└─────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────┐
│   DeterministicRetrieval (Engine)       │
│  ┌─────────────────────────────────┐     │
│  │  Mode: deterministic|semantic|  │    │
│  │        hybrid                     │    │
│  └─────────────────────────────────┘     │
│  ┌─────────────────────────────────┐     │
│  │  Path Resolver                  │    │
│  │  - absolute                     │    │
│  │  - home-relative                │    │
│  │  - memory-relative              │    │
│  │  - base-relative                │    │
│  └─────────────────────────────────┘     │
│  ┌─────────────────────────────────┐     │
│  │  EpisodicMemoryAdapter          │    │
│  │  - daily notes                  │    │
│  │  - agent configs                │    │
│  │  - comm logs                    │    │
│  └─────────────────────────────────┘     │
└─────────────────────────────────────────┘
```

## Use Cases

1. **Debugging**: When you need to know *exactly* which file was retrieved
2. **Reproducibility**: Scripts that must work identically every time
3. **Path traversal**: Walking directory structures deterministically
4. **Memory inspection**: Querying OpenClaw's episodic memory by date/path
5. **Backup/sync**: Reliable file enumeration for operations

## Roadmap

- [ ] Semantic embedding integration (optional backend)
- [ ] Fuzzy path matching for typo tolerance
- [ ] Watch mode for monitoring file changes
- [ ] Integration with OpenClaw agent system

## License

MIT License - See LICENSE file for details

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all 23+ tests pass
5. Submit a pull request

---

**Part of the OpenClaw ecosystem** — Predictable intelligence for autonomous agents.
