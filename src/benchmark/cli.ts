import process from "node:process";

import { applyCliOverrides, loadConfig } from "./config.js";
import { BenchmarkRunner } from "./runner.js";
import type { BenchmarkConfig } from "./types.js";

async function main(): Promise<void> {
  const args = process.argv.slice(2);
  const overrides: Partial<BenchmarkConfig> = {};
  let configPath: string | undefined;
  let maxPapers: number | undefined;

  for (let index = 0; index < args.length; index += 1) {
    const arg = args[index];
    const next = args[index + 1];
    switch (arg) {
      case "--config":
        configPath = next;
        index += 1;
        break;
      case "--papers-dir":
        overrides.papersDir = next;
        index += 1;
        break;
      case "--results-dir":
        overrides.resultsDir = next;
        index += 1;
        break;
      case "--model":
        overrides.model = next;
        index += 1;
        break;
      case "--reasoning-effort":
        overrides.reasoningEffort = next as BenchmarkConfig["reasoningEffort"];
        index += 1;
        break;
      case "--max-turns":
        overrides.maxTurnsPerPaper = Number(next);
        index += 1;
        break;
      case "--page-render-dpi":
        overrides.pageRenderDpi = Number(next);
        index += 1;
        break;
      case "--representative-output-frames":
        overrides.representativeOutputFrames = Number(next);
        index += 1;
        break;
      case "--max-papers":
        maxPapers = Number(next);
        index += 1;
        break;
      case "--help":
        printHelp();
        return;
      default:
        throw new Error(`Unknown argument: ${arg}`);
    }
  }

  const baseConfig = await loadConfig(configPath);
  const config = applyCliOverrides(baseConfig, overrides);
  const runner = new BenchmarkRunner(config);
  const summary = await runner.run(maxPapers);

  console.log(JSON.stringify(summary, null, 2));
}

function printHelp(): void {
  console.log(
    [
      "Usage: npm run benchmark -- [options]",
      "",
      "Options:",
      "  --config <path>",
      "  --papers-dir <path>",
      "  --results-dir <path>",
      "  --model <name>",
      "  --reasoning-effort <minimal|low|medium|high|xhigh>",
      "  --max-turns <number>",
      "  --page-render-dpi <number>",
      "  --representative-output-frames <number>",
      "  --max-papers <number>",
    ].join("\n"),
  );
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
