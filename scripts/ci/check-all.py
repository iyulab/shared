#!/usr/bin/env python3
"""Run every check this repository enforces.

This is the single entry point: CI runs this one command, and so should you before
pushing. Nothing lists the individual checks twice - the contract check runs first, then
every `test-*.py` beside this file, discovered rather than enumerated, so a new test file
is picked up by adding it.

    python3 scripts/ci/check-all.py

Run from the repository root. Exits non-zero if any check fails.
"""

import glob
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CONTRACT_CHECK = os.path.join(HERE, "check-workflows.py")


def discover():
    """The contract check first, then every test-*.py beside it, in a stable order."""
    checks = [CONTRACT_CHECK]
    checks.extend(sorted(glob.glob(os.path.join(HERE, "test-*.py"))))
    return checks


def main():
    checks = discover()
    if not os.path.isfile(CONTRACT_CHECK):
        sys.exit("cannot find {} - run this from the repository root".format(CONTRACT_CHECK))

    failed = []
    for check in checks:
        name = os.path.basename(check)
        print("\n=== {} ===".format(name), flush=True)
        result = subprocess.run([sys.executable, check])
        if result.returncode != 0:
            failed.append(name)

    print("\n" + "=" * 60)
    if failed:
        print("FAILED: {}".format(", ".join(failed)))
        return 1
    print("all {} check(s) passed".format(len(checks)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
