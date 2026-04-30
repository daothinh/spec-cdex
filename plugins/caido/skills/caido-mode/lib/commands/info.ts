/** Info commands: viewer, plugins, health, setup, auth-status. */

import { Client } from "@caido/sdk-client";
import { getClient, getSecretsPath, loadConfig, readSecrets, SecretsTokenCache, writeSecrets } from "../client";
import { PLUGIN_PACKAGES_QUERY } from "../graphql";

export async function cmdViewer() {
  const client = await getClient();
  const viewer = await client.user.viewer();
  console.log(JSON.stringify(viewer, null, 2));
}

export async function cmdPlugins() {
  const client = await getClient();
  const result = await client.graphql.query(PLUGIN_PACKAGES_QUERY, {});
  console.log(JSON.stringify((result as any).pluginPackages, null, 2));
}

export async function cmdHealth() {
  const client = await getClient();
  const health = await client.health();
  console.log(JSON.stringify(health, null, 2));
}

export async function cmdSetup(pat: string, url: string) {
  console.log(`Connecting to ${url}...`);

  const setupCache = new SecretsTokenCache();
  await setupCache.clear();

  const client = new Client({
    url,
    auth: { pat, cache: setupCache },
  });

  try {
    await client.connect({ ready: { retries: 3, timeout: 5000, interval: 1000 } });
  } catch (err: any) {
    console.error(`Failed to connect: ${err.message}`);
    console.error("\nMake sure:");
    console.error(`  1. Caido is running at ${url}`);
    console.error("  2. The PAT was created in Caido -> Settings -> Developer -> Personal Access Tokens");
    process.exit(1);
  }

  const viewer = await client.user.viewer();
  console.log(`Authenticated as: ${(viewer as any).username || (viewer as any).id || JSON.stringify(viewer)}`);

  const secrets = readSecrets();
  if (!secrets.caido) secrets.caido = {};
  secrets.caido.url = url;
  secrets.caido.pat = pat;
  writeSecrets(secrets);

  console.log(`\nSaved to ${getSecretsPath()}`);
  console.log(`URL: ${url}`);
  console.log(`PAT: ${pat.slice(0, 12)}...`);
  console.log("Access token: cached");
}

export async function cmdAuthStatus() {
  const config = loadConfig();
  const statusCache = new SecretsTokenCache();
  const client = new Client({
    url: config.url,
    auth: { pat: config.pat, cache: statusCache },
  });

  try {
    await client.connect({ ready: { retries: 2, timeout: 3000, interval: 1000 } });
    const viewer = await client.user.viewer();
    const health = await client.health();
    console.log(JSON.stringify({
      authenticated: true,
      user: viewer,
      health,
      url: config.url,
      secretsPath: getSecretsPath(),
    }, null, 2));
  } catch (err: any) {
    console.log(JSON.stringify({
      authenticated: false,
      error: err.message,
      url: config.url,
      secretsPath: getSecretsPath(),
    }, null, 2));
  }
}
