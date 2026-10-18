# AI Agent Handoff & Continuity Brief — Siphon

You are resuming work as the lead engineer on **Siphon**, an open-source, NewPipe-like Linux desktop application for extracting and downloading YouTube video and audio as a standalone AppImage.

## Mandatory Continuity Protocol

Before writing any code or modifying any files, you MUST execute the following orientation steps:

1. **Read the 7 core handoff files in this exact sequential order:**
   1. `AI_HANDOFF.md` — Project summary, fixed technology stack, milestone state, and strict operating rules.
   2. `PROJECT_STATE.md` — Current snapshot of completed items, work in progress, and upcoming deliverables.
   3. `ARCHITECTURE.md` — Append-only Architectural Decision Records (ADRs) explaining technical rationales.
   4. `TASKS.md` — Active development roadmap with atomic checkboxes.
   5. `KNOWN_ISSUES.md` — Active bug register and diagnosis history.
   6. `DEV_SETUP.md` — Local environment setup, dependencies, running, testing, and containerized build workflow.
   7. `CHANGELOG.md` — Session history and release ledger.

2. **Core Invariant Rules:**
   - **Network & Ports:** Always bind Uvicorn to `127.0.0.1` on port `0`. Read back the dynamically assigned port and connect `pywebview`. Never hardcode port 8000. Never bind `0.0.0.0`.
   - **Testing:** Every feature or endpoint must have a passing `pytest` test before marking its task complete in `TASKS.md`.
   - **Git Hygiene:** Commit after every completed atomic task using conventional commit messages.
   - **Session Closure:** At the end of every session, update `PROJECT_STATE.md`, `CHANGELOG.md`, `KNOWN_ISSUES.md`, and `ARCHITECTURE.md` before stopping.

## Required Initial Response

Do NOT start writing code or modifying files immediately. In your very first response, output ONLY:

1. A **5-bullet summary** of your current understanding of the project and current state.
2. The current milestone and active work-in-progress task.
3. Your proposed **next 3 atomic tasks** based on `TASKS.md`.
4. Any blockers, questions, or environmental checks.

**STOP and WAIT for explicit user approval before writing any code or modifying files.**
