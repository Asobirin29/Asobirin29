#!/usr/bin/env node

import { readFile, writeFile } from "node:fs/promises";
import { resolve } from "node:path";
import { loadConfig, repositoryRoot } from "./lib/config.mjs";
import { ACTIVITY_END, ACTIVITY_START, JOKE_END, JOKE_START } from "./lib/readme.mjs";

const dryRun = process.argv.includes("--dry-run");
const token = process.env.GITHUB_TOKEN || process.env.GH_TOKEN;

const jokeFallbacks = [
  "Why do programmers wear glasses? Because they can't C#.",
  "There are 10 types of people in the world: those who understand binary, and those who don't.",
  "How many programmers does it take to change a light bulb? None, that's a hardware problem.",
  "A SQL query goes into a bar, walks up to two tables and asks, 'Can I join you?'",
  "['hip', 'hip'] (hip hip array!)",
  "Why did the programmer quit his job? Because he didn't get arrays.",
  "To understand recursion, you must first understand recursion."
];

async function fetchProgrammingJoke() {
  try {
    const response = await fetch("https://v2.jokeapi.dev/joke/Programming?safe-mode&type=single", {
      headers: { "User-Agent": "Ahmad-Sobirin-Profile-Agent" },
      signal: AbortSignal.timeout(4000)
    });
    if (response.ok) {
      const data = await response.json();
      if (data.joke) {
        return `> _${data.joke}_`;
      }
    }
  } catch (err) {
    console.log("Failed to fetch online joke, using fallback: " + err.message);
  }
  const randomFallback = jokeFallbacks[Math.floor(Math.random() * jokeFallbacks.length)];
  return `> _${randomFallback}_`;
}

function formatDate(value) {
  return new Intl.DateTimeFormat("en", { month: "short", day: "numeric", year: "numeric" }).format(new Date(value));
}

function eventToLine(event) {
  const repo = event.repo?.name;
  if (!repo) return null;
  const date = formatDate(event.created_at);
  const repoLink = `https://github.com/${repo}`;

  if (event.type === "PushEvent") {
    const commits = event.payload?.commits?.length || 1;
    return `- ${date}: pushed ${commits} ${commits === 1 ? "commit" : "commits"} to [${repo}](${repoLink}).`;
  }
  if (event.type === "CreateEvent") {
    return `- ${date}: created a ${event.payload?.ref_type || "resource"} in [${repo}](${repoLink}).`;
  }
  if (event.type === "PullRequestEvent") {
    const action = event.payload?.action || "updated";
    const number = event.payload?.pull_request?.number;
    const url = event.payload?.pull_request?.html_url || repoLink;
    return `- ${date}: ${action} pull request${number ? ` [#${number}](${url})` : ""} in [${repo}](${repoLink}).`;
  }
  if (event.type === "IssuesEvent") {
    const action = event.payload?.action || "updated";
    const number = event.payload?.issue?.number;
    const url = event.payload?.issue?.html_url || repoLink;
    return `- ${date}: ${action} issue${number ? ` [#${number}](${url})` : ""} in [${repo}](${repoLink}).`;
  }
  return null;
}

function replaceSection(readme, startMarker, endMarker, content) {
  const startIndex = readme.indexOf(startMarker);
  const endIndex = readme.indexOf(endMarker);
  if (startIndex === -1 || endIndex === -1 || endIndex <= startIndex) {
    throw new Error(`README markers ${startMarker} and ${endMarker} are missing or malformed.`);
  }
  return `${readme.slice(0, startIndex + startMarker.length)}\n${content}\n${readme.slice(endIndex)}`;
}

try {
  const config = await loadConfig();
  const readmePath = resolve(repositoryRoot, "README.md");
  let readme = await readFile(readmePath, "utf8");
  let updated = false;

  // 1. Update activity if enabled
  if (config.activity.enabled) {
    try {
      console.log("Fetching recent activity...");
      const headers = { Accept: "application/vnd.github+json", "User-Agent": `${config.profile.username}-profile-readme` };
      if (token) headers.Authorization = `Bearer ${token}`;
      const response = await fetch(`https://api.github.com/users/${config.profile.username}/events/public?per_page=50`, { headers });
      if (!response.ok) throw new Error(`GitHub API returned ${response.status} ${response.statusText}.`);

      const events = await response.json();
      const lines = events
        .map(eventToLine)
        .filter(Boolean)
        .filter((line, index, all) => all.indexOf(line) === index)
        .slice(0, config.activity.limit);
      const content = lines.length ? lines.join("\n") : "_No recent public activity was found._";
      readme = replaceSection(readme, ACTIVITY_START, ACTIVITY_END, content);
      updated = true;
      console.log("Activity block prepared.");
    } catch (activityError) {
      console.warn(`Could not update recent activity: ${activityError.message}`);
    }
  }

  // 2. Update developer joke if enabled
  if (config.joke.enabled) {
    console.log("Fetching new programming joke...");
    const jokeContent = await fetchProgrammingJoke();
    readme = replaceSection(readme, JOKE_START, JOKE_END, jokeContent);
    updated = true;
    console.log("Joke block prepared.");
  }

  if (updated) {
    if (dryRun) {
      console.log("\n--- Dry Run Output ---");
      console.log(readme);
      console.log("----------------------");
      console.log("Dry run complete. README.md was not modified.");
    } else {
      await writeFile(readmePath, readme);
      console.log("README.md successfully updated with new content.");
    }
  } else {
    console.log("Neither activity nor jokes are enabled. Nothing to update.");
  }
} catch (error) {
  console.error(error.message);
  process.exitCode = 1;
}
