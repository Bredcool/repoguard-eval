# RepoGuard-Eval Execution Lifecycle

## 1. Purpose

This document defines the intended lifecycle of a RepoGuard-Eval execution job and distinguishes implemented lifecycle operations from planned orchestration behavior.

## 2. Target Lifecycle States

An execution job is expected to move through these conceptual stages:

1. CREATED
2. WORKSPACE_PREPARED
3. FIXTURE_READY
4. SNAPSHOT_CREATED
5. PATCH_VALIDATED
6. PATCH_APPLIED
7. CONTAINER_CREATED
8. WORKSPACE_TRANSFERRED
9. EXECUTING
10. RESULT_COLLECTED
11. CLEANING
12. COMPLETED

A job may terminate early with:

- FAILED
- TIMED_OUT
- RESOURCE_EXCEEDED
- CANCELLED
- INFRA_ERROR

These are target lifecycle states. A complete state machine and orchestration service are not yet implemented.

## 3. Implemented Lifecycle Operations

### 3.1 Workspace Preparation

Implemented by `WorkspaceManager`.

1. Generate a unique job UUID.
2. Create a dedicated workspace directory.
3. Validate workspace identity and managed-root containment.
4. Clean up the workspace when requested.

### 3.2 Fixture Preparation

Implemented by `FixtureManager`.

1. Validate the fixture source.
2. Validate the destination name.
3. Reject overlapping paths.
4. Reject symbolic links, junctions, and unsupported special files.
5. Copy repository contents into the workspace.
6. Remove partial copies if preparation fails.

### 3.3 Repository Snapshot

Implemented by `SnapshotManager`.

1. Validate the workspace and repository path.
2. Enumerate repository entries deterministically.
3. Record file sizes and SHA-256 hashes.
4. Store the snapshot in memory.
5. Verify repository contents against the snapshot when requested.

### 3.4 Patch Validation

Implemented by `PatchValidator`.

1. Validate patch content and encoding.
2. Enforce patch size and file-count limits.
3. Parse unified diff headers and hunks.
4. Validate target paths.
5. Reject unsafe paths and unsupported patch features.
6. Return a validated patch without modifying the repository.

### 3.5 Patch Application

Implemented by `PatchApplier`.

1. Create a staging copy of the repository.
2. Check patch applicability with Git.
3. Apply the patch in staging.
4. Create a post-application snapshot.
5. Verify the allowed change set.
6. Verify the original repository remains unchanged.
7. Promote the staged repository.
8. Attempt backup cleanup and rollback on caught promotion failures.

The promotion operation is not guaranteed to be crash-atomic.

### 3.6 Docker Runtime Preparation

Implemented by `DockerProcessManager` and `DockerRuntimeManager`.

1. Validate the requested trusted image.
2. Create a per-job Docker-managed volume.
3. Create a restricted container.
4. Configure network, filesystem, capabilities, and resource limits.
5. Start and inspect the container.
6. Stop and clean up runtime resources when requested.

### 3.7 Workspace Transfer

Implemented by `DockerVolumeTransfer`.

1. Validate runtime and workspace inputs.
2. Validate the repository source.
3. Copy repository data into the container.
4. Retrieve output from the container.
5. Validate copied output.
6. Remove partial output when transfer fails.

Actual Docker integration verified upload, container-side file creation, download, and content verification.

## 4. Planned Lifecycle Operations

The following operations are not yet implemented:

- Controlled command execution inside containers.
- Per-command timeout enforcement for repository build and test processes.
- Go, Python, and C++ runner profiles.
- Bounded stdout and stderr collection.
- Output truncation indicators.
- Structured execution result generation.
- Full orchestration across all lifecycle stages.
- Unified cleanup handling for every success and failure path.

## 5. Failure Handling Requirements

The complete execution system must:

- Treat execution failures separately from infrastructure failures.
- Record timeout and resource-limit events.
- Preserve stdout and stderr within configured limits.
- Attempt cleanup after failures and timeouts.
- Record cleanup failures as infrastructure diagnostics.
- Never convert an unsuccessful execution into success because cleanup failed.

## 6. Idempotency Requirements

Cleanup operations should be safe to repeat.

Partially created jobs must remain recoverable and removable. Runtime ownership validation and idempotent cleanup require additional hardening before the execution lifecycle is considered complete.

## 7. Verification Status

Latest Phase 3 verification:

- 184 execution unit tests passed.
- 5 tests skipped due to Windows platform limitations.
- 0 test failures.
- Actual Docker transfer integration passed.

Phase 3 is paused after Docker workspace transfer. The target lifecycle above must not be interpreted as a fully implemented execution pipeline.
