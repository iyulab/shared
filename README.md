# shared

Shared assets used across iyulab repositories — workflows, scripts, brand assets, and agent skills.

## Structure

```
.github/workflows/   reusable workflows
scripts/             helper scripts, plus the checks CI runs
templates/           ready-to-copy files
assets/              company logo and icon files
skills/              agent-usable skills and guidance
claudedocs/          development notes for this repository - not a shared asset
```

## How to use

**Workflows** — reference directly from any iyulab repository:

```
uses: iyulab/shared/.github/workflows/<name>.yml@main
```

### What the reusable workflows own

A calling job accepts only a fixed set of keys, so most job-level settings can only exist inside the
workflow being called. These workflows own them on the caller's behalf:

| Concern | Owned by | What that means for the caller |
|---|---|---|
| Node.js baseline | `publish-npm.yml` | The `node_version` input carries the current baseline. Omit it and you follow the baseline; pin it and you stop following it. |
| Job timeout | both workflows | Declared in the called workflow. A calling job cannot set `timeout-minutes` at all — without it the job would inherit the 6-hour default. |
| Publish concurrency | `publish-npm.yml` | One publish at a time per calling repository. A re-pushed tag queues instead of racing. |
| Publish idempotency | `publish-npm.yml` | A version already present on the registry is skipped, not republished. |
| What ships | `publish-npm.yml` | The package is packed once, the tarball is checked, and that same tarball is published. Every path the packed `package.json` declares — `main`, `module`, `types`, `browser`, `bin`, and every `exports`/`imports` target, `*` patterns included — must be in it, or the publish stops. |
| Package-specific checks | the caller, via `verify_command` | Optional. Runs after the built-in check with `PACKED_DIR` (the extracted package root) and `PACKED_TARBALL` set; a non-zero exit stops the publish. Use it for invariants only your package knows, such as a side-effect module the sources register still being present in the build output. |

If one of these has to differ for your repository, it has to change in the workflow itself — for most
of them the calling side has no syntax to express it. See CONTRIBUTING.md for the rule and the full
list of keys a caller cannot use.

### What a caller cannot change

These are fixed in the called workflow. None of them can be overridden from the calling side today,
and none has an input:

| Fixed | Value | If you need it different |
|---|---|---|
| Runner | `ubuntu-latest` | `runs-on` is not a key a calling job may use. It would have to become an input. |
| Registry | the public npm registry | `publish-npm.yml` sets `registry-url` and publishes with `--access public`. Publishing elsewhere, or as a restricted package, is not supported. |
| Install strategy | `npm install` | Lockfiles are optional across consumers, so the workflow does not use `npm ci`. The npm cache is enabled only when a lock file is present. |
| Lifecycle scripts | `prepublishOnly`, then `prepack`/`prepare`/`postpack` | npm runs no package scripts when publishing a tarball, so `publish` and `postpublish` cannot run. A package that declares either is refused before packing rather than having them skipped silently. |

Say so on an issue if one of these blocks you — the shape of the fix (an input, or a second
workflow) depends on how many consumers need the variation.

### What `cleanup-expired-artifacts.yml` does not do

It removes the records GitHub leaves behind for artifacts whose retention period has passed. It
reclaims **no storage**: the content is deleted at expiry, and downloading an expired artifact
returns `410 Artifact has expired`. The API keeps reporting the original `size_in_bytes` on the
leftover record, so a byte count taken from it measures nothing.

To control artifact storage, set `retention-days` on upload. That is the only lever that changes how
much is stored.

**Templates** — copy a file from `templates/` into your repository and adjust as needed.

**Assets** — copy a file from `assets/` into your project, or reference one directly:

```
https://raw.githubusercontent.com/iyulab/shared/main/assets/brand/iyulab.svg
```

**Scripts** — called by the shared workflows, but can also be run standalone.

**Skills** — guidance for agents, meant to be read and interpreted by AI rather than humans.
[Learn more about skills here](https://agentskills.io/specification).
