import fs from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import { execFile as execFileCb } from "node:child_process";
import { promisify } from "node:util";
import { fileURLToPath } from "node:url";

const execFile = promisify(execFileCb);
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..");

const catalogPath = path.join(repoRoot, "plugins", "catalog.json");
const claudeMarketplacePath = path.join(repoRoot, ".claude-plugin", "marketplace.json");
const codexMarketplacePath = path.join(repoRoot, ".agents", "plugins", "marketplace.json");
const pluginRootDir = path.join(repoRoot, "plugins");

const BLOCKED_REASON = "Staged in root repo but withheld from the Codex marketplace until its Claude-specific workflow is ported.";
const CATEGORY_COLORS = {
  Coding: "#1F2937",
  Productivity: "#475569",
  Security: "#7C2D12"
};
const ACRONYMS = new Map([
  ["adb", "ADB"],
  ["ai", "AI"],
  ["algorand", "Algorand"],
  ["api", "API"],
  ["apk", "APK"],
  ["asan", "ASan"],
  ["aws", "AWS"],
  ["cfg", "CFG"],
  ["ci", "CI"],
  ["cli", "CLI"],
  ["codex", "Codex"],
  ["cpp", "C++"],
  ["csharp", "C#"],
  ["dex", "DEX"],
  ["dind", "DinD"],
  ["dwarf", "DWARF"],
  ["gh", "GH"],
  ["git", "Git"],
  ["go", "Go"],
  ["graphql", "GraphQL"],
  ["http", "HTTP"],
  ["idor", "IDOR"],
  ["ir", "IR"],
  ["java", "Java"],
  ["javascript", "JavaScript"],
  ["json", "JSON"],
  ["k8s", "K8s"],
  ["kani", "Kani"],
  ["lean", "Lean"],
  ["llvm", "LLVM"],
  ["mcp", "MCP"],
  ["mitmproxy", "mitmproxy"],
  ["ossfuzz", "OSS-Fuzz"],
  ["pbt", "PBT"],
  ["pdf", "PDF"],
  ["poc", "PoC"],
  ["pov", "PoV"],
  ["python", "Python"],
  ["ql", "QL"],
  ["sarif", "SARIF"],
  ["sdk", "SDK"],
  ["semgrep", "Semgrep"],
  ["solana", "Solana"],
  ["sql", "SQL"],
  ["teal", "TEAL"],
  ["toml", "TOML"],
  ["ts", "TS"],
  ["typescript", "TypeScript"],
  ["ui", "UI"],
  ["uv", "uv"],
  ["vyper", "Vyper"],
  ["web3", "Web3"],
  ["workflow", "Workflow"],
  ["xss", "XSS"],
  ["yara", "YARA"],
  ["zeroize", "Zeroize"]
]);

async function main() {
  const catalog = await readJson(catalogPath);
  const repoUrl = await detectRepoUrl();
  const backupRoot = await fs.mkdtemp(path.join(os.tmpdir(), "sync-root-plugins-"));
  const claudeMarket = {
    name: catalog.claudeMarketplace.name,
    owner: catalog.claudeMarketplace.owner,
    plugins: []
  };
  const codexMarket = {
    name: catalog.codexMarketplace.name,
    interface: catalog.codexMarketplace.interface,
    plugins: []
  };

  let syncedCount = 0;
  let generatedCount = 0;

  try {
    for (const entry of catalog.plugins) {
      const pluginRoot = path.join(pluginRootDir, entry.name);

      if (entry.sourceKind === "skills") {
        await syncSkillsPlugin(catalog, entry, pluginRoot, backupRoot);
        syncedCount += 1;
      }

      const meta = await resolveMetadata(catalog, entry, pluginRoot, repoUrl);

      if (entry.sourceKind === "skills") {
        await writeClaudeManifest(pluginRoot, meta);
        await writeCodexManifest(catalog, pluginRoot, meta);
        generatedCount += 1;
      }

      claudeMarket.plugins.push({
        name: meta.name,
        source: `./plugins/${meta.name}`,
        description: meta.description
      });

      if (entry.codexStatus === "available") {
        codexMarket.plugins.push({
          name: meta.name,
          source: {
            source: "local",
            path: `./plugins/${meta.name}`
          },
          policy: {
            installation: "AVAILABLE",
            authentication: "ON_INSTALL"
          },
          category: meta.category
        });
      }
    }

    await writeJson(claudeMarketplacePath, claudeMarket);
    await writeJson(codexMarketplacePath, codexMarket);

    console.log(
      [
        `Synced ${syncedCount} source plugins into root plugins/.`,
        `Generated manifests for ${generatedCount} staged plugins.`,
        `Claude marketplace entries: ${claudeMarket.plugins.length}.`,
        `Codex marketplace entries: ${codexMarket.plugins.length}.`
      ].join(" ")
    );
  } finally {
    await fs.rm(backupRoot, { recursive: true, force: true });
  }
}

async function syncSkillsPlugin(catalog, entry, pluginRoot, backupRoot) {
  const sourceRoot = path.resolve(
    repoRoot,
    entry.sourcePath ?? path.join(catalog.defaults.skillsSourceRoot, entry.name)
  );

  await ensureExists(sourceRoot, `Missing source plugin: ${sourceRoot}`);
  const preserved = await backupPreservedPaths(pluginRoot, backupRoot);
  await safeRemove(pluginRoot);
  await fs.mkdir(pluginRoot, { recursive: true });
  await fs.cp(sourceRoot, pluginRoot, {
    recursive: true,
    force: true,
    filter: (sourcePath) => {
      const base = path.basename(sourcePath);
      return ![".git", "node_modules", "__pycache__"].includes(base);
    }
  });
  await restorePreservedPaths(pluginRoot, preserved);
  await ensureSkillStub(entry, pluginRoot);
}

async function resolveMetadata(catalog, entry, pluginRoot, repoUrl) {
  if (entry.sourceKind === "root") {
    const claudeManifest = await readJson(path.join(pluginRoot, ".claude-plugin", "plugin.json"));
    const codexManifest = await readJson(path.join(pluginRoot, ".codex-plugin", "plugin.json"));
    const interfaceMeta = codexManifest.interface ?? {};
    const description =
      entry.description ??
      codexManifest.description ??
      claudeManifest.description ??
      (await deriveDescription(pluginRoot));

    return {
      name: entry.name,
      version: entry.version ?? codexManifest.version ?? claudeManifest.version ?? "0.1.0",
      description,
      displayName: entry.displayName ?? interfaceMeta.displayName ?? toDisplayName(entry.name),
      shortDescription:
        entry.shortDescription ??
        interfaceMeta.shortDescription ??
        truncateSentence(description, 72),
      longDescription:
        entry.longDescription ??
        interfaceMeta.longDescription ??
        description,
      repository: entry.repository ?? codexManifest.repository ?? claudeManifest.repository ?? repoUrl,
      homepage: entry.homepage ?? codexManifest.homepage ?? repoUrl,
      license: entry.license ?? codexManifest.license ?? claudeManifest.license ?? "MIT",
      author:
        codexManifest.author ??
        claudeManifest.author ?? {
          name: entry.authorName ?? "workers.io"
        },
      category: entry.category ?? interfaceMeta.category ?? "Productivity",
      defaultPrompt:
        entry.defaultPrompt ??
        interfaceMeta.defaultPrompt ??
        [`Use the ${entry.displayName ?? toDisplayName(entry.name)} workflow on this repository`],
      keywords: codexManifest.keywords ?? buildKeywords(entry.name, entry.category),
      capabilities: interfaceMeta.capabilities ?? catalog.defaults.codexCapabilities
    };
  }

  const description = entry.description ?? (await deriveDescription(pluginRoot));
  return {
    name: entry.name,
    version: entry.version ?? "0.1.0",
    description,
    displayName: entry.displayName ?? toDisplayName(entry.name),
    shortDescription: entry.shortDescription ?? truncateSentence(description, 72),
    longDescription:
      entry.longDescription ??
      (entry.codexStatus === "blocked"
        ? `${description} ${BLOCKED_REASON}`
        : description),
    repository: entry.repository ?? repoUrl,
    homepage: entry.homepage ?? repoUrl,
    license: entry.license ?? catalog.defaults.skillsLicense,
    author: {
      name: entry.authorName ?? catalog.defaults.skillsAuthorName
    },
    category: entry.category ?? "Productivity",
    defaultPrompt:
      entry.defaultPrompt ??
      [`Use the ${entry.displayName ?? toDisplayName(entry.name)} workflow on this repository`],
    keywords: buildKeywords(entry.name, entry.category),
    capabilities: entry.capabilities ?? catalog.defaults.codexCapabilities
  };
}

async function writeClaudeManifest(pluginRoot, meta) {
  const claudeManifestPath = path.join(pluginRoot, ".claude-plugin", "plugin.json");
  const manifest = {
    name: meta.name,
    version: meta.version,
    description: meta.description,
    author: meta.author,
    homepage: meta.homepage,
    repository: meta.repository,
    license: meta.license
  };
  await writeJson(claudeManifestPath, manifest);
}

async function writeCodexManifest(catalog, pluginRoot, meta) {
  const codexManifestPath = path.join(pluginRoot, ".codex-plugin", "plugin.json");
  const manifest = {
    name: meta.name,
    version: meta.version,
    description: meta.description,
    author: meta.author,
    homepage: meta.homepage,
    repository: meta.repository,
    license: meta.license,
    keywords: meta.keywords,
    skills: "./skills/",
    interface: {
      displayName: meta.displayName,
      shortDescription: meta.shortDescription,
      longDescription: meta.longDescription,
      developerName: meta.author.name,
      category: meta.category,
      capabilities: meta.capabilities ?? catalog.defaults.codexCapabilities,
      websiteURL: meta.homepage,
      defaultPrompt: meta.defaultPrompt,
      brandColor: CATEGORY_COLORS[meta.category] ?? CATEGORY_COLORS.Productivity,
      screenshots: []
    }
  };
  await writeJson(codexManifestPath, manifest);
}

async function deriveDescription(pluginRoot) {
  const readmePath = path.join(pluginRoot, "README.md");
  if (await exists(readmePath)) {
    const readme = await fs.readFile(readmePath, "utf8");
    const paragraph = extractReadmeParagraph(readme);
    if (paragraph) {
      return paragraph;
    }
  }

  const skillRoots = await listSkillRoots(pluginRoot);
  for (const skillRoot of skillRoots) {
    const skillPath = path.join(skillRoot, "SKILL.md");
    if (!(await exists(skillPath))) {
      continue;
    }
    const frontmatter = parseFrontmatter(await fs.readFile(skillPath, "utf8"));
    if (frontmatter.description) {
      return sanitizeDescription(frontmatter.description);
    }
  }

  return `Root-ported plugin for ${toDisplayName(path.basename(pluginRoot))}.`;
}

async function ensureSkillStub(entry, pluginRoot) {
  const skillRoots = await listSkillRoots(pluginRoot);
  if (skillRoots.length > 0) {
    return;
  }

  const skillDir = path.join(pluginRoot, "skills", entry.name);
  const skillFile = path.join(skillDir, "SKILL.md");
  const displayName = entry.displayName ?? toDisplayName(entry.name);
  const statusLine =
    entry.codexStatus === "available"
      ? "This root-only wrapper exists because the source plugin ships non-skill assets."
      : "This root-only wrapper keeps the plugin installable in the root repo while Codex marketplace exposure stays blocked.";

  const content = `---
name: ${entry.name}
description: Root-only wrapper for the ${displayName} plugin.
---

# ${displayName}

${statusLine}

This plugin is primarily driven by non-skill assets such as hooks, commands, or MCP configuration.

See:
- \`README.md\`
- \`hooks/\`
- \`commands/\`
- \`.mcp.json\`
`;

  await fs.mkdir(skillDir, { recursive: true });
  await fs.writeFile(skillFile, content, "utf8");
}

function extractReadmeParagraph(readme) {
  const lines = readme.split(/\r?\n/);
  const paragraphs = [];
  let current = [];
  let inFence = false;

  for (const line of lines) {
    const trimmed = line.trim();

    if (trimmed.startsWith("```")) {
      inFence = !inFence;
      continue;
    }
    if (inFence) {
      continue;
    }
    if (!trimmed) {
      if (current.length > 0) {
        paragraphs.push(current.join(" "));
        current = [];
      }
      continue;
    }
    if (
      trimmed.startsWith("#") ||
      trimmed.startsWith(">") ||
      /^[-*]\s/.test(trimmed) ||
      /^\d+\.\s/.test(trimmed)
    ) {
      if (current.length > 0) {
        paragraphs.push(current.join(" "));
        current = [];
      }
      continue;
    }
    current.push(trimmed);
  }
  if (current.length > 0) {
    paragraphs.push(current.join(" "));
  }

  const paragraph = paragraphs.find((entry) => entry.length >= 30);
  return paragraph ? sanitizeDescription(paragraph) : "";
}

function parseFrontmatter(text) {
  const match = text.match(/^---\r?\n([\s\S]*?)\r?\n---/);
  if (!match) {
    return {};
  }

  const data = {};
  const lines = match[1].split(/\r?\n/);
  for (let index = 0; index < lines.length; index += 1) {
    const line = lines[index];
    const kv = line.match(/^([A-Za-z0-9_-]+):\s*(.*)$/);
    if (!kv) {
      continue;
    }
    const [, key, rawValue] = kv;
    if (["|", "|-", "|+", ">", ">-", ">+"].includes(rawValue.trim())) {
      const block = [];
      index += 1;
      while (index < lines.length && (/^\s/.test(lines[index]) || lines[index] === "")) {
        block.push(lines[index].trim());
        index += 1;
      }
      index -= 1;
      data[key] = block.join(rawValue.trim().startsWith(">") ? " " : "\n").trim();
      continue;
    }
    data[key] = stripQuotes(rawValue.trim());
  }
  return data;
}

function sanitizeDescription(value) {
  return value
    .replace(/\[(.*?)\]\((.*?)\)/g, "$1")
    .replace(/`/g, "")
    .replace(/\s+/g, " ")
    .replace(/^A Claude Code plugin that\s+/i, "")
    .replace(/^A Claude Code plugin\s+/i, "")
    .replace(/^A Claude skill that\s+/i, "")
    .replace(/^A Claude skill\s+/i, "A Codex skill ")
    .replace(/^Claude Code plugin that\s+/i, "")
    .replace(/^Claude Code plugin\s+/i, "")
    .replace(/^This plugin\s+/i, "")
    .replace(/\bClaude Code\b/g, "Codex")
    .replace(/\bClaude skill\b/g, "Codex skill")
    .replace(/\bfor use in Claude\b/gi, "for use in Codex")
    .trim();
}

function truncateSentence(value, maxLength) {
  if (value.length <= maxLength) {
    return value;
  }
  return `${value.slice(0, maxLength - 1).trimEnd()}...`;
}

function toDisplayName(name) {
  return name
    .split("-")
    .map((part) => ACRONYMS.get(part.toLowerCase()) ?? capitalize(part))
    .join(" ");
}

function capitalize(value) {
  if (!value) {
    return value;
  }
  return value.charAt(0).toUpperCase() + value.slice(1);
}

function buildKeywords(name, category) {
  const parts = name.split("-").map((part) => part.toLowerCase());
  return Array.from(new Set([...parts, name.toLowerCase(), category.toLowerCase(), "codex", "plugin"]));
}

async function listSkillRoots(pluginRoot) {
  const skillsDir = path.join(pluginRoot, "skills");
  if (!(await exists(skillsDir))) {
    return [];
  }
  const entries = await fs.readdir(skillsDir, { withFileTypes: true });
  return entries
    .filter((entry) => entry.isDirectory())
    .map((entry) => path.join(skillsDir, entry.name))
    .sort();
}

async function detectRepoUrl() {
  try {
    const { stdout } = await execFile("git", ["config", "--get", "remote.origin.url"], {
      cwd: repoRoot
    });
    const trimmed = stdout.trim();
    if (!trimmed) {
      throw new Error("empty origin url");
    }
    return normalizeRepoUrl(trimmed);
  } catch {
    return "https://github.com/daothinh/spec-codex";
  }
}

function normalizeRepoUrl(remoteUrl) {
  if (remoteUrl.startsWith("git@github.com:")) {
    return remoteUrl
      .replace("git@github.com:", "https://github.com/")
      .replace(/\.git$/, "");
  }
  return remoteUrl.replace(/\.git$/, "");
}

async function safeRemove(targetPath) {
  const normalized = path.resolve(targetPath);
  const pluginsRoot = path.resolve(pluginRootDir);
  if (!normalized.startsWith(`${pluginsRoot}${path.sep}`)) {
    throw new Error(`Refusing to remove path outside plugins/: ${targetPath}`);
  }
  await fs.rm(normalized, { recursive: true, force: true });
}

async function backupPreservedPaths(pluginRoot, backupRoot) {
  const preserveManifestPath = path.join(pluginRoot, ".codex-port", "preserve-paths.json");
  if (!(await exists(preserveManifestPath))) {
    return null;
  }

  const preserveManifest = await readJson(preserveManifestPath);
  const preservePaths = Array.isArray(preserveManifest)
    ? preserveManifest
    : Array.isArray(preserveManifest.paths)
      ? preserveManifest.paths
      : [];
  const uniquePaths = Array.from(
    new Set([".codex-port/preserve-paths.json", ...preservePaths])
  );
  const backupDir = path.join(backupRoot, path.basename(pluginRoot));

  await fs.mkdir(backupDir, { recursive: true });

  for (const relativePath of uniquePaths) {
    const normalizedRelativePath = path.normalize(relativePath);
    const sourcePath = path.resolve(pluginRoot, normalizedRelativePath);
    if (!sourcePath.startsWith(`${path.resolve(pluginRoot)}${path.sep}`)) {
      throw new Error(`Refusing to preserve path outside plugin root: ${relativePath}`);
    }
    if (!(await exists(sourcePath))) {
      continue;
    }
    const destinationPath = path.join(backupDir, normalizedRelativePath);
    await fs.mkdir(path.dirname(destinationPath), { recursive: true });
    await fs.cp(sourcePath, destinationPath, { recursive: true, force: true });
  }

  return backupDir;
}

async function restorePreservedPaths(pluginRoot, backupDir) {
  if (!backupDir || !(await exists(backupDir))) {
    return;
  }

  const entries = await fs.readdir(backupDir, { withFileTypes: true });
  for (const entry of entries) {
    const sourcePath = path.join(backupDir, entry.name);
    const destinationPath = path.join(pluginRoot, entry.name);
    await fs.cp(sourcePath, destinationPath, { recursive: true, force: true });
  }
}

async function ensureExists(targetPath, errorMessage) {
  if (!(await exists(targetPath))) {
    throw new Error(errorMessage);
  }
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

async function writeJson(targetPath, value) {
  await fs.mkdir(path.dirname(targetPath), { recursive: true });
  await fs.writeFile(targetPath, `${JSON.stringify(value, null, 2)}\n`, "utf8");
}

function stripQuotes(value) {
  return value.replace(/^['"]|['"]$/g, "");
}

main().catch((error) => {
  console.error(error instanceof Error ? error.message : String(error));
  process.exitCode = 1;
});
