# RepoGuard-Eval — System Overview

## 1. Project Overview

RepoGuard-Eval is an evidence-based evaluation benchmark for AI-powered Go repository debugging.

The platform is designed to evaluate how effectively AI agents investigate, debug, and resolve issues in Go repositories.

The project emphasizes:

- Evidence-based debugging and evaluation.
- Reproducible benchmark execution.
- Verifiable repository changes.
- Modular evaluation architecture.
- Secure execution of untrusted repositories.

## 2. Architectural Goals

The architecture is intended to support:

1. Modular development across frontend, backend, and evaluation components.
2. Reproducible benchmark execution.
3. Evidence collection and traceability.
4. Independent evaluation of AI-generated repository changes.
5. Secure handling of untrusted source repositories.
6. Future extensibility for additional evaluation capabilities.

## 3. Planned Technology Stack

| Component | Technology | Intended Responsibility |
| --- | --- | --- |
| Frontend | React, TypeScript, Vite | User interface |
| Routing | React Router | Frontend navigation |
| UI State | Redux Toolkit | Client-side application state |
| Server State | TanStack Query | Server data and asynchronous request state |
| Core Backend | Go | Core application API and domain operations |
| Evaluation Engine | Python | Evaluation orchestration and scoring workflows |
| Native Extensions | C++ | Selected performance-sensitive workloads |
| Database | PostgreSQL | Structured persistent data |
| Version Control | Git | Source history and change tracking |

The table describes the intended architecture. Components that have not yet been implemented should not be considered operational.

## 4. High-Level Architecture

The planned system is organized into the following logical areas.

### Frontend

The React application provides the user-facing interface for:

- Repository management.
- Benchmark discovery.
- Evaluation workflows.
- Evaluation result inspection.
- Project documentation.

The current frontend contains the application shell, navigation, placeholder pages, reusable UI components, and state-management foundations.

### Core Backend

The planned Go backend will provide the core application API and domain operations.

It is not yet implemented in the current Phase 1 foundation.

### Evaluation Engine

The planned Python evaluation engine will support benchmark orchestration and evaluation workflows.

It is not yet implemented in the current Phase 1 foundation.

### Native Extensions

C++ is reserved for selected performance-sensitive or specialized workloads.

No C++ extension is currently implemented.

### Data Layer

PostgreSQL is the intended relational database for persistent application data.

Database integration is outside the current Phase 1 implementation.

## 5. Current Implementation Status

| Area | Phase 1 Status |
| --- | --- |
| Monorepo foundation | Implemented |
| React frontend | Implemented |
| TypeScript configuration | Implemented |
| Vite development and production build | Implemented |
| React Router | Implemented |
| Redux Toolkit | Implemented |
| TanStack Query provider | Implemented |
| Application layout | Implemented |
| Reusable UI components | Implemented |
| Placeholder feature pages | Implemented |
| Frontend automated tests | Implemented |
| Go backend | Not implemented |
| Python evaluation engine | Not implemented |
| C++ extensions | Not implemented |
| PostgreSQL integration | Not implemented |
| Repository execution sandbox | Not implemented |

## 6. Repository Structure

repoguard-eval/
├── apps/
│   └── web/                 # React frontend
├── docs/
│   ├── architecture/        # System-level documentation
│   └── frontend/            # Frontend technical documentation
├── .github/
├── .gitignore
├── package.json
└── README.md

See the frontend documentation for the detailed source structure.

## 7. Development Principles

The project follows these principles:

- Evidence over assumptions.
- Reproducibility over unverifiable results.
- Modular architecture over tightly coupled components.
- Explicit implementation status over overstated capabilities.
- Security-conscious handling of untrusted repositories.

## 8. Scope of This Document

```text
This document describes the intended system architecture and the implementation status at the end of Phase 1.

It should be updated when new architectural components are implemented or when technical decisions change.
