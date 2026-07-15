#!/usr/bin/env node

import { readFile, writeFile } from "node:fs/promises";
import { resolve } from "node:path";
import { loadConfig, repositoryRoot } from "./lib/config.mjs";
import { JOKE_END, JOKE_START } from "./lib/readme.mjs";

const JOKE_API_URL = "https://v2.jokeapi.dev/joke/Programming?blacklistFlags=nsfw,religious,political,racist,sexist,explicit&type=single";

async function fetchJoke() {
  try {
    const response = await fetch(JOKE_API_URL);
    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
    const data = await response.json();
    return data.joke;
  } catch (error) {
    console.error("Failed to fetch joke:", error);
    return null;
  }
}

async function updateReadme() {
  try {
    const config = await loadConfig();
    if (!config.joke?.enabled) {
      console.log("Joke feature is disabled in configuration.");
      return;
    }

    const readmePath = resolve(repositoryRoot, "README.md");
    let readme = await readFile(readmePath, "utf8");

    const startIndex = readme.indexOf(JOKE_START);
    const endIndex = readme.indexOf(JOKE_END);

    if (startIndex === -1 || endIndex === -1) {
      console.error("Could not find joke markers in README.md");
      process.exitCode = 1;
      return;
    }

    const joke = await fetchJoke();
    if (!joke) {
      console.log("Using existing joke as fetch failed.");
      return;
    }

    // Wrap the joke in a neat blockquote
    const formattedJoke = `\n> ${joke.split("\\n").join("\\n> ")}\n`;

    const updatedReadme = readme.slice(0, startIndex + JOKE_START.length) + formattedJoke + readme.slice(endIndex);
    
    await writeFile(readmePath, updatedReadme, "utf8");
    console.log("Successfully updated daily developer joke.");
  } catch (error) {
    console.error("Update failed:", error.message);
    process.exitCode = 1;
  }
}

updateReadme();
