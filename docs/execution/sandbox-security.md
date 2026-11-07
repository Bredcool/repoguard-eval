# RepoGuard-Eval Sandbox Security

## 1. Purpose

This document defines the security requirements and currently implemented controls for executing untrusted repository content during AI-agent evaluation.

The primary objective is to prevent repository code and AI-generated patches from gaining unrestricted access to the host environment.

## 2. Threat Model

The system treats the following as untrusted:

- Repository source code.
- AI-generated patches.
- Build and test scripts.
- Project configuration files.
- Dependency metadata.
- Runtime output.
- Files created by repository processes.

Potential threats include:

- Path traversal.
- Symlink and junction escapes.
- Malformed or oversized patches.
- Unauthorized filesystem modifications.
- Host command execution.
- Resource exhaustion.
- Network access from untrusted code.
- Container or workspace cleanup failures.
- Attempts to interfere with other execution jobs.

## 3. Workspace Isolation

Implemented controls:

- Each workspace receives a unique UUID-based directory.
- Workspace identity is validated before filesystem operations.
- Workspace paths must remain inside the managed root.
- Workspace root and workspace paths reject symbolic links and junctions.
- Cleanup targets only the validated job workspace.

Limitations:

- Filesystem checks can be subject to time-of-check/time-of-use races.
- Stronger operating-system-level isolation is not currently implemented.

## 4. Fixture Safety

Implemented controls:

- Fixture sources must be existing directories.
- Destination names follow a restricted character pattern.
- Source and destination paths must not overlap.
- Symbolic links and junctions are rejected.
- Unsupported special files are rejected.
- Partial copies are removed when copying fails.

## 5. Snapshot Integrity

Implemented controls:

- Repository entries are enumerated deterministically.
- Regular files are hashed using SHA-256.
- File sizes and entry types are recorded.
- Symbolic links, junctions, and unsupported special files are rejected.
- Snapshot verification compares repository state with the recorded manifest.

Snapshots are currently in-memory objects and are not persisted as signed or immutable manifests.

## 6. Patch Validation

Implemented controls:

- Patch content must be valid and non-empty.
- Patch size is limited to 1 MiB.
- Patch file count is limited to 100.
- Unified diff structure and hunk counts are validated.
- Git extended headers and binary patches are rejected.
- Absolute paths, traversal, drive paths, backslashes, and unsafe path forms are rejected.
- Duplicate targets are rejected.
- Existing symlink and junction path components are checked.
- Validation does not modify repository contents.

Filesystem path validation remains subject to TOCTOU limitations.

## 7. Patch Application Safety

Implemented controls:

- Patches are validated before application.
- Git applies patches in a staging copy.
- `git apply --check` runs before patch application.
- Post-application snapshots are created.
- Changes are checked against the validated patch target set.
- The original repository is verified before promotion.
- Backup restoration is attempted if promotion fails with a caught exception.

Limitations:

- Two filesystem renames are not crash-atomic.
- A process or machine crash during promotion may require manual recovery.
- Filesystem race conditions are not fully eliminated.

## 8. Docker Isolation

Implemented controls in `DockerRuntimeManager`:

- Trusted Docker image allowlist.
- Dedicated container per job.
- Dedicated Docker-managed volume per job.
- Network disabled using `--network none`.
- Read-only container root filesystem.
- Linux capabilities dropped using `--cap-drop ALL`.
- `no-new-privileges` security option.
- Configurable memory limit.
- Configurable CPU limit.
- Configurable PID limit.
- Restricted temporary filesystem.
- Dedicated workspace mount.
- No host repository bind mount.
- No Docker socket mount.

Docker image versions must be controlled and allowlisted.

Docker container isolation is defense in depth, not an absolute security guarantee.

## 9. Docker Process Safety

Implemented controls in `DockerProcessManager`:

- Subprocess argument arrays.
- `shell=False`.
- Standard input disabled.
- Standard output and standard error captured.
- Configurable subprocess timeout.
- Process failures converted into execution exceptions.

The manager is currently focused on Docker CLI operations. A dedicated command executor for repository processes inside containers has not yet been implemented.

## 10. Docker Volume Transfer Safety

Implemented controls in `DockerVolumeTransfer`:

- Runtime and workspace input validation.
- Restricted source and destination names.
- Source path containment checks.
- Rejection of symbolic links, junctions, and unsupported special files.
- Host-to-container and container-to-host transfer using Docker CLI.
- Validation of retrieved directory contents.
- Partial destination cleanup on transfer failure.

Runtime ownership verification and cleanup idempotency need further hardening.

## 11. Resource and Output Controls

Currently implemented at Docker runtime creation:

- Memory limit.
- CPU limit.
- PID limit.
- Restricted temporary filesystem.

Not yet implemented:

- Per-command execution timeout inside the container.
- Bounded stdout and stderr collection.
- Output truncation metadata.
- Language-specific build and test process controls.
- Full resource-usage reporting.

## 12. Remaining Security Work

Before treating the execution sandbox as complete, the following work remains:

1. Strengthen runtime ownership verification against Docker inspect metadata.
2. Make container and volume cleanup robust and idempotent.
3. Implement a controlled command executor.
4. Enforce command-level timeouts.
5. Implement bounded output collection.
6. Add Go, Python, and C++ runner profiles.
7. Add integration tests for failure and cleanup paths.
8. Review filesystem race conditions and isolation assumptions.

## 13. Current Verification

Latest Phase 3 verification:

- 184 execution unit tests passed.
- 5 tests skipped due to Windows platform limitations.
- 0 test failures.
- Actual Docker transfer integration passed.

The current implementation provides meaningful workspace, patch, and Docker isolation controls, but it is not yet a complete hardened sandbox for arbitrary hostile workloads.
