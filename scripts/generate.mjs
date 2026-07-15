#!/usr/bin/env node

import { resolve } from "node:path";
import { loadConfig, readFlag, repositoryRoot } from "./lib/config.mjs";
import { generateHeroAssets } from "./lib/hero.mjs";
import { generateProfileReadme } from "./lib/readme.mjs";
import { generateRadarAssets } from "./lib/radar.mjs";
import { generateVisualizerAssets } from "./lib/visualizer.mjs";
import { generatePacmanAssets } from "./lib/pacman.mjs";

const source = readFlag("--source");
if (!source) {
  console.error("Usage: npm run generate -- --source /absolute/path/to/transparent-portrait.png");
  process.exit(1);
}

try {
  const config = await loadConfig(readFlag("--config"));
  const manifest = await generateHeroAssets({
    config,
    sourcePath: resolve(source),
    outputDirectory: resolve(repositoryRoot, "assets/hero")
  });
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
  await generateProfileReadme({ config, manifest, readmePath: resolve(repositoryRoot, "README.md") });
  console.log(`Profile generated successfully (asset version ${manifest.version}).`);
} catch (error) {
  console.error(error.message);
  process.exitCode = 1;
}
