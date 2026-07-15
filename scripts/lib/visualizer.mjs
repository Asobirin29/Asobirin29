import { mkdir, writeFile } from "node:fs/promises";
import { resolve } from "node:path";
import { paletteDefinitions } from "./hero.mjs";

export function createVisualizerSvg(colors) {
  const barCount = 20;
  const barWidth = 8;
  const barGap = 5;
  const height = 110;
  const width = barCount * (barWidth + barGap) + barGap; // 20 * 13 + 5 = 265
  
  const bars = [];
  for (let i = 0; i < barCount; i++) {
    const x = barGap + i * (barWidth + barGap);
    
    // Generates a sequence of values that make the bars bounce at varying offsets.
    const pathValues = [];
    const minVal = 8;
    const maxVal = 95;
    for (let step = 0; step < 8; step++) {
      pathValues.push(Math.floor(minVal + Math.random() * (maxVal - minVal)));
    }
    pathValues.push(pathValues[0]); // Complete loop
    
    const duration = (0.7 + Math.random() * 0.9).toFixed(2);
    const delay = -(Math.random() * 1.5).toFixed(2);
    
    const heightSequence = pathValues.join(";");
    const ySequence = pathValues.map((h) => height - h).join(";");
    
    bars.push(`<rect class="bar" x="${x}" y="${height - minVal}" width="${barWidth}" height="${minVal}" rx="${(barWidth/2).toFixed(1)}" fill="url(#bar-grad)">
      <animate attributeName="height" values="${heightSequence}" dur="${duration}s" begin="${delay}s" repeatCount="indefinite" />
      <animate attributeName="y" values="${ySequence}" dur="${duration}s" begin="${delay}s" repeatCount="indefinite" />
    </rect>`);
  }
  
  return `<svg xmlns="http://www.w3.org/2000/svg" width="100%" height="100%" viewBox="0 0 ${width + 40} ${height + 65}" role="img">
  <defs>
    <linearGradient id="bar-grad" x1="0" y1="1" x2="0" y2="0">
      <stop offset="0%" stop-color="${colors.blue}" />
      <stop offset="50%" stop-color="${colors.cyan}" />
      <stop offset="100%" stop-color="${colors.violet}" />
    </linearGradient>
    <filter id="glow" x="-20%" y="-20%" width="140%" height="140%">
      <feGaussianBlur stdDeviation="3" result="blur" />
      <feComposite in="SourceGraphic" in2="blur" operator="over" />
    </filter>
  </defs>
  <style>
    .bg { fill: ${colors.panel}; fill-opacity: 0.45; stroke: ${colors.blue}; stroke-opacity: 0.25; stroke-width: 1.5; rx: 12px; }
    .bar { filter: url(#glow); opacity: 0.85; }
    .title { font-family: 'Courier New', Consolas, monospace; font-size: 11px; font-weight: 700; fill: ${colors.cyan}; letter-spacing: 1.5px; }
    .status { font-family: 'Courier New', Consolas, monospace; font-size: 9px; fill: ${colors.muted}; }
    .song { font-family: 'Courier New', Consolas, monospace; font-size: 10px; font-weight: 700; fill: ${colors.primary}; }
  </style>
  <rect x="2" y="2" width="${width + 36}" height="${height + 61}" class="bg" />
  <text x="20" y="25" class="title">SPOTIFY.STREAM</text>
  <circle cx="${width + 16}" cy="21" r="4.5" fill="${colors.green}">
    <animate attributeName="opacity" values="1;0.2;1" dur="1.5s" repeatCount="indefinite" />
  </circle>
  <text x="20" y="44" class="song">Listening to: Cyberpunk Ambient Beats</text>
  <text x="20" y="58" class="status">Device: Dev-Station-Node / status: active</text>
  <g transform="translate(18, 50)">
    ${bars.join('\n    ')}
  </g>
</svg>`;
}

export async function generateVisualizerAssets({ config, outputDirectory }) {
  if (!config.musicVisualizer?.enabled) return null;
  const palette = paletteDefinitions[config.appearance.palette];
  await mkdir(outputDirectory, { recursive: true });
  
  const darkSvg = createVisualizerSvg(palette.dark);
  const lightSvg = createVisualizerSvg(palette.light);
  
  await Promise.all([
    writeFile(resolve(outputDirectory, "music-visualizer-dark.svg"), darkSvg),
    writeFile(resolve(outputDirectory, "music-visualizer-light.svg"), lightSvg)
  ]);
  
  return {
    dark: "music-visualizer-dark.svg",
    light: "music-visualizer-light.svg"
  };
}
