import test from "node:test";
import assert from "node:assert/strict";
import { buildEditedRequest } from "../lib/commands/replay.ts";

test("buildEditedRequest swaps method, path, headers, and body", () => {
  const raw = [
    "GET /api/users/123 HTTP/1.1",
    "Host: example.com",
    "Cookie: a=b",
    "X-Test: old",
    "",
    "",
  ].join("\r\n");

  const edited = buildEditedRequest(raw, {
    method: "POST",
    path: "/api/users/999",
    setHeaders: ["X-Test: new", "X-Role: admin"],
    removeHeaders: ["Cookie"],
    body: "{\"active\":true}",
    replacements: [],
  });

  assert.match(edited, /^POST \/api\/users\/999 HTTP\/1\.1/);
  assert.doesNotMatch(edited, /Cookie:/);
  assert.match(edited, /X-Test: new/);
  assert.match(edited, /X-Role: admin/);
  assert.match(edited, /Content-Length: 15/);
  assert.match(edited, /\{"active":true\}$/);
});

test("buildEditedRequest applies textual replacements before structured edits", () => {
  const raw = [
    "GET /api/me HTTP/1.1",
    "Host: example.com",
    "Authorization: Bearer user123",
    "",
    "",
  ].join("\n");

  const edited = buildEditedRequest(raw, {
    replacements: ["user123:::user999"],
    setHeaders: [],
    removeHeaders: [],
  });

  assert.match(edited, /Bearer user999/);
});
