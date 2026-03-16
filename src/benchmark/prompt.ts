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
  pageManifestPath: string;
  figureManifestPath: string;
  cycle: number;
  previousSummary?: string;
  technicalEvaluationPath?: string | null;
  outputImagePaths: string[];
  contactSheetPath?: string | null;
};

export function buildCyclePrompt(params: PromptParams): string {
  const outputSection =
    params.outputImagePaths.length > 0
      ? [
          "Latest Morpheus outputs have been sampled and attached to this turn.",
          `Sampled output image paths: ${params.outputImagePaths.join(", ")}`,
          params.contactSheetPath ? `Contact sheet path: ${params.contactSheetPath}` : "",
        ]
          .filter(Boolean)
          .join("\n")
      : "No Morpheus output images are attached yet. Produce an initial runnable model and run it.";

  return [
    `Benchmark paper: ${params.paperName}`,
    `PDF path: ${params.pdfPath}`,
    `Run ID: ${params.runId}`,
    `Run directory: ${params.runDir}`,
    `Paper text path: ${params.paperTextPath}`,
    `Page manifest path: ${params.pageManifestPath}`,
    `Figure manifest path: ${params.figureManifestPath}`,
    `Host cycle: ${params.cycle}`,
    "",
    "Rules:",
    "- Use the Morpheus skill as the source of modeling behavior.",
    "- Do not edit repository source files. Only work inside the run directory via MCP tools.",
    "- Use MCP tools for references, XML writing, Morpheus execution, run summaries, output sampling, and technical evaluation.",
    "- Preserve executability first, then use the paper images and output images to judge reproduction quality.",
    "- If no model exists yet, create one, run Morpheus, and evaluate the technical score.",
    "- If output images are attached and they reveal obvious mismatches, you may revise the model and rerun.",
    "- If you revise and rerun during this turn, set needsAnotherImageReview=true so the host can attach the fresh outputs next turn.",
    "- Only return JSON matching the provided schema.",
    "",
    "Required tool sequence for the first workable model:",
    "1. read_file_text(paper.txt) and the staging manifests as needed.",
    "2. list_references(...) and read_reference(...) for the closest Morpheus examples.",
    "3. write_model_xml(...)",
    "4. run_morpheus_model(...)",
    "5. summarize_morpheus_run(...)",
    "6. evaluate_technical_run(...)",
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

export function parseCycleResponse(raw: string): AgentCycleResponse {
  return JSON.parse(raw) as AgentCycleResponse;
}
