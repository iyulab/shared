import { readFile, writeFile } from "node:fs/promises";
import { join } from "node:path";
import { pathToFileURL } from "node:url";

const packageJsonPath = pathToFileURL(join(process.cwd(), "package.json"));
const packageJsonRaw = await readFile(packageJsonPath, "utf8");
const packageJson = JSON.parse(packageJsonRaw);

if (packageJson.exports === undefined) {
  console.log("No exports field found in package.json. Nothing to rewrite.");
  process.exit(0);
}

const rewriteValue = (value) => {
  if (typeof value === "string") {
    if (value.startsWith("./src/")) {
      return value.replace(/^\.\/src\//, "./dist/");
    }

    if (value.startsWith("src/")) {
      return value.replace(/^src\//, "./dist/");
    }

    return value;
  }

  if (Array.isArray(value)) {
    return value.map(rewriteValue);
  }

  if (value && typeof value === "object") {
    return Object.fromEntries(Object.entries(value).map(([key, child]) => [key, rewriteValue(child)]));
  }

  return value;
};

packageJson.exports = rewriteValue(packageJson.exports);

await writeFile(packageJsonPath, `${JSON.stringify(packageJson, null, 2)}\n`, "utf8");
console.log("Rewrote exports paths from src to dist where applicable.");