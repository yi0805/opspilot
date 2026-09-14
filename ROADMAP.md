# OpsPilot Roadmap

## Phase 1 — Foundation

### Task 001 — Application Scaffold

**Goal:** Establish the backend/frontend application structure.

**Planned scope:**

- FastAPI backend
- React + TypeScript + Vite frontend
- PostgreSQL-ready persistence layer
- configuration/environment handling
- health endpoint
- basic backend tests
- frontend test/build setup
- root `.gitignore`
- local development instructions

Do not implement the LLM agent yet.

### Task 002 — Business Data Layer

**Goal:** Create realistic synthetic business data and deterministic query services.

**Planned domains:**

- products
- sales
- inventory
- campaigns

**Planned scope:**

- database models/schema
- seed data
- query/data-access layer
- business query services
- tests

## Phase 2 — AI Agent

### Task 003 — LLM Tool Calling

**Goal:** Allow an LLM to answer business questions by selecting and executing structured tools.

**Planned tools:**

- `query_sales`
- `query_inventory`
- `query_campaigns`
- `get_product_details`

**Planned scope:**

- tool schemas
- tool execution
- LLM integration
- structured outputs
- tool-call validation
- tests

### Task 004 — Business Reasoning and Traceability

**Goal:** Support questions requiring multiple data sources and produce evidence-based recommendations.

**Planned scope:**

- multi-tool workflows
- recommendation generation
- evidence/source information
- guardrails
- graceful failure handling
- tests

## Phase 3 — Product Experience

### Task 005 — Frontend Experience

**Goal:** Build a clean interface for asking business questions and understanding the result.

**Planned scope:**

- question input
- example prompts
- recommendation/result presentation
- evidence/tool activity
- loading states
- error states
- responsive layout

Keep the UI polished but small.

## Phase 4 — Production Quality

### Task 006 — Production Hardening

**Goal:** Make the repository portfolio-ready.

**Planned scope:**

- expanded automated tests
- linting
- type checking
- GitHub Actions CI
- Docker if justified
- error handling
- security/config review
- README architecture documentation
- example questions
- screenshots

## Phase 5 — Deployment

### Task 007 — AWS and Terraform

**Goal:** Deploy a verified working version using a small, cost-conscious AWS architecture.

**Planned scope:**

- choose minimal AWS architecture
- Terraform
- secrets/configuration strategy
- deployment
- production smoke testing
- documentation

Only technologies actually implemented and verified may later be claimed on the resume.
