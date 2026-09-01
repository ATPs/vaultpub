import { spawnSync } from "node:child_process";
import { cpSync, existsSync, mkdirSync, rmSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const frontendDir = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const nodeModulesDir = resolve(frontendDir, "node_modules");
const hasLockfile = existsSync(resolve(frontendDir, "package-lock.json"));
const outputDir = resolve(frontendDir, "../src/vaultpub/django_app/static/vaultpub");
const shell = process.platform === "win32";

function run(command, args) {
  const result = spawnSync(command, args, {
    cwd: frontendDir,
    stdio: "inherit",
    shell,
  });

  if (result.error) {
    throw result.error;
  }
  if (result.status !== 0) {
    throw new Error(`${command} ${args.join(" ")} failed with exit code ${result.status}`);
  }
}

try {
  run("npm", hasLockfile ? ["ci"] : ["install", "--no-package-lock"]);
  run("npm", ["run", "build:bundle"]);
  mkdirSync(resolve(outputDir, "assets"), { recursive: true });
  cpSync(
    resolve(nodeModulesDir, "reveal.js/dist/theme"),
    resolve(outputDir, "assets/reveal-themes"),
    { recursive: true },
  );
} finally {
  rmSync(nodeModulesDir, { recursive: true, force: true });
}
