# RG-GO-001: Transaction Atomicity Failure

## Problem

The order service has an inconsistent transaction lifecycle.

An order operation performs two business operations:

1. Create an order.
2. Reserve inventory for that order.

Both operations must succeed or fail together.

Currently, the service may persist an order even when inventory reservation fails.

## Your Task

Investigate the transaction handling implementation and fix the underlying defect.

## Expected Behavior

- Order creation and inventory reservation must execute within the same transaction.
- Both operations must commit together.
- Any operation failure must prevent partial persistence.
- Transaction errors must be propagated to the caller.
- Existing public APIs must remain compatible.

## Constraints

- Do not remove business operations.
- Do not bypass transaction handling.
- Do not weaken or modify tests to hide failures.
- Keep the implementation maintainable.

## Verification

Run:

`go test ./...`

All relevant tests must pass.

## Submission

Submit a patch containing only the changes necessary to fix the transaction defect.
