# GymAI - AI Development Instructions

> This document defines the engineering standards, architecture, and development workflow for the gym-ai project.
>
> Every AI coding assistant (Codex, ChatGPT, Claude, Gemini, Cursor, etc.) MUST read and follow this document before making any changes to the project.

---

# 1. Project Overview

## Project Name

gym-ai

## Project Type

Production-ready AI-powered fitness coaching platform.

## Primary Goal

Build a scalable web application that helps users achieve their fitness goals through personalized workout planning, workout tracking, progress monitoring, and, in later phases, AI-powered coaching.

## MVP Goal

The first version focuses on building a stable, modular fitness platform.

The MVP includes:

- Authentication
- User Profiles
- Exercise Library
- Workout Planning
- Workout Tracking
- Progress Tracking
- Dashboard

The MVP DOES NOT include AI features.

AI will only be introduced after the core platform is stable.

## Long-Term Vision

gym-ai should evolve into an intelligent fitness coach capable of:

- Understanding user history
- Remembering previous workouts
- Recommending personalized workouts
- Tracking long-term progress
- Providing conversational coaching
- Integrating future AI capabilities without requiring major architectural changes

All architectural decisions should support this long-term vision.

---

# 2. Development Philosophy

This project follows a professional software engineering workflow.

The objective is not only to build GymAI but also to maintain a clean, scalable, production-quality codebase that can evolve over time.

Every implementation decision must prioritize maintainability, readability, scalability, and simplicity.

---

## Core Principles

### 1. Documentation First

No implementation should begin before the architecture and requirements are clearly documented.

Whenever there is uncertainty, documentation takes priority over writing code.

---

### 2. Architecture Before Code

Never start implementing features before understanding:

- Why the feature exists.
- Where it belongs.
- How it communicates with other modules.
- How it fits into the overall architecture.

---

### 3. Build the MVP First

Always build the smallest complete solution.

Avoid implementing future ideas during the MVP.

Examples of features that are intentionally postponed:

- AI Coach
- Voice Assistant
- Nutrition Planning
- Trainer Marketplace
- Community Features
- Wearable Device Integration

These features will be introduced in future phases.

---

### 4. Simplicity Over Complexity

Prefer the simplest solution that satisfies the current business requirements.

Do not introduce unnecessary abstractions, design patterns, dependencies, or optimizations unless there is a clear benefit.

---

### 5. Modular Design

Every feature should be developed as an independent module.

Each module owns its own:

- API routes
- Business logic
- Schemas
- Models
- Repository layer
- Validation

Modules should communicate through clearly defined interfaces rather than directly depending on each other's internal implementation.

---

### 6. Single Responsibility Principle

Every class, function, and module should have one clear responsibility.

Avoid creating large files that perform multiple unrelated tasks.

---

### 7. Incremental Development

Development should proceed in small, reviewable steps.

Complete one feature before starting another.

Avoid partially implemented modules.

---

### 8. AI is an Enhancement

The application must function correctly without AI.

Artificial Intelligence should improve the user experience rather than replace core business logic.

The system architecture should allow AI to be added later without requiring major restructuring.

---

### 9. Explain Before Implementing

Whenever generating code, explain:

- Why the code is needed.
- Why it belongs in that location.
- Which design decision it supports.
- How it interacts with the rest of the system.

The goal is education as well as implementation.

---

### 10. Think Like a Senior Engineer

Every implementation should be evaluated using the following questions:

- Is this maintainable?
- Is this scalable?
- Is this readable?
- Is this modular?
- Is this necessary?
- Can another developer understand this easily?
- Will this decision still make sense one year from now?

If the answer is "No" to any of these questions, reconsider the implementation.

---

# 3. Technology Stack

This section documents the approved technology stack for GymAI. Each technology has been selected to ensure high performance, maintainability, type safety, and architectural scalability.

---

## 3.1 Frontend Stack

### 1. Next.js (App Router)
- **Role**: Primary Frontend Framework.
- **Rationale**: Next.js provides server-side rendering (SSR), static site generation (SSG), dynamic routing via the App Router, and built-in optimization for performance and SEO. The App Router architecture aligns cleanly with component layout isolation and modern React Server Components (RSC).

### 2. TypeScript
- **Role**: Programming Language.
- **Rationale**: Ensures strict type safety across the application, reduces runtime errors, and improves developer velocity with clear interfaces and self-documenting code models shared across components.

### 3. Tailwind CSS
- **Role**: Utility-First Styling Framework.
- **Rationale**: Enables rapid UI development with consistency across components, zero runtime CSS overhead, and full customization without leaving the JSX/TSX environment.

### 4. Shadcn/UI
- **Role**: UI Component Library.
- **Rationale**: Provides accessible, fully customizable, unstyled core components built on Radix UI primitives. It allows complete ownership of component code without third-party styling constraints.

### 5. React Hook Form
- **Role**: Form Management.
- **Rationale**: Delivers high-performance form state management with minimal re-renders, seamlessly handling complex form validation flows required for fitness and user profile tracking.

### 6. Zod
- **Role**: Schema Validation.
- **Rationale**: Provides TypeScript-first schema validation for forms, data fetching, and API payload parsing. Works natively with React Hook Form to guarantee runtime type safety.

### 7. Axios
- **Role**: HTTP Client.
- **Rationale**: Offers a robust interface for HTTP requests with support for request/response interceptors, automatic JSON data transformation, and centralized error handling for backend communication.

---

## 3.2 Backend Stack

### 1. FastAPI
- **Role**: Primary Backend Web Framework.
- **Rationale**: A high-performance Python framework leveraging asynchronous processing (async/await), automatic OpenAPI documentation generation, and native integration with Pydantic for request validation.

### 2. Python
- **Role**: Backend Programming Language.
- **Rationale**: Provides an extensive ecosystem, high readability, and effortless compatibility with future AI and machine learning integrations planned for subsequent project phases.

### 3. SQLAlchemy
- **Role**: Object-Relational Mapper (ORM).
- **Rationale**: Serves as the industry-standard database abstraction layer for Python. Provides clean domain model mapping, asynchronous database access, complex query building, and strong transaction safety.

### 4. Alembic
- **Role**: Database Migration Tool.
- **Rationale**: Designed specifically for SQLAlchemy to track schema evolution deterministically, enabling safe, reproducible database migrations across all deployment environments.

### 5. Pydantic
- **Role**: Data Validation & Serialization.
- **Rationale**: Enforces strict data structures, environment configuration parsing, and domain request/response serialization with high runtime performance.

### 6. JSON Web Tokens (JWT)
- **Role**: Authentication Mechanism.
- **Rationale**: Provides stateless, scalable session management and authorization across distributed backend services and REST API endpoints.

### 7. bcrypt
- **Role**: Password Hashing.
- **Rationale**: Industry-standard cryptographic hashing algorithm used to securely store and protect user passwords against brute-force vulnerabilities.

---

## 3.3 Database & API Architecture

### 1. PostgreSQL
- **Role**: Relational Database Management System (RDBMS).
- **Rationale**: An enterprise-grade, highly reliable relational database providing ACID compliance, complex data querying, JSON store capabilities, and seamless scalability for workout history and user data.

### 2. REST (Representational State Transfer)
- **Role**: API Architectural Style.
- **Rationale**: Establishes standardized, stateless HTTP endpoints between Next.js and FastAPI, ensuring clean decoupling between presentation layers and backend services.

---

## 3.4 Infrastructure & Tools

### 1. Docker & Docker Compose
- **Role**: Containerization & Local Orchestration.
- **Rationale**: Guarantees identical execution environments between local development and production. Docker Compose orchestrates multi-container setups (Frontend, Backend, PostgreSQL) effortlessly.

### 2. Git & GitHub
- **Role**: Version Control & Collaboration.
- **Rationale**: Facilitates structured branch workflows, code reviews, audit trails, and automated CI/CD pipeline integration.

---

## 3.5 AI Integration Strategy

### AI Capabilities (Post-MVP Phase)
- **Role**: Intelligence & Personalization Layer.
- **Rationale**: Artificial Intelligence features (e.g., adaptive coaching, workout recommendations) are explicitly deferred until the core application foundation, database schemas, and workout tracking modules are fully stabilized.

---

# 4. Project Architecture

This section defines the architectural patterns, structural design, and governance rules for GymAI. The application is designed as a **Modular Monolith** adhering strictly to **Clean Architecture** principles on the backend and a **Feature-Based Architecture** on the frontend.

---

## 4.1 Overall Architecture

GymAI is built with a total separation of concerns between the presentation client and the backend server:

- **Modular Monolith**: The backend runs as a unified executable service, but internal functionality is strictly isolated into domain modules.
- **Clean Architecture**: Domain rules and business logic are completely decoupled from frameworks, databases, and external interfaces.
- **REST API**: Communication between client and server occurs exclusively over stateless, versioned REST endpoints over HTTP/S.
- **Decoupled Client & Server**: The Next.js frontend and FastAPI backend operate independently, communicating solely via structured API requests and responses.

---

## 4.2 Backend Architecture (Clean Architecture & Modular Monolith)

The backend code is organized into self-contained business modules (e.g., `auth`, `users`, `exercises`, `workouts`, `progress`, `ai_coach`, `admin`). Each module maintains its own clean boundary containing four distinct layers:

### 1. Layer Responsibilities

#### A. Domain Layer (`domain/`)
- **Responsibility**: Contains core domain entities, value objects, domain events, and pure business validation rules.
- **Rules**: Zero external dependencies. It does not import FastAPI, SQLAlchemy, Pydantic, or any third-party libraries. It represents the pure business domain.

#### B. Application Layer (`application/`)
- **Responsibility**: Implements application use cases, orchestration services, and Data Transfer Objects (DTOs).
- **Rules**: Coordinates workflows between domain entities and repository interfaces. Defines abstract interfaces (contracts) for infrastructure services.

#### C. Infrastructure Layer (`infrastructure/`)
- **Responsibility**: Provides technical implementations of interfaces defined by Domain and Application layers (e.g., SQLAlchemy database repositories, external HTTP clients, cache adapters).
- **Rules**: Handles external framework specifics, ORM models, and database communication.

#### D. Presentation Layer (`presentation/`)
- **Responsibility**: Exposes HTTP REST controllers, FastAPI route handlers, endpoint schemas, and dependency injection wireups.
- **Rules**: Validates incoming HTTP requests, invokes Application Services, and formats outgoing HTTP responses.

---

### 2. Dependency Rule

Dependencies strictly flow **inward** toward the pure Domain logic:

```text
Presentation Layer (FastAPI Routes)
         │
         ▼
Application Layer (Use Cases & DTOs)
         │
         ▼
  Domain Layer (Entities & Pure Rules)
         ▲
         │ (Implements Interfaces)
Infrastructure Layer (SQLAlchemy / Repositories)
```

- **Presentation** depends on **Application**.
- **Application** depends on **Domain**.
- **Infrastructure** depends on **Application** and **Domain** (by implementing repository interfaces).
- **Domain** depends on **NONE**. It is completely isolated and pure.

### 3. Importance of Dependency Direction
- **Framework Independence**: The core business logic is completely decoupled from FastAPI, SQLAlchemy, or any specific database vendor.
- **High Testability**: Domain rules and application use cases can be unit-tested rapidly in total isolation without needing a database connection or spinning up HTTP servers.
- **Long-Term Adaptability**: Databases, third-party services, or web frameworks can be swapped or upgraded without rewriting core business logic.

---

## 4.3 Frontend Architecture (Feature-Based Architecture)

The Next.js frontend follows a scalable **Feature-Based Architecture**, partitioning code by business capabilities rather than arbitrary technical types.

### 1. Directory Responsibilities

- **`app/`**: Next.js App Router root handling layout routing, page definitions, route groups (`(auth)`, `(dashboard)`), and global providers.
- **`features/`**: Houses self-contained domain features (`auth`, `workouts`, `exercises`, `progress`, `ai-coach`, `admin`). Each feature contains its own private components, hooks, API callers, and types.
- **`components/`**: Reusable generic UI components (buttons, dialogs, form controls, navigation bars) shared across the entire application.
- **`hooks/`**: Global reusable React hooks (e.g., `useDebounce`, `useMediaQuery`).
- **`lib/`**: Configuration wrappers for third-party libraries (e.g., Axios client instances, React Query configuration).
- **`services/`**: Global system services and baseline API client interfaces.
- **`types/`**: Shared TypeScript type definitions, common backend DTO contracts, and global interfaces.
- **`styles/`**: Global design system definitions, utility classes, and CSS configurations.

### 2. Reusable vs. Feature-Specific Components

- **Reusable Components (`src/components/`)**: Unaware of specific business domain concepts. They focus purely on UI rendering, accessibility, and presentation (e.g., a generic `Button` or `Modal`).
- **Feature Components (`src/features/<feature>/components/`)**: Bound directly to business domain logic and data structures (e.g., `WorkoutLoggerCard`, `ExerciseFilterBar`, `UserProfileForm`).

---

## 4.4 End-to-End Communication Flow

When a user interacts with GymAI, data flows sequentially through the architecture:

```text
[User Action]
     │
     ▼
[1. Next.js UI Component]
     │ (Triggers event / state change)
     ▼
[2. Feature API Client / Axios]
     │ (Sends JSON HTTP Request over REST)
     ▼
[3. FastAPI Route Handler (Presentation)]
     │ (Parses request payload & validates with Pydantic)
     ▼
[4. Application Service (Application)]
     │ (Orchestrates use-case workflow & enforces rules)
     ▼
[5. Repository Interface -> Implementation (Infrastructure)]
     │ (Executes SQL queries via SQLAlchemy ORM)
     ▼
[6. PostgreSQL Database]
     │ (Persists or retrieves data records)
     ▼
[7. Response Serialization & Return]
     │ (DB Record -> Domain Model -> DTO -> HTTP JSON Response -> React UI update)
     ▼
[User Views Updated UI]
```

### Step Breakdown:
1. **User**: Performs an action on the interface (e.g., clicking "Save Workout").
2. **Next.js UI**: Captures event, validates local state via Zod/React Hook Form, and calls the feature service.
3. **Axios Client**: Formats and executes an asynchronous HTTP request (e.g., `POST /api/v1/workouts`).
4. **FastAPI Endpoint**: Receives the request, checks auth JWT, validates request body schemas, and routes execution.
5. **Application Service**: Executes the business use case, interacts with domain entities, and invokes database repositories.
6. **Repository Layer**: Converts entity state into SQLAlchemy models and executes database operations.
7. **PostgreSQL**: Executes ACID transactions and returns raw query records.
8. **Response Return**: Data flows back up through DTO serialization, returning structured JSON over HTTP to update the Next.js UI.

---

## 4.5 Architectural Scalability: Modular Monolith Rationale

GymAI deliberately selects a **Modular Monolith** pattern over a Microservices architecture for the MVP and early production phases.

### Rationale:
- **Accelerated Velocity**: Avoids complex distributed systems overhead, network latency, and service mesh management during initial development.
- **Simplified Debugging & Tracing**: Single unified runtime process enables straightforward local debugging, centralized logging, and transactional consistency.
- **Lower Infrastructure Overhead**: Drastically reduces deployment complexity and server hosting costs compared to running multiple microservice clusters.
- **Seamless Future Extraction**: Because modules maintain zero direct internal dependencies and enforce strict Clean Architecture boundaries, any module (e.g., `ai_coach` or `workouts`) can be easily extracted into a standalone microservice in the future if scale demands it.

---

## 4.6 Core Architectural Principles

All development on GymAI must uphold the following core engineering principles:

1. **Separation of Concerns (SoC)**: UI, orchestration, domain rules, and data access remain strictly segregated into dedicated layers.
2. **Single Responsibility Principle (SRP)**: Each class, module, and component must have one single, well-defined reason to change.
3. **Dependency Inversion Principle (DIP)**: High-level application policies must never depend on low-level infrastructure details. Both depend on abstract interfaces.
4. **High Cohesion & Low Coupling**: Code within a module must be tightly related to its domain, while dependencies between different modules must be kept to a minimum.
5. **Maintainability & Testability**: Every business rule must be unit-testable in milliseconds without requiring database or network connections.

---

## 4.7 Architecture Governance & Enforcement Rules

The following rules are mandatory for human engineers and AI coding assistants alike:

> [!IMPORTANT]
> 1. **Strict Layer Boundary Isolation**: No module or layer may bypass its defined hierarchy. Presentation must never call Repositories or SQL directly.
> 2. **Clean Domain Purity**: The `domain/` directory must NEVER import external frameworks (SQLAlchemy, FastAPI, Pydantic, HTTP libraries).
> 3. **No Business Logic in Controllers**: FastAPI route handlers (`presentation/`) must only handle HTTP concerns, request parsing, and response formatting. Business logic belongs exclusively in `application/` and `domain/`.
> 4. **Cross-Module Communication**: Modules must communicate through public Application Layer services or interfaces, NEVER by directly querying another module's internal database tables.
> 5. **Mandatory Compliance for AI Assistants**: All AI-generated code proposals must strictly adhere to this section. Any code violating layer encapsulation or dependency rules will be rejected.

---

# 5. Folder Structure & Project Organization

This section defines the mandatory physical folder structure and structural organization rules for GymAI. Maintaining a predictable, highly organized directory layout ensures high maintainability, rapid navigation, and seamless collaboration between human engineers and AI coding assistants.

---

## 5.1 Top-Level Directory Responsibilities

The root directory contains high-level operational boundaries separating client code, server code, infrastructure, and supporting tooling.

### 1. `backend/`
- **Purpose**: Houses the FastAPI backend application, database migrations, domain modules, and backend tests.
- **What Belongs Inside**: Python source code (`app/`), database migration scripts (`alembic/`), dependencies configuration (`pyproject.toml`), environment templates (`.env.example`), and backend test suites (`tests/`).
- **What Should NEVER Be Placed Inside**: Frontend React components, public web assets, HTML templates, or raw user file uploads.

### 2. `frontend/`
- **Purpose**: Holds the Next.js TypeScript web application, design components, and client-side feature modules.
- **What Belongs Inside**: Next.js App Router code (`src/app/`), feature modules (`src/features/`), UI design primitives (`src/components/`), frontend configuration files (`next.config.js`, `tsconfig.json`, `package.json`), and public assets (`public/`).
- **What Should NEVER Be Placed Inside**: Python scripts, backend database models, raw SQL files, or secret server environment variables.

### 3. `docs/`
- **Purpose**: Serves as the central repository for project documentation, architectural decision records (ADRs), API specifications, and development guidelines.
- **What Belongs Inside**: Technical specifications, system flowcharts, database schemas, onboarding guides, and AI instructions (`docs/ai/development_guide.md`).
- **What Should NEVER Be Placed Inside**: Executable application code, temporary debug logs, or configuration secrets.

### 4. `docker/`
- **Purpose**: Isolates container definitions and environment orchestration configurations for development and production environments.
- **What Belongs Inside**: Container build manifests (`Dockerfile.backend`, `Dockerfile.frontend`) and compose orchestration templates (`docker-compose.dev.yml`, `docker-compose.prod.yml`).
- **What Should NEVER Be Placed Inside**: Application source code files, database dump backups, or runtime log files.

### 5. `scripts/`
- **Purpose**: Contains automated developer utility scripts, build helpers, and maintenance tools.
- **What Belongs Inside**: Database seed scripts, migration automation wrappers, environment bootstrap scripts (`setup.sh`, `seed_data.py`).
- **What Should NEVER Be Placed Inside**: Production business logic, API route handlers, or persistent data models.

### 6. `config/`
- **Purpose**: Holds infrastructure service configurations and operational environment rules.
- **What Belongs Inside**: Nginx reverse proxy settings, Prometheus/Grafana monitoring rules, log rotation configs, and CORS policies.
- **What Should NEVER Be Placed Inside**: Hardcoded credentials, private keys, or application business logic.

### 7. `logs/`
- **Purpose**: Stores local runtime log output generated by background application processes during execution.
- **What Belongs Inside**: Local development log files (`backend.log`, `access.log`, `error.log`) strictly managed via `.gitignore`.
- **What Should NEVER Be Placed Inside**: Version-controlled application code, database secrets, or documentation.

### 8. `uploads/`
- **Purpose**: Local staging directory for user-generated file uploads (e.g., profile avatars, workout attachments) in development setups.
- **What Belongs Inside**: Temporary or locally served user media files.
- **What Should NEVER Be Placed Inside**: Core static application branding, system binaries, or application code.

### 9. `static/`
- **Purpose**: Stores global, non-changing public static assets that are served directly by web servers.
- **What Belongs Inside**: System logos, default media templates, static documentation assets, and public branding files.
- **What Should NEVER Be Placed Inside**: User-generated dynamic content or confidential business documents.

### 10. `tests/`
- **Purpose**: Root-level testing container dedicated to cross-service system integration and End-to-End (E2E) testing.
- **What Belongs Inside**: System-wide integration benchmarks, automated Playwright/Cypress E2E suites, and load test scripts.
- **What Should NEVER Be Placed Inside**: Isolated unit tests (which live inside `backend/tests/` or `frontend/`).

---

## 5.2 Internal Backend Organization (`backend/`)

The backend codebase enforces a clean Modular Monolith structure:

```text
backend/
├── alembic/              # Database migration scripts and environment configurations
├── app/                  # Application source root
│   ├── api/              # Global API routing table and version aggregators
│   ├── common/           # Cross-cutting utility functions, base DTOs, and helpers
│   ├── core/             # Central system configs, security tokens, and DB sessions
│   ├── main.py           # FastAPI entry point initialization
│   └── modules/          # Business domain modules (Clean Architecture)
│       ├── admin/
│       ├── ai_coach/
│       ├── auth/
│       ├── exercises/
│       ├── progress/
│       ├── users/
│       └── workouts/
└── tests/                # Automated backend test suites (unit, integration, e2e)
```

### Purpose of Backend Directories:

1. **`app/`**: The primary root container for all Python backend execution code.
2. **`modules/`**: Contains independent business domain modules (`auth`, `users`, `workouts`, etc.). Each module strictly encapsulating its own `domain/`, `application/`, `infrastructure/`, and `presentation/` layers.
3. **`core/`**: Houses application-wide infrastructure mechanisms, including environment settings parsing (`config.py`), JWT security verification (`security.py`), and database connection session factories (`db/session.py`).
4. **`api/`**: The presentation aggregation layer (`api/v1/router.py`) responsible for mounting endpoints from individual domain modules into unified versioned route endpoints.
5. **`alembic/` (Database)**: Controls database schema versions, evolution scripts, and SQLAlchemy migration environments.
6. **`tests/`**: Contains structured tests segregated into `unit/` (isolated logic tests), `integration/` (repository and database queries), and `e2e/` (full API pipeline validation).

---

## 5.3 Internal Frontend Organization (`frontend/`)

The frontend codebase enforces a feature-sliced architecture under `src/`:

```text
frontend/
├── public/               # Public static assets (favicons, images, icons)
└── src/                  # Application source code
    ├── app/              # Next.js App Router (Pages, Layouts, Route Groups)
    ├── components/       # Global generic UI components (Buttons, Modals, Inputs)
    ├── features/         # Domain-driven feature modules (auth, workouts, etc.)
    ├── hooks/            # Shared generic React hooks (useMediaQuery, useDebounce)
    ├── lib/              # Third-party library initializations (Axios, React Query)
    ├── services/         # Global baseline API client services
    ├── styles/           # Global CSS variables, Tailwind directives, and themes
    ├── types/            # Global TypeScript interface declarations and DTOs
    └── utils/            # Generic pure utility helper functions
```

### Distinction Between `app/`, `features/`, and `components/`

To prevent structural confusion, developers and AI coding assistants must strictly observe the differences between these three UI layers:

| Directory | Layer Responsibility | Business Knowledge | Examples |
| :--- | :--- | :--- | :--- |
| **`app/`** | **Routing & Page Composition** | Minimal (Routing & Layouts only) | `app/(dashboard)/workouts/page.tsx`, `layout.tsx` |
| **`features/`** | **Domain Business Logic & UI** | High (Deep business domain knowledge) | `features/workouts/components/WorkoutLogger.tsx` |
| **`components/`** | **Generic UI Presentation** | Zero (Completely domain-agnostic) | `components/ui/Button.tsx`, `components/ui/Modal.tsx` |

1. **`app/`**: Focuses strictly on routing, SSR page definitions, metadata tags, and top-level page layout composition. Page files should be light wrappers that import business components from `features/`.
2. **`features/`**: Contains all business domain components, feature-specific hooks, local API calls, and types. Code here understands specific business concepts like "Exercises", "Sets", and "Reps".
3. **`components/`**: Houses domain-agnostic design system primitives. A component inside `components/ui/` must NEVER import from `features/` or reference specific business entities.

---

## 5.4 Project Organization Rules

All project contributors and AI coding tools must strictly comply with the following structural rules:

> [!IMPORTANT]
> 1. **Feature Encapsulation**: Every new business capability must belong to its own dedicated module (`backend/app/modules/<feature>` and `frontend/src/features/<feature>`).
> 2. **No Utility Dumping**: Do NOT create generic "dumping ground" files like `helpers.py` or `utils.ts` containing hundreds of unrelated functions. Place utility functions near the domain logic that consumes them.
> 3. **Purity of Shared Directories**: Code placed in global folders (`components/ui/`, `common/`, `lib/`) MUST remain strictly generic and free of feature-specific business logic.
> 4. **Feature Locality**: Keep code as close as possible to where it is used. If a component, hook, or type is used by only one feature, it MUST reside inside that feature's directory.
> 5. **Flat & Cohesive Structure**: Avoid deep, arbitrary folder nesting (e.g., `components/forms/inputs/buttons/primary/`). Maintain shallow, highly cohesive directory hierarchies that are intuitive to navigate.
> 6. **Mandatory AI Compliance**: AI assistants generating new code must inspect existing folder structures before creating files and must strictly place new code into its designated domain module.
