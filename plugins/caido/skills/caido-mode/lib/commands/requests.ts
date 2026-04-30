/** HTTP history commands: search, recent, get, get-response, export-curl. */

import { getClient } from "../client";
import { decodeRaw, formatHttpRaw, rawToCurl } from "../output";
import type { OutputOpts } from "../types";

export async function cmdSearch(filter: string, limit: number, after?: string, idsOnly?: boolean) {
  const client = await getClient();
  let builder = client.request.list().filter(filter).first(limit);
  if (after) builder = builder.after(after);

  const connection = await builder;

  if (idsOnly) {
    const ids = connection.edges.map(edge => edge.node.request.id);
    console.log(JSON.stringify(ids));
    return;
  }

  const results = connection.edges.map(edge => ({
    id: edge.node.request.id,
    method: edge.node.request.method,
    host: edge.node.request.host,
    path: edge.node.request.path,
    query: edge.node.request.query || undefined,
    isTls: edge.node.request.isTls,
    port: edge.node.request.port,
    statusCode: edge.node.response?.statusCode,
    roundtrip: edge.node.response?.roundtripTime,
    responseLength: edge.node.response?.length,
    createdAt: edge.node.request.createdAt,
    cursor: edge.cursor,
  }));

  console.log(JSON.stringify({
    results,
    pageInfo: connection.pageInfo,
    count: results.length,
  }, null, 2));
}

export async function cmdRecent(limit: number) {
  const client = await getClient();
  const connection = await client.request.list()
    .descending("req", "id")
    .first(limit);

  const results = connection.edges.map(edge => ({
    id: edge.node.request.id,
    method: edge.node.request.method,
    host: edge.node.request.host,
    path: edge.node.request.path,
    statusCode: edge.node.response?.statusCode,
    roundtrip: edge.node.response?.roundtripTime,
    createdAt: edge.node.request.createdAt,
  }));

  console.log(JSON.stringify({ results, count: results.length }, null, 2));
}

export async function cmdGet(requestId: string, opts: OutputOpts) {
  const client = await getClient();
  const result = await client.request.get(requestId, { raw: true });

  if (!result) {
    console.error(`Request ${requestId} not found`);
    process.exit(1);
  }

  const output: Record<string, any> = {
    id: result.request.id,
    method: result.request.method,
    host: result.request.host,
    path: result.request.path,
    port: result.request.port,
    isTls: result.request.isTls,
    createdAt: result.request.createdAt,
  };

  if (!opts.noRequest && result.request.raw) {
    output.raw = formatHttpRaw(decodeRaw(result.request.raw), opts);
  }

  if (result.response) {
    output.response = {
      statusCode: result.response.statusCode,
      roundtrip: result.response.roundtripTime,
      length: result.response.length,
    };
    if (result.response.raw) {
      output.response.raw = formatHttpRaw(decodeRaw(result.response.raw), opts);
    }
  }

  console.log(JSON.stringify(output, null, 2));
}

export async function cmdGetResponse(requestId: string, opts: OutputOpts) {
  const client = await getClient();
  const result = await client.request.get(requestId, {
    requestRaw: false,
    responseRaw: true,
  });

  if (!result) {
    console.error(`Request ${requestId} not found`);
    process.exit(1);
  }

  if (!result.response) {
    console.log(JSON.stringify({ error: "No response for this request" }));
    return;
  }

  const output: Record<string, any> = {
    statusCode: result.response.statusCode,
    roundtrip: result.response.roundtripTime,
    length: result.response.length,
  };

  if (result.response.raw) {
    output.raw = formatHttpRaw(decodeRaw(result.response.raw), opts);
  }

  console.log(JSON.stringify(output, null, 2));
}

export async function cmdExportCurl(requestId: string) {
  const client = await getClient();
  const result = await client.request.get(requestId, { raw: true });

  if (!result) {
    console.error(`Request ${requestId} not found`);
    process.exit(1);
  }

  const raw = decodeRaw(result.request.raw);
  if (!raw) {
    console.error("No raw data for this request");
    process.exit(1);
  }

  console.log(rawToCurl(raw, result.request.host, result.request.port, result.request.isTls));
}
