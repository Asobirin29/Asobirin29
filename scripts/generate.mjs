#!/usr/bin/env node

import { resolve } from "node:path";
import { loadConfig, readFlag, repositoryRoot } from "./lib/config.mjs";
import { generateHeroAssets } from "./lib/hero.mjs";
import { generateProfileReadme } from "./lib/readme.mjs";
import { generateRadarAssets } from "./lib/radar.mjs";
import { generateVisualizerAssets } from "./lib/visualizer.mjs";
import { generatePacmanAssets } from "./lib/pacman.mjs";
import { execSync } from "node:child_process";
import { readFile } from "node:fs/promises";
import { existsSync } from "node:fs";

const source = readFlag("--source");
if (!source) {
  console.error("Usage: npm run generate -- --source /absolute/path/to/transparent-portrait.png");
  process.exit(1);
}

try {
  const config = await loadConfig(readFlag("--config"));
  const heroOutputDir = resolve(repositoryRoot, "assets/hero");
  console.log("Generating hero assets using Python generator...");
  execSync(`node scripts/generate-hero.mjs --source "${resolve(source)}" --config "${readFlag("--config") || resolve(repositoryRoot, "profile.config.json")}"`, { stdio: "inherit", cwd: repositoryRoot });
  
  const manifest = JSON.parse(await readFile(resolve(heroOutputDir, "manifest.json"), "utf8"));
  
  let manifestGreen = null;
  const greenConfigPath = resolve(repositoryRoot, "profile-green.config.json");
  if (existsSync(greenConfigPath)) {
    console.log("Generating green hero assets using Python generator...");
    execSync(`node scripts/generate-hero.mjs --source "${resolve(source)}" --config "${greenConfigPath}"`, { stdio: "inherit", cwd: repositoryRoot });
    manifestGreen = JSON.parse(await readFile(resolve(heroOutputDir, "manifest.json"), "utf8"));
  }
  await generateRadarAssets({
    config,
    outputDirectory: resolve(repositoryRoot, "assets/visuals")
  });
  await generateVisualizerAssets({
    config,
    outputDirectory: resolve(repositoryRoot, "assets/visuals")
  });
  await generatePacmanAssets({
    config,
    outputDirectory: resolve(repositoryRoot, "assets/visuals")
  });
  await generateProfileReadme({ config, manifest, manifestGreen, readmePath: resolve(repositoryRoot, "README.md") });
  console.log(`Profile generated successfully (asset version ${manifest.version}).`);
} catch (error) {
  console.error(error.message);
  process.exitCode = 1;
}
