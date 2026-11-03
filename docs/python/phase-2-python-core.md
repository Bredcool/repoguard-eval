
# RepoGuard-Eval — Phase 2: Python Core Foundation

**Project:** RepoGuard-Eval
**Phase:** 2
**Status:** Completed
**Python Version:** 3.13.5
**Package Version:** 0.1.0

---

## 1. Objective

Establish an independent Python evaluation package that provides the foundational application infrastructure for RepoGuard-Eval.

The Python core is responsible for:

- Application configuration.
- Domain models and schema validation.
- Task definition loading.
- Experiment management.
- Command-line interaction.
- Structured logging.
- Centralized exception handling.
- Automated unit testing.

The package uses a `src` layout and can be installed independently in editable mode.

## 2. Technology Stack

| Technology | Purpose |
| --- | --- |
| Python 3.13 | Core runtime |
| setuptools | Package build backend |
| Pydantic v2 | Domain models and validation |
| Pydantic Settings | Application configuration |
| Typer | CLI framework |
| pytest | Unit testing |
| pytest-cov | Statement coverage |
| python-dotenv | `.env` configuration support |

## 3. Package Architecture

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
│       │   ├── __init__.py
│       │   ├── app.py
│       │   └── experiment.py
│       ├── exceptions/
│       │   ├── __init__.py
│       │   └── errors.py
│       ├── experiments/
│       │   ├── __init__.py
│       │   ├── experiment.py
│       │   └── metadata.py
│       ├── logging/
│       │   ├── __init__.py
│       │   └── logger.py
│       ├── models/
│       │   ├── __init__.py
│       │   ├── enums.py
│       │   ├── experiment.py
│       │   └── task.py
│       └── tasks/
│           ├── __init__.py
│           ├── loader.py
│           └── validator.py
└── tests/
    ├── conftest.py
    ├── fixtures/
    │   ├── experiments/
    │   └── tasks/
    └── unit/
        ├── test_cli.py
        ├── test_config.py
        ├── test_exceptions.py
        ├── test_experiment.py
        ├── test_experiment_service.py
        ├── test_logging.py
        ├── test_task_loader.py
        ├── test_task_models.py
        └── test_task_validator.py
```

## 4. Implemented Components

### 4.1 Package Foundation

Implemented:

- Python package metadata.
- Editable installation.
- Development dependency group.
- Package discovery through setuptools.
- Console script entry point.
- Python module entry point.

Installation:

```bash
python -m pip install -e ".[dev]"
```

### 4.2 Application Configuration

Module:

`repoguard_eval.config.app`

Implemented:

- Pydantic Settings integration.
- `RG_` environment variable prefix.
- `.env` loading with UTF-8 encoding.
- Environment and log-level validation.
- Application directory configuration.
- Directory initialization.
- Cached settings through `get_settings()`.

### 4.3 Domain Models

Modules:

- `repoguard_eval.models.task`
- `repoguard_eval.models.experiment`
- `repoguard_eval.models.enums`

Implemented task models:

- `TaskMetadata`
- `RepositoryConfig`
- `TaskRequirements`
- `TaskEvaluation`
- `TaskDefinition`

Implemented enumerations:

- `TaskDifficulty`
- `TaskStatus`
- `EvaluationType`
- `ExperimentStatus`

Implemented experiment model:

- `ExperimentDefinition`

Pydantic validation is used to enforce schema constraints and reject invalid data.

### 4.4 Task Loading and Validation

Modules:

- `repoguard_eval.tasks.loader`
- `repoguard_eval.tasks.validator`

Implemented:

- JSON task loading.
- File existence validation.
- File type validation.
- JSON parsing error handling.
- Schema validation.
- Structured task loading exceptions.

### 4.5 Experiment Management

Module:

`repoguard_eval.experiments.experiment`

Implemented:

- Experiment creation.
- UUID-based experiment identifiers.
- Timestamp metadata.
- Experiment metadata.
- JSON serialization.
- Experiment persistence.
- Experiment loading.
- Experiment retrieval by identifier.
- Error handling for invalid or inaccessible experiment files.

### 4.6 Command-Line Interface

Module:

`repoguard_eval.cli`

Framework: Typer.

Implemented commands:

```text
repoguard --help
repoguard task validate <task-file>
repoguard experiment create --task-id <task-id>
```

Also supports:

```bash
python -m repoguard_eval --help
```

### 4.7 Logging

Module:

`repoguard_eval.logging.logger`

Implemented:

- Application logger configuration.
- JSON log formatter.
- Text log formatter.
- Configurable logging levels.
- Exception information in structured logs.
- Named logger retrieval.

### 4.8 Exception Handling

Module:

`repoguard_eval.exceptions.errors`

Implemented exception hierarchy:

```text
RepoGuardError
├── ConfigurationError
├── TaskLoadError
└── ExperimentError
```

Centralized exceptions provide consistent error handling across application components.

## 5. Testing and Quality Assurance

Testing framework: pytest.

Coverage framework: pytest-cov.

Test modules:

| Test module | Responsibility |
| --- | --- |
| `test_cli.py` | CLI commands and entry points |
| `test_config.py` | Application settings |
| `test_exceptions.py` | Exception hierarchy |
| `test_experiment.py` | Experiment domain model |
| `test_experiment_service.py` | Experiment management |
| `test_logging.py` | Logging behavior |
| `test_task_loader.py` | Task loading and error handling |
| `test_task_models.py` | Task model validation |
| `test_task_validator.py` | Task validation |

### Verified Results

Latest full test execution:

```text
61 passed in 0.92s
```

Coverage:

```text
TOTAL    252    0    100%
```

Dependency verification:

```text
No broken requirements found.
```

All executable Python statements included in the coverage report were covered by the test suite.

Note: Statement coverage does not guarantee complete branch coverage or integration correctness.

## 6. Verification Commands

Run from `apps/evaluator` with the virtual environment activated.

```bash
python -m pytest -v
```

```bash
python -m pytest \
  --cov=repoguard_eval \
  --cov-report=term-missing \
  -v
```

```bash
python -m pip check
```

```bash
repoguard --help
```

```bash
python -m repoguard_eval --help
```

## 7. Phase 2 Completion Criteria

| Requirement | Status |
| --- | --- |
| Python environment | Completed |
| Package foundation | Completed |
| Application configuration | Completed |
| Domain models | Completed |
| Task loader and validator | Completed |
| Experiment management | Completed |
| CLI implementation | Completed |
| Logging | Completed |
| Exception handling | Completed |
| Unit testing | Completed |
| Coverage verification | Completed |
| Documentation | Completed |
| Final repository verification | Pending |

## 8. Phase Outcome

Phase 2 establishes the Python core as an independently installable and testable package.

The implementation provides the foundational infrastructure required for subsequent evaluation-engine development.

**Phase 2 status:** Implementation and QA completed. Final repository verification remains pending.
