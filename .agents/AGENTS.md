# Offer-Radar Agent Guidelines & SDLC Rules

## 1. Project Overview & Core Constraints

**Offer-Radar** is a local aggregator of classifieds listings (starting with OLX.pl for Jobs and Real Estate), engineered to enable effortless offer review and rating (Save, Reject, Skip) while eliminating previously seen listings.

### Architectural Invariants
- **Strict Clean Architecture**: Core business logic and domain models must remain completely decoupled from data storage, web scrapers, and UI frameworks.
- **Local Storage**: Uses local SQLite database with SQLAlchemy ORM and aiosqlite.
- **Scraper Extensibility**: Scrapers must adhere to domain interfaces so new classified portals can be integrated without modifying core application logic.

---

## 2. Clean Architecture & DDD Layer Boundaries

The codebase inside `src/` is strictly partitioned into four architectural layers:

```
src/
├── domain/         # Core entities, value objects, domain interfaces (Protocols/ABCs)
├── application/    # Use cases, application services, flow orchestration
├── infrastructure/ # Concrete database repositories, HTTP scrapers, config file I/O
└── cli/            # Presentation layer (Typer, Questionary, Rich formatting)
```

### Dependency Rules (Inward Only)
1. **Domain (`src/domain/`)**:
   - Contains pure business models (e.g., `Offer`, `OfferPrice`, `SearchSession`, `Settings`) and abstract interface contracts (`SearchSessionRepository`, `SettingsRepository`).
   - **Rule**: Must NEVER import from `src/application/`, `src/infrastructure/`, or `src/cli/`. Zero external framework dependencies.
2. **Application (`src/application/`)**:
   - Contains use case orchestrators (e.g., `SessionManager`, sync logic).
   - **Rule**: Depends ONLY on `src/domain/`. Must NEVER import from `src/infrastructure/` or `src/cli/`.
3. **Infrastructure (`src/infrastructure/`)**:
   - Implements domain repository interfaces and provides concrete services (`SQLiteSearchSessionRepository`, `TOMLSettingsRepository`, `httpx` scrapers).
   - **Rule**: Depends on `src/domain/`. Must NEVER import from `src/cli/`.
4. **CLI / Presentation (`src/cli/`)**:
   - User interaction via Typer, Questionary menus, and Rich tables/progress bars.
   - **Rule**: Interacts exclusively with `src/application/` use cases and `src/domain/` entities. Must NEVER directly instantiate or access infrastructure implementations.

---

## 3. Technology Stack & Tooling

- **Python**: `>= 3.13`
- **Package Manager & Toolchain**: `uv`
- **Build System**: `hatchling`
- **Database & Persistence**: `SQLite`, `aiosqlite`, `sqlalchemy` (ORM)
- **Scraping & Networking**: `httpx` (async), `beautifulsoup4`, `lxml`, `soupsieve`
- **CLI Presentation**: `typer`, `click` (cross-platform raw key input), `questionary` (interactive selection), `rich` (tables, progress bars), `colorama`
- **Configuration & Localization**: `TOML` (`config.toml`), `Babel` (`locales/`)
- **Testing & Quality**: `pytest`, `pytest-asyncio`, `ruff` (linter & formatter)

---

## 4. Shell Conventions (PowerShell)

- All terminal commands MUST run in PowerShell.
- Command chaining: Use `;` (PowerShell does NOT support `&&`).
- Use native PowerShell commands (`Remove-Item`, `Test-Path`, `$env:VAR`).

---

## 5. Quality Gates & Automated Verification

Always execute Python commands through `uv run` to ensure virtual environment consistency.

Before proposing code changes or completing a workflow step, verify all quality gates:

1. **Code Formatting**:
   ```powershell
   uv run ruff format .
   ```
2. **Code Linting**:
   ```powershell
   uv run ruff check .
   ```
3. **Translation Integrity** (required when user-facing CLI strings are added or modified):
   ```powershell
   uv run pybabel compile -d locales --statistics
   ```
4. **Test Suite**:
   ```powershell
   uv run pytest
   ```

---

## 6. Git Discipline & Branching Strategy

### Dedicated Feature Branches
- **Never commit directly to `main`**.
- Always branch off `main` using structured kebab-case names:
  - `feat/<kebab-name>`: New features or capabilities.
  - `fix/<kebab-name>`: Bug fixes or corrections.
  - `refactor/<kebab-name>`: Architectural cleanups and structural improvements.
  - `docs/<kebab-name>`: Documentation additions or updates.

### Single Responsibility Principle (SRP) Commits
- **No God Commits**: Never bundle multi-layer changes into a monolithic commit.
- Keep commits atomic and logically separated by architectural layer.
- Format all commit messages using **Conventional Commits**:
  `git commit -m "<type>(<scope>): <short description>"`
  - **Scopes**: `domain`, `app`, `infra`, `cli`, `config`, `docs`, `tests`.
  - **Types**: `feat`, `fix`, `refactor`, `test`, `docs`, `chore`.
  - Examples:
    - `feat(domain): add portal scraper interface and listing filter contract`
    - `feat(infra): implement otodom scraper using httpx and beautifulsoup4`
    - `feat(cli): add portal selector prompt in new search interactive menu`
    - `test(infra): add unit tests for otodom listing parser`

### Pull Request Readiness
- When all layers are implemented, verified by quality gates, and committed via SRP:
  - Verify clean working tree (`git status`).
  - Provide a clear PR summary detailing the architectural changes, test results, and merge checklist.

---

## 7. Antigravity Workflow & Skills Integration

- **Feature Delivery**: Run the `.agents/skills/feature-workflow` skill for end-to-end feature implementation following inside-out Clean Architecture.
- **Code Review & Audits**: Run the `.agents/skills/code-review` skill to audit branch diffs for layer boundary violations and test compliance.
- **Planning & Specs**: Use Antigravity native artifacts (`write_to_file` in the artifact directory with `RequestFeedback: true`) for interactive plan review with the user.
- **Deep Investigation**: Leverage the `research` subagent for deep codebase exploration without filling primary context.
