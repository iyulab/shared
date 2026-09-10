#!/usr/bin/env python3
"""Check this repository's workflow contract.

Run from the repository root. Verifies what CONTRIBUTING.md states:

  1. Every workflow and template file is valid YAML.
  2. Every job in .github/workflows/ declares a timeout-minutes bound. Without one
     the job inherits the 6-hour default, and a caller cannot override it.
  3. Template jobs stay callers: they call a reusable workflow and carry none of the
     keys a calling job cannot express.
  4. No absolute filesystem path, host address, or literal credential is committed.

Exits non-zero with one line per problem.
"""

import glob
import os
import re
import sys

try:
    import yaml
except ImportError:  # pragma: no cover - depends on the runner image
    sys.exit("PyYAML is required. On GitHub-hosted Ubuntu runners it is preinstalled.")

# Keys a job that calls a reusable workflow may declare. Anything else is a syntax
# error on the calling side, which is why the called workflow has to own it.
# GitHub extends this list occasionally - `cache-mode` was added after the first nine -
# so treat a "forbidden key" report on a key GitHub now accepts as a signal to re-read
# the reusable-workflow reference rather than to work around the checker.
CALLER_ALLOWED = frozenset(
    {
        "name",
        "uses",
        "with",
        "secrets",
        "needs",
        "if",
        "permissions",
        "strategy",
        "concurrency",
        "cache-mode",
    }
)

MAX_TIMEOUT_MINUTES = 60

LEAK_PATTERNS = [
    # A drive-letter path: one letter, a colon, then a separator. The lookbehind stops a
    # URL scheme from matching (the letter before the colon must not follow another
    # letter), and the lookahead stops a doubled separator such as a scheme's own.
    # Written without a literal example so this file does not match its own pattern.
    (r"(?<![A-Za-z])[A-Za-z]:[\\/](?![\\/])", "absolute filesystem path"),
    (r"\b(?:\d{1,3}\.){3}\d{1,3}\b", "literal IP address"),
    (r"\bnpm_[A-Za-z0-9]{20,}\b", "literal npm token"),
    (r"\bgh[pousr]_[A-Za-z0-9]{20,}\b", "literal GitHub token"),
]

WORKFLOW_GLOB = ".github/workflows/*.yml"
TEMPLATE_GLOB = "templates/*.yml"

# Delimit the CONTRIBUTING.md sentence that publishes the list above, so the two can be
# compared. If that wording changes, these change with it.
CALLER_LIST_SENTENCE = "A job that calls a reusable workflow accepts only"
CALLER_LIST_END = "Every other job-level key"

# The self-test plants each pattern above on purpose, so scanning it reports every one of
# them. Its values are all documentation-range placeholders (RFC 5737 addresses, obviously
# fake tokens) and it ships no real configuration, so excluding it costs no coverage.
LEAK_SCAN_EXCLUDED = frozenset({"scripts/ci/test-check-workflows.py"})


def check(root="."):
    """Return (problems, counts) for the repository rooted at `root`."""
    problems = []
    counts = {"workflows": 0, "jobs": 0, "templates": 0}

    def rel(path):
        return os.path.relpath(path, root).replace(os.sep, "/")

    def load(path):
        try:
            with open(path, encoding="utf-8") as handle:
                return yaml.safe_load(handle)
        except yaml.YAMLError as error:
            problems.append("{}: not valid YAML - {}".format(rel(path), error))
            return None

    for path in sorted(glob.glob(os.path.join(root, WORKFLOW_GLOB))):
        document = load(path)
        if document is None:
            continue
        counts["workflows"] += 1

        # Without a permissions block the job takes whatever the calling repository grants
        # by default, which is the opposite of least privilege for a workflow other repos
        # run. Declaring it at either level is fine; declaring it nowhere is not.
        jobs = document.get("jobs") or {}
        if "permissions" not in document and not all("permissions" in job for job in jobs.values()):
            problems.append(
                "{}: no permissions declared. Without it the job inherits the calling "
                "repository's default token scopes (see CONTRIBUTING.md).".format(rel(path))
            )

        for job_id, job in jobs.items():
            counts["jobs"] += 1
            if "uses" in job:
                # A calling job cannot declare a timeout; the called workflow owns it.
                continue

            timeout = job.get("timeout-minutes")
            if timeout is None:
                problems.append(
                    "{}: job '{}' has no timeout-minutes. Without one it inherits the 6-hour "
                    "default and no caller can override it (see CONTRIBUTING.md).".format(rel(path), job_id)
                )
            elif isinstance(timeout, bool) or not isinstance(timeout, int):
                problems.append(
                    "{}: job '{}' timeout-minutes must be a number, got {!r}.".format(rel(path), job_id, timeout)
                )
            elif not 1 <= timeout <= MAX_TIMEOUT_MINUTES:
                problems.append(
                    "{}: job '{}' timeout-minutes is {}; expected 1..{}.".format(
                        rel(path), job_id, timeout, MAX_TIMEOUT_MINUTES
                    )
                )

    for path in sorted(glob.glob(os.path.join(root, TEMPLATE_GLOB))):
        document = load(path)
        if document is None:
            continue
        counts["templates"] += 1

        for job_id, job in (document.get("jobs") or {}).items():
            if "uses" not in job:
                problems.append("{}: job '{}' does not call a reusable workflow.".format(rel(path), job_id))
                continue
            forbidden = sorted(set(job) - CALLER_ALLOWED)
            if forbidden:
                problems.append(
                    "{}: job '{}' declares {}, which a calling job cannot express. Those settings "
                    "belong in the called workflow.".format(rel(path), job_id, forbidden)
                )

    # CONTRIBUTING.md publishes the same allowed-key list this file enforces. They drifted
    # apart once already, when GitHub added a key: the prose stayed stale and the checker
    # would have rejected a legal template. Compare them instead of trusting them to agree.
    contributing = os.path.join(root, "CONTRIBUTING.md")
    if os.path.isfile(contributing):
        with open(contributing, encoding="utf-8") as handle:
            prose = handle.read()
        start = prose.find(CALLER_LIST_SENTENCE)
        end = prose.find(CALLER_LIST_END, start + 1)
        if start == -1 or end == -1:
            problems.append(
                "CONTRIBUTING.md: could not find the allowed-key sentence (expected it to start "
                "{!r} and to be followed by {!r}). If the wording changed, update "
                "CALLER_LIST_SENTENCE/CALLER_LIST_END in scripts/ci/check-workflows.py to "
                "match.".format(CALLER_LIST_SENTENCE, CALLER_LIST_END)
            )
        else:
            documented = set(re.findall(r"`([a-z-]+)`", prose[start:end]))
            if documented != set(CALLER_ALLOWED):
                problems.append(
                    "CONTRIBUTING.md lists the caller-allowed keys as {}, but "
                    "scripts/ci/check-workflows.py enforces {}. They have to say the same "
                    "thing.".format(sorted(documented), sorted(CALLER_ALLOWED))
                )

    scanned = set(glob.glob(os.path.join(root, WORKFLOW_GLOB)))
    scanned |= set(glob.glob(os.path.join(root, TEMPLATE_GLOB)))
    scanned |= set(glob.glob(os.path.join(root, "scripts", "**", "*"), recursive=True))
    scanned |= set(glob.glob(os.path.join(root, "skills", "**", "*"), recursive=True))
    scanned |= {os.path.join(root, name) for name in ("README.md", "CONTRIBUTING.md")}

    for path in sorted(scanned):
        if not os.path.isfile(path) or rel(path) in LEAK_SCAN_EXCLUDED:
            continue
        try:
            with open(path, encoding="utf-8") as handle:
                text = handle.read()
        except (OSError, UnicodeDecodeError):
            continue
        for pattern, label in LEAK_PATTERNS:
            for match in re.finditer(pattern, text):
                problems.append("{}: contains a {} ({!r}).".format(rel(path), label, match.group(0)))

    return problems, counts


def main():
    problems, counts = check(".")
    print(
        "checked {} workflow file(s), {} job(s), {} template(s)".format(
            counts["workflows"], counts["jobs"], counts["templates"]
        )
    )
    if problems:
        print("\n{} problem(s):".format(len(problems)), file=sys.stderr)
        for problem in problems:
            print("  - {}".format(problem), file=sys.stderr)
        return 1
    print("workflow contract OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
