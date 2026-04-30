/** Replay, edit, session, collection, and fuzz commands. */

import { getClient } from "../client";
import { decodeRaw, formatHttpRaw } from "../output";
import {
  CREATE_AUTOMATE_SESSION,
  CREATE_REPLAY_SESSION_RAW,
  GET_AUTOMATE_SESSION,
  START_AUTOMATE_TASK,
} from "../graphql";
import type { OutputOpts } from "../types";

export interface EditOptions {
  method?: string;
  path?: string;
  setHeaders: string[];
  removeHeaders: string[];
  body?: string;
  replacements: string[];
}

export function buildEditedRequest(raw: string, edits: EditOptions): string {
  let updatedRaw = raw;

  for (const replacement of edits.replacements) {
    const [from, to] = replacement.split(":::");
    if (from && to !== undefined) {
      updatedRaw = updatedRaw.replaceAll(from, to);
    }
  }

  const lineEnd = updatedRaw.includes("\r\n") ? "\r\n" : "\n";
  const parts = updatedRaw.split(lineEnd + lineEnd);
  const headerBlock = parts[0];
  let bodyPart = parts.slice(1).join(lineEnd + lineEnd);

  const headerLines = headerBlock.split(lineEnd);
  let requestLine = headerLines[0];
  let headers = headerLines.slice(1);

  if (edits.method) {
    const spaceIdx = requestLine.indexOf(" ");
    if (spaceIdx > 0) {
      requestLine = edits.method + requestLine.substring(spaceIdx);
    }
  }

  if (edits.path) {
    const firstSpace = requestLine.indexOf(" ");
    const lastSpace = requestLine.lastIndexOf(" ");
    if (firstSpace > 0 && lastSpace > firstSpace) {
      requestLine = requestLine.substring(0, firstSpace + 1) + edits.path + requestLine.substring(lastSpace);
    }
  }

  for (const name of edits.removeHeaders) {
    headers = headers.filter(header => !header.toLowerCase().startsWith(name.toLowerCase() + ":"));
  }

  for (const header of edits.setHeaders) {
    const colonIdx = header.indexOf(":");
    if (colonIdx > 0) {
      const name = header.substring(0, colonIdx).trim();
      headers = headers.filter(existing => !existing.toLowerCase().startsWith(name.toLowerCase() + ":"));
      headers.push(header.trim());
    }
  }

  if (edits.body !== undefined) {
    bodyPart = edits.body;
    const contentLength = new TextEncoder().encode(bodyPart).length;
    headers = headers.filter(header => !header.toLowerCase().startsWith("content-length:"));
    headers.push(`Content-Length: ${contentLength}`);
  }

  return [requestLine, ...headers].join(lineEnd) + lineEnd + lineEnd + bodyPart;
}

export async function cmdReplay(requestId: string, rawOverride: string | undefined, opts: OutputOpts) {
  const client = await getClient();
  const original = await client.request.get(requestId, { raw: true });
  if (!original) {
    console.error(`Request ${requestId} not found`);
    process.exit(1);
  }

  const session = await client.replay.sessions.create({
    requestSource: { id: requestId },
  });

  const raw = rawOverride || decodeRaw(original.request.raw);
  if (!raw) {
    console.error("No raw data for this request");
    process.exit(1);
  }

  const result = await client.replay.send(session.id, {
    raw,
    connection: {
      host: original.request.host,
      port: original.request.port,
      isTLS: original.request.isTls,
    },
  });

  const output: Record<string, any> = {
    sessionId: session.id,
    status: result.status,
    error: result.error,
  };

  if (result.entry) {
    output.entryId = result.entry.id;
    if (result.entry.response) {
      output.response = {
        statusCode: result.entry.response.statusCode,
        roundtrip: result.entry.response.roundtripTime,
        length: result.entry.response.length,
      };
      if (result.entry.response.raw) {
        output.response.raw = formatHttpRaw(decodeRaw(result.entry.response.raw), opts);
      }
    }
  }

  console.log(JSON.stringify(output, null, 2));
}

export async function cmdSendRaw(host: string, port: number, tls: boolean, raw: string, opts: OutputOpts) {
  const client = await getClient();

  const createResult = await client.graphql.mutation(CREATE_REPLAY_SESSION_RAW, {
    input: {
      requestSource: {
        raw: {
          connectionInfo: { host, port, isTLS: tls },
          raw: Buffer.from(raw).toString("base64"),
        },
      },
    },
  });
  const session = (createResult as any).createReplaySession.session;

  const result = await client.replay.send(session.id, {
    raw,
    connection: { host, port, isTLS: tls },
  });

  const output: Record<string, any> = {
    sessionId: session.id,
    status: result.status,
    error: result.error,
  };

  if (result.entry?.response) {
    output.response = {
      statusCode: result.entry.response.statusCode,
      roundtrip: result.entry.response.roundtripTime,
      length: result.entry.response.length,
    };
    if (result.entry.response.raw) {
      output.response.raw = formatHttpRaw(decodeRaw(result.entry.response.raw), opts);
    }
  }

  console.log(JSON.stringify(output, null, 2));
}

export async function cmdEdit(requestId: string, edits: EditOptions, opts: OutputOpts) {
  const client = await getClient();
  const original = await client.request.get(requestId, { raw: true });

  if (!original) {
    console.error(`Request ${requestId} not found`);
    process.exit(1);
  }

  const raw = decodeRaw(original.request.raw);
  if (!raw) {
    console.error("No raw data for this request");
    process.exit(1);
  }

  const modifiedRaw = buildEditedRequest(raw, edits);
  const session = await client.replay.sessions.create({
    requestSource: { id: requestId },
  });

  const result = await client.replay.send(session.id, {
    raw: modifiedRaw,
    connection: {
      host: original.request.host,
      port: original.request.port,
      isTLS: original.request.isTls,
    },
  });

  const output: Record<string, any> = {
    sessionId: session.id,
    status: result.status,
    error: result.error,
  };

  if (!opts.noRequest) {
    output.modifiedRequest = formatHttpRaw(modifiedRaw, opts);
  }

  if (result.entry?.response) {
    output.response = {
      statusCode: result.entry.response.statusCode,
      roundtrip: result.entry.response.roundtripTime,
      length: result.entry.response.length,
    };
    if (result.entry.response.raw) {
      output.response.raw = formatHttpRaw(decodeRaw(result.entry.response.raw), opts);
    }
  }

  console.log(JSON.stringify(output, null, 2));
}

export async function cmdReplaySessions(limit: number) {
  const client = await getClient();
  const connection = await client.replay.sessions.list().first(limit);

  const results = connection.edges.map(edge => ({
    id: edge.node.id,
    name: edge.node.name,
    collectionId: edge.node.collectionId,
    activeEntryId: edge.node.activeEntryId,
  }));

  console.log(JSON.stringify({ results, count: results.length }, null, 2));
}

export async function cmdCreateSession(requestId: string) {
  const client = await getClient();
  const session = await client.replay.sessions.create({
    requestSource: { id: requestId },
  });
  console.log(JSON.stringify({
    id: session.id,
    name: session.name,
    collectionId: session.collectionId,
  }, null, 2));
}

export async function cmdRenameSession(sessionId: string, name: string) {
  const client = await getClient();
  await client.replay.sessions.rename(sessionId, name);
  console.log(JSON.stringify({ id: sessionId, name, renamed: true }, null, 2));
}

export async function cmdDeleteSessions(ids: string[]) {
  const client = await getClient();
  await client.replay.sessions.delete(ids);
  console.log(JSON.stringify({ deleted: ids }, null, 2));
}

export async function cmdReplayCollections(limit: number) {
  const client = await getClient();
  const connection = await client.replay.collections.list().first(limit);

  const results = connection.edges.map(edge => ({
    id: edge.node.id,
    name: edge.node.name,
  }));

  console.log(JSON.stringify({ results, count: results.length }, null, 2));
}

export async function cmdCreateCollection(name: string) {
  const client = await getClient();
  const collection = await client.replay.collections.create({ name });
  console.log(JSON.stringify({ id: collection.id, name: collection.name }, null, 2));
}

export async function cmdRenameCollection(collectionId: string, name: string) {
  const client = await getClient();
  await client.replay.collections.rename(collectionId, name);
  console.log(JSON.stringify({ id: collectionId, name, renamed: true }, null, 2));
}

export async function cmdDeleteCollection(collectionId: string) {
  const client = await getClient();
  await client.replay.collections.delete(collectionId);
  console.log(JSON.stringify({ deleted: collectionId }, null, 2));
}

export async function cmdCreateAutomateSession(requestId: string) {
  const client = await getClient();
  const result = await client.graphql.mutation(CREATE_AUTOMATE_SESSION, {
    input: { requestSource: { id: requestId } },
  });
  console.log(JSON.stringify((result as any).createAutomateSession.session, null, 2));
}

export async function cmdFuzz(sessionId: string) {
  const client = await getClient();
  const check = await client.graphql.query(GET_AUTOMATE_SESSION, { id: sessionId });
  const session = (check as any).automateSession;
  if (!session) {
    console.error(`Automate session ${sessionId} not found`);
    process.exit(1);
  }

  console.log(JSON.stringify({
    note: "Starting automate task with existing session settings. Configure payloads in Caido UI.",
    sessionId,
  }, null, 2));

  const startResult = await client.graphql.mutation(START_AUTOMATE_TASK, { automateSessionId: sessionId });
  const task = (startResult as any).startAutomateTask.automateTask;

  console.log(JSON.stringify({
    sessionId,
    taskId: task.id,
    status: "started",
  }, null, 2));
}
