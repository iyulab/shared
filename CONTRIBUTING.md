# Contributing

Before pushing, run the checks CI runs:

```
python3 scripts/ci/check-all.py
```

It needs Python with PyYAML, plus `bash` and `node` for the shared-script tests.

- Place reusable workflows under .github/workflows/.
- Move non-trivial workflow logic into scripts/.
- Add a flat YAML file to templates/ when a workflow is meant to be consumed by other repositories.
- Store company assets under assets/.

## Reusable workflows

A job that calls a reusable workflow accepts only `name`, `uses`, `with`, `secrets`, `needs`,
`if`, `permissions`, `strategy`, `concurrency`, and `cache-mode`. Every other job-level key —
`timeout-minutes`, `continue-on-error`, `env`, `defaults`, `runs-on`, `container`, `services` — is a
syntax error on the calling side. A consumer can neither supply it nor override it.

GitHub extends the allowed list from time to time; `cache-mode` joined it after the original nine.
`scripts/ci/check-workflows.py` enforces the same list, so when GitHub adds a key, both this
paragraph and that file change together.

So each of those keys is declared here or nowhere. Where one is missing, the GitHub default applies
and no consumer can change it. Declare the bound instead of inheriting the default:

- `timeout-minutes` on every job. Without it the default is 6 hours.
- Anything else from that list the workflow actually depends on.

Declare `permissions` too, narrowed to what the workflow actually uses. It is not on the forbidden
list — a caller *can* set it — but leaving it out means the job runs with whatever the calling
repository grants by default, which is the wrong default for a workflow other repositories run.

Prefer a fixed value over an input: an input is only worth adding once consumers need to vary it,
and a caller that passes nothing cannot drift from the baseline. Keep the reason in a comment beside
the value so a later edit does not drop it for lack of one.
