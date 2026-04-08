import type { AgentCycleResponse } from "./types.js";

export const FINAL_RESPONSE_SCHEMA = {
  type: "object",
  properties: {
    runId: { type: "string" },
    status: {
      type: "string",
      enum: ["in_progress", "completed", "failed"],
    },
    summary: { type: "string" },
    modelChanged: { type: "boolean" },
    morpheusRan: { type: "boolean" },
    needsAnotherCycle: { type: "boolean" },
    needsAnotherImageReview: { type: "boolean" },
    reproduction: {
      type: ["object", "null"],
      properties: {
        source_coverage: criterionSchema(),
        mechanism_mapping: criterionSchema(),
        observable_alignment: criterionSchema(),
        parameter_plausibility: criterionSchema(),
        total_score: { type: "number" },
        summary: { type: "string" },
      },
      required: [
        "source_coverage",
        "mechanism_mapping",
        "observable_alignment",
        "parameter_plausibility",
        "total_score",
        "summary",
      ],
      additionalProperties: false,
    },
  },
  required: [
    "runId",
    "status",
    "summary",
    "modelChanged",
    "morpheusRan",
    "needsAnotherCycle",
    "needsAnotherImageReview",
    "reproduction",
  ],
  additionalProperties: false,
} as const;

function criterionSchema() {
  return {
    type: "object",
    properties: {
      score: { type: "number", enum: [0, 1, 2] },
      evidence: {
        type: "array",
        items: { type: "string" },
      },
      rationale: { type: "string" },
    },
    required: ["score", "evidence", "rationale"],
    additionalProperties: false,
  };
}

type PromptParams = {
  paperName: string;
  pdfPath: string;
  focusText?: string | null;
  runId: string;
  runDir: string;
  paperTextPath: string;
  pageRenderDpi: number;
  representativeOutputFrames: number;
  pageManifestPath?: string | null;
  figureManifestPath?: string | null;
  likelyFigurePages?: number[];
  cycle: number;
  previousSummary?: string;
  previousReproductionScore?: number | null;
  hostContinuationReason?: string;
  technicalEvaluationPath?: string | null;
  paperImagePaths: string[];
  outputImagePaths: string[];
  contactSheetPath?: string | null;
};

export function buildCyclePrompt(params: PromptParams): string {
  const metadataLines = [
    `Benchmark paper: ${params.paperName}`,
    `PDF path: ${params.pdfPath}`,
    params.focusText ? `Benchmark focus: ${params.focusText}` : null,
    `Run ID: ${params.runId}`,
    `Run directory: ${params.runDir}`,
    `Paper text path: ${params.paperTextPath}`,
    `Preferred paper page render DPI when needed: ${params.pageRenderDpi}`,
    `Preferred Morpheus output image sample count when needed: ${params.representativeOutputFrames}`,
    params.pageManifestPath ? `Page manifest path: ${params.pageManifestPath}` : "No page manifest exists yet.",
    params.figureManifestPath
      ? `Figure manifest path: ${params.figureManifestPath}`
      : "No figure manifest exists yet.",
    params.likelyFigurePages && params.likelyFigurePages.length > 0
      ? `Likely figure pages: ${params.likelyFigurePages.join(", ")}`
      : null,
    `Host cycle: ${params.cycle}`,
  ]
    .filter((l): l is string => l !== null)
    .join("\n");

  const paperImageSection =
    params.paperImagePaths.length > 0
      ? [
          "Requested paper page images are attached to this turn.",
          `Attached paper image paths: ${params.paperImagePaths.join(", ")}`,
        ].join("\n")
      : [
          "No paper page images are attached yet.",
          params.figureManifestPath
            ? "If you need visual paper inspection, use the figure manifest and render only specific pages with render_pdf_pages(pages=[...])."
            : "If you need visual paper inspection, render only specific pages with render_pdf_pages(pages=[...]).",
        ].join(" ");

  const outputSection =
    params.outputImagePaths.length > 0
      ? [
          "Latest Morpheus outputs have been sampled and attached to this turn.",
          `Sampled output image paths: ${params.outputImagePaths.join(", ")}`,
          params.contactSheetPath ? `Contact sheet path: ${params.contactSheetPath}` : null,
        ]
          .filter((l): l is string => l !== null)
          .join("\n")
      : "No Morpheus output images are attached to this turn. If you need visual inspection, call sample_output_images after a successful run.";

  const technicalSection = params.technicalEvaluationPath
    ? `Latest technical evaluation path: ${params.technicalEvaluationPath}`
    : "No technical evaluation is available yet.";

  const dynamicSections = [paperImageSection, outputSection, technicalSection].join("\n\n");

  // Cycle 2+: skip the static rule blocks and use a compact continuation reference instead.
  if (params.cycle > 1) {
    const reproScore =
      params.previousReproductionScore != null
        ? String(params.previousReproductionScore)
        : "not yet scored";
    const continuationBlock = [
      "<cycle_continuation>",
      `Continuing from cycle ${params.cycle - 1}. All rules, tool-persistence rules, dependency checks, completeness contract, and verification loop from cycle 1 remain in effect.`,
      params.previousSummary ? `Previous summary: ${params.previousSummary}` : null,
      `Previous reproduction score: ${reproScore}`,
      params.hostContinuationReason
        ? `Host continuation reason: ${params.hostContinuationReason}`
        : null,
      `Continue improving the existing model in run_id=${params.runId}; do not call create_run or write outside ${params.runDir}.`,
      "Completion now requires a flawless reproduction rubric (8/8, every criterion 2/2) and max technical score, or no remaining host cycles.",
      "</cycle_continuation>",
    ]
      .filter((l): l is string => l !== null)
      .join("\n");
    return [metadataLines, continuationBlock, dynamicSections].join("\n\n");
  }

  // Cycle 1: full rule set using GPT-5.4 XML block structure.
  const toolPersistenceBlock = [
    "<tool_persistence_rules>",
    "- Use the Morpheus skill as the source of modeling behavior. Do not read SKILL.md through a file tool; the skill is already loaded.",
    "- Use MCP tools for references, XML writing, Morpheus execution, run summaries, output sampling, and technical evaluation. Do not edit repository source files.",
    `- Do not call create_run. The host already created run_id=${params.runId} at ${params.runDir}.`,
    `- Always pass run_id="${params.runId}" to write_model_xml, run_morpheus_model, summarize_morpheus_run, sample_output_images, render_pdf_pages, and evaluate_technical_run.`,
    '- Always write the canonical model as file_name="model.xml"; do not create paper-specific subfolders.',
    "- Never use shell or command_execution to edit model.xml, delete files, or clean up the run directory. Use write_model_xml for model changes; read-only shell inspection is allowed only when strictly necessary.",
    "- Do not stop early; keep calling tools until a valid model runs and technical evaluation passes.",
    "- If a tool returns an error, diagnose from the error message and retry with a corrected input.",
    "- Preserve executability first, then use paper images and output images to judge reproduction quality.",
    "</tool_persistence_rules>",
  ].join("\n");

  const dependencyBlock = [
    "<dependency_checks>",
    "For the first workable model, follow this sequence:",
    "1. read_file_text(paper.txt)",
    "2. list_references(...) and read_reference(...) for the closest Morpheus examples",
    "3. write_model_xml(...)",
    "4. run_morpheus_model(...)",
    "5. summarize_morpheus_run(...)",
    "6. evaluate_technical_run(...)",
    "Read paper.txt once at the start; reread only if more detail is needed.",
    "Render paper pages or sample output images only when visual inspection is needed; the host will attach them in an immediate follow-up review turn within the same cycle.",
    "Do not assume previously attached images will be reattached in later cycles.",
    "</dependency_checks>",
  ].join("\n");

  const completenessBlock = [
    "<completeness_contract>",
    "- Treat the task as incomplete until: a model runs, technical evaluation passes, the reproduction rubric is filled, and you have judged whether another full benchmark cycle is still needed.",
    "- status=completed only when technical_evaluation_path exists, the reproduction rubric is filled with cited evidence, every reproduction criterion is 2/2, total_score is 8/8, technical evaluation is max score, and needsAnotherCycle=false.",
    "- If Morpheus fails and cannot be recovered, set status=failed; reproduction may be null.",
    "</completeness_contract>",
  ].join("\n");

  const focusBlock = params.focusText
    ? [
        "<benchmark_focus>",
        `Primary target for this paper: ${params.focusText}`,
        "- If the paper contains multiple models or figures, prioritize this target for model design, observable selection, and reproduction scoring.",
        "- Use other paper context when it supports this target, but do not spend benchmark cycles reproducing unrelated models.",
        "</benchmark_focus>",
      ].join("\n")
    : null;

  const verificationBlock = [
    "<verification_loop>",
    "Before setting status=completed:",
    "- Confirm model.xml exists and ran without fatal errors.",
    "- Confirm technical_evaluation_path exists.",
    "- Confirm the reproduction rubric is fully filled with paper section/figure and output file citations.",
    "- If reproduction is still partial, coarse, heuristic, missing a cited mechanism, missing a paper observable, or below 8/8, set status=in_progress and needsAnotherCycle=true.",
    "- Reserve status=completed only for a technically maxed, biologically flawless reproduction; imperfect reproductions should keep iterating until the host turn budget runs out.",
    "- If any required artifact is missing, set status=in_progress and state what remains.",
    "</verification_loop>",
  ].join("\n");

  const outputContractBlock = [
    "<output_contract>",
    "- Return exactly the JSON schema provided. No prose, no markdown fences.",
    "- reproduction evidence strings must cite specific paper pages/figures and output files by name.",
    "- Set needsAnotherCycle=true if reproduction is below 8/8, technical evaluation is below max score, or you identified a concrete weakness that another cycle could improve.",
    "- Set needsAnotherImageReview=true only if that next cycle specifically needs additional paper/output image inspection.",
    "</output_contract>",
  ].join("\n");

  return [
    metadataLines,
    focusBlock,
    toolPersistenceBlock,
    dependencyBlock,
    completenessBlock,
    verificationBlock,
    outputContractBlock,
    dynamicSections,
  ]
    .filter((l): l is string => l !== null)
    .join("\n\n");
}

type ImageReviewPromptParams = {
  paperName: string;
  focusText?: string | null;
  runId: string;
  cycle: number;
  paperImagePaths: string[];
  outputImagePaths: string[];
  contactSheetPath?: string | null;
  technicalEvaluationPath?: string | null;
};

export function buildImageReviewPrompt(params: ImageReviewPromptParams): string {
  return [
    `Image review follow-up for benchmark paper: ${params.paperName}`,
    params.focusText ? `Benchmark focus: ${params.focusText}` : "",
    `Run ID: ${params.runId}`,
    `Host cycle: ${params.cycle}`,
    "",
    "This is the immediate image-review follow-up for the current cycle.",
    "The images you requested or generated are attached now.",
    "Inspect them directly before deciding whether the model is a plausible reproduction.",
    "Do not reread SKILL.md through a file tool.",
    "Do not use shell or command_execution to edit model.xml, delete files, or clean up artifacts; use write_model_xml for model changes.",
    "Only rerun Morpheus if the images clearly show that the current model is wrong.",
    "Do not call create_run; continue using the existing run_id only.",
    "If reproduction is below 8/8, technical evaluation is below max score, or you identified a concrete weakness, set needsAnotherCycle=true.",
    "Set needsAnotherImageReview=true only if that next cycle specifically needs more image inspection.",
    params.paperImagePaths.length > 0 ? `Attached paper image paths: ${params.paperImagePaths.join(", ")}` : "",
    params.outputImagePaths.length > 0 ? `Attached output image paths: ${params.outputImagePaths.join(", ")}` : "",
    params.contactSheetPath ? `Attached contact sheet path: ${params.contactSheetPath}` : "",
    params.technicalEvaluationPath ? `Latest technical evaluation path: ${params.technicalEvaluationPath}` : "",
    "",
    "<available_tools>",
    "If revision is needed: write_model_xml → run_morpheus_model → summarize_morpheus_run → evaluate_technical_run.",
    "</available_tools>",
    "",
    "Return JSON matching the provided schema.",
  ]
    .filter(Boolean)
    .join("\n");
}

export function parseCycleResponse(raw: string): AgentCycleResponse {
  return JSON.parse(raw) as AgentCycleResponse;
}
