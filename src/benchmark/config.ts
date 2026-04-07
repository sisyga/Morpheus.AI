import { mkdir, readFile } from "node:fs/promises";
import path from "node:path";
import process from "node:process";

import type { BenchmarkConfig } from "./types.js";

const DEFAULT_CONFIG_PATH = "benchmark.config.json";

export async function loadConfig(configPath?: string): Promise<BenchmarkConfig> {
  const resolvedPath = path.resolve(process.cwd(), configPath ?? DEFAULT_CONFIG_PATH);
  const raw = await readFile(resolvedPath, "utf8");
  const parsed = JSON.parse(raw) as Partial<BenchmarkConfig>;

  const config: BenchmarkConfig = {
    papersDir: path.resolve(process.cwd(), parsed.papersDir ?? "benchmark_papers"),
    resultsDir: path.resolve(process.cwd(), parsed.resultsDir ?? "benchmark_runs"),
    benchmarkFocusDir:
      parsed.benchmarkFocusDir === null
        ? null
        : path.resolve(process.cwd(), parsed.benchmarkFocusDir ?? "benchmark_focus"),
    model: parsed.model ?? "gpt-5.4",
    reasoningEffort: parsed.reasoningEffort ?? "xhigh",
    maxTurnsPerPaper: parsed.maxTurnsPerPaper ?? 5,
    pageRenderDpi: parsed.pageRenderDpi ?? 150,
    representativeOutputFrames: parsed.representativeOutputFrames ?? 5,
    codexQuotaFallbackEnabled: parsed.codexQuotaFallbackEnabled ?? true,
    codexQuotaFallbackWaitMinutes: parsed.codexQuotaFallbackWaitMinutes ?? 300,
    codexQuotaMaxRetries: parsed.codexQuotaMaxRetries ?? 3,
    codexQuotaRetryBufferSeconds: parsed.codexQuotaRetryBufferSeconds ?? 60,
    mcpCommand: parsed.mcpCommand ?? ["python", "server.py"],
    skillPaths: (parsed.skillPaths ?? [".agents/skills/morpheus/SKILL.md"]).map((skillPath) =>
      path.resolve(process.cwd(), skillPath),
    ),
  };

  await mkdir(config.resultsDir, { recursive: true });
  return config;
}

export function applyCliOverrides(
  config: BenchmarkConfig,
  overrides: Partial<BenchmarkConfig>,
): BenchmarkConfig {
  return {
    ...config,
    ...overrides,
    papersDir: overrides.papersDir ? path.resolve(process.cwd(), overrides.papersDir) : config.papersDir,
    resultsDir: overrides.resultsDir ? path.resolve(process.cwd(), overrides.resultsDir) : config.resultsDir,
    benchmarkFocusDir:
      overrides.benchmarkFocusDir === undefined
        ? config.benchmarkFocusDir
        : overrides.benchmarkFocusDir === null
          ? null
          : path.resolve(process.cwd(), overrides.benchmarkFocusDir),
    skillPaths: overrides.skillPaths
      ? overrides.skillPaths.map((skillPath) => path.resolve(process.cwd(), skillPath))
      : config.skillPaths,
  };
}
