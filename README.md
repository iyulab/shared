# shared

Shared assets used across iyulab repositories — workflows, scripts, brand assets, and agent skills.

## Structure

```
.github/workflows/   reusable workflows
scripts/             helper scripts
templates/           ready-to-copy files
assets/              company logo and icon files
skills/              agent-usable skills and guidance
```

## How to use

**Workflows** — reference directly from any iyulab repository:

```
uses: iyulab/shared/.github/workflows/<name>.yml@main
```

**Templates** — copy a file from `templates/` into your repository and adjust as needed.

**Assets** — reference files in `assets/` directly via raw URL or copy into your project.

**Scripts** — called by the shared workflows, but can also be run standalone.

**Skills** — guidance for agents, meant to be read and interpreted by AI rather than humans.
[Learn more about skills here](https://agentskills.io/specification).
