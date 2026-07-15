import { readFile, writeFile } from "node:fs/promises";
import { resolve } from "node:path";

export const ACTIVITY_START = "<!-- AUTO:ACTIVITY:START -->";
export const ACTIVITY_END = "<!-- AUTO:ACTIVITY:END -->";
export const JOKE_START = "<!-- AUTO:JOKE:START -->";
export const JOKE_END = "<!-- AUTO:JOKE:END -->";

function escapeCell(value) {
  return String(value).replaceAll("|", "\\|").replaceAll("\n", " ");
}

function badgeSegment(value) {
  return encodeURIComponent(String(value).replaceAll("-", "--").replaceAll("_", "__").replaceAll(" ", "_"));
}

function renderLinks(links) {
  return links.map((link) => {
    const logo = link.logo ? `&logo=${encodeURIComponent(link.logo)}&logoColor=white` : "";
    const image = `https://img.shields.io/badge/${badgeSegment(link.label)}-${badgeSegment(link.value)}-${link.color}?style=for-the-badge${logo}`;
    return `  <a href="${link.url}"><img alt="${link.label}" src="${image}"></a>`;
  }).join("\n");
}

function renderFocus(focus) {
  return [
    "| Area | What I am exploring |",
    "| --- | --- |",
    ...focus.map((item) => `| **${escapeCell(item.name)}** | ${escapeCell(item.description)} |`)
  ].join("\n");
}

function renderProjects(projects) {
  return [
    "| Project | Focus | Why it matters |",
    "| --- | --- | --- |",
    ...projects.map((project) => {
      const homepage = project.homepage ? ` [Live](${project.homepage})` : "";
      return `| [**${escapeCell(project.name)}**](${project.url}) | ${escapeCell(project.focus)} | ${escapeCell(project.summary)}${homepage} |`;
    })
  ].join("\n");
}

function extractActivity(readme) {
  const startIndex = readme.indexOf(ACTIVITY_START);
  const endIndex = readme.indexOf(ACTIVITY_END);
  if (startIndex === -1 || endIndex === -1 || endIndex <= startIndex) return null;
  return readme.slice(startIndex + ACTIVITY_START.length, endIndex).trim();
}

async function readExistingActivity(readmePath) {
  try {
    const existing = await readFile(readmePath, "utf8");
    return extractActivity(existing);
  } catch (error) {
    if (error.code === "ENOENT") return null;
    throw error;
  }
}

function extractJoke(readme) {
  const startIndex = readme.indexOf(JOKE_START);
  const endIndex = readme.indexOf(JOKE_END);
  if (startIndex === -1 || endIndex === -1 || endIndex <= startIndex) return null;
  return readme.slice(startIndex + JOKE_START.length, endIndex).trim();
}

async function readExistingJoke(readmePath) {
  try {
    const existing = await readFile(readmePath, "utf8");
    return extractJoke(existing);
  } catch (error) {
    if (error.code === "ENOENT") return null;
    throw error;
  }
}

function renderStats(username, palette) {
  const themes = {
    signal: {
      dark: { bg: "020617", title: "22d3ee", text: "e5e7eb", icon: "38bdf8", ring: "22d3ee", fire: "7c3aed" },
      light: { bg: "f8fbff", title: "0891b2", text: "172554", icon: "2563eb", ring: "0891b2", fire: "6d28d9" }
    },
    ocean: {
      dark: { bg: "02131a", title: "2dd4bf", text: "e5f6f8", icon: "38bdf8", ring: "2dd4bf", fire: "6366f1" },
      light: { bg: "f4fcfc", title: "0f766e", text: "123047", icon: "0284c7", ring: "0f766e", fire: "4f46e5" }
    },
    solar: {
      dark: { bg: "090d14", title: "22d3ee", text: "f3f4f6", icon: "60a5fa", ring: "22d3ee", fire: "f59e0b" },
      light: { bg: "fbfcfe", title: "0891b2", text: "292524", icon: "2563eb", ring: "0891b2", fire: "b45309" }
    }
  };
  
  const colors = themes[palette] || themes.signal;
  
  const darkStatsUrl = `https://github-stats-extended.vercel.app/api?username=${username}&show_icons=true&bg_color=${colors.dark.bg}&title_color=${colors.dark.title}&text_color=${colors.dark.text}&icon_color=${colors.dark.icon}&hide_border=true`;
  const lightStatsUrl = `https://github-stats-extended.vercel.app/api?username=${username}&show_icons=true&bg_color=${colors.light.bg}&title_color=${colors.light.title}&text_color=${colors.light.text}&icon_color=${colors.light.icon}&hide_border=true`;
  
  const darkStreakUrl = `https://github-readme-streak-stats.herokuapp.com/?user=${username}&background=${colors.dark.bg}&ring=${colors.dark.ring}&fire=${colors.dark.fire}&currStreakNum=${colors.dark.text}&sideNums=64748b&sideLabels=${colors.dark.text}&dates=64748b&hide_border=true`;
  const lightStreakUrl = `https://github-readme-streak-stats.herokuapp.com/?user=${username}&background=${colors.light.bg}&ring=${colors.light.ring}&fire=${colors.light.fire}&currStreakNum=${colors.light.text}&sideNums=64748b&sideLabels=${colors.light.text}&dates=64748b&hide_border=true`;

  return `\n## GitHub Stats\n
<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="${darkStatsUrl}">
    <source media="(prefers-color-scheme: light)" srcset="${lightStatsUrl}">
    <img src="${darkStatsUrl}" alt="GitHub Stats" width="49%">
  </picture>
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="${darkStreakUrl}">
    <source media="(prefers-color-scheme: light)" srcset="${lightStreakUrl}">
    <img src="${darkStreakUrl}" alt="GitHub Streak" width="49%">
  </picture>
</p>
`;
}

function renderVisuals(config) {
  const radarEnabled = config.skillsRadar?.enabled;
  const visualizerEnabled = config.musicVisualizer?.enabled;
  
  if (!radarEnabled && !visualizerEnabled) return "";
  
  let content = "";
  if (radarEnabled && visualizerEnabled) {
    content = `
| Skills Radar Map | Live Audio Stream |
| --- | --- |
| <picture><source media="(prefers-color-scheme: dark)" srcset="./assets/visuals/skills-radar-dark.svg"><source media="(prefers-color-scheme: light)" srcset="./assets/visuals/skills-radar-light.svg"><img src="./assets/visuals/skills-radar-dark.svg" width="100%"></picture> | <picture><source media="(prefers-color-scheme: dark)" srcset="./assets/visuals/music-visualizer-dark.svg"><source media="(prefers-color-scheme: light)" srcset="./assets/visuals/music-visualizer-light.svg"><img src="./assets/visuals/music-visualizer-dark.svg" width="100%"></picture> |
`;
  } else if (radarEnabled) {
    content = `
<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="./assets/visuals/skills-radar-dark.svg">
    <source media="(prefers-color-scheme: light)" srcset="./assets/visuals/skills-radar-light.svg">
    <img src="./assets/visuals/skills-radar-dark.svg" width="60%">
  </picture>
</p>
`;
  } else {
    content = `
<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="./assets/visuals/music-visualizer-dark.svg">
    <source media="(prefers-color-scheme: light)" srcset="./assets/visuals/music-visualizer-light.svg">
    <img src="./assets/visuals/music-visualizer-dark.svg" width="60%">
  </picture>
</p>
`;
  }
  
  return `\n## Interactive Maps & Status\n${content}\n`;
}

export async function generateProfileReadme({ config, manifest, readmePath }) {
  const existingActivity = await readExistingActivity(readmePath);
  const activity = existingActivity || "_Recent public activity will appear here after the workflow runs._";
  const activitySection = config.activity.enabled
    ? `\n## Recent Activity\n\n${ACTIVITY_START}\n${activity}\n${ACTIVITY_END}\n`
    : "";
    
  const existingJoke = await readExistingJoke(readmePath);
  const joke = existingJoke || "_Daily developer jokes will appear here after the workflow runs._";
  const jokeSection = config.joke.enabled
    ? `\n## Daily Developer Joke\n\n${JOKE_START}\n${joke}\n${JOKE_END}\n`
    : "";
    
  const techStack = config.techStack.map((item) => `\`${item}\``).join(" · ");
  const about = config.profile.about.join("\n\n");
  const statsSection = renderStats(config.profile.username, config.appearance.palette);
  const visualsSection = renderVisuals(config);

  const pacmanSection = config.pacman?.enabled
    ? `\n<p align="center">\n  <picture>\n    <source media="(prefers-color-scheme: dark)" srcset="./assets/visuals/pacman-dark.svg">\n    <source media="(prefers-color-scheme: light)" srcset="./assets/visuals/pacman-light.svg">\n    <img alt="Pacman Animation" src="./assets/visuals/pacman-dark.svg" width="100%">\n  </picture>\n</p>\n`
    : "";

  const readme = `<!-- Generated by GitHub Profile Agent Console. Edit profile.config.json, then run npm run generate. -->
<p align="center">
  <picture>
    <source media="(max-width: 760px) and (prefers-color-scheme: dark)" srcset="./assets/hero/${manifest.assets.mobileDark}">
    <source media="(max-width: 760px)" srcset="./assets/hero/${manifest.assets.mobileLight}">
    <source media="(prefers-color-scheme: dark)" srcset="./assets/hero/${manifest.assets.desktopDark}">
    <source media="(prefers-color-scheme: light)" srcset="./assets/hero/${manifest.assets.desktopLight}">
    <img src="./assets/hero/${manifest.assets.desktopDark}" alt="${config.profile.name} - ${config.profile.headline}" width="100%">
  </picture>
</p>

<p align="center">
${renderLinks(config.links)}
</p>

## About Me

${about}

## Current Focus

${renderFocus(config.focus)}

## Featured Work

${renderProjects(config.projects)}

## Research Direction

${config.research.narrative}

## Tech Stack

${techStack}
${visualsSection}
${pacmanSection}
${statsSection}
## GitHub Contributions

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/Asobirin29/Asobirin29/pacman-output/pacman-contribution-graph.svg">
  <source media="(prefers-color-scheme: light)" srcset="https://raw.githubusercontent.com/Asobirin29/Asobirin29/pacman-output/pacman-contribution-graph.svg">
  <img alt="Pacman Contribution Graph" src="https://raw.githubusercontent.com/Asobirin29/Asobirin29/pacman-output/pacman-contribution-graph.svg" width="100%">
</picture>
${activitySection}${jokeSection}
---

<p align="center">
  ${config.footer}
</p>
`;

  await writeFile(resolve(readmePath), readme);
  return readme;
}
