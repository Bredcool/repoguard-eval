# Benchmark Task Validation

## Purpose

Every benchmark task must demonstrate that its reference implementation
passes the evaluator test suite while its defective baseline is detected.

## Validation Requirements

1. The defective baseline must reproduce the intended defect.
2. The reference patch must apply cleanly to a fresh repository copy.
3. The reference implementation must pass all applicable tests.
4. The defective baseline must fail tests that detect the intended defect.
5. Hidden tests must remain outside the agent-visible repository.
6. Regression tests must verify expected behavior remains intact.
7. Adversarial tests must cover failure paths and incorrect operation ordering.

## Validation Workflow

1. Copy the defective repository into a temporary workspace.
2. Apply the reference patch to a separate temporary workspace.
3. Inject hidden, regression, and adversarial tests into each workspace.
4. Run the same test suite against both implementations.
5. Record test counts and outcomes in the task validation report.

## RG-GO-001 Results

| Test category | Count |
|---|---:|
| Visible | 2 |
| Hidden | 5 |
| Regression | 2 |
| Adversarial | 2 |
| Total | 11 |

Reference implementation: 11 passed, 0 failed.

Defective baseline: 4 passed, 7 failed.

## Limitations

RG-GO-001 currently uses an in-memory transaction implementation.
It does not establish correctness against a production database.

Difficulty is an initial design classification and requires empirical
calibration across multiple agent runs.
