#!/usr/bin/env bash

set -euo pipefail

tag_name="${GITHUB_REF_NAME:-}"

if [[ -z "$tag_name" ]]; then
  echo "GITHUB_REF_NAME is not set. This workflow must run from a Git tag." >&2
  exit 1
fi

if [[ ! "$tag_name" =~ ^v[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
  echo "Invalid tag '$tag_name'. Expected a tag in the form v1.2.3." >&2
  exit 1
fi

if [[ -z "${GITHUB_ENV:-}" ]]; then
  echo "GITHUB_ENV is not set, so TAG_VERSION cannot be exported." >&2
  exit 1
fi

tag_version="${tag_name#v}"
echo "TAG_VERSION=$tag_version" >> "$GITHUB_ENV"
echo "Validated tag '$tag_name' and exported TAG_VERSION=$tag_version"