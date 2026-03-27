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

## Change management

- Keep skill content aligned with the actual implementation.