/** Helpers for reading local finding bundles and deriving Caido finding content. */

import { existsSync, readFileSync } from "fs";
import { basename, join, resolve } from "path";

const DEFAULT_SECTION_FILES = [
  "claim.md",
  "facts.md",
  "impact.md",
  "poc.md",
  "reverify.md",
  "severity.md",
] as const;

export interface BundleSection {
  fileName: string;
  label: string;
  text: string;
}

function labelFromFileName(fileName: string): string {
  return fileName
    .replace(/\.md$/i, "")
    .split(/[-_]/g)
    .map(part => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

export function firstMeaningfulLine(text: string): string | undefined {
  for (const rawLine of text.split(/\r?\n/)) {
    const line = rawLine.trim();
    if (!line) continue;
    const stripped = line
      .replace(/^#+\s*/, "")
      .replace(/^[-*+]\s+/, "")
      .replace(/^\d+\.\s+/, "")
      .trim();
    if (stripped) return stripped;
  }
  return undefined;
}

export function loadBundleSections(bundlePath: string, fileNames: readonly string[] = DEFAULT_SECTION_FILES): BundleSection[] {
  const resolvedBundle = resolve(bundlePath);
  const sections: BundleSection[] = [];
  for (const fileName of fileNames) {
    const filePath = join(resolvedBundle, fileName);
    if (!existsSync(filePath)) continue;
    const text = readFileSync(filePath, "utf-8").trim();
    if (!text) continue;
    sections.push({
      fileName,
      label: labelFromFileName(fileName),
      text,
    });
  }
  return sections;
}

export function deriveFindingTitle(bundlePath: string, fallback?: string): string {
  const sections = loadBundleSections(bundlePath, ["claim.md"]);
  const claimTitle = sections.length > 0 ? firstMeaningfulLine(sections[0].text) : undefined;
  return claimTitle || fallback || basename(resolve(bundlePath));
}

export function renderFindingDescription(bundlePath: string): string {
  const sections = loadBundleSections(bundlePath);
  if (sections.length === 0) return "";
  return sections
    .map(section => `## ${section.label}\n\n${section.text}`)
    .join("\n\n");
}
