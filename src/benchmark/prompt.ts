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
  technicalEvaluationPath?: string | null;
  paperImagePaths: string[];
  outputImagePaths: string[];
  contactSheetPath?: string | null;
};

export function buildCyclePrompt(params: PromptParams): string {
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
        ].join("\n");

  const outputSection =
    params.outputImagePaths.length > 0
      ? [
          "Latest Morpheus outputs have been sampled and attached to this turn.",
          `Sampled output image paths: ${params.outputImagePaths.join(", ")}`,
          params.contactSheetPath ? `Contact sheet path: ${params.contactSheetPath}` : "",
        ]
          .filter(Boolean)
          .join("\n")
      : "No Morpheus output images are attached to this turn. If you need visual inspection, call sample_output_images after a successful run.";

  return [
    `Benchmark paper: ${params.paperName}`,
    `PDF path: ${params.pdfPath}`,
    `Run ID: ${params.runId}`,
    `Run directory: ${params.runDir}`,
    `Paper text path: ${params.paperTextPath}`,
    `Preferred paper page render DPI when needed: ${params.pageRenderDpi}`,
    `Preferred Morpheus output image sample count when needed: ${params.representativeOutputFrames}`,
    params.pageManifestPath ? `Page manifest path: ${params.pageManifestPath}` : "No page manifest exists yet.",
    params.figureManifestPath ? `Figure manifest path: ${params.figureManifestPath}` : "No figure manifest exists yet.",
    params.likelyFigurePages && params.likelyFigurePages.length > 0
      ? `Likely figure pages: ${params.likelyFigurePages.join(", ")}`
      : "",
    `Host cycle: ${params.cycle}`,
    "",
    "Rules:",
    "- Use the Morpheus skill as the source of modeling behavior.",
    "- Do not edit repository source files. Only work inside the run directory via MCP tools.",
    "- Use MCP tools for references, XML writing, Morpheus execution, run summaries, output sampling, and technical evaluation.",
    "- Do not read SKILL.md through a file tool. The skill is already loaded.",
    "- Start from paper text and references. Do not request paper page images unless you need visual inspection.",
    "- Read paper.txt once at the start of the run, then reread it only if you need more detail later.",
    "- Preserve executability first, then use the paper images and output images to judge reproduction quality.",
    "- If you need paper figures, render only the specific pages you want to inspect, using the preferred DPI unless a different one is necessary.",
    "- If you need Morpheus output images, call sample_output_images with the preferred sample count unless a different count is necessary.",
    "- If you sample output images or render paper pages during this turn, the host may attach them in one immediate follow-up review turn within the same cycle.",
    "- Do not assume previously attached images will be reattached in later host cycles. Request them again only if you still need them.",
    "- If no model exists yet, create one, run Morpheus, and evaluate the technical score.",
    "- If output images are attached and they reveal obvious mismatches, you may revise the model and rerun.",
    "- Set needsAnotherImageReview=true only if, after this cycle and any immediate image follow-up, you still need another host cycle.",
    "- Only return JSON matching the provided schema.",
    "",
    "Required tool sequence for the first workable model:",
    "1. read_file_text(paper.txt).",
    "2. list_references(...) and read_reference(...) for the closest Morpheus examples.",
    "3. write_model_xml(...)",
    "4. run_morpheus_model(...)",
    "5. summarize_morpheus_run(...)",
    "6. evaluate_technical_run(...)",
    "",
    paperImageSection,
    "",
    outputSection,
    "",
    params.technicalEvaluationPath
      ? `Latest technical evaluation path: ${params.technicalEvaluationPath}`
      : "No technical evaluation is available yet.",
    params.previousSummary ? `Previous cycle summary: ${params.previousSummary}` : "",
    "",
    "Completion policy:",
    "- status=completed only when you have both a technical result and a filled reproduction rubric.",
    "- reproduction evidence strings must cite paper pages/figures and output files.",
    "- If you are blocked by Morpheus execution or missing outputs, status=failed and reproduction may be null.",
  ]
    .filter(Boolean)
    .join("\n");
}

type ImageReviewPromptParams = {
  paperName: string;
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
    `Run ID: ${params.runId}`,
    `Host cycle: ${params.cycle}`,
    "",
    "This is the immediate image-review follow-up for the current cycle.",
    "The images you requested or generated are attached now.",
    "Inspect them directly before deciding whether the model is a plausible reproduction.",
    "Do not reread SKILL.md through a file tool.",
    "Only rerun Morpheus if the images clearly show that the current model is wrong.",
    "If you rerun and still need another host cycle after this review turn, set needsAnotherImageReview=true.",
    params.paperImagePaths.length > 0 ? `Attached paper image paths: ${params.paperImagePaths.join(", ")}` : "",
    params.outputImagePaths.length > 0 ? `Attached output image paths: ${params.outputImagePaths.join(", ")}` : "",
    params.contactSheetPath ? `Attached contact sheet path: ${params.contactSheetPath}` : "",
    params.technicalEvaluationPath ? `Latest technical evaluation path: ${params.technicalEvaluationPath}` : "",
    "",
    "Return JSON matching the provided schema.",
  ]
    .filter(Boolean)
    .join("\n");
}

export function parseCycleResponse(raw: string): AgentCycleResponse {
  return JSON.parse(raw) as AgentCycleResponse;
}
