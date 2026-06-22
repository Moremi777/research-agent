# AGENTS

Purpose: give AI coding agents the minimal, high-value context they need to work productively in this repository.

Key guidance
- Read the workspace `CLAUDE.md` for the WAT framework and workflows: [CLAUDE.md](CLAUDE.md)
- Link, don't embed: prefer referencing existing docs under `workflows/` and `tools/` instead of copying them.
- Ask before changing workflows or running paid APIs or external services.
- Use deterministic tools in `tools/` when available; create small, testable helpers only when necessary.
- Keep edits minimal and focused; explain any non-trivial refactor in the repo and update workflows.
- When uncertain, ask a clarifying question rather than guessing.

Operational notes for agents
- Use the repository layout in `CLAUDE.md` as the source of truth for where to place scripts and workflows.
- Prefer `AGENTS.md` over `.github/copilot-instructions.md` for repo-scoped agent guidance. If `.github/copilot-instructions.md` exists, merge relevant parts rather than duplicating.
- Track multi-step work with the repo todo list tool (managed by maintainers) and mark progress.

Next steps suggestions
- Create focused agent skills for common tasks (tests, lint, release) as separate `workflows/` or skills files.

Contact
- If behavior should differ for specific subsystems, add short per-subsystem instructions under `workflows/` and link them here.
