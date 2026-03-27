import { readFile } from "node:fs/promises";
import { join } from "node:path";
import { pathToFileURL } from "node:url";

const packageJsonPath = pathToFileURL(join(process.cwd(), "package.json"));
const packageJsonRaw = await readFile(packageJsonPath, "utf8");
const packageJson = JSON.parse(packageJsonRaw);
const packageVersion = packageJson.version;
const tagVersion = process.env.TAG_VERSION;

if (!tagVersion) {
  console.error("TAG_VERSION is not set. Run tag validation before version verification.");
  process.exit(1);
}

if (!packageVersion) {
  console.error("package.json does not contain a version field.");
  process.exit(1);
}

if (packageVersion !== tagVersion) {
  console.error(
    `Version mismatch: tag version is ${tagVersion}, but package.json version is ${packageVersion}.`
  );
  process.exit(1);
}

console.log(`Verified package.json version ${packageVersion} matches tag version ${tagVersion}.`);