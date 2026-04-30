/** Codex-specific helper commands for local evidence export and finding sync. */

import { mkdirSync, writeFileSync } from "fs";
import { join, resolve } from "path";
import { deriveFindingTitle, renderFindingDescription } from "../bundle";
import { getClient } from "../client";
import { decodeRaw, formatHttpRaw, rawToCurl } from "../output";
import type { OutputOpts } from "../types";

export interface ExportEvidenceOptions extends OutputOpts {
  outDir: string;
  includeRequestRaw: boolean;
}

export async function cmdExportEvidence(requestId: string, options: ExportEvidenceOptions) {
  const client = await getClient();
  const result = await client.request.get(requestId, { raw: true });

  if (!result) {
    console.error(`Request ${requestId} not found`);
    process.exit(1);
  }

  const rawRequest = decodeRaw(result.request.raw);
  if (!rawRequest) {
    console.error("No raw data for this request");
    process.exit(1);
  }

  const outDir = resolve(options.outDir);
  mkdirSync(outDir, { recursive: true });

  const requestJsonPath = join(outDir, `request-${requestId}.json`);
  const curlPath = join(outDir, `request-${requestId}.curl.txt`);
  const responsePath = join(outDir, `response-${requestId}.txt`);
  const requestRawPath = join(outDir, `request-${requestId}.txt`);

  const metadata: Record<string, any> = {
    id: result.request.id,
    exportedAt: new Date().toISOString(),
    request: {
      method: result.request.method,
      host: result.request.host,
      path: result.request.path,
      query: result.request.query || undefined,
      port: result.request.port,
      isTls: result.request.isTls,
      createdAt: result.request.createdAt,
    },
    response: result.response ? {
      statusCode: result.response.statusCode,
      roundtrip: result.response.roundtripTime,
      length: result.response.length,
    } : null,
    files: {
      requestJson: requestJsonPath,
      curl: curlPath,
    },
  };

  writeFileSync(requestJsonPath, JSON.stringify(metadata, null, 2));
  writeFileSync(curlPath, `${rawToCurl(rawRequest, result.request.host, result.request.port, result.request.isTls)}\n`);

  if (options.includeRequestRaw) {
    writeFileSync(requestRawPath, rawRequest);
    metadata.files.requestRaw = requestRawPath;
    writeFileSync(requestJsonPath, JSON.stringify(metadata, null, 2));
  }

  if (result.response?.raw) {
    writeFileSync(responsePath, formatHttpRaw(decodeRaw(result.response.raw), options));
    metadata.files.responseRaw = responsePath;
    writeFileSync(requestJsonPath, JSON.stringify(metadata, null, 2));
  }

  console.log(JSON.stringify({
    requestId,
    outDir,
    files: metadata.files,
  }, null, 2));
}

export interface SyncFindingOptions {
  bundlePath: string;
  requestId?: string;
  findingId?: string;
  reporter?: string;
  dedupeKey?: string;
  title?: string;
  description?: string;
}

export async function cmdSyncFinding(options: SyncFindingOptions) {
  const client = await getClient();
  const bundlePath = resolve(options.bundlePath);
  const title = options.title || deriveFindingTitle(bundlePath);
  const description = options.description || renderFindingDescription(bundlePath);

  if (options.findingId) {
    const existing = await client.finding.get(options.findingId);
    if (!existing) {
      console.error(`Finding ${options.findingId} not found`);
      process.exit(1);
    }

    const finding = await client.finding.update(options.findingId, {
      title: title || existing.title,
      description: description || existing.description || "",
      hidden: existing.hidden,
    });

    console.log(JSON.stringify({
      action: "updated",
      bundlePath,
      finding,
    }, null, 2));
    return;
  }

  if (!options.requestId) {
    console.error("sync-finding requires --request-id when creating a new Caido finding");
    process.exit(1);
  }

  const finding = await client.finding.create(options.requestId, {
    title,
    description,
    reporter: options.reporter || "caido-mode",
    dedupeKey: options.dedupeKey,
  });

  console.log(JSON.stringify({
    action: "created",
    bundlePath,
    requestId: options.requestId,
    finding,
  }, null, 2));
}
