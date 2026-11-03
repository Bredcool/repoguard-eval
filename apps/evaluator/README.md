
# RepoGuard-Eval — Python Core

Independent Python evaluation framework for RepoGuard-Eval.

The Python core provides task definition loading and validation, experiment management, application configuration, structured logging, and a command-line interface.

## Requirements

- Python 3.13.x
- pip
- Git

The project currently targets Python 3.13 only.

## Project Structure

```text
apps/evaluator/
├── .env.example
├── .python-version
├── pyproject.toml
├── README.md
├── examples/
│   └── tasks/
│       └── example_task.json
├── src/
│   └── repoguard_eval/
│       ├── __init__.py
│       ├── __main__.py
│       ├── cli.py
│       ├── config/
│       ├── exceptions/
│       ├── experiments/
│       ├── logging/
│       ├── models/
│       └── tasks/
└── tests/
    ├── conftest.py
    ├── fixtures/
    └── unit/
```

The package follows the Python `src` layout to separate application source code from tests and development files.

## Installation

Run these commands from the `apps/evaluator` directory.

### 1. Create a virtual environment

```bash
python -m venv .venv
```

### 2. Activate the environment

Windows Git Bash:

```bash
source .venv/Scripts/activate
```

Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

### 3. Install the package

Install the package in editable mode with development dependencies:

```bash
python -m pip install -e ".[dev]"
```

### 4. Verify installation

```bash
python --version
python -m pip check
repoguard --help
```

## Configuration

Application settings are managed using Pydantic Settings.

Environment variables use the `RG_` prefix.

| Variable | Description |
| --- | --- |
| `RG_APP_NAME` | Application name |
| `RG_APP_VERSION` | Application version |
| `RG_ENVIRONMENT` | Runtime environment |
| `RG_DEBUG` | Debug mode |
| `RG_LOG_LEVEL` | Logging level |
| `RG_DATA_DIR` | Application data directory |
| `RG_TASKS_DIR` | Task definitions directory |
| `RG_EXPERIMENTS_DIR` | Experiment storage directory |
| `RG_CONFIG_DIR` | Configuration directory |

Supported environments:

- `development`
- `testing`
- `production`

Supported log levels:

- `DEBUG`
- `INFO`
- `WARNING`
- `ERROR`
- `CRITICAL`

Copy `.env.example` to `.env` when local environment customization is needed.

```bash
cp .env.example .env
```

The `.env` file is excluded from version control.

## CLI Usage

The package provides the `repoguard` command.

### Display help

```bash
repoguard --help
```

### Validate a task definition

```bash
repoguard task validate examples/tasks/example_task.json
```

The command loads the JSON task definition, validates its schema, and reports the validation result.

### Create an experiment

```bash
repoguard experiment create --task-id example-task
```

Create an experiment with a custom name:

```bash
repoguard experiment create \
  --task-id example-task \
  --name "Baseline Evaluation"
```

Experiment metadata is stored as JSON in the configured experiments directory.

### Run the CLI as a Python module

```bash
python -m repoguard_eval --help
```

## Development

### Run all unit tests

```bash
python -m pytest -v
```

### Run tests with coverage

```bash
python -m pytest \
  --cov=repoguard_eval \
  --cov-report=term-missing \
  -v
```

### Check dependencies

```bash
python -m pip check
```

## Core Components

| Component | Responsibility |
| --- | --- |
| `config/` | Application settings and configuration |
| `exceptions/` | Centralized application exceptions |
| `experiments/` | Experiment creation, persistence, and retrieval |
| `logging/` | Application logging and JSON formatting |
| `models/` | Pydantic domain models and enumerations |
| `tasks/` | Task loading and validation |
| `cli.py` | Typer command-line interface |
| `__main__.py` | Python module entry point |

## Testing Status

Latest verified results:

- Unit tests: 61 passed
- Statement coverage: 100%
- Dependency check: no broken requirements

These results represent the current development verification and should be updated when the test suite changes.

## Development Status

**Phase 2 — Python Core Foundation**

Implemented:

- Python package foundation
- Application configuration
- Pydantic task and experiment models
- Task loader and validator
- Experiment management
- CLI commands
- Structured logging
- Centralized exception handling
- Unit tests and coverage verification
