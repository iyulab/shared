#!/usr/bin/env python3
"""Contract tests for the scripts the reusable workflows execute.

These scripts run inside every consuming repository's publish, so a regression
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
PACK_FOR_PUBLISH = os.path.join("scripts", "node", "pack-for-publish.sh")
VERIFY_PACKED = os.path.join("scripts", "node", "verify-packed-manifest.mjs")

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
    for key in ("TAG_VERSION", "GITHUB_REF_NAME", "GITHUB_ENV", "RUNNER_TEMP", "PACKED_DIR", "PACKED_TARBALL"):
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


def write_tree(root, files):
    """Create `files` ({relative path: text}) under `root`."""
    for relative, text in files.items():
        path = os.path.join(root, *relative.split("/"))
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(text)


# ------------------------------------------------------------ verify-packed-manifest.mjs

def test_verify_packed_manifest(node):
    script = os.path.abspath(VERIFY_PACKED)

    def call(manifest, files, packed_dir=True):
        workspace = tempfile.mkdtemp(prefix="packed-")
        write_tree(workspace, dict(files, **{"package.json": json.dumps(manifest)}))
        env = {"PACKED_DIR": workspace} if packed_dir else {}
        result = run([node, script], cwd=tempfile.gettempdir(), env=env)
        shutil.rmtree(workspace, ignore_errors=True)
        return result.returncode, result.stderr

    complete = {
        "name": "p",
        "main": "dist/index",
        "module": "./dist/index.js",
        "types": "./dist/index",
        "browser": {"./dist/node.js": "./dist/browser.js", "fs": False},
        "bin": {"p": "./bin/cli.js"},
        "exports": {
            ".": {"types": "./dist/index.d.ts", "import": "./dist/index.js"},
            "./sub/*": {"import": "./dist/sub/*.js"},
            "./assets/": "./dist/assets/",
            "./internal/*": None,
            "./package.json": "./package.json",
        },
        "imports": {"#dep": "some-package", "#util": "./dist/util.js"},
    }
    tree = {
        "dist/index.js": "",
        "dist/index.d.ts": "",
        "dist/browser.js": "",
        "dist/util.js": "",
        "dist/sub/deep/a.js": "",
        "dist/assets/logo.svg": "",
        "bin/cli.js": "",
    }
    code, stderr = call(complete, tree)
    report(
        "verify-packed: every declared entry point resolves (extensions, patterns, folders, null, bare names)",
        code == 0,
        stderr.strip(),
    )

    # The exact class this guards: the manifest still declares a module the tarball lost.
    dropped = dict(tree)
    del dropped["dist/index.js"]
    code, stderr = call(complete, dropped)
    report(
        "verify-packed: a declared module missing from the tarball fails and names the field",
        code != 0 and 'exports["."]["import"]: ./dist/index.js' in stderr and "module:" in stderr,
        stderr.strip(),
    )

    code, stderr = call({"name": "p", "exports": {"./sub/*": "./dist/sub/*.js"}}, {"dist/other.js": ""})
    report(
        "verify-packed: a subpath pattern that matches no packed file fails",
        code != 0 and "./dist/sub/*.js" in stderr,
        stderr.strip(),
    )

    # rewrite-exports only rewrites `exports`, so `main` can still name src/. The check
    # reads the packed manifest and so reports it instead of letting it ship.
    code, stderr = call({"name": "p", "main": "./src/index.js", "exports": "./dist/index.js"}, {"dist/index.js": ""})
    report(
        "verify-packed: a 'main' left pointing at unpacked sources fails",
        code != 0 and "main: ./src/index.js" in stderr,
        stderr.strip(),
    )

    code, stderr = call({"name": "p", "exports": "../outside.js"}, {"dist/index.js": ""})
    report("verify-packed: a target outside the package root fails", code != 0, stderr.strip())

    code, stderr = call({"name": "p", "bin": "./bin/cli"}, {"bin/cli.js": ""})
    report("verify-packed: 'bin' is taken verbatim (no extension lookup)", code != 0, stderr.strip())

    code, stderr = call({"name": "p", "version": "1.0.0"}, {"README.md": ""})
    report("verify-packed: a manifest declaring no entry points passes", code == 0, stderr.strip())

    code, _ = call({"name": "p"}, {}, packed_dir=False)
    report("verify-packed: fails when PACKED_DIR is unset", code != 0)


# ------------------------------------------------------------------- pack-for-publish.sh

def test_pack_for_publish(bash, node):
    script = os.path.abspath(PACK_FOR_PUBLISH)
    verify = os.path.abspath(VERIFY_PACKED)

    def call(manifest, files, with_runner_temp=True, with_github_env=True):
        workspace = tempfile.mkdtemp(prefix="pack-")
        package = os.path.join(workspace, "pkg")
        runner_temp = os.path.join(workspace, "runner-temp")
        os.makedirs(runner_temp)
        write_tree(package, dict(files, **{"package.json": json.dumps(manifest)}))
        env_file = os.path.join(workspace, "github_env")
        open(env_file, "w", encoding="utf-8").close()
        env = {}
        if with_runner_temp:
            env["RUNNER_TEMP"] = runner_temp
        if with_github_env:
            env["GITHUB_ENV"] = env_file
        result = run([bash, script], cwd=package, env=env)
        with open(env_file, encoding="utf-8") as handle:
            exported = dict(line.split("=", 1) for line in handle.read().splitlines() if "=" in line)
        return workspace, result, exported

    def packed_files(exported):
        root = exported.get("PACKED_DIR", "")
        found = set()
        for directory, _, names in os.walk(root):
            for name in names:
                found.add(os.path.relpath(os.path.join(directory, name), root).replace(os.sep, "/"))
        return found

    manifest = {
        "name": "fixture",
        "version": "1.0.0",
        "files": ["dist"],
        "exports": "./dist/index.js",
        # Proves the order: prepublishOnly has to run before the tarball is made, as it
        # would in a directory publish, or the file it writes could not be in it.
        "scripts": {"prepublishOnly": "node -e \"require('fs').writeFileSync('dist/stamp.txt', 'x')\""},
    }
    workspace, result, exported = call(manifest, {"dist/index.js": "", "src/index.ts": ""})
    files = packed_files(exported)
    tarball = exported.get("PACKED_TARBALL", "")
    report(
        "pack: exports PACKED_TARBALL and PACKED_DIR for the packed tarball",
        result.returncode == 0 and tarball.endswith("fixture-1.0.0.tgz") and os.path.isfile(tarball),
        "exit={} exported={!r} stderr={}".format(result.returncode, exported, result.stderr.strip()),
    )
    report(
        "pack: PACKED_DIR holds what npm packed, not the working tree",
        {"package.json", "dist/index.js"} <= files and "src/index.ts" not in files,
        repr(sorted(files)),
    )
    report("pack: prepublishOnly runs before the tarball is made", "dist/stamp.txt" in files, repr(sorted(files)))

    # The two steps together, the way the workflow runs them.
    verified = run([node, verify], env={"PACKED_DIR": exported.get("PACKED_DIR", "")})
    report("pack + verify: a complete package passes", verified.returncode == 0, verified.stderr.strip())
    shutil.rmtree(workspace, ignore_errors=True)

    # `files` leaves out a module the manifest exports - built locally, absent from the tarball.
    narrow = {"name": "fixture", "version": "1.0.0", "files": ["dist/index.js"], "exports": {".": "./dist/index.js", "./extra": "./dist/extra.js"}}
    workspace, result, exported = call(narrow, {"dist/index.js": "", "dist/extra.js": ""})
    verified = run([node, verify], env={"PACKED_DIR": exported.get("PACKED_DIR", "")})
    report(
        "pack + verify: a module built locally but left out of the tarball fails",
        result.returncode == 0 and verified.returncode != 0 and "./dist/extra.js" in verified.stderr,
        "pack exit={} verify exit={} {}".format(result.returncode, verified.returncode, verified.stderr.strip()),
    )
    shutil.rmtree(workspace, ignore_errors=True)

    refused = dict(manifest, scripts={"postpublish": "echo done"})
    workspace, result, exported = call(refused, {"dist/index.js": ""})
    report(
        "pack: refuses publish/postpublish scripts a tarball publish would skip",
        result.returncode != 0 and "postpublish" in result.stderr and not exported,
        "exit={} stderr={}".format(result.returncode, result.stderr.strip()),
    )
    shutil.rmtree(workspace, ignore_errors=True)

    workspace, result, _ = call(manifest, {"dist/index.js": ""}, with_runner_temp=False)
    report("pack: fails when RUNNER_TEMP is unset", result.returncode != 0)
    shutil.rmtree(workspace, ignore_errors=True)

    workspace, result, _ = call(manifest, {"dist/index.js": ""}, with_github_env=False)
    report("pack: fails when GITHUB_ENV is unset", result.returncode != 0)
    shutil.rmtree(workspace, ignore_errors=True)


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
    test_verify_packed_manifest(node)
    test_pack_for_publish(bash, node)

    print("\n{} case(s), {} failure(s)".format(passes + len(failures), len(failures)))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
