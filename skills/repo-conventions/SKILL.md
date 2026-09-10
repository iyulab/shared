---
name: repo-conventions
description: Repository conventions for the iyulab/shared hybrid repository.
---

# Repository conventions

## Structure rules

- Reusable workflows go in .github/workflows/.
- Non-trivial workflow logic goes in scripts/.
- Consumer-ready workflow files go in templates/ as flat YAML files.
- Company assets go in assets/.
- Agent-readable guidance goes in skills/.
- Do not duplicate implementation files inside skills/.

## Reusable workflow guarantees

A calling job cannot declare `timeout-minutes`, `env`, `runs-on`, or most other job-level keys, so
the called workflow owns them. CONTRIBUTING.md holds the rule and the full key list — do not restate
it here.

## Change management

- Keep skill content aligned with the actual implementation.