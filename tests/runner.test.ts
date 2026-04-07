import assert from "node:assert/strict";
import test from "node:test";

import {
  decideContinuation,
  getCodexQuotaResetWaitMs,
  isCodexQuotaLimitError,
} from "../src/benchmark/runner.js";
import type { ReproductionReport } from "../src/benchmark/types.js";

const flawlessReproduction = {
  source_coverage: { score: 2, evidence: ["paper page 1"], rationale: "Covered sources." },
  mechanism_mapping: { score: 2, evidence: ["model.xml"], rationale: "Mapped mechanisms." },
  observable_alignment: { score: 2, evidence: ["plot_00000.png"], rationale: "Matched outputs." },
  parameter_plausibility: { score: 2, evidence: ["model.xml"], rationale: "Plausible parameters." },
  total_score: 8,
  summary: "Flawless reproduction.",
} satisfies ReproductionReport;

test("decideContinuation keeps iterating completed but imperfect reproductions", () => {
  const decision = decideContinuation({
    cycle: 1,
    maxCycles: 5,
    technical: { ok: true, total_score: 7, max_possible_score: 7, evaluation_json_path: "technical.json" },
    cycleResponse: {
      runId: "run_123",
      status: "completed",
      summary: "Completed, but coarse.",
      modelChanged: true,
      morpheusRan: true,
      needsAnotherCycle: false,
      needsAnotherImageReview: false,
      reproduction: {
        ...flawlessReproduction,
        observable_alignment: {
          score: 1,
          evidence: ["plot_00000.png"],
          rationale: "Partial match.",
        },
        total_score: 7,
      },
    },
  });

  assert.equal(decision.shouldContinue, true);
  assert.match(decision.reason ?? "", /7\/8/);
});

test("decideContinuation allows completion only when reproduction and technical scores are maxed", () => {
  const decision = decideContinuation({
    cycle: 3,
    maxCycles: 5,
    technical: { ok: true, total_score: 7, max_possible_score: 7, evaluation_json_path: "technical.json" },
    cycleResponse: {
      runId: "run_123",
      status: "completed",
      summary: "Completed.",
      modelChanged: true,
      morpheusRan: true,
      needsAnotherCycle: false,
      needsAnotherImageReview: false,
      reproduction: flawlessReproduction,
    },
  });

  assert.equal(decision.shouldContinue, false);
  assert.equal(decision.reason, null);
});

test("isCodexQuotaLimitError detects Codex usage quota messages", () => {
  assert.equal(
    isCodexQuotaLimitError("Codex Exec exited with code 1: usage limit reached. Try again at 4:30 PM."),
    true,
  );
  assert.equal(isCodexQuotaLimitError("Turn stream ended before completion."), false);
});

test("getCodexQuotaResetWaitMs uses relative reset times plus buffer", () => {
  const waitMs = getCodexQuotaResetWaitMs("Codex quota reached; try again in 2 hours, 30 minutes.", {
    fallbackWaitMs: 300 * 60 * 1000,
    retryBufferMs: 60 * 1000,
  });

  assert.equal(waitMs, (2 * 60 * 60 + 30 * 60 + 60) * 1000);
});

test("getCodexQuotaResetWaitMs uses same-day clock reset times", () => {
  const waitMs = getCodexQuotaResetWaitMs("Codex usage limit reached. Try again at 4:30 PM.", {
    fallbackWaitMs: 300 * 60 * 1000,
    retryBufferMs: 60 * 1000,
    now: new Date(2026, 3, 7, 15, 0, 0, 0),
  });

  assert.equal(waitMs, (90 * 60 + 60) * 1000);
});

test("getCodexQuotaResetWaitMs falls back to configured 5h wait when reset time is missing", () => {
  const waitMs = getCodexQuotaResetWaitMs("Codex quota reached.", {
    fallbackWaitMs: 300 * 60 * 1000,
    retryBufferMs: 60 * 1000,
  });

  assert.equal(waitMs, (300 * 60 + 60) * 1000);
});
