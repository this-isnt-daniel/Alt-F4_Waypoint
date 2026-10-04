# AI Disclosure Statement

In accordance with the Tech-Triathlon 2026 Hackathon submission guidelines, the following document explicitly outlines the use of Artificial Intelligence (AI) tools during the development, architecture, and coding phases of the Alt-F4 Waypoint solution.

## Human Responsibility & Review Statement

**AI tools were used strictly as development assistance. Team members thoroughly reviewed, modified, tested, and accepted all resulting code, documentation, and logic.** The final architecture, implementation decisions, validation (including all Docker/Infrastructure integrations, canonical schemas, and role logic), and ultimate submission decisions remained fully the responsibility of the human team.

## AI Tools Utilized

- **Antigravity (Google DeepMind):** Used exclusively within the IDE context as a sophisticated pair-programming agent.
- **ChatGPT:** Occasional prompt-assisted querying for Python/React syntax references and boilerplate generation.

## AI-Assisted Work Categories

AI provided suggestions, generated drafts, and accelerated implementation across the following vectors:
- **Code Generation Assistance:** Used to rapidly scaffold standard FastAPI endpoints, SQLAlchemy boilerplate models, and React/Vite UI components based on precise human-authored structural specifications.
- **Documentation Drafting:** Assisted in transforming raw architecture decisions and source code into readable markdown documentation (e.g., initial `docker-compose` README generation and markdown formatting).
- **Test Planning:** Provided checklists for endpoint coverage and mocked out standard unit test fixtures (Pytest) based on the schemas.
- **Debugging Assistance:** Expedited error resolution (like deciphering opaque Node.js lockfile issues or Python import conflicts) during integration.

## Purely Human (Non-AI) Work

The core proprietary value and critical systems of the application were achieved solely by human intervention and design:
- **Domain & UI Decisions:** Role boundaries, specific user workflows, validation logic, and frontend visual UX decisions were decided purely by the team.
- **Optimizer Integration:** The modeling, parameterization, and integration of the Google OR-Tools CP-SAT engine were deliberately hand-crafted to adhere to the explicit constraints of the Datathon (which strictly prohibit automated end-to-end proprietary modeling generation).
- **Dataset Interpretation & Hardening:** All handling of canonical constraint bounds (e.g., matching vehicle volume limits and temperature constraints to product schemas) and validation testing against the competition dataset rules were performed manually.
- **Infrastructure Correctness & Final Validation:** Ensuring the flawless end-to-end execution of `docker compose up`, strict dependency management, idempotent seeding, and execution of the Judge Walkthrough were verified manually by human execution.
