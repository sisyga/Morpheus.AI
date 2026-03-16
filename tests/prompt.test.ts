import assert from "node:assert/strict";
import test from "node:test";

import { buildCyclePrompt, parseCycleResponse } from "../src/benchmark/prompt.js";

test("buildCyclePrompt includes staged artifact paths", () => {
  const prompt = buildCyclePrompt({
    paperName: "1_Szabo2010_clean.pdf",
    pdfPath: "benchmark_papers/1_Szabo2010_clean.pdf",
    runId: "run_123",
    runDir: "benchmark_runs/run_123",
    paperTextPath: "benchmark_runs/run_123/paper.txt",
    pageManifestPath: "benchmark_runs/run_123/paper_page_manifest.json",
    figureManifestPath: "benchmark_runs/run_123/paper_figure_manifest.json",
    cycle: 2,
    previousSummary: "Initial run complete",
    technicalEvaluationPath: "benchmark_runs/run_123/technical_evaluation.json",
    outputImagePaths: ["benchmark_runs/run_123/plot_00000.png"],
    contactSheetPath: "benchmark_runs/run_123/sample_contact_sheet.png",
  });

  assert.match(prompt, /Run ID: run_123/);
  assert.match(prompt, /technical_evaluation\.json/);
  assert.match(prompt, /plot_00000\.png/);
});

test("parseCycleResponse accepts a valid structured response", () => {
  const parsed = parseCycleResponse(
    JSON.stringify({
      runId: "run_123",
      status: "completed",
      summary: "Completed successfully.",
      modelChanged: false,
      morpheusRan: true,
      needsAnotherImageReview: false,
      reproduction: {
        source_coverage: { score: 2, evidence: ["paper page 1"], rationale: "Used paper text and figures." },
        mechanism_mapping: { score: 2, evidence: ["paper page 3"], rationale: "Matched the core mechanisms." },
        observable_alignment: { score: 1, evidence: ["plot_00000.png"], rationale: "Partial visual match." },
        parameter_plausibility: { score: 1, evidence: ["model.xml"], rationale: "Parameters are plausible but coarse." },
        total_score: 6,
        summary: "Good first reproduction.",
      },
    }),
  );

  assert.equal(parsed.status, "completed");
  assert.equal(parsed.reproduction?.total_score, 6);
});
