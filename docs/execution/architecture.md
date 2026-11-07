# RepoGuard-Eval Execution Architecture

## 1. Purpose

This document describes the execution architecture for validating and evaluating AI-generated repository patches.

The execution infrastructure is designed to isolate untrusted repository content from the trusted evaluation engine and provide reproducible, evidence-based execution results.

## 2. Trust Boundaries

### Trusted Components

- Evaluation Engine
- Execution infrastructure and policy configuration
- Workspace and fixture managers
- Snapshot and patch management components
- Docker process and runtime managers
- Trusted, allowlisted Docker images

### Untrusted Inputs

- Repository fixtures
- AI-generated patches
- Build scripts and test scripts
- Repository configuration files
- Dependency metadata
- Runtime process output

Untrusted repository code must not be executed directly by the host Python process.

## 3. Implemented Components

### 3.1 Workspace Manager

`WorkspaceManager` provides isolated per-job workspace directories.

Responsibilities:
- Create unique workspace directories using UUID job identifiers.
- Validate workspace identity and managed-root containment.
- Reject symbolic links and junctions in protected workspace paths.
- Clean up individual workspaces.
- Convert filesystem failures into `ExecutionError`.

### 3.2 Fixture Manager

`FixtureManager` prepares repository fixtures inside workspaces.

Responsibilities:
- Validate fixture source directories.
- Validate destination names.
- Reject overlapping source and destination paths.
- Reject symbolic links, junctions, and unsupported special files.
- Copy directory and regular-file contents.
- Remove partial destinations when copying fails.

### 3.3 Repository Snapshot Manager

`SnapshotManager` creates deterministic repository snapshots.

Responsibilities:
- Record repository file and directory entries.
- Sort entries deterministically.
- Calculate SHA-256 hashes and file sizes.
- Reject symbolic links, junctions, and unsupported special files.
- Verify repository state against an existing snapshot.

Snapshots are currently maintained in memory; persistent manifest storage is not implemented.

### 3.4 Patch Model and Validator

The patch model represents incoming unified diffs.

`PatchValidator`:
- Validates patch type, content, encoding, and size.
- Enforces file-count limits.
- Parses unified diff headers and hunks.
- Rejects unsupported Git extended headers and binary patches.
- Rejects unsafe paths, traversal, duplicate targets, and invalid hunks.
- Checks target paths and existing symlink or junction components.
- Performs validation without modifying the repository.

### 3.5 Patch Applier

`PatchApplier` applies validated patches using Git in a staging repository.

Workflow:
1. Validate the workspace and patch.
2. Create a staging copy of the repository.
3. Run `git apply --check`.
4. Apply the patch in staging.
5. Create a post-application snapshot.
6. Verify that changes are limited to permitted patch targets.
7. Verify that the original repository remains unchanged.
8. Promote staging into the repository path.
9. Attempt backup cleanup.

The promotion process uses filesystem renames and rollback for caught exceptions. It is not guaranteed to be crash-atomic.

### 3.6 Docker Process Manager

`DockerProcessManager` wraps Docker CLI subprocess execution.

Responsibilities:
- Execute Docker commands using argument arrays.
- Use `shell=False`.
- Disable interactive standard input.
- Capture standard output and standard error.
- Apply subprocess timeouts.
- Convert process failures into `ExecutionError`.
- Return structured command results.

### 3.7 Docker Runtime Manager

`DockerRuntimeManager` manages per-job Docker resources.

Implemented capabilities:
- Trusted-image allowlist.
- Per-job Docker-managed volumes.
- Per-job containers.
- Container start, inspection, stop, and cleanup operations.
- Runtime resource configuration.

Container security configuration includes:
- `--network none`
- `--read-only`
- `--cap-drop ALL`
- `--security-opt no-new-privileges`
- Memory limit
- CPU limit
- PID limit
- Restricted temporary filesystem
- Dedicated workspace volume
- No host repository bind mount

### 3.8 Docker Volume Transfer

`DockerVolumeTransfer` transfers repository data between host workspaces and Docker containers using `docker cp`.

Responsibilities:
- Validate runtime and workspace inputs.
- Validate source and destination names.
- Reject symbolic links, junctions, and unsupported special files.
- Transfer repository fixtures into containers.
- Retrieve execution output from containers.
- Remove partial output when transfer validation fails.

An actual Docker integration test verified repository upload, container-side file creation, result download, and output content.

## 4. Target Components Not Yet Implemented

The following components remain future work:

- Command Executor for controlled commands inside containers.
- Go execution runner.
- Python execution runner.
- C++ execution runner.
- Bounded output collection and truncation metadata.
- Structured execution result schema.
- Full execution orchestration.
- Comprehensive cleanup coordination across all failure paths.
- End-to-end execution workflow from task input to final evaluation result.

## 5. Target Execution Flow

1. Receive a validated execution request.
2. Create a unique job identifier.
3. Create an isolated workspace.
4. Prepare the repository fixture.
5. Create a baseline repository snapshot.
6. Validate the AI-generated patch.
7. Apply the patch in staging.
8. Verify the resulting repository state.
9. Create a restricted Docker runtime.
10. Transfer the prepared repository into the container.
11. Execute a fixed language runner profile.
12. Collect bounded execution output and metadata.
13. Clean up container, volume, and workspace.
14. Return a structured execution result.

Steps involving command execution, language runners, structured result collection, and complete orchestration are not yet implemented.

## 6. Security Considerations and Limitations

- Repository commands must never be executed directly on the host.
- Docker commands must use argument arrays and `shell=False`.
- Repository input must not be interpolated into shell commands.
- Containers must not receive the Docker socket.
- Host repositories must not be mounted directly into containers.
- Runner images must be explicitly allowlisted.
- Docker resource limits must be configured for untrusted workloads.
- Filesystem validation is subject to potential time-of-check/time-of-use races.
- Docker container isolation is not an absolute security boundary.
- Patch promotion uses rollback for caught failures but is not crash-atomic.
- Runtime ownership verification and cleanup idempotency require additional hardening.

A stronger isolation backend such as gVisor or microVMs may be considered for hostile multi-tenant workloads.

## 7. Current Implementation Status

Phase 3 currently provides:

- Workspace lifecycle management.
- Fixture validation and copying.
- Repository snapshots and verification.
- Unified diff validation.
- Staged patch application and post-application verification.
- Docker CLI process management.
- Docker runtime and resource configuration.
- Docker-managed workspace volumes.
- Host-to-container and container-to-host transfer.

Verification status:

- Execution unit tests: 184 passed, 5 skipped, 0 failed.
- Docker transfer integration: passed.
- Docker integration verified repository upload, container-side execution, result download, and output content.

The five skipped unit tests are platform-related limitations on Windows, involving symbolic links, junction-related behavior, or FIFO support.

Phase 3 is intentionally being paused before command execution and language runner implementation so development can prioritize benchmark task engineering and the core evaluation workflow.
