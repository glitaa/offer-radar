---
name: code-review
description: >-
  Use this skill to perform a comprehensive code review and quality audit on current changes, feature branches, or pull requests in Offer-Radar. Checks Clean Architecture boundary compliance, atomic SRP commit hygiene, code quality (ruff), translation completeness (babel), and test suite pass rate (pytest), generating a structured review report artifact.
---

# Code Review & Architecture Audit Runbook

This runbook guides auditing an Offer-Radar branch, commit set, or PR against project architectural rules and quality standards.

---

## 1. Scope & Git Inspection

1. **Check Current Branch & Status**:
   ```powershell
   git branch --show-current
   git status
   ```
   Confirm the review is being conducted on a dedicated feature branch, not directly on `main`.
2. **Review Commit History**:
   ```powershell
   git log --oneline main..HEAD
   ```
   Verify:
   - Commits follow Conventional Commits format (`type(scope): description`).
   - Single Responsibility Principle (SRP) is honored: changes in domain, application, infrastructure, and CLI are logically separated into distinct commits rather than bundled together.

---

## 2. Clean Architecture Dependency Audit

Inspect the git diff (`git diff main..HEAD`) to verify strict adherence to the Clean Architecture dependency rule:

```
┌──────────────┐     ┌─────────────────┐     ┌──────────────────────┐
│  src/domain/ │ ◄── │ src/application │ ◄── │ src/infrastructure/  │
└──────────────┘     └─────────────────┘     │ & src/cli/           │
                                             └──────────────────────┘
```

1. **Domain Layer (`src/domain/`)**:
   - MUST NOT import from `src/application/`, `src/infrastructure/`, or `src/cli/`.
   - MUST NOT import external database (SQLAlchemy, aiosqlite), HTTP (httpx), or UI (typer, rich) libraries.
2. **Application Layer (`src/application/`)**:
   - May import from `src/domain/`.
   - MUST NOT import from `src/infrastructure/` or `src/cli/`.
3. **Infrastructure Layer (`src/infrastructure/`)**:
   - Implements domain repository interfaces.
   - MUST NOT import from `src/cli/`.
4. **CLI Presentation Layer (`src/cli/`)**:
   - Interacts with application use cases and domain models.
   - MUST NOT import or instantiate concrete infrastructure classes directly.

---

## 3. Automated Quality Gate Audit

Run the full automated test and linting suite:

```powershell
# 1. Check code formatting
uv run ruff format --check .

# 2. Check linting rules
uv run ruff check .

# 3. Check translation compile status
uv run pybabel compile -d locales --statistics

# 4. Run test suite
uv run pytest
```

Record any errors, warnings, or missing coverage.

---

## 4. Review Report Artifact Generation

Generate an Antigravity Review Artifact (`brain/<conv-id>/...`) summarizing the review:

- **Review Summary**: Status (`APPROVED`, `APPROVED WITH SUGGESTIONS`, or `CHANGES REQUESTED`).
- **Architecture Invariants Checklist**:
  - [ ] Domain independence verified
  - [ ] Application layer boundaries preserved
  - [ ] Infrastructure isolation confirmed
  - [ ] CLI decouples from infrastructure
- **Commit Hygiene (SRP)**:
  - [ ] Conventional Commit format used
  - [ ] Atomic commits per layer (No God Commits)
- **Quality Gate Results**:
  - Ruff formatting: Pass / Fail
  - Ruff linting: Pass / Fail
  - Babel catalogs: Pass / Fail
  - Pytest: `X` passed, `0` failed
- **Actionable Recommendations**: Bulleted list of specific changes or cleanups required.
