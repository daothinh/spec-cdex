import test from "node:test";
import assert from "node:assert/strict";
import { extractHeaders, rawToCurl, truncateBody } from "../lib/output.ts";

test("extractHeaders stops before the body", () => {
  const raw = "HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\n\r\nhello";
  assert.equal(extractHeaders(raw), "HTTP/1.1 200 OK\r\nContent-Type: text/plain");
});

test("truncateBody limits lines and chars", () => {
  const raw = "HTTP/1.1 200 OK\r\nX-Test: 1\r\n\r\nline1\nline2\nline3";
  const truncated = truncateBody(raw, 2, 100);
  assert.match(truncated, /\[TRUNCATED at 2 lines, total 3\]/);
});

test("rawToCurl preserves headers and body", () => {
  const raw = [
    "POST /api/users HTTP/1.1",
    "Host: example.com",
    "Authorization: Bearer token",
    "Content-Type: application/json",
    "",
    "{\"role\":\"admin\"}",
  ].join("\r\n");
  const curl = rawToCurl(raw, "example.com", 443, true);
  assert.match(curl, /^curl -X POST 'https:\/\/example.com\/api\/users'/);
  assert.match(curl, /Authorization: Bearer token/);
  assert.match(curl, /-d '\{"role":"admin"\}'/);
});
