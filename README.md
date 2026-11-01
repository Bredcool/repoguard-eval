
# RepoGuard-Eval

Evidence-based evaluation benchmark for AI-powered Go repository debugging.

## Overview

RepoGuard-Eval is a modular benchmark platform designed to evaluate how effectively AI agents investigate, debug, and resolve issues in Go repositories.

The project emphasizes:

- Evidence-based debugging and evaluation.
- Reproducible benchmark execution.
- Verifiable repository changes.
- Modular evaluation architecture.
- Secure execution of untrusted repositories.

## Project Goals

RepoGuard-Eval aims to provide a structured environment for evaluating AI-powered repository debugging.

The intended platform includes:

- Repository management.
- Benchmark scenarios and test cases.
- AI agent evaluation workflows.
- Evidence collection and result inspection.
- Reproducible evaluation processes.

## Technology Stack

| Component | Technology |
| --- | --- |
| Frontend | React, TypeScript, Vite |
| Routing | React Router |
| UI State | Redux Toolkit, React Redux |
| Server State | TanStack Query |
| Frontend Testing | Vitest, React Testing Library, jsdom |
| Browser Automation Dependency | Playwright |
| Planned Core Backend | Go |
| Planned Evaluation Engine | Python |
| Planned Native Extensions | C++ |
| Planned Database | PostgreSQL |
| Version Control | Git |

Technologies marked as planned are architectural targets and are not necessarily implemented yet.

## Repository Structure

repoguard-eval/
├── apps/
│   └── web/                 # React frontend
├── docs/
│   ├── architecture/        # System architecture
│   └── frontend/            # Frontend technical documentation
├── .github/                 # GitHub configuration
├── .gitignore
├── package.json             # Root workspace configuration
├── package-lock.json
└── README.md

See the source directories under apps/web/src/ for the detailed frontend implementation.
Prerequisites

- Node.js 22+
- npm 10+
- Git
Getting Started

## 1. Install dependencies

npm install

## 2. Start the frontend development server

npm run dev

The Vite development server is configured to use:
<http://127.0.0.1:5173/>

## 3. Run frontend tests

npm test

## 4. Run TypeScript validation

npm run typecheck

## 5. Create a production build

npm run build

## 6. Preview the production build

```text
npm run preview --workspace @repoguard/web

Available Root Scripts
Command Description
npm run dev Start the frontend development server
npm run build Typecheck and build the frontend
npm test Run frontend tests
npm run typecheck Run TypeScript validation

Additional frontend scripts are available in apps/web/package.json.
Documentation
Project documentation is organized as follows:
Document Description
System Overview Project goals and system architecture
Frontend Architecture Frontend structure and component organization
Routing and State Management Routing, Redux Toolkit, and TanStack Query
Design System Styling foundation and reusable components
Frontend Testing Testing strategy and verification results

Phase 1 Status
Phase 1 establishes the repository and frontend foundation.

Completed areas:
- Monorepo foundation.
- React, TypeScript, and Vite setup.
- React Router configuration.
- Redux Toolkit integration.
- TanStack Query provider setup.
- Application layout and navigation.
- Shared design tokens and CSS foundation.
- Reusable UI and feedback components.
- Placeholder feature pages.
- Frontend automated tests.
- Production build verification.
- Technical documentation.
Latest confirmed verification:
Check Result
TypeScript typecheck Passed
Automated test files 15 passed
Automated tests 115 passed
Production build Passed
npm audit 0 vulnerabilities

Current Implementation Scope
The current implementation is a frontend foundation.

The following planned components are not yet implemented:
- Go core backend.
- Python evaluation engine.
- C++ native extensions.
- PostgreSQL integration.
- Repository execution sandbox.
- Backend-connected benchmark and evaluation workflows.
Feature pages currently provide the initial navigation and interface structure.
Development Principles
- Evidence over assumptions.
- Reproducibility over unverifiable results.
- Modular architecture.
- Explicit implementation status.
- Security-conscious repository handling.
Project Status
Under active development.

See the docs/ directory for architecture and implementation details.
