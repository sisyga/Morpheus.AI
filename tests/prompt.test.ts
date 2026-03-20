import assert from "node:assert/strict";
import test from "node:test";

import {
  buildCyclePrompt,
  buildImageReviewPrompt,
  parseCycleResponse,
} from "../src/benchmark/prompt.js";

test("buildCyclePrompt prefers on-demand image inspection", () => {
  const prompt = buildCyclePrompt({
    paperName: "1_Szabo2010_clean.pdf",
    pdfPath: "benchmark_papers/1_Szabo2010_clean.pdf",
    runId: "run_123",
    runDir: "benchmark_runs/run_123",
    paperTextPath: "benchmark_runs/run_123/paper.txt",
    pageRenderDpi: 150,
    representativeOutputFrames: 5,
    pageManifestPath: "benchmark_runs/run_123/paper_page_manifest.json",
    figureManifestPath: "benchmark_runs/run_123/paper_figure_manifest.json",
    likelyFigurePages: [2, 4],
    cycle: 2,
    previousSummary: "Initial run complete",
    technicalEvaluationPath: "benchmark_runs/run_123/technical_evaluation.json",
    paperImagePaths: [],
    outputImagePaths: ["benchmark_runs/run_123/plot_00000.png"],
    contactSheetPath: "benchmark_runs/run_123/sample_contact_sheet.png",
  });

  assert.match(prompt, /Run ID: run_123/);
  assert.match(prompt, /technical_evaluation\.json/);
  assert.match(prompt, /plot_00000\.png/);
  assert.match(prompt, /Likely figure pages: 2, 4/);
  assert.match(prompt, /render only the specific pages/i);
});

test("buildImageReviewPrompt lists attached review images", () => {
  const prompt = buildImageReviewPrompt({
    paperName: "1_Szabo2010_clean.pdf",
    runId: "run_123",
    cycle: 2,
    paperImagePaths: ["benchmark_runs/run_123/paper_pages/page_0002.png"],
    outputImagePaths: ["benchmark_runs/run_123/plot_00000.png"],
    contactSheetPath: "benchmark_runs/run_123/sample_contact_sheet.png",
    technicalEvaluationPath: "benchmark_runs/run_123/technical_evaluation.json",
  });

  assert.match(prompt, /Image review follow-up/);
  assert.match(prompt, /page_0002\.png/);
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
      needsAnotherCycle: false,
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
  assert.equal(parsed.needsAnotherCycle, false);
});

test("buildCyclePrompt distinguishes another cycle from image review", () => {
  const prompt = buildCyclePrompt({
    paperName: "1_Szabo2010_clean.pdf",
    pdfPath: "benchmark_papers/1_Szabo2010_clean.pdf",
    runId: "run_123",
    runDir: "benchmark_runs/run_123",
    paperTextPath: "benchmark_runs/run_123/paper.txt",
    pageRenderDpi: 150,
    representativeOutputFrames: 5,
    pageManifestPath: null,
    figureManifestPath: null,
    likelyFigurePages: [],
    cycle: 1,
    previousSummary: undefined,
    technicalEvaluationPath: null,
    paperImagePaths: [],
    outputImagePaths: [],
    contactSheetPath: null,
  });

  assert.match(prompt, /needsAnotherCycle=true/i);
  assert.match(prompt, /needsAnotherImageReview=true/i);
});
