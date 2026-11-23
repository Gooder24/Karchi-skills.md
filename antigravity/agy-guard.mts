// agy-guard: Antigravity (agy) with only the models Karchi allows (Karchi, 2026-11-23).
//
// T3 runs it as the Antigravity executable (providerInstances.antigravity_m_j.config.binaryPath =
// ~/.work/karchi-skills/antigravity/bin/agy). In `agy acp` it leaves other models out of every list the agent
// sends, so T3 offers and accepts only these, and refuses a request that picks another model anyway.
// Run directly (`bin/agy -p … --model X`) it refuses another --model and passes the rest to agy unchanged.
// To allow another model, add its family to ALLOWED; models ids are the family plus an effort (-low, -high…).
import { spawn } from "node:child_process";
import { homedir } from "node:os";
import { join } from "node:path";
import { createInterface } from "node:readline";

const ALLOWED = ["gemini-4-neon", "gemini-4-hydrogen", "gemini-pro-orchestrator-neon"];
const REAL_AGY = process.env.AGY_GUARD_REAL ?? join(homedir(), ".local/bin/agy");

const allowed = (id: unknown) =>
  typeof id === "string" && ALLOWED.some((family) => id === family || id.startsWith(`${family}-`));

type Json = null | boolean | number | string | Json[] | { [key: string]: Json };
const isObject = (value: Json | undefined): value is { [key: string]: Json } =>
  typeof value === "object" && value !== null && !Array.isArray(value);

// Removes other models wherever agy lists them: models.availableModels and the "model" config option.
function filterModels(value: Json): Json {
  if (Array.isArray(value)) return value.map(filterModels);
  if (!isObject(value)) return value;
  const out: { [key: string]: Json } = {};
  for (const [key, child] of Object.entries(value)) {
    if (key === "availableModels" && Array.isArray(child)) {
      out[key] = child.filter((model) => isObject(model) && allowed(model.modelId));
    } else if (key === "options" && value.id === "model" && Array.isArray(child)) {
      out[key] = child.filter((option) => isObject(option) && allowed(option.value));
    } else out[key] = filterModels(child);
  }
  if (value.id === "model" && typeof value.currentValue === "string" && !allowed(value.currentValue)) {
    out.currentValue = ALLOWED[0];
  }
  return out;
}

// The model a client request asks for, when it is one.
function requestedModel(message: Json): unknown {
  if (!isObject(message) || !isObject(message.params)) return undefined;
  if (message.method === "session/set_model") return message.params.modelId ?? "";
  if (message.method === "session/set_config_option" && message.params.configId === "model") {
    return message.params.value ?? "";
  }
  return undefined;
}

function runAcp(args: string[]) {
  const agy = spawn(REAL_AGY, args, { stdio: ["pipe", "pipe", "inherit"] });
  agy.on("exit", (code, signal) => process.exit(code ?? (signal ? 1 : 0)));
  process.on("SIGTERM", () => agy.kill("SIGTERM"));
  process.on("SIGINT", () => agy.kill("SIGINT"));

  createInterface({ input: agy.stdout }).on("line", (line) => {
    let message: Json;
    try {
      message = JSON.parse(line);
    } catch {
      process.stdout.write(`${line}\n`);
      return;
    }
    process.stdout.write(`${JSON.stringify(filterModels(message))}\n`);
  });

  createInterface({ input: process.stdin }).on("line", (line) => {
    let message: Json | undefined;
    try {
      message = JSON.parse(line);
    } catch {}
    const model = message === undefined ? undefined : requestedModel(message);
    if (model !== undefined && !allowed(model) && isObject(message) && message.id !== undefined) {
      const error = {
        code: -32602,
        message: `Model '${String(model)}' is not allowed here. Allowed: ${ALLOWED.join(", ")}.`,
      };
      process.stdout.write(`${JSON.stringify({ jsonrpc: "2.0", id: message.id, error })}\n`);
      return;
    }
    agy.stdin.write(`${line}\n`);
  }).on("close", () => agy.stdin.end());
}

function runCli(args: string[]) {
  const at = args.findIndex((arg) => arg === "--model" || arg.startsWith("--model="));
  if (at !== -1) {
    const model = args[at].startsWith("--model=") ? args[at].slice("--model=".length) : args[at + 1];
    if (!allowed(model)) {
      process.stderr.write(`agy-guard: model '${model ?? ""}' is not allowed. Allowed: ${ALLOWED.join(", ")}.\n`);
      process.exit(2);
    }
  }
  const agy = spawn(REAL_AGY, args, { stdio: "inherit" });
  agy.on("exit", (code, signal) => process.exit(code ?? (signal ? 1 : 0)));
}

const args = process.argv.slice(2);
if (args[0] === "acp") runAcp(args);
else runCli(args);
