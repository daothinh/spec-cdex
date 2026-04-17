import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..");

const catalogPath = path.join(repoRoot, "plugins", "catalog.json");
const claudeMarketplacePath = path.join(repoRoot, ".claude-plugin", "marketplace.json");
const codexMarketplacePath = path.join(repoRoot, ".agents", "plugins", "marketplace.json");

async function main() {
  const catalog = await readJson(catalogPath);
  const claudeMarketplace = await readJson(claudeMarketplacePath);
  const codexMarketplace = await readJson(codexMarketplacePath);

  const errors = [];
  const pluginEntries = new Map(catalog.plugins.map((entry) => [entry.name, entry]));
  const claudeNames = new Set(claudeMarketplace.plugins.map((entry) => entry.name));
  const codexNames = new Set(codexMarketplace.plugins.map((entry) => entry.name));

  for (const entry of catalog.plugins) {
    const pluginRoot = path.join(repoRoot, "plugins", entry.name);
    const skillsDir = path.join(pluginRoot, "skills");
    const claudeManifestPath = path.join(pluginRoot, ".claude-plugin", "plugin.json");
    const codexManifestPath = path.join(pluginRoot, ".codex-plugin", "plugin.json");

    if (entry.sourceKind === "skills") {
      const sourcePath = path.resolve(
        repoRoot,
        entry.sourcePath ?? path.join(catalog.defaults.skillsSourceRoot, entry.name)
      );
      if (!(await exists(sourcePath))) {
        errors.push(`Missing source plugin path for ${entry.name}: ${sourcePath}`);
      }
    }

    if (!(await exists(pluginRoot))) {
      errors.push(`Missing root plugin directory for ${entry.name}: ${pluginRoot}`);
      continue;
    }
    if (!(await exists(skillsDir))) {
      errors.push(`Missing skills/ directory for ${entry.name}: ${skillsDir}`);
    }
    if (!(await exists(claudeManifestPath))) {
      errors.push(`Missing Claude manifest for ${entry.name}: ${claudeManifestPath}`);
      continue;
    }
    if (!(await exists(codexManifestPath))) {
      errors.push(`Missing Codex manifest for ${entry.name}: ${codexManifestPath}`);
      continue;
    }

    const claudeManifest = await readJson(claudeManifestPath);
    const codexManifest = await readJson(codexManifestPath);

    validateManifestParity(entry.name, claudeManifest, codexManifest, errors);
    validateCodexManifest(entry.name, codexManifest, errors);

    if (!claudeNames.has(entry.name)) {
      errors.push(`Claude marketplace is missing ${entry.name}`);
    }
    if (entry.codexStatus === "available" && !codexNames.has(entry.name)) {
      errors.push(`Codex marketplace should include ${entry.name}`);
    }
    if (entry.codexStatus !== "available" && codexNames.has(entry.name)) {
      errors.push(`Codex marketplace must not include blocked plugin ${entry.name}`);
    }

    const skillFiles = await findFiles(skillsDir, (targetPath) => path.basename(targetPath) === "SKILL.md");
    for (const skillFile of skillFiles) {
      const missingLinks = await validateSkillLinks(skillFile);
      errors.push(...missingLinks.map((link) => `${path.relative(repoRoot, skillFile)} -> missing ${link}`));
    }
  }

  for (const marketEntry of claudeMarketplace.plugins) {
    if (!pluginEntries.has(marketEntry.name)) {
      errors.push(`Claude marketplace contains unknown plugin ${marketEntry.name}`);
    }
    validateClaudeMarketplaceEntry(marketEntry, errors);
  }
  for (const marketEntry of codexMarketplace.plugins) {
    if (!pluginEntries.has(marketEntry.name)) {
      errors.push(`Codex marketplace contains unknown plugin ${marketEntry.name}`);
      continue;
    }
    validateCodexMarketplaceEntry(marketEntry, pluginEntries.get(marketEntry.name), errors);
  }

  if (errors.length > 0) {
    console.error(`Validation failed with ${errors.length} issue(s):`);
    for (const issue of errors) {
      console.error(`- ${issue}`);
    }
    process.exitCode = 1;
    return;
  }

  console.log(
    `Validation passed for ${catalog.plugins.length} plugins. Claude entries=${claudeMarketplace.plugins.length}, Codex entries=${codexMarketplace.plugins.length}.`
  );
}

function validateManifestParity(name, claudeManifest, codexManifest, errors) {
  for (const field of ["name", "version", "description", "repository", "license"]) {
    if ((claudeManifest[field] ?? null) !== (codexManifest[field] ?? null)) {
      errors.push(`${name}: Claude/Codex manifest mismatch for ${field}`);
    }
  }
}

function validateCodexManifest(name, codexManifest, errors) {
  if (codexManifest.skills !== "./skills/") {
    errors.push(`${name}: Codex manifest skills path must be ./skills/`);
  }
  if (!codexManifest.interface?.displayName) {
    errors.push(`${name}: Codex manifest missing interface.displayName`);
  }
  if (!codexManifest.interface?.category) {
    errors.push(`${name}: Codex manifest missing interface.category`);
  }
}

async function validateSkillLinks(skillFile) {
  const content = stripCodeFences(await fs.readFile(skillFile, "utf8"));
  const baseDir = path.dirname(skillFile);
  const missing = [];

  const markdownLinkPattern = /\[[^\]]+\]\(([^)]+)\)/g;
  let match;
  while ((match = markdownLinkPattern.exec(content)) !== null) {
    const target = match[1].trim();
    if (!target || target.startsWith("http://") || target.startsWith("https://") || target.startsWith("#")) {
      continue;
    }
    const [fileTarget] = target.split("#", 1);
    if (!fileTarget || !looksLikeRelativeFile(fileTarget)) {
      continue;
    }
    if (!isLiteralPath(fileTarget)) {
      continue;
    }
    const resolved = await resolveExistingPath(baseDir, fileTarget);
    if (!resolved) {
      missing.push(fileTarget);
    }
  }

  const contentWithoutMarkdownLinks = content.replace(/\[[^\]]+\]\(([^)]+)\)/g, "");

  const baseDirPattern = /\{baseDir\}\/([A-Za-z0-9_./-]+\.[A-Za-z0-9]+)/g;
  while ((match = baseDirPattern.exec(contentWithoutMarkdownLinks)) !== null) {
    const target = match[1];
    const resolved = await resolveExistingPath(baseDir, `{baseDir}/${target}`);
    if (!resolved) {
      missing.push(`{baseDir}/${target}`);
    }
  }

  const inlinePathPattern =
    /(?<![A-Za-z0-9_./-])((?:references|scripts|workflows|resources|templates|agents|schemas|commands|hooks|plugins|skills|\.agents)\/[A-Za-z0-9_./-]+\.[A-Za-z0-9]+)(?![A-Za-z0-9_./-])/g;
  while ((match = inlinePathPattern.exec(contentWithoutMarkdownLinks)) !== null) {
    const target = match[1];
    const resolved = await resolveExistingPath(baseDir, target);
    if (!resolved) {
      missing.push(target);
    }
  }

  return Array.from(new Set(missing));
}

function stripCodeFences(content) {
  return content.replace(/```[\s\S]*?```/g, "");
}

function validateClaudeMarketplaceEntry(entry, errors) {
  if (entry.source !== `./plugins/${entry.name}`) {
    errors.push(`Claude marketplace source mismatch for ${entry.name}`);
  }
}

function validateCodexMarketplaceEntry(entry, pluginEntry, errors) {
  if (entry.source?.source !== "local") {
    errors.push(`Codex marketplace source.source mismatch for ${entry.name}`);
  }
  if (entry.source?.path !== `./plugins/${entry.name}`) {
    errors.push(`Codex marketplace source.path mismatch for ${entry.name}`);
  }
  if (entry.policy?.installation !== "AVAILABLE") {
    errors.push(`Codex marketplace installation policy mismatch for ${entry.name}`);
  }
  if (entry.policy?.authentication !== "ON_INSTALL") {
    errors.push(`Codex marketplace authentication policy mismatch for ${entry.name}`);
  }
  if (pluginEntry?.category && entry.category !== pluginEntry.category) {
    errors.push(`Codex marketplace category mismatch for ${entry.name}`);
  }
}

function looksLikeRelativeFile(target) {
  return (
    target.startsWith("{baseDir}/") ||
    target.startsWith("./") ||
    target.startsWith("../") ||
    target.startsWith("plugins/") ||
    target.startsWith(".agents/") ||
    target.startsWith("skills/") ||
    /^[A-Za-z0-9_.-]+\/.+/.test(target)
  );
}

function isLiteralPath(target) {
  return !target.includes("{") && !target.includes("}") && !target.includes("*");
}

async function resolveExistingPath(baseDir, target) {
  const candidates = [];

  if (target.startsWith("{baseDir}/")) {
    const relativeTarget = target.slice("{baseDir}/".length);
    if (!isLiteralPath(relativeTarget)) {
      return null;
    }
    candidates.push(path.resolve(baseDir, relativeTarget));
    candidates.push(path.resolve(baseDir, "..", "..", relativeTarget));
  } else if (
    target.startsWith("plugins/") ||
    target.startsWith(".agents/") ||
    target.startsWith("skills/")
  ) {
    candidates.push(path.resolve(repoRoot, target));
  } else {
    candidates.push(path.resolve(baseDir, target));
    candidates.push(path.resolve(baseDir, "..", "..", target));
  }

  for (const candidate of candidates) {
    if (await exists(candidate)) {
      return candidate;
    }
  }

  return null;
}

async function findFiles(rootDir, predicate) {
  const results = [];
  const stack = [rootDir];

  while (stack.length > 0) {
    const current = stack.pop();
    const entries = await fs.readdir(current, { withFileTypes: true });
    for (const entry of entries) {
      const fullPath = path.join(current, entry.name);
      if (entry.isDirectory()) {
        stack.push(fullPath);
      } else if (predicate(fullPath)) {
        results.push(fullPath);
      }
    }
  }

  return results;
}

async function exists(targetPath) {
  try {
    await fs.access(targetPath);
    return true;
  } catch {
    return false;
  }
}

async function readJson(targetPath) {
  return JSON.parse(await fs.readFile(targetPath, "utf8"));
}

main().catch((error) => {
  console.error(error instanceof Error ? error.message : String(error));
  process.exitCode = 1;
});
