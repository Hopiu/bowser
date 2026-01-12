# Skills Index

This file defines **canonical project skills** the LLM must follow. Each skill specifies the *one correct command* for a common project action.

1. **Run the Project** → `uv run bowser`
2. **Test the Project** → `uv run pytest`
3. **Lint the Project** → `uv run ruff`

Deviating from these commands is considered incorrect behavior unless explicitly instructed.

---

# Skill: Run the Project with `uv run bowser`

## Purpose
Teach the LLM **how and when to run this project** using the canonical command:

```bash
uv run bowser
```

This skill ensures the LLM consistently uses the correct entry point, avoids ad‑hoc commands, and follows project conventions.

---

## Canonical Command

**Always run the project using:**

```bash
uv run bowser
```

Do **not**:
- Call `python` directly
- Run scripts via file paths
- Use alternative task runners (e.g. `make`, `poetry run`, `pipenv run`)

`uv` is the authoritative environment and dependency manager for this project, and `bowser` is the defined runtime entry point.

---

## What `uv run bowser` Means

- `uv run`:
  - Ensures dependencies are resolved and installed according to the project configuration
  - Executes commands inside the correct, isolated environment

- `bowser`:
  - The project’s primary executable / CLI
  - Encapsulates startup logic, configuration loading, and runtime behavior

Together, they guarantee a reproducible and correct execution environment.

---

## When to Use This Command

Use `uv run bowser` whenever you need to:

- Start the application
- Run the main service or agent
- Execute project logic end‑to‑end
- Validate runtime behavior
- Demonstrate how the project is launched

If the task says **“run the project”**, **“start the app”**, or **“execute Bowser”**, this is the command.

---

## When *Not* to Use This Command

Do **not** use `uv run bowser` when:

- Running tests (use the project’s test command instead)
- Running one‑off scripts unless explicitly routed through `bowser`
- Installing dependencies
- Linting or formatting code

If unsure, default to **not running anything** and explain what would be executed.

---

## How to Explain This to Humans

When documenting or instructing users, say:

> “Run the project with `uv run bowser`.”

Optionally add:

> “This ensures the correct environment and entry point are used.”

Do **not** over‑explain unless the user asks.

---

## Error Handling Guidance

If `uv run bowser` fails:

1. Assume a dependency or configuration issue
2. Report the error output verbatim
3. Do **not** substitute another execution method
4. Suggest fixing the root cause, not changing the command

---

## Mental Model for the LLM

- There is **one** correct way to run the project
- That way is **stable and intentional**
- Deviating from it is a bug

Think of `uv run bowser` as:

> “The project’s on‑switch.”

---

## Summary (Checklist)

Before suggesting how to run the project, verify:

- [ ] You are using `uv run`
- [ ] You are invoking `bowser`
- [ ] You are not calling Python directly
- [ ] You are not inventing alternate commands

If all are true, you are doing it right.


---

# Skill: Test the Project with `uv run pytest`

## Purpose
Teach the LLM **how and when to run tests** for this project using the canonical command:

```bash
uv run pytest
```

This skill ensures tests are executed in the correct environment, using the project’s standard tooling, without inventing alternate commands.

---

## Canonical Command

**Always run tests using:**

```bash
uv run pytest
```

Do **not**:
- Call `pytest` directly
- Use `python -m pytest`
- Run tests via ad-hoc scripts or task runners

`uv` is the authoritative environment manager, and `pytest` is the test runner for this project.

---

## What `uv run pytest` Means

- `uv run`:
  - Ensures dependencies (including test dependencies) are resolved correctly
  - Runs inside the same environment model as the application

- `pytest`:
  - Discovers and runs the project’s test suite
  - Applies project-level configuration (e.g. `pytest.ini`, `pyproject.toml`)

Together, they guarantee consistent and reproducible test execution.

---

## When to Use This Command

Use `uv run pytest` whenever you need to:

- Run the full test suite
- Verify a change before or after modifying code
- Reproduce a failing test
- Validate behavior without starting the application

If the task says **“run tests”**, **“test the project”**, or **“verify with pytest”**, this is the command.

---

## When *Not* to Use This Command

Do **not** use `uv run pytest` when:

- Running the application (use `uv run bowser`)
- Installing dependencies
- Linting or formatting code
- Executing non-test scripts

If unsure, default to explaining what tests would be run rather than executing them.

---

## Error Handling Guidance

If `uv run pytest` fails:

1. Capture and report the full pytest output
2. Identify whether the failure is:
   - A test assertion failure
   - A missing dependency or import error
   - A configuration issue
3. Do **not** change the command to work around the failure
4. Fix the underlying cause, then re-run the same command

---

## Mental Model for the LLM

- There is **one** correct way to run tests
- Test execution should mirror the real runtime environment
- Consistency matters more than convenience

Think of `uv run pytest` as:

> “The project’s truth-check.”

---

## Summary (Checklist)

Before suggesting how to test the project, verify:

- [ ] You are using `uv run`
- [ ] You are invoking `pytest`
- [ ] You are not calling Python directly
- [ ] You are not inventing alternate test commands

If all are true, you are doing it right.


---

# Skill: Lint the Project with `uv run ruff`

## Purpose
Teach the LLM **how and when to lint the project** using the canonical command:

```bash
uv run ruff
```

This skill ensures linting is performed consistently, using the project’s configured rules and environment.

---

## Canonical Command

**Always lint the project using:**

```bash
uv run ruff
```

Do **not**:
- Call `ruff` directly
- Use alternative linters unless explicitly instructed
- Invoke formatting or linting via ad-hoc scripts

`uv` guarantees the correct environment, and `ruff` enforces the project’s linting standards.

---

## What `uv run ruff` Means

- `uv run`:
  - Executes linting inside the managed project environment
  - Ensures the correct version of `ruff` and dependencies are used

- `ruff`:
  - Performs fast, opinionated linting
  - Applies rules configured in project files (e.g. `pyproject.toml`)

Together, they provide deterministic and repeatable lint results.

---

## When to Use This Command

Use `uv run ruff` whenever you need to:

- Check code quality
- Identify linting or style issues
- Validate changes before committing
- Respond to a request to “lint the project” or “run ruff”

---

## When *Not* to Use This Command

Do **not** use `uv run ruff` when:

- Running the application (`uv run bowser`)
- Running tests (`uv run pytest`)
- Formatting code unless `ruff` is explicitly configured to do so
- Installing dependencies

If unsure, explain what linting would check instead of executing it.

---

## Error Handling Guidance

If `uv run ruff` reports issues:

1. Treat findings as authoritative
2. Report errors or warnings clearly
3. Do **not** suppress or bypass lint rules
4. Fix the code, then re-run the same command

---

## Mental Model for the LLM

- Linting enforces shared standards
- Speed and consistency matter more than flexibility
- There is **one** correct linting command

Think of `uv run ruff` as:

> “The project’s code-quality gate.”

---

## Summary (Checklist)

Before suggesting how to lint the project, verify:

- [ ] You are using `uv run`
- [ ] You are invoking `ruff`
- [ ] You are not inventing alternate linting tools

If all are true, you are doing it right.

