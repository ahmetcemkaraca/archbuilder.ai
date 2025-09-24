Portable Copilot instructions and prompts

How to use
- Copy the entire .github folder into the root of any project repository.
- In VS Code, enable use of instruction files:
  - Settings → Search for “useInstructionFiles” → Enable “GitHub Copilot: Use Instruction Files”.
- Prompts appear in Chat as slash commands. Type / to see them (for example: /universal-app-autobuilder).

What’s included
- .github/copilot-instructions.md — General rules (secure defaults, trio docs, SemVer).
- .github/instructions/*.instructions.md — Role/language specific rules with applyTo globs.
- .github/prompts/*.prompt.md — Reusable prompts for requirements, design, tasks, and shipping a vertical slice.

Conventions
- Code and code comments are always in English.
- Chat responses are in Turkish.
- Every 4 significant prompt runs, append an entry to version.md (do not remove existing content).
- If a user idea is incorrect/unsafe/illogical, append to hata.md with the idea, diagnosis, and correct solution.

Notes
- The prompts only reference root-level files (requirements.md, design.md, tasks.md) and local instruction files, so they work in any repo.
- If external services are needed but unavailable, prompts will mock behind interfaces and document setup steps.
