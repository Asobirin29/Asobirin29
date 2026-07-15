import { mkdir, writeFile } from "node:fs/promises";
import { resolve } from "node:path";
import { paletteDefinitions } from "./hero.mjs";

export function createPacmanSvg(colors) {
  const width = 800;
  const height = 60;
  
  // Mouth animation values for Pacman (using path data)
  const mouthOpen = "M 30,30 L 50,15 A 25,25 0 1,1 50,45 Z";
  const mouthClosed = "M 30,30 L 55,30 A 25,25 0 1,1 55,30 Z";
  
  return `<svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${height}" viewBox="0 0 ${width} ${height}">
  <defs>
    <style>
      .bg { fill: ${colors.panel}; fill-opacity: 0.1; }
      .pacman { fill: #facc15; }
      .ghost-body { fill: #f43f5e; }
      .ghost-eyes { fill: #ffffff; }
      .ghost-pupil { fill: #1e3a8a; }
      .dot { fill: #fbbf24; }
      .text { font-family: 'Courier New', Consolas, monospace; font-size: 14px; fill: ${colors.title}; font-weight: bold; }
    </style>
  </defs>
  
  <rect width="${width}" height="${height}" rx="10" class="bg" />
  <text x="15" y="35" class="text">L I F E : ❤️ ❤️ ❤️</text>
  <text x="${width - 150}" y="35" class="text">S C O R E : 9999</text>

  <!-- Dots -->
  <g>
    ${Array.from({ length: 15 }).map((_, i) => `<circle cx="${300 + i * 30}" cy="30" r="4" class="dot">
      <animate attributeName="opacity" values="1;1;0;0" keyTimes="0;0.5;0.51;1" dur="4s" begin="${(i * 4 / 15).toFixed(2)}s" repeatCount="indefinite" />
    </circle>`).join('\n    ')}
  </g>

  <!-- Pacman Group moving right -->
  <g>
    <animateTransform attributeName="transform" type="translate" values="250,0; ${width - 250},0; 250,0" keyTimes="0;0.5;1" dur="8s" repeatCount="indefinite" />
    
    <!-- Pacman SVG -->
    <path class="pacman" d="${mouthOpen}">
      <animate attributeName="d" values="${mouthOpen}; ${mouthClosed}; ${mouthOpen}" dur="0.4s" repeatCount="indefinite" />
      <animateTransform attributeName="transform" type="scale" values="1,1; -1,1; 1,1" keyTimes="0;0.499;1" dur="8s" additive="sum" repeatCount="indefinite" />
    </path>
    
    <!-- Ghost -->
    <g>
      <animateTransform attributeName="transform" type="translate" values="-70,0; -70,0; 70,0" keyTimes="0;0.499;1" dur="8s" repeatCount="indefinite" />
      
      <path class="ghost-body" d="M 30,45 L 30,25 A 15,15 0 0,1 60,25 L 60,45 L 55,40 L 50,45 L 45,40 L 40,45 L 35,40 Z">
        <animateTransform attributeName="transform" type="translate" values="0,-2; 0,2; 0,-2" dur="0.5s" repeatCount="indefinite" />
      </path>
      <!-- Eyes -->
      <g>
        <animateTransform attributeName="transform" type="translate" values="0,-2; 0,2; 0,-2" dur="0.5s" repeatCount="indefinite" />
        <circle cx="40" cy="22" r="4" class="ghost-eyes" />
        <circle cx="50" cy="22" r="4" class="ghost-eyes" />
        <circle cx="42" cy="22" r="1.5" class="ghost-pupil">
          <animate attributeName="cx" values="40;44;40" dur="2s" repeatCount="indefinite" />
        </circle>
        <circle cx="52" cy="22" r="1.5" class="ghost-pupil">
          <animate attributeName="cx" values="50;54;50" dur="2s" repeatCount="indefinite" />
        </circle>
      </g>
    </g>
  </g>
</svg>`;
}

export async function generatePacmanAssets({ config, outputDirectory }) {
  if (!config.pacman?.enabled) return null;
  const palette = paletteDefinitions[config.appearance.palette];
  await mkdir(outputDirectory, { recursive: true });
  
  const darkSvg = createPacmanSvg(palette.dark);
  const lightSvg = createPacmanSvg(palette.light);
  
  await Promise.all([
    writeFile(resolve(outputDirectory, "pacman-dark.svg"), darkSvg),
    writeFile(resolve(outputDirectory, "pacman-light.svg"), lightSvg)
  ]);
  
  return {
    dark: "pacman-dark.svg",
    light: "pacman-light.svg"
  };
}
