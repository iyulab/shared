#!/usr/bin/env python3
"""Contract tests for the scripts the reusable workflows execute.

These three scripts run inside every consuming repository's publish, so a regression
here breaks publishing everywhere at once. Each case runs the real script the way the
workflow does - same environment variables, same working directory - and asserts the
exit status and the observable effect.

Run from the repository root.
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile

VALIDATE_TAG = os.path.join("scripts", "github", "validate-tag.sh")
VERIFY_VERSION = os.path.join("scripts", "node", "verify-package-version.mjs")
REWRITE_EXPORTS = os.path.join("scripts", "node", "rewrite-exports-src-to-dist.mjs")

failures = []
passes = 0


def report(name, ok, detail=""):
    global passes
    if ok:
        passes += 1
        print("  ok   {}".format(name))
    else:
        failures.append(name)
        print("  FAIL {}{}".format(name, " - " + detail if detail else ""))


def run(command, cwd=None, env=None):
    environment = dict(os.environ)
    # Keep an inherited value from leaking into a case that means to unset it.
    for key in ("TAG_VERSION", "GITHUB_REF_NAME", "GITHUB_ENV"):
        environment.pop(key, None)
    environment.update(env or {})
    return subprocess.run(
        command, cwd=cwd, env=environment, capture_output=True, text=True, encoding="utf-8"
    )


# --------------------------------------------------------------------------- validate-tag.sh

def test_validate_tag(bash):
    script = os.path.abspath(VALIDATE_TAG)

    def call(tag, with_github_env=True):
        workspace = tempfile.mkdtemp(prefix="tag-")
        env_file = os.path.join(workspace, "github_env")
        open(env_file, "w", encoding="utf-8").close()
        env = {}
        if tag is not None:
            env["GITHUB_REF_NAME"] = tag
        if with_github_env:
            env["GITHUB_ENV"] = env_file
        result = run([bash, script], cwd=workspace, env=env)
        with open(env_file, encoding="utf-8") as handle:
            exported = handle.read()
        shutil.rmtree(workspace, ignore_errors=True)
        return result.returncode, exported

    code, exported = call("v1.2.3")
    report(
        "validate-tag: v1.2.3 is accepted and exports TAG_VERSION",
        code == 0 and exported.strip() == "TAG_VERSION=1.2.3",
        "exit={} exported={!r}".format(code, exported),
    )

    code, exported = call("v10.20.30")
    report(
        "validate-tag: multi-digit components are accepted",
        code == 0 and exported.strip() == "TAG_VERSION=10.20.30",
        "exit={} exported={!r}".format(code, exported),
    )

    for tag, why in [
        ("1.2.3", "no v prefix"),
        ("v1.2", "missing patch component"),
        ("v1.2.3.4", "extra component"),
        ("vnot-a-version", "not numeric"),
        ("", "empty"),
    ]:
        code, exported = call(tag)
        report(
            "validate-tag: rejects {!r} ({})".format(tag, why),
            code != 0 and exported == "",
            "exit={} exported={!r}".format(code, exported),
        )

    # Pinned deliberately: the publish step runs `npm publish` with no --tag, so a
    # prerelease that got through would take the `latest` dist-tag. Rejecting it here is
    # the current contract, not an oversight.
    code, _ = call("v1.2.3-beta.1")
    report("validate-tag: rejects a prerelease tag (no dist-tag handling downstream)", code != 0)

    code, _ = call(None)
    report("validate-tag: fails when GITHUB_REF_NAME is unset", code != 0)

    code, _ = call("v1.2.3", with_github_env=False)
    report("validate-tag: fails when GITHUB_ENV is unset", code != 0)


# ------------------------------------------------------------------- verify-package-version.mjs

def test_verify_version(node):
    script = os.path.abspath(VERIFY_VERSION)

    def call(package_json, tag_version):
        workspace = tempfile.mkdtemp(prefix="verify-")
        if package_json is not None:
            with open(os.path.join(workspace, "package.json"), "w", encoding="utf-8") as handle:
                json.dump(package_json, handle)
        env = {"TAG_VERSION": tag_version} if tag_version is not None else {}
        result = run([node, script], cwd=workspace, env=env)
        shutil.rmtree(workspace, ignore_errors=True)
        return result.returncode

    report(
        "verify-version: matching version passes",
        call({"name": "p", "version": "1.2.3"}, "1.2.3") == 0,
    )
    report(
        "verify-version: mismatched version fails",
        call({"name": "p", "version": "1.2.4"}, "1.2.3") != 0,
    )
    report(
        "verify-version: fails when TAG_VERSION is unset",
        call({"name": "p", "version": "1.2.3"}, None) != 0,
    )
    report(
        "verify-version: fails when package.json has no version",
        call({"name": "p"}, "1.2.3") != 0,
    )


# --------------------------------------------------------- rewrite-exports-src-to-dist.mjs

def test_rewrite_exports(node):
    script = os.path.abspath(REWRITE_EXPORTS)

    def call(package_json):
        workspace = tempfile.mkdtemp(prefix="rewrite-")
        path = os.path.join(workspace, "package.json")
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(package_json, handle)
        result = run([node, script], cwd=workspace)
        with open(path, encoding="utf-8") as handle:
            after = json.load(handle)
        shutil.rmtree(workspace, ignore_errors=True)
        return result.returncode, after

    code, after = call({"name": "p", "exports": "./src/index.js"})
    report(
        "rewrite-exports: './src/' prefix becomes './dist/'",
        code == 0 and after["exports"] == "./dist/index.js",
        repr(after.get("exports")),
    )

    code, after = call({"name": "p", "exports": "src/index.js"})
    report(
        "rewrite-exports: bare 'src/' prefix is normalized to './dist/'",
        code == 0 and after["exports"] == "./dist/index.js",
        repr(after.get("exports")),
    )

    code, after = call(
        {
            "name": "p",
            "exports": {
                ".": {"types": "./src/index.d.ts", "import": "./src/index.js"},
                "./sub": {"import": ["./src/a.js", "./src/b.js"]},
            },
        }
    )
    rewritten = (
        after["exports"]["."]["types"] == "./dist/index.d.ts"
        and after["exports"]["."]["import"] == "./dist/index.js"
        and after["exports"]["./sub"]["import"] == ["./dist/a.js", "./dist/b.js"]
    )
    report(
        "rewrite-exports: nested objects and arrays are rewritten recursively",
        code == 0 and rewritten,
        json.dumps(after.get("exports")),
    )

    code, after = call({"name": "p", "exports": {"./keep": "./lib/index.js"}})
    report(
        "rewrite-exports: a path outside src/ is left alone",
        code == 0 and after["exports"]["./keep"] == "./lib/index.js",
        json.dumps(after.get("exports")),
    )

    code, after = call({"name": "p", "version": "1.0.0"})
    report(
        "rewrite-exports: no exports field is a no-op that still succeeds",
        code == 0 and "exports" not in after and after["version"] == "1.0.0",
        json.dumps(after),
    )

    # The script only rewrites `exports`. Pinned so that if `main`/`types` ever need the
    # same treatment, the change is a deliberate one rather than a silent gap.
    code, after = call({"name": "p", "main": "./src/index.js", "exports": "./src/index.js"})
    report(
        "rewrite-exports: 'main' is intentionally untouched (exports only)",
        code == 0 and after["main"] == "./src/index.js" and after["exports"] == "./dist/index.js",
        json.dumps(after),
    )


def main():
    bash = shutil.which("bash")
    node = shutil.which("node")
    if not bash:
        sys.exit("bash not found; it is required to test validate-tag.sh")
    if not node:
        sys.exit("node not found; it is required to test the .mjs scripts")

    test_validate_tag(bash)
    test_verify_version(node)
    test_rewrite_exports(node)

    print("\n{} case(s), {} failure(s)".format(passes + len(failures), len(failures)))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
