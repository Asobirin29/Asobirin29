import { mkdir, writeFile } from "node:fs/promises";
import { resolve } from "node:path";
import { paletteDefinitions } from "./hero.mjs";

export function createRadarSvg(config, colors) {
  const skills = config.skillsRadar.skills;
  const skillEntries = Object.entries(skills);
  const N = skillEntries.length;
  if (N < 3) {
    throw new Error("Skills Radar requires at least 3 skills to render a polygon.");
  }
  
  const cx = 220;
  const cy = 205;
  const r = 110;
  
  // Concentric polygon grids (25%, 50%, 75%, 100%)
  const grids = [0.25, 0.5, 0.75, 1.0];
  const gridPaths = grids.map((scale) => {
    const points = [];
    for (let i = 0; i < N; i++) {
      const angle = (i * 2 * Math.PI) / N - Math.PI / 2;
      const x = cx + r * scale * Math.cos(angle);
      const y = cy + r * scale * Math.sin(angle);
      points.push(`${x.toFixed(1)},${y.toFixed(1)}`);
    }
    return `<polygon points="${points.join(" ")}" class="grid-line" />`;
  });
  
  // Axis lines and labels
  const axes = [];
  const labels = [];
  const skillPoints = [];
  
  skillEntries.forEach(([skillName, value], i) => {
    const angle = (i * 2 * Math.PI) / N - Math.PI / 2;
    
    // Axis line
    const axisX = cx + r * Math.cos(angle);
    const axisY = cy + r * Math.sin(angle);
    axes.push(`<line x1="${cx}" y1="${cy}" x2="${axisX.toFixed(1)}" y2="${axisY.toFixed(1)}" class="grid-line" />`);
    
    // Label placement
    const labelDist = r + 24;
    const labelX = cx + labelDist * Math.cos(angle);
    const labelY = cy + labelDist * Math.sin(angle) + 4; // slight vertical adjust
    
    let textAnchor = "middle";
    if (Math.cos(angle) > 0.1) textAnchor = "start";
    else if (Math.cos(angle) < -0.1) textAnchor = "end";
    
    labels.push(`<text x="${labelX.toFixed(1)}" y="${labelY.toFixed(1)}" text-anchor="${textAnchor}" class="label-text">${skillName} (${value}%)</text>`);
    
    // Skill point coordinate
    const ptX = cx + r * (value / 100) * Math.cos(angle);
    const ptY = cy + r * (value / 100) * Math.sin(angle);
    skillPoints.push(`${ptX.toFixed(1)},${ptY.toFixed(1)}`);
  });
  
  const skillPolygon = skillPoints.join(" ");
  
  return `<svg xmlns="http://www.w3.org/2000/svg" width="100%" height="100%" viewBox="0 0 440 375" role="img">
  <defs>
    <radialGradient id="radar-glow" cx="50%" cy="50%" r="50%">
      <stop offset="0%" stop-color="${colors.cyan}" stop-opacity="0.3" />
      <stop offset="70%" stop-color="${colors.violet}" stop-opacity="0.1" />
      <stop offset="100%" stop-color="${colors.blue}" stop-opacity="0" />
    </radialGradient>
    <filter id="radar-shadow" x="-20%" y="-20%" width="140%" height="140%">
      <feGaussianBlur stdDeviation="4" result="blur" />
      <feComposite in="SourceGraphic" in2="blur" operator="over" />
    </filter>
  </defs>
  <style>
    .radar-bg { fill: ${colors.panel}; fill-opacity: 0.45; stroke: ${colors.blue}; stroke-opacity: 0.25; stroke-width: 1.5; rx: 12px; }
    .grid-line { fill: none; stroke: ${colors.muted}; stroke-opacity: 0.3; stroke-width: 0.8; }
    .skill-poly { fill: url(#radar-glow); stroke: ${colors.cyan}; stroke-width: 2.2; filter: url(#radar-shadow); opacity: 0.88; }
    .skill-poly-outline { fill: none; stroke: ${colors.violet}; stroke-width: 1; opacity: 0.6; }
    .label-text { font-family: 'Courier New', Consolas, monospace; font-size: 10.5px; font-weight: 700; fill: ${colors.primary}; }
    .radar-title { font-family: 'Courier New', Consolas, monospace; font-size: 11px; font-weight: 700; fill: ${colors.cyan}; letter-spacing: 1.5px; }
  </style>
  
  <rect x="2" y="2" width="436" height="371" class="radar-bg" />
  <text x="20" y="25" class="radar-title">SKILLS.RADAR.MAP</text>
  
  <g>
    <!-- Background grid -->
    ${gridPaths.join("\n    ")}
    ${axes.join("\n    ")}
    
    <!-- Skill Area Polygon -->
    <polygon points="${skillPolygon}" class="skill-poly">
      <animate attributeName="opacity" values="0.88;0.65;0.88" dur="4s" repeatCount="indefinite" />
    </polygon>
    <polygon points="${skillPolygon}" class="skill-poly-outline" />
    
    <!-- Labels -->
    ${labels.join("\n    ")}
  </g>
</svg>`;
}

export async function generateRadarAssets({ config, outputDirectory }) {
  if (!config.skillsRadar?.enabled) return null;
  const palette = paletteDefinitions[config.appearance.palette];
  await mkdir(outputDirectory, { recursive: true });
  
  const darkSvg = createRadarSvg(config, palette.dark);
  const lightSvg = createRadarSvg(config, palette.light);
  
  await Promise.all([
    writeFile(resolve(outputDirectory, "skills-radar-dark.svg"), darkSvg),
    writeFile(resolve(outputDirectory, "skills-radar-light.svg"), lightSvg)
  ]);
  
  return {
    dark: "skills-radar-dark.svg",
    light: "skills-radar-light.svg"
  };
}
