import assert from "node:assert/strict";
import path from "node:path";
import test from "node:test";

import {
  buildTurnInput,
  collectInspectionArtifacts,
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
    technical: {
      ok: true,
      total_score: 7,
      max_possible_score: 7,
      evaluation_json_path: "technical.json",
      breakdown: {
        model_graph_matches_xml: true,
        latest_primary_plot_within_last_time: true,
        latest_logger_plot_within_last_time: true,
      },
    },
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

test("decideContinuation keeps iterating when inspection artifacts were not reviewed", () => {
  const decision = decideContinuation({
    cycle: 2,
    maxCycles: 5,
    reviewRequired: true,
    reviewExecuted: false,
    technical: {
      ok: true,
      total_score: 7,
      max_possible_score: 7,
      evaluation_json_path: "technical.json",
    },
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

  assert.equal(decision.shouldContinue, true);
  assert.match(decision.reason ?? "", /image-review turn did not run/i);
});

test("decideContinuation keeps iterating when technical guardrails detect stale plot timestamps", () => {
  const decision = decideContinuation({
    cycle: 2,
    maxCycles: 5,
    technical: {
      ok: true,
      total_score: 7,
      max_possible_score: 7,
      evaluation_json_path: "technical.json",
      breakdown: {
        model_graph_matches_xml: true,
        latest_primary_plot: "plot_00800.png",
        latest_primary_plot_within_last_time: false,
        latest_logger_plot_within_last_time: true,
      },
    },
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

  assert.equal(decision.shouldContinue, true);
  assert.match(decision.reason ?? "", /latest primary plot/i);
});

test("collectInspectionArtifacts unwraps both nested and flat MCP payloads", () => {
  const artifacts = collectInspectionArtifacts(
    [
      {
        type: "mcp_tool_call",
        status: "completed",
        tool: "render_pdf_pages",
        result: {
          structured_content: {
            result: {
              pages: [{ page: 2, path: "paper_pages/page_0002.png" }],
              manifest_path: "paper_page_manifest.json",
            },
          },
        },
      },
      {
        type: "mcp_tool_call",
        status: "completed",
        tool: "sample_output_images",
        result: {
          structured_content: {
            selected_images: ["attempts/attempt_001/plot_00000.png"],
            contact_sheet_path: "attempts/attempt_001/sample_contact_sheet.png",
          },
        },
      },
    ] as any,
    "benchmark_runs/run_123",
  );

  assert.deepEqual(artifacts.paperImagePaths, [path.join("benchmark_runs/run_123", "paper_pages/page_0002.png")]);
  assert.deepEqual(artifacts.outputImagePaths, [path.join("benchmark_runs/run_123", "attempts/attempt_001/plot_00000.png")]);
  assert.equal(
    artifacts.contactSheetPath,
    path.join("benchmark_runs/run_123", "attempts/attempt_001/sample_contact_sheet.png"),
  );
  assert.equal(artifacts.pageManifestPath, path.join("benchmark_runs/run_123", "paper_page_manifest.json"));
});

test("buildTurnInput attaches discovered inspection artifacts as local images", () => {
  const input = buildTurnInput(
    "review prompt",
    ["benchmark_runs/run_123/paper_pages/page_0002.png"],
    ["benchmark_runs/run_123/attempts/attempt_001/plot_00000.png"],
    "benchmark_runs/run_123/attempts/attempt_001/sample_contact_sheet.png",
  );

  assert.deepEqual(input, [
    { type: "text", text: "review prompt" },
    { type: "local_image", path: "benchmark_runs/run_123/paper_pages/page_0002.png" },
    { type: "local_image", path: "benchmark_runs/run_123/attempts/attempt_001/plot_00000.png" },
    { type: "local_image", path: "benchmark_runs/run_123/attempts/attempt_001/sample_contact_sheet.png" },
  ]);
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
