# RepoGuard-Eval Benchmarks

Version: 1.0.0

## Purpose

A reproducible benchmark suite for evaluating AI coding agents
on realistic repository-level software defects.

## Languages

- Go
- Python
- C++

## Categories

- Transaction Integrity
- Concurrency and Race Conditions
- API and State Management
- Error Handling
- Async Execution
- Input Validation
- Resource Management
- Memory Safety
- Ownership and Object Lifetime
- Undefined Behavior

## Task Structure

Each public task contains:

- task.json
- README.md
- repository/
- visible/

Evaluator-private materials are maintained separately:

- Reference patches
- Expected behavior
- Hidden tests
- Regression tests

## Security

Private benchmark materials must never be included in
the agent-visible repository package.

The evaluator must construct separate execution inputs
for agent execution and private verification.

## Versioning

Semantic Versioning:

- PATCH: non-functional corrections
- MINOR: backward-compatible additions
- MAJOR: breaking evaluation contract changes

## Current Benchmark Tasks

| Task ID | Language | Category | Difficulty | Status |
|---|---|---|---|---|
| RG-GO-001 | Go | Transaction Integrity | Medium | Development |

### RG-GO-001: Transaction Atomicity Failure

Tests transaction lifecycle correctness in an order service.

The intended defect commits a transaction before inventory reservation,
causing partial persistence and operations on a closed transaction.

Validation:

- Reference: 11/11 passed.
- Defective baseline: 7/11 failed.
- Test categories: visible, hidden, regression, adversarial.

The current implementation uses an in-memory transaction model.
Production database integration and empirical difficulty calibration remain
future validation work.
