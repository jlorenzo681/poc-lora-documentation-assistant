# Alternatives to Make for Script Management

While `make` is a classic tool, there are modern alternatives better suited for task running and script management.

## 1. Just (Recommended)

`just` is a handy command runner that saves and runs project-specific commands. It's often preferred over `make` for non-build tasks because it preserves arguments, has better error handling, and uses a simplified syntax.

### Justfile Example
Create a `justfile` in your project root:

```just
# List available commands
default:
    @just --list

# Install dependencies
install:
    uv sync

# Build container
build:
    ./scripts/build.sh

# Deploy application
deploy:
    ./scripts/deploy.sh

# Run locally
run:
    streamlit run app.py
```

### Why switch?
- **No .PHONY**: You don't need to declare failing targets.
- **Argument Passing**: Easily pass arguments to commands (e.g., `just logs -f`).
- **Shell Agnostic**: Works consistently across shells.
- **Better Errors**: Clearer error messages.

## 2. Poe the Poet (Python-specific)

Since this is a Python project using `pyproject.toml`, `poethepoet` is a great native option. You define tasks directly in `pyproject.toml`.

### pyproject.toml configuration

```toml
[tool.poe.tasks]
deploy = "./scripts/deploy.sh"
build = "./scripts/build.sh"
run = "streamlit run app.py"
test = "pytest"
```

### Usage
```bash
poe deploy
poe run
```

## 3. Task (Go-Task)

`task` is a task runner / build tool that aims to be simpler and easier to use than GNU Make. It uses a YAML schema (`Taskfile.yml`).

```yaml
version: '3'

tasks:
  deploy:
    desc: Deploy the application
    cmds:
      - ./scripts/deploy.sh
```

## Summary
For this project:
- If you prefer a **standalone tool** like Make but better: **Use Just**.
- If you want to keep everything in **pyproject.toml**: **Use Poe**.
