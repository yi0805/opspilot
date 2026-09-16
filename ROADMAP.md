# OpsPilot Roadmap

## Phase 1 — Foundation

### Task 001 — Application Scaffold

**Status:** Complete

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

**Status:** Complete

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

**Status:** Complete

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

**Status:** Complete

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

**Status:** Complete

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

**Status:** Complete

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

**Status:** Complete

**Goal:** Deploy a verified working version using a small, cost-conscious AWS architecture.

**Planned scope:**

- choose minimal AWS architecture
- Terraform
- secrets/configuration strategy
- deployment
- production smoke testing
- documentation

**Completion evidence:** Terraform infrastructure was applied, the frontend was deployed behind CloudFront, health and frontend smoke checks passed, and one controlled evidence-backed live agent request completed successfully.

### Task 008 — CloudFront-Only Lambda Origin Access

**Status:** Complete

**Goal:** Restrict Lambda Function URL invocation to the CloudFront distribution using Lambda Function URL AWS_IAM authentication and CloudFront Origin Access Control.

**Completion evidence:** The Lambda Function URL now uses `AWS_IAM`; CloudFront OAC signs Lambda-origin requests; direct unsigned Function URL requests return HTTP 403; CloudFront frontend and API smoke checks passed; one controlled evidence-backed live agent request completed successfully; and the final Terraform plan was clean.

### Task 009 — Portfolio Presentation Polish

**Status:** Complete

**Goal:** Improve recruiter-facing project presentation without changing application behavior.

**Completion evidence:** Reorganized the README for a recruiter-first introduction, surfaced the live demo, added concise engineering highlights, improved screenshot presentation with a completed-analysis result, and preserved the architecture and verified technical documentation.

Only technologies actually implemented and verified may later be claimed on the resume.

### Task 010 — OpenRouter Provider Migration

**Status:** Complete

**Goal:** Migrate the repository's AI-provider configuration from direct OpenAI API access to OpenRouter while preserving the Responses API tool-calling workflow and application behavior.

**Completion evidence:** Runtime configuration, Lambda secret loading, Terraform secret access, and automated tests use the OpenRouter key, model, and endpoint. Task 020 production verification confirmed OpenRouter is live with model `openai/gpt-5.6-luna`; Task 021 records that verified state.

### Task 014 — Safe OpenRouter Provider Error Observability

**Status:** Complete

**Goal:** Add minimal server-side diagnostics for OpenRouter SDK failures without exposing provider details to API clients or sensitive request data to logs.

**Completion evidence:** Reasoning and final provider request failures now emit only their stage, exception class name, allowlisted HTTP status code, and allowlisted request ID. The existing generic HTTP 502 response remains unchanged, and focused tests assert sensitive exception content is excluded from logs.

### Task 018 — Remove Incompatible OpenRouter `require_parameters` Routing Constraint

**Status:** Complete

**Goal:** Remove the incompatible OpenRouter `provider.require_parameters` routing constraint from Responses API requests while preserving the agent workflow and output guardrails.

**Completion evidence:** Both reasoning and final Responses API requests omit `provider.require_parameters`. Local fake-client tests confirm the requests retain their model, instructions, tools, sequential execution setting, and final structured-output settings; all backend checks pass. Task 020 production verification confirmed the removal fixed the previous OpenRouter 404 routing failure; Task 021 records that verified result.

### Task 021 — OpenRouter Production Verification Closeout

**Status:** Complete

**Goal:** Record the production-verified OpenRouter architecture and migration status without changing runtime, infrastructure, or deployment state.

**Completion evidence:** The deployed Lambda image `f1b397c1d32208df885fd7a36dbf73c504c1f390` completed a CloudFront agent request with HTTP 200 and status `completed`, including `query_sales` and `query_inventory` evidence from `synthetic_business_data`, with no provider-failure warning. CloudFront and `/api/health` were healthy, unsigned Function URL access returned HTTP 403, the `AWS_IAM`/buffered Function URL and SigV4-signing OAC remained intact, and the final Terraform plan reported no changes.
