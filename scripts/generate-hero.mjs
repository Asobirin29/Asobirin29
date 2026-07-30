#!/usr/bin/env node

import { resolve } from "node:path";
import { execSync } from "node:child_process";
import { readFlag, repositoryRoot } from "./lib/config.mjs";

const source = readFlag("--source");
if (!source) {
  console.error("Usage: npm run generate:hero -- --source /absolute/path/to/transparent-portrait.png");
  process.exit(1);
}

try {
  const configPath = readFlag("--config") || resolve(repositoryRoot, "profile.config.json");
  const outputDir = resolve(repositoryRoot, "assets/hero");
  
  const pythonPath = resolve(repositoryRoot, ".venv", "Scripts", "python.exe");
  const command = `"${pythonPath}" scripts/generate_hero.py --config "${configPath}" --source "${resolve(source)}" --outdir "${outputDir}"`;
  execSync(command, { stdio: "inherit", cwd: repositoryRoot });
  
  console.log(`Generation complete.`);
} catch (error) {
  console.error("Failed to generate hero assets:", error.message);
  process.exitCode = 1;
}
