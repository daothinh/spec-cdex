import test from "node:test";
import assert from "node:assert/strict";
import { mkdtempSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { deriveFindingTitle, firstMeaningfulLine, renderFindingDescription } from "../lib/bundle.ts";

test("firstMeaningfulLine strips markdown heading markers", () => {
  const line = firstMeaningfulLine("\n# IDOR in user profile endpoint\n\nBody");
  assert.equal(line, "IDOR in user profile endpoint");
});

test("deriveFindingTitle uses claim.md when present", () => {
  const dir = mkdtempSync(join(tmpdir(), "caido-bundle-"));
  writeFileSync(join(dir, "claim.md"), "# Broken access control in /api/users/:id\n\nMore");
  assert.equal(deriveFindingTitle(dir), "Broken access control in /api/users/:id");
});

test("renderFindingDescription joins known sections", () => {
  const dir = mkdtempSync(join(tmpdir(), "caido-bundle-"));
  writeFileSync(join(dir, "claim.md"), "# Claim title");
  writeFileSync(join(dir, "facts.md"), "Observed facts");
  const description = renderFindingDescription(dir);
  assert.match(description, /## Claim/);
  assert.match(description, /## Facts/);
  assert.match(description, /Observed facts/);
});
