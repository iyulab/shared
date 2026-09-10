#!/usr/bin/env python3
"""Self-test for check-workflows.py.

A check that has only ever been seen to pass proves nothing. Each case below plants a
regression the checker is supposed to catch, and asserts it is caught. Run from the
repository root; the real workflow and template files are the fixtures, copied into a
temporary tree and then mutated.
"""

import os
import shutil
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from importlib import import_module

checker = import_module("check-workflows")


def build(root):
    """Copy the repository's real workflow, template and contributing files into `root`."""
    os.makedirs(os.path.join(root, ".github", "workflows"))
    os.makedirs(os.path.join(root, "templates"))
    os.makedirs(os.path.join(root, "scripts"))
    for name in os.listdir(".github/workflows"):
        shutil.copy(os.path.join(".github/workflows", name), os.path.join(root, ".github", "workflows", name))
    for name in os.listdir("templates"):
        shutil.copy(os.path.join("templates", name), os.path.join(root, "templates", name))
    open(os.path.join(root, "README.md"), "w", encoding="utf-8").close()
    # The real one: the checker compares its published key list against its own.
    shutil.copy("CONTRIBUTING.md", os.path.join(root, "CONTRIBUTING.md"))


def write(root, relative_path, text):
    path = os.path.join(root, relative_path)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


def edit(root, relative_path, old, new):
    path = os.path.join(root, relative_path)
    with open(path, encoding="utf-8") as handle:
        text = handle.read()
    if old not in text:
        raise AssertionError("fixture edit found no '{}' in {}".format(old, relative_path))
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text.replace(old, new))


CI = ".github/workflows/ci.yml"

# (name, mutation, expected problem count) - 0 means the checker must stay quiet.
CASES = [
    ("clean tree", lambda root: None, 0),
    ("job without timeout-minutes", lambda root: edit(root, CI, "\n    timeout-minutes: 10\n", "\n"), 1),
    ("timeout-minutes as a string", lambda root: edit(root, CI, "timeout-minutes: 10", 'timeout-minutes: "10"'), 1),
    ("timeout-minutes as a boolean", lambda root: edit(root, CI, "timeout-minutes: 10", "timeout-minutes: true"), 1),
    ("timeout-minutes above the ceiling", lambda root: edit(root, CI, "timeout-minutes: 10", "timeout-minutes: 600"), 1),
    ("timeout-minutes of zero", lambda root: edit(root, CI, "timeout-minutes: 10", "timeout-minutes: 0"), 1),
    (
        "template caller declaring a forbidden key",
        lambda root: edit(root, "templates/publish-npm.yml", "\n  publish:\n", "\n  publish:\n    timeout-minutes: 20\n"),
        1,
    ),
    # cache-mode was added to the caller-allowed list after the original nine keys. A
    # template using it must not be reported, or CI would block a legal workflow.
    (
        "template caller may use cache-mode",
        lambda root: edit(root, "templates/publish-npm.yml", "\n  publish:\n", "\n  publish:\n    cache-mode: read-only\n"),
        0,
    ),
    # The published list and the enforced list drifted apart once; these keep them tied.
    (
        "CONTRIBUTING dropping a key from the published list is caught",
        lambda root: edit(root, "CONTRIBUTING.md", "`concurrency`, and `cache-mode`", "and `concurrency`"),
        1,
    ),
    (
        "CONTRIBUTING wording change is reported, not silently skipped",
        lambda root: edit(root, "CONTRIBUTING.md", "A job that calls a reusable workflow accepts only", "A caller may declare only"),
        1,
    ),
    (
        "workflow without a permissions block is caught",
        lambda root: edit(root, CI, "\npermissions:\n  contents: read\n", "\n"),
        1,
    ),
    ("invalid YAML", lambda root: write(root, ".github/workflows/broken.yml", "jobs:\n  a:\n   - [unclosed\n"), 1),
    ("backslash drive path", lambda root: write(root, "scripts/leak.sh", "echo " + "C:" + chr(92) + "Users\n"), 1),
    ("forward-slash drive path", lambda root: write(root, "scripts/leak.sh", "echo C:/Users/someone\n"), 1),
    ("literal IP address", lambda root: write(root, "scripts/leak.sh", "connect 203.0.113.42\n"), 1),
    ("literal npm token", lambda root: write(root, "scripts/leak.sh", "T=npm_abcdefghijklmnopqrstuvwxyz012345\n"), 1),
    ("literal GitHub token", lambda root: write(root, "scripts/leak.sh", "T=ghp_abcdefghijklmnopqrstuvwxyz012345\n"), 1),
    ("leak inside skills/ is scanned too", lambda root: write(root, "skills/x/SKILL.md", "host 203.0.113.9\n"), 1),
    ("URL is not a drive path", lambda root: write(root, "scripts/ok.sh", "url=https://registry.npmjs.org\n"), 0),
    ("action ref is not a drive path", lambda root: write(root, "scripts/ok.sh", "uses: actions/checkout@v5\n"), 0),
]


def main():
    failures = 0
    for name, mutate, expected in CASES:
        root = tempfile.mkdtemp(prefix="wfcheck-")
        try:
            build(root)
            mutate(root)
            problems, _ = checker.check(root)
            got = len(problems)
            if got == expected:
                print("  ok   {}".format(name))
            else:
                failures += 1
                print("  FAIL {} - expected {} problem(s), got {}".format(name, expected, got))
                for problem in problems:
                    print("         {}".format(problem))
        finally:
            shutil.rmtree(root, ignore_errors=True)

    print("\n{} case(s), {} failure(s)".format(len(CASES), failures))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
