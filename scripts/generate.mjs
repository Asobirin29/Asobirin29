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
  console.log("Generating hero assets using original JS generator...");
  const manifest = await generateHeroAssets({
    config,
    sourcePath: resolve(source),
    outputDirectory: heroOutputDir
  });
  
  


  // Generate About Me terminal (neon red)
  console.log("Generating About Me terminal (neon red)...");
  const pythonExe = resolve(repositoryRoot, ".venv/Scripts/python.exe");
  const configPath = readFlag("--config") || resolve(repositoryRoot, "profile.config.json");
  execSync(`"${pythonExe}" scripts/generate_about.py --config "${configPath}" --outdir "${heroOutputDir}"`, { stdio: "inherit", cwd: repositoryRoot });
  const aboutManifest = JSON.parse(await readFile(resolve(heroOutputDir, "about-manifest.json"), "utf8"));

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
  await generateProfileReadme({ config, manifest, aboutManifest, readmePath: resolve(repositoryRoot, "README.md") });
  console.log(`Profile generated successfully (asset version ${manifest.version}).`);
} catch (error) {
  console.error(error.message);
  process.exitCode = 1;
}
