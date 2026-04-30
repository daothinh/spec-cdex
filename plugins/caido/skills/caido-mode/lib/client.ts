/** Caido SDK client singleton with Codex-native secrets storage. */

import { Client, type CachedToken, type TokenCache } from "@caido/sdk-client";
import { existsSync, mkdirSync, readFileSync, writeFileSync } from "fs";
import { homedir } from "os";
import { dirname, join } from "path";

export const DEFAULT_CAIDO_URL = "http://localhost:8080";
export const SECRETS_PATH_ENV = "CAIDO_SECRETS_PATH";

export interface CaidoConfig {
  url: string;
  pat: string;
}

export function getSecretsPath(): string {
  return process.env[SECRETS_PATH_ENV] || join(homedir(), ".codex", "caido", "secrets.json");
}

export function readSecrets(): Record<string, any> {
  const secretsPath = getSecretsPath();
  try {
    if (existsSync(secretsPath)) {
      return JSON.parse(readFileSync(secretsPath, "utf-8"));
    }
  } catch {}
  return {};
}

export function writeSecrets(secrets: Record<string, any>): void {
  const secretsPath = getSecretsPath();
  const dir = dirname(secretsPath);
  if (!existsSync(dir)) mkdirSync(dir, { recursive: true });
  writeFileSync(secretsPath, JSON.stringify(secrets, null, 2));
}

/**
 * Custom TokenCache that persists access tokens to the Codex secret file.
 * The first PAT-authenticated connect exchanges the PAT for an access token.
 */
export class SecretsTokenCache implements TokenCache {
  private cachedToken: CachedToken | null = null;

  async load(): Promise<CachedToken | undefined> {
    if (this.cachedToken) return this.cachedToken;
    try {
      const secrets = readSecrets();
      if (secrets.caido?.cachedToken?.accessToken) {
        this.cachedToken = secrets.caido.cachedToken;
        return this.cachedToken;
      }
    } catch {}
    return undefined;
  }

  async save(token: CachedToken): Promise<void> {
    this.cachedToken = token;
    const secrets = readSecrets();
    if (!secrets.caido) secrets.caido = {};
    secrets.caido.cachedToken = token;
    writeSecrets(secrets);
  }

  async clear(): Promise<void> {
    this.cachedToken = null;
    const secrets = readSecrets();
    if (secrets.caido?.cachedToken) {
      delete secrets.caido.cachedToken;
      writeSecrets(secrets);
    }
  }
}

export function loadConfig(): CaidoConfig {
  const envPat = process.env.CAIDO_PAT;
  const envUrl = process.env.CAIDO_URL;
  const secrets = readSecrets();
  const saved = secrets.caido || {};

  const url = envUrl || saved.url || DEFAULT_CAIDO_URL;
  const pat = envPat || saved.pat;

  if (pat) return { url, pat };

  console.error("Error: No Caido PAT found.\n");
  console.error("Setup:");
  console.error("  1. Open Caido -> Settings -> Developer -> Personal Access Tokens");
  console.error("  2. Create a token");
  console.error("  3. Run: npx tsx caido-client.ts setup <token>");
  console.error("  Or set env vars: CAIDO_PAT=<token> CAIDO_URL=http://localhost:8080");
  console.error(`  Optional secret cache path override: ${SECRETS_PATH_ENV}=<absolute-path>`);
  process.exit(1);
}

let clientSingleton: Client | null = null;
const tokenCache = new SecretsTokenCache();

export async function getClient(): Promise<Client> {
  if (clientSingleton) return clientSingleton;

  const config = loadConfig();
  clientSingleton = new Client({
    url: config.url,
    auth: { pat: config.pat, cache: tokenCache },
  });

  try {
    await clientSingleton.connect({ ready: { retries: 3, timeout: 5000, interval: 1000 } });
  } catch (err: any) {
    if (err.message?.includes("not ready")) {
      console.error("Error: Caido instance is not ready. Is Caido running?");
      console.error(`  Tried: ${config.url}`);
    } else {
      console.error(`Connection error: ${err.message}`);
    }
    process.exit(1);
  }

  return clientSingleton;
}
