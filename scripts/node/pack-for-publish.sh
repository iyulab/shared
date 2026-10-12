#!/usr/bin/env bash

# Pack the package in the current directory and extract the tarball, so the steps that
# follow verify - and then publish - exactly the artifact that ships.
#
# Exports to GITHUB_ENV:
#   PACKED_TARBALL  the .tgz that the publish step uploads
#   PACKED_DIR      the extracted package root (the packed package.json sits at its top)
#
# Lifecycle scripts: `npm publish <tarball>` runs none of the package's scripts - npm
# runs them only when publishing a directory. Packing here runs prepack/prepare/postpack,
# and prepublishOnly is run first so the pre-publish order matches a directory publish.
# `publish`/`postpublish` cannot be honored once the publish is a tarball, so a package
# that declares them is refused rather than having them skipped without a word.

set -euo pipefail

if [[ -z "${GITHUB_ENV:-}" ]]; then
  echo "GITHUB_ENV is not set, so PACKED_TARBALL and PACKED_DIR cannot be exported." >&2
  exit 1
fi

if [[ -z "${RUNNER_TEMP:-}" ]]; then
  echo "RUNNER_TEMP is not set, so there is nowhere to put the tarball." >&2
  exit 1
fi

unsupported=$(node -e '
  const scripts = require("./package.json").scripts || {};
  console.log(["publish", "postpublish"].filter((name) => scripts[name]).join(" "));
')
if [[ -n "$unsupported" ]]; then
  echo "package.json declares lifecycle script(s) this workflow cannot run: $unsupported" >&2
  echo "The workflow publishes the verified tarball, and npm runs no package scripts for a" >&2
  echo "tarball publish. Move that work to prepublishOnly (before) or out of the package." >&2
  exit 1
fi

npm run prepublishOnly --if-present

destination="$RUNNER_TEMP/npm-pack"
rm -rf "$destination"
mkdir -p "$destination/extracted"

npm pack --pack-destination "$destination"

shopt -s nullglob
tarballs=("$destination"/*.tgz)
if [[ ${#tarballs[@]} -ne 1 ]]; then
  echo "Expected npm pack to write exactly one tarball to $destination, found ${#tarballs[@]}." >&2
  exit 1
fi
tarball="${tarballs[0]}"

# Extract from inside the destination with relative names: GNU tar reads a colon in an
# archive argument as a remote host, which a drive-letter path would trip.
(cd "$destination" && tar -xzf "$(basename "$tarball")" -C extracted)

if [[ ! -f "$destination/extracted/package/package.json" ]]; then
  echo "The tarball has no package/package.json - it is not an npm package tarball." >&2
  exit 1
fi

echo "PACKED_TARBALL=$tarball" >> "$GITHUB_ENV"
echo "PACKED_DIR=$destination/extracted/package" >> "$GITHUB_ENV"
echo "Packed $(basename "$tarball") and extracted it for verification."
