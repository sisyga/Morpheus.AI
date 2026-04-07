import assert from "node:assert/strict";
import test from "node:test";

import { applyCliOverrides, loadConfig } from "../src/benchmark/config.js";

test("loadConfig reads the default benchmark config", async () => {
  const config = await loadConfig();
  assert.equal(config.model, "gpt-5.4");
  assert.equal(config.reasoningEffort, "xhigh");
  assert.equal(config.maxTurnsPerPaper, 5);
  assert.equal(config.pageRenderDpi, 150);
  assert.equal(config.codexQuotaFallbackEnabled, true);
  assert.equal(config.codexQuotaFallbackWaitMinutes, 300);
  assert.equal(config.codexQuotaMaxRetries, 3);
  assert.equal(config.codexQuotaRetryBufferSeconds, 60);
  assert.ok(config.papersDir.endsWith("benchmark_papers"));
  assert.ok(config.benchmarkFocusDir?.endsWith("benchmark_focus"));
});

test("applyCliOverrides resolves local path overrides", async () => {
  const config = await loadConfig();
  const overridden = applyCliOverrides(config, {
    papersDir: "alt_papers",
    resultsDir: "alt_results",
    benchmarkFocusDir: "alt_focus",
  });

  assert.ok(overridden.papersDir.endsWith("alt_papers"));
  assert.ok(overridden.resultsDir.endsWith("alt_results"));
  assert.ok(overridden.benchmarkFocusDir?.endsWith("alt_focus"));
  assert.equal(overridden.model, config.model);
});
