# RepoGuard-Eval — Project Roadmap

**Tagline:** Evidence over Claims. Execution over Assumptions.

## Project Overview

RepoGuard-Eval is an evidence-based benchmark platform for evaluating AI agents on repository debugging tasks.

The project focuses on reproducible execution, secure repository isolation, benchmark quality, objective evaluation, and measurable agent performance.

## Phase Progress

| Phase | Name | Status |
|---|---|---|
| 0 | Project Planning | COMPLETE |
| 1 | Repository & Frontend Foundation | COMPLETE |
| 2 | Python Core Foundation | COMPLETE |
| 3 | Repository Execution & Sandbox | COMPLETE |
| 4 | Benchmark Task Engineering | COMPLETE |
| 5 | Model Provider Integration | NEXT |
| 6 | Evaluation & Scoring Engine | PLANNED |
| 7 | Experiment Orchestration | PLANNED |
| 8 | Reporting & Research Analysis | PLANNED |
| 9 | Dashboard Backend & API Integration | PLANNED |
| 10 | Frontend Dashboard Implementation | PLANNED |
| 11 | System Integration & Quality Assurance | PLANNED |
| 12 | Hackathon Submission & Release | PLANNED |

---

## Completed Phases

### Phase 0 — Project Planning

Established project objectives, scope, architecture direction, technology stack, and implementation roadmap.

### Phase 1 — Repository & Frontend Foundation

Established the monorepo, repository structure, and frontend foundation.

### Phase 2 — Python Core Foundation

Implemented the initial Python evaluator foundation, including CLI structure, configuration, task models, loading, validation, and core utilities.

### Phase 3 — Repository Execution & Sandbox

Implemented the repository execution foundation:

- Workspace management and isolation.
- Fixture copying and validation.
- Repository snapshots.
- Patch validation and application.
- Docker process and runtime integration.
- Execution lifecycle and sandbox security.

Documentation:
- `docs/execution/architecture.md`
- `docs/execution/execution-lifecycle.md`
- `docs/execution/sandbox-security.md`

### Phase 4 — Benchmark Task Engineering

**Status: COMPLETE**

Implemented the benchmark registry, task loader, benchmark metadata validation, and agent-visible workspace preparation.

Completed work:

- Benchmark manifest and registry.
- Strict benchmark metadata validation.
- Task ID and directory validation.
- Repository fixture path validation.
- Private benchmark directory protection.
- Agent workspace isolation.
- Partial workspace cleanup on copy failure.
- Benchmark task documentation and validation report.
- RG-GO-001 transaction-integrity benchmark.

#### Phase 4 Validation Results

| Validation | Result |
|---|---:|
| Benchmark unit tests | 16 passed |
| Full evaluator test suite | 261 passed |
| Platform-dependent skipped tests | 5 skipped |
| Integration smoke test | PASSED |
| Baseline validation | 4 passed, 7 failed |
| Reference patch application | PASSED |
| Reference validation | 11 passed, 0 failed |

The baseline failed as expected, demonstrating that the benchmark detects the intended defect. The reference implementation passed all 11 tests.

Five evaluator tests were skipped because the Windows environment does not support the required symbolic link or FIFO operations under the current permissions/platform.

Benchmark documentation:
- `benchmarks/README.md`
- `benchmarks/docs/task-validation.md`
- `benchmarks/docs/difficulty-model.md`

**Phase 4 acceptance criteria: PASSED.**

---

## Upcoming Phases

### Phase 5 — Model Provider Integration

**Status: NEXT**

Integrate external AI model providers into the evaluator so agents can receive benchmark tasks and repository context, investigate defects, and return diagnoses and code patches.

Planned scope:

- Provider abstraction and adapter architecture.
- Model and provider configuration.
- Prompt templates and repository context construction.
- Request and response normalization.
- Diagnosis extraction.
- Patch extraction.
- Timeout, retry, and rate-limit handling.
- Token and cost usage tracking.
- Raw model response preservation.
- Provider integration tests.

Expected deliverables:

- Provider abstraction.
- At least one working model provider adapter.
- Prompt templates.
- Normalized response parser.
- Diagnosis and patch extraction.
- Usage tracking.
- Raw response storage.
- Integration tests.

Acceptance criteria:

- At least one provider can successfully receive a benchmark task and return a response.
- Model ID and provider configuration are explicit.
- Responses can be normalized and relevant patches extracted.
- API errors and timeouts are handled.
- Raw responses are preserved for evaluation and debugging.
- API keys and secrets are not exposed in source code or logs.

### Phase 6 — Evaluation & Scoring Engine

Implement deterministic and rubric-based evaluation, failure classification, evidence assessment, and score calculation.

### Phase 7 — Experiment Orchestration

Implement repeatable benchmark experiments, agent execution orchestration, run management, and experiment metadata.

### Phase 8 — Reporting & Research Analysis

Implement result aggregation, performance analysis, benchmark statistics, and research-oriented reporting.

### Phase 9 — Dashboard Backend & API Integration

Implement backend APIs and connect evaluation results, experiment data, and reporting services.

### Phase 10 — Frontend Dashboard Implementation

Implement the frontend dashboard for benchmark management, experiment monitoring, result inspection, and performance visualization.

### Phase 11 — System Integration & Quality Assurance

Perform end-to-end integration, reliability testing, security verification, regression testing, and system-level quality assurance.

### Phase 12 — Hackathon Submission & Release

Finalize documentation, benchmark artifacts, reproducibility instructions, release preparation, and hackathon submission.

---

## Project Completion Policy

A phase is considered complete only when:

1. Its planned implementation scope is fulfilled.
2. Relevant automated tests pass.
3. Acceptance criteria are verified.
4. Required documentation is updated.
5. No unresolved critical issue blocks the next phase.

Phase completion must be based on implementation and verification evidence, not merely on code being written.
