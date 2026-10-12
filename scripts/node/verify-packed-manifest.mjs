// Verify that every path the packed package.json points at is present in the tarball.
//
// The manifest is read from the extracted tarball, not from the working tree: what is
// checked is what a consumer installs. A build or a `files` glob that drops a module
// otherwise ships unnoticed, because nothing before `npm publish` looks at the artifact.
//
// Reads the extracted package root from PACKED_DIR (the directory holding the packed
// package.json). Exits non-zero, listing every unresolved entry point, if any is missing.

import { readdir, readFile } from "node:fs/promises";
import { join, posix } from "node:path";

const packedDir = process.env.PACKED_DIR;

if (!packedDir) {
  console.error("PACKED_DIR is not set. Pack the package before verifying it.");
  process.exit(1);
}

const listFiles = async (root) => {
  const files = new Set();
  const walk = async (relative) => {
    for (const entry of await readdir(join(root, relative), { withFileTypes: true })) {
      const child = relative ? `${relative}/${entry.name}` : entry.name;
      if (entry.isDirectory()) {
        await walk(child);
      } else {
        files.add(child);
      }
    }
  };
  await walk("");
  return files;
};

let manifest;
try {
  manifest = JSON.parse(await readFile(join(packedDir, "package.json"), "utf8"));
} catch (error) {
  console.error(`Cannot read package.json from the packed tarball at ${packedDir}: ${error.message}`);
  process.exit(1);
}

const files = await listFiles(packedDir);

// Package-relative path without the leading "./", or null when the target leaves the
// package root and so can never be inside the tarball.
const normalize = (target) => {
  const joined = posix.normalize(target.replace(/\\/g, "/"));
  if (joined.startsWith("../") || joined === ".." || posix.isAbsolute(joined)) {
    return null;
  }
  return joined.replace(/^\.\//, "");
};

const isDirectoryPrefix = (prefix) => [...files].some((file) => file.startsWith(prefix));

// How each field is resolved, mirroring the tool that reads it:
//   exact  - `exports`/`imports` targets and `bin`: Node and npm take the path verbatim.
//   legacy - `main`/`module`/`browser`: CommonJS-style lookup tries extensions and index files.
//   types  - `types`/`typings`: TypeScript also accepts the path without its `.d.ts`.
const CANDIDATES = {
  exact: (path) => [path],
  legacy: (path) => [
    path,
    ...[".js", ".json", ".node"].map((ext) => path + ext),
    ...["index.js", "index.json", "index.node"].map((index) => posix.join(path, index)),
  ],
  types: (path) => [path, `${path}.d.ts`, posix.join(path, "index.d.ts")],
};

const resolves = (target, mode) => {
  const path = normalize(target);
  if (path === null) {
    return false;
  }

  // A subpath pattern: Node substitutes any string, slashes included, for "*".
  if (path.includes("*")) {
    const escaped = path.split("*").map((part) => part.replace(/[.+?^${}()|[\]\\]/g, "\\$&"));
    const pattern = new RegExp(`^${escaped.join(".+")}$`);
    return [...files].some((file) => pattern.test(file));
  }

  // A trailing-slash folder mapping (deprecated, but still resolved by Node).
  if (target.endsWith("/")) {
    return isDirectoryPrefix(`${path.replace(/\/$/, "")}/`);
  }

  return CANDIDATES[mode](path).some((candidate) => files.has(candidate));
};

const entries = [];

const addString = (field, value, mode) => {
  if (typeof value === "string" && value !== "") {
    entries.push({ field, target: value, mode });
  }
};

// Walk a conditional/subpath map. `null` targets explicitly block a subpath and are
// skipped; arrays are fallback lists, and every listed target has to exist to be useful.
// A target that does not start with "." names another package (`imports` allows that),
// so only package-relative targets are checked.
const addTargets = (field, value) => {
  if (typeof value === "string") {
    if (value.startsWith(".")) {
      entries.push({ field, target: value, mode: "exact" });
    }
  } else if (Array.isArray(value)) {
    value.forEach((child, index) => addTargets(`${field}[${index}]`, child));
  } else if (value && typeof value === "object") {
    for (const [key, child] of Object.entries(value)) {
      addTargets(`${field}[${JSON.stringify(key)}]`, child);
    }
  }
};

addString("main", manifest.main, "legacy");
addString("module", manifest.module, "legacy");
addString("types", manifest.types, "types");
addString("typings", manifest.typings, "types");

if (typeof manifest.browser === "string") {
  addString("browser", manifest.browser, "legacy");
} else if (manifest.browser && typeof manifest.browser === "object") {
  // The object form maps module paths to replacements; `false` means "omit", and a
  // bare name means another package. Only package-relative replacements are files.
  for (const [key, value] of Object.entries(manifest.browser)) {
    if (typeof value === "string" && value.startsWith(".")) {
      addString(`browser[${JSON.stringify(key)}]`, value, "legacy");
    }
  }
}

if (typeof manifest.bin === "string") {
  addString("bin", manifest.bin, "exact");
} else if (manifest.bin && typeof manifest.bin === "object") {
  for (const [name, value] of Object.entries(manifest.bin)) {
    addString(`bin[${JSON.stringify(name)}]`, value, "exact");
  }
}

addTargets("exports", manifest.exports);
addTargets("imports", manifest.imports);

const missing = entries.filter((entry) => !resolves(entry.target, entry.mode));

if (missing.length > 0) {
  console.error(
    `${missing.length} of ${entries.length} entry point(s) declared by the packed package.json ` +
      "are not in the tarball:"
  );
  for (const { field, target } of missing) {
    console.error(`  - ${field}: ${target}`);
  }
  console.error(
    "The build did not produce these files, or the `files` field left them out. " +
      "Publishing would ship a package whose declared entry points do not resolve."
  );
  process.exit(1);
}

console.log(
  `Verified ${entries.length} entry point(s) declared by the packed package.json against ` +
    `${files.size} packed file(s).`
);
