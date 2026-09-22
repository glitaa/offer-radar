---
name: feature-workflow
description: >-
  Use this skill for end-to-end delivery of new features, bug fixes, or architectural changes in Offer-Radar. Guides the agent through requirement scoping, dedicated branch creation, interactive artifact planning, inside-out Clean Architecture implementation, atomic SRP commits, automated quality gates, and Pull Request preparation.
---

# Feature Workflow Runbook

This runbook guides the complete development lifecycle for Offer-Radar changes, enforcing Clean Architecture boundaries, atomic commits, and quality gates.

---

## Phase 1: Context Gathering & Branch Setup

1. **Check Git Status**:
   - Inspect the current working tree:
     ```powershell
     git status
     ```
   - If uncommitted changes exist, pause to review or stash them before starting.
2. **Clarify Requirements**:
   - If the task is ambiguous or involves architectural trade-offs, ask clarifying questions using `ask_question` or recommend `/grill-me`.
   - For broad codebase exploration or third-party documentation lookup, consider delegating to the `research` subagent to preserve the primary context window.
3. **Establish Dedicated Branch**:
   - **Never work on `main`**.
   - Create and checkout a descriptive kebab-case branch:
     ```powershell
     git checkout -b <type>/<kebab-name>
     ```
     - Example: `feat/otodom-scraper`, `fix/dedup-hash-collision`, `refactor/session-manager`

---

## Phase 2: Interactive Planning Artifact

Before modifying production code, generate an Antigravity Plan Artifact:

1. Create a markdown plan in the artifact directory (`brain/<conv-id>/...`) with metadata:
   - `RequestFeedback: true`
   - `UserFacing: true`
2. Structure the plan artifact:
   - **Objective & Scope**: Summary of user needs and expected behavior.
   - **Layer Architecture Mapping**: Breakdown of required changes across layers (`domain`, `application`, `infrastructure`, `cli`).
   - **Task Checklist**: Specific files to create/modify per layer.
   - **Verification Strategy**: Unit/integration tests and CLI manual test scenarios.
3. Wait for the user to review the plan and click **Proceed** or provide feedback.

---

## Phase 3: Clean Architecture Implementation (Inside-Out)

Execute the plan from the inside out. For each layer, implement the code, run its tests, and make an atomic commit satisfying the Single Responsibility Principle (SRP).

```
   ┌─────────────────────────────────────────────────────────┐
   │ 1. Domain: Entities & Interfaces (src/domain/)          │
   ├─────────────────────────────────────────────────────────┤
   │ 2. Application: Use Cases & Orchestration (src/app/)    │
   ├─────────────────────────────────────────────────────────┤
   │ 3. Infrastructure: DB Repos & Scrapers (src/infra/)     │
   ├─────────────────────────────────────────────────────────┤
   │ 4. CLI: Typer, Menus, Rich & i18n (src/cli/)            │
   └─────────────────────────────────────────────────────────┘
```

### 3.1 Domain Layer (`src/domain/`)
- Define or update pure business models (`Offer`, `Settings`, etc.) and abstract interface contracts (`SearchSessionRepository`, `PortalScraper`).
- **Constraint**: Zero imports from outer layers (`application`, `infrastructure`, `cli`).
- Verify: `uv run pytest tests/test_domain/` (or related test files).
- Commit:
  ```powershell
  git add src/domain/ tests/
  git commit -m "feat(domain): <concise description>"
  ```

### 3.2 Application Layer (`src/application/`)
- Implement use cases and application services (`SessionManager`, sync routines).
- **Constraint**: Import only from `src/domain/`.
- Verify: `uv run pytest tests/test_application/`
- Commit:
  ```powershell
  git add src/application/ tests/
  git commit -m "feat(app): <concise description>"
  ```

### 3.3 Infrastructure Layer (`src/infrastructure/`)
- Implement concrete repository adapters (SQLAlchemy ORM models, SQLite repos), scrapers (`httpx`), or config storage.
- **Constraint**: Depend on `src/domain/`. Do NOT import from `src/cli/`.
- Verify: `uv run pytest tests/test_infrastructure/`
- Commit:
  ```powershell
  git add src/infrastructure/ tests/
  git commit -m "feat(infra): <concise description>"
  ```

### 3.4 CLI / Presentation Layer (`src/cli/`)
- Add or update Typer commands, Questionary interactive prompts, and Rich output components.
- Wrap user-facing strings with `_("...")` for Babel localization.
- If translations are added/edited:
  ```powershell
  uv run pybabel compile -d locales --statistics
  ```
- Verify: `uv run pytest tests/test_cli/`
- Commit:
  ```powershell
  git add src/cli/ locales/ tests/
  git commit -m "feat(cli): <concise description>"
  ```

---

## Phase 4: Full Quality Gate Verification

Before finalizing the branch, execute all automated checks in PowerShell:

```powershell
# 1. Format code
uv run ruff format .

# 2. Lint code
uv run ruff check .

# 3. Verify translation catalogs
uv run pybabel compile -d locales --statistics

# 4. Run entire test suite
uv run pytest
```

If formatting or lint fixes resulted in modifications, commit them:
```powershell
git add -u
git commit -m "chore: format and lint code"
```

---

## Phase 5: Pull Request Readiness & Summary

1. Inspect git log to confirm atomic SRP commits:
   ```powershell
   git log --oneline main..HEAD
   ```
2. Present a comprehensive Pull Request proposal to the user:
   - **PR Title**: Concise conventional title (e.g., `feat: integrate Otodom portal scraper`).
   - **Summary of Changes**: Bullet points grouped by architectural layer.
   - **Testing Verification**: Status of pytest, ruff, and babel checks.
   - **Next Steps**: Command to push branch (`git push -u origin <branch>`) and submit via GitHub CLI (`gh pr create`).
