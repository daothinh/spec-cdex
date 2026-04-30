#!/usr/bin/env -S npx tsx
/**
 * Caido SDK Client for Codex.
 * Built on @caido/sdk-client plus thin Codex-native helpers.
 */

import { parseOutputOpts } from "./lib/types";
import { cmdSearch, cmdRecent, cmdGet, cmdGetResponse, cmdExportCurl } from "./lib/commands/requests";
import {
  cmdReplay,
  cmdSendRaw,
  cmdEdit,
  cmdReplaySessions,
  cmdCreateSession,
  cmdRenameSession,
  cmdDeleteSessions,
  cmdReplayCollections,
  cmdCreateCollection,
  cmdRenameCollection,
  cmdDeleteCollection,
  cmdCreateAutomateSession,
  cmdFuzz,
} from "./lib/commands/replay";
import { cmdFindings, cmdGetFinding, cmdCreateFinding, cmdUpdateFinding } from "./lib/commands/findings";
import {
  cmdScopes,
  cmdCreateScope,
  cmdUpdateScope,
  cmdDeleteScope,
  cmdFilters,
  cmdCreateFilter,
  cmdUpdateFilter,
  cmdDeleteFilter,
  cmdEnvs,
  cmdCreateEnv,
  cmdSelectEnv,
  cmdEnvSet,
  cmdDeleteEnv,
  cmdProjects,
  cmdSelectProject,
  cmdHostedFiles,
  cmdDeleteHostedFile,
  cmdTasks,
  cmdCancelTask,
} from "./lib/commands/management";
import { cmdInterceptStatus, cmdInterceptSet } from "./lib/commands/intercept";
import { cmdViewer, cmdPlugins, cmdHealth, cmdSetup, cmdAuthStatus } from "./lib/commands/info";
import { cmdExportEvidence, cmdSyncFinding } from "./lib/commands/evidence";

const DEBUG = process.env.DEBUG === "1";

function valueAfter(args: string[], flag: string): string | undefined {
  const idx = args.indexOf(flag);
  return idx >= 0 ? args[idx + 1] : undefined;
}

function repeatedValuesAfter(args: string[], flag: string): string[] {
  const values: string[] = [];
  for (let i = 0; i < args.length; i++) {
    if (args[i] === flag && args[i + 1]) {
      values.push(args[i + 1]);
      i++;
    }
  }
  return values;
}

function hasFlag(args: string[], flag: string): boolean {
  return args.includes(flag);
}

function printUsage() {
  console.log(`
Caido SDK Client for Codex

Usage:
  caido-client.ts <command> [options]

Core request workflow:
  search <httpql>                  Search request history
  recent [--limit <n>]             Show recent requests
  get <request-id>                 Show request + response
  get-response <request-id>        Show response only
  edit <request-id> [options]      Mutate an existing request and replay it
  replay <request-id>              Replay a request as-is
  send-raw --host <h> --raw <r>    Send a custom raw request
  export-curl <request-id>         Export a request as curl
  export-evidence <request-id> --out <dir>
                                   Save local request metadata, curl, and response artifacts

Findings:
  findings [--limit <n>]           List findings
  get-finding <id>                 Get one finding
  create-finding <request-id> --title <t> [--description <d>] [--reporter <r>] [--dedupe-key <k>]
  update-finding <id> [--title <t>] [--description <d>] [--hidden|--visible]
  sync-finding --bundle <dir> [--request-id <id>] [--finding-id <id>] [--reporter <r>] [--dedupe-key <k>]

Replay, sessions, automate:
  create-session <request-id>
  rename-session <id> <name>
  replay-sessions [--limit <n>]
  delete-sessions <id,id,...>
  replay-collections [--limit <n>]
  create-collection <name>
  rename-collection <id> <name>
  delete-collection <id>
  create-automate-session <request-id>
  fuzz <session-id>

Scope, filters, envs:
  scopes | create-scope | update-scope | delete-scope
  filters | create-filter | update-filter | delete-filter
  envs | create-env | select-env | env-set | delete-env

Project, tasks, hosted files, intercept:
  projects | select-project
  tasks | cancel-task
  hosted-files | delete-hosted-file
  intercept-status | intercept-enable | intercept-disable

Info and auth:
  viewer | plugins | health
  setup <pat> [url]
  auth-status

Examples:
  npx tsx caido-client.ts search 'req.method.eq:"POST" AND resp.code.eq:200'
  npx tsx caido-client.ts edit 123 --path /api/users/999 --compact
  npx tsx caido-client.ts export-evidence 123 --out audit-targets/acme/findings/F001/artifacts/caido
  npx tsx caido-client.ts sync-finding --bundle audit-targets/acme/findings/F001 --request-id 123
`);
}

async function main() {
  const args = process.argv.slice(2);
  const command = args[0];

  if (!command || command === "--help" || command === "-h" || command === "help") {
    printUsage();
    return;
  }

  switch (command) {
    case "search": {
      if (!args[1]) {
        console.error("Error: HTTPQL filter required");
        process.exit(1);
      }
      const limit = parseInt(valueAfter(args, "--limit") || "20", 10);
      await cmdSearch(args[1], limit, valueAfter(args, "--after"), hasFlag(args, "--ids-only"));
      return;
    }

    case "recent": {
      const limit = parseInt(valueAfter(args, "--limit") || "20", 10);
      await cmdRecent(limit);
      return;
    }

    case "get": {
      if (!args[1]) {
        console.error("Error: request-id required");
        process.exit(1);
      }
      await cmdGet(args[1], parseOutputOpts(args, 2));
      return;
    }

    case "get-response": {
      if (!args[1]) {
        console.error("Error: request-id required");
        process.exit(1);
      }
      await cmdGetResponse(args[1], parseOutputOpts(args, 2));
      return;
    }

    case "replay": {
      if (!args[1]) {
        console.error("Error: request-id required");
        process.exit(1);
      }
      await cmdReplay(args[1], valueAfter(args, "--raw"), parseOutputOpts(args, 2));
      return;
    }

    case "send-raw": {
      const host = valueAfter(args, "--host");
      const raw = valueAfter(args, "--raw");
      if (!host || !raw) {
        console.error("Error: send-raw requires --host and --raw");
        process.exit(1);
      }
      const port = parseInt(valueAfter(args, "--port") || "443", 10);
      const tls = !hasFlag(args, "--no-tls");
      await cmdSendRaw(host, port, tls, raw, parseOutputOpts(args, 1));
      return;
    }

    case "edit": {
      if (!args[1]) {
        console.error("Error: request-id required");
        process.exit(1);
      }
      await cmdEdit(args[1], {
        method: valueAfter(args, "--method"),
        path: valueAfter(args, "--path"),
        setHeaders: repeatedValuesAfter(args, "--set-header"),
        removeHeaders: repeatedValuesAfter(args, "--remove-header"),
        body: valueAfter(args, "--body"),
        replacements: repeatedValuesAfter(args, "--replace"),
      }, parseOutputOpts(args, 2));
      return;
    }

    case "export-curl": {
      if (!args[1]) {
        console.error("Error: request-id required");
        process.exit(1);
      }
      await cmdExportCurl(args[1]);
      return;
    }

    case "export-evidence": {
      if (!args[1]) {
        console.error("Error: request-id required");
        process.exit(1);
      }
      const outDir = valueAfter(args, "--out");
      if (!outDir) {
        console.error("Error: export-evidence requires --out <dir>");
        process.exit(1);
      }
      await cmdExportEvidence(args[1], {
        ...parseOutputOpts(args, 2),
        outDir,
        includeRequestRaw: hasFlag(args, "--include-request-raw"),
      });
      return;
    }

    case "create-session": {
      if (!args[1]) {
        console.error("Error: request-id required");
        process.exit(1);
      }
      await cmdCreateSession(args[1]);
      return;
    }

    case "rename-session": {
      if (!args[1] || !args[2]) {
        console.error("Error: session-id and name required");
        process.exit(1);
      }
      await cmdRenameSession(args[1], args[2]);
      return;
    }

    case "replay-sessions": {
      await cmdReplaySessions(parseInt(valueAfter(args, "--limit") || "20", 10));
      return;
    }

    case "delete-sessions": {
      if (!args[1]) {
        console.error("Error: comma-separated session IDs required");
        process.exit(1);
      }
      await cmdDeleteSessions(args[1].split(",").map(id => id.trim()).filter(Boolean));
      return;
    }

    case "replay-collections": {
      await cmdReplayCollections(parseInt(valueAfter(args, "--limit") || "20", 10));
      return;
    }

    case "create-collection": {
      if (!args[1]) {
        console.error("Error: collection name required");
        process.exit(1);
      }
      await cmdCreateCollection(args[1]);
      return;
    }

    case "rename-collection": {
      if (!args[1] || !args[2]) {
        console.error("Error: collection-id and name required");
        process.exit(1);
      }
      await cmdRenameCollection(args[1], args[2]);
      return;
    }

    case "delete-collection": {
      if (!args[1]) {
        console.error("Error: collection-id required");
        process.exit(1);
      }
      await cmdDeleteCollection(args[1]);
      return;
    }

    case "create-automate-session": {
      if (!args[1]) {
        console.error("Error: request-id required");
        process.exit(1);
      }
      await cmdCreateAutomateSession(args[1]);
      return;
    }

    case "fuzz": {
      if (!args[1]) {
        console.error("Error: session-id required");
        process.exit(1);
      }
      await cmdFuzz(args[1]);
      return;
    }

    case "findings": {
      await cmdFindings(parseInt(valueAfter(args, "--limit") || "20", 10));
      return;
    }

    case "get-finding": {
      if (!args[1]) {
        console.error("Error: finding-id required");
        process.exit(1);
      }
      await cmdGetFinding(args[1]);
      return;
    }

    case "create-finding": {
      if (!args[1]) {
        console.error("Error: request-id required");
        process.exit(1);
      }
      const title = valueAfter(args, "--title");
      if (!title) {
        console.error("Error: --title required");
        process.exit(1);
      }
      await cmdCreateFinding(
        args[1],
        title,
        valueAfter(args, "--description"),
        valueAfter(args, "--reporter"),
        valueAfter(args, "--dedupe-key"),
      );
      return;
    }

    case "update-finding": {
      if (!args[1]) {
        console.error("Error: finding-id required");
        process.exit(1);
      }
      let hidden: boolean | undefined;
      if (hasFlag(args, "--hidden")) hidden = true;
      if (hasFlag(args, "--visible")) hidden = false;
      await cmdUpdateFinding(
        args[1],
        valueAfter(args, "--title"),
        valueAfter(args, "--description"),
        hidden,
      );
      return;
    }

    case "sync-finding": {
      const bundlePath = valueAfter(args, "--bundle");
      if (!bundlePath) {
        console.error("Error: sync-finding requires --bundle <dir>");
        process.exit(1);
      }
      await cmdSyncFinding({
        bundlePath,
        requestId: valueAfter(args, "--request-id"),
        findingId: valueAfter(args, "--finding-id"),
        reporter: valueAfter(args, "--reporter"),
        dedupeKey: valueAfter(args, "--dedupe-key"),
        title: valueAfter(args, "--title"),
        description: valueAfter(args, "--description"),
      });
      return;
    }

    case "projects":
      await cmdProjects();
      return;

    case "select-project": {
      if (!args[1]) {
        console.error("Error: project id required");
        process.exit(1);
      }
      await cmdSelectProject(args[1]);
      return;
    }

    case "scopes":
      await cmdScopes();
      return;

    case "create-scope": {
      if (!args[1]) {
        console.error("Error: scope name required");
        process.exit(1);
      }
      const allow = (valueAfter(args, "--allow") || "").split(",").map(value => value.trim()).filter(Boolean);
      const deny = (valueAfter(args, "--deny") || "").split(",").map(value => value.trim()).filter(Boolean);
      await cmdCreateScope(args[1], allow, deny);
      return;
    }

    case "update-scope": {
      if (!args[1]) {
        console.error("Error: scope id required");
        process.exit(1);
      }
      const allowRaw = valueAfter(args, "--allow");
      const denyRaw = valueAfter(args, "--deny");
      await cmdUpdateScope(
        args[1],
        valueAfter(args, "--name"),
        allowRaw ? allowRaw.split(",").map(value => value.trim()).filter(Boolean) : undefined,
        denyRaw ? denyRaw.split(",").map(value => value.trim()).filter(Boolean) : undefined,
      );
      return;
    }

    case "delete-scope": {
      if (!args[1]) {
        console.error("Error: scope id required");
        process.exit(1);
      }
      await cmdDeleteScope(args[1]);
      return;
    }

    case "filters":
      await cmdFilters();
      return;

    case "create-filter": {
      if (!args[1]) {
        console.error("Error: filter name required");
        process.exit(1);
      }
      const query = valueAfter(args, "--query");
      if (!query) {
        console.error("Error: --query required");
        process.exit(1);
      }
      await cmdCreateFilter(args[1], query, valueAfter(args, "--alias"));
      return;
    }

    case "update-filter": {
      if (!args[1]) {
        console.error("Error: filter id required");
        process.exit(1);
      }
      await cmdUpdateFilter(
        args[1],
        valueAfter(args, "--name"),
        valueAfter(args, "--query"),
        valueAfter(args, "--alias"),
      );
      return;
    }

    case "delete-filter": {
      if (!args[1]) {
        console.error("Error: filter id required");
        process.exit(1);
      }
      await cmdDeleteFilter(args[1]);
      return;
    }

    case "envs":
      await cmdEnvs();
      return;

    case "create-env": {
      if (!args[1]) {
        console.error("Error: environment name required");
        process.exit(1);
      }
      await cmdCreateEnv(args[1]);
      return;
    }

    case "select-env":
      await cmdSelectEnv(args[1]);
      return;

    case "env-set": {
      if (!args[1] || !args[2] || args[3] === undefined) {
        console.error("Error: env-set requires <env-id> <var-name> <value>");
        process.exit(1);
      }
      await cmdEnvSet(args[1], args[2], args[3]);
      return;
    }

    case "delete-env": {
      if (!args[1]) {
        console.error("Error: environment id required");
        process.exit(1);
      }
      await cmdDeleteEnv(args[1]);
      return;
    }

    case "hosted-files":
      await cmdHostedFiles();
      return;

    case "delete-hosted-file": {
      if (!args[1]) {
        console.error("Error: hosted file id required");
        process.exit(1);
      }
      await cmdDeleteHostedFile(args[1]);
      return;
    }

    case "tasks":
      await cmdTasks();
      return;

    case "cancel-task": {
      if (!args[1]) {
        console.error("Error: task id required");
        process.exit(1);
      }
      await cmdCancelTask(args[1]);
      return;
    }

    case "intercept-status":
      await cmdInterceptStatus();
      return;

    case "intercept-enable":
      await cmdInterceptSet(true);
      return;

    case "intercept-disable":
      await cmdInterceptSet(false);
      return;

    case "viewer":
      await cmdViewer();
      return;

    case "plugins":
      await cmdPlugins();
      return;

    case "health":
      await cmdHealth();
      return;

    case "setup": {
      const pat = args[1];
      if (!pat) {
        console.error("Usage: npx tsx caido-client.ts setup <pat> [url]");
        process.exit(1);
      }
      await cmdSetup(pat, args[2] || process.env.CAIDO_URL || "http://localhost:8080");
      return;
    }

    case "auth-status":
      await cmdAuthStatus();
      return;

    default:
      console.error(`Unknown command: ${command}`);
      printUsage();
      process.exit(1);
  }
}

main().catch((err: any) => {
  console.error(`Error: ${err.message}`);
  if (DEBUG && err.stack) console.error(err.stack);
  process.exit(1);
});
