import { mkdir, readdir, writeFile } from "node:fs/promises";
import path from "node:path";
import process from "node:process";

import { Codex, type Thread, type ThreadEvent, type ThreadItem, type ThreadOptions, type UserInput } from "@openai/codex-sdk";

import {
  buildCyclePrompt,
  buildImageReviewPrompt,
  FINAL_RESPONSE_SCHEMA,
  parseCycleResponse,
} from "./prompt.js";
import { PythonBridge } from "./python-bridge.js";
import type {
  AgentCycleResponse,
  BenchmarkConfig,
  BenchmarkSummary,
  InspectionArtifacts,
  PaperRunResult,
  ToolResult,
} from "./types.js";

type CreateRunResult = ToolResult<{
  run_id: string;
  run_dir: string;
  run_manifest_path: string;
}>;

type ExtractPaperResult = ToolResult<{
  run_id: string;
  run_dir: string;
  text_path: string;
}>;

type RenderPagesResult = ToolResult<{
  pages: Array<{ page: number; path: string }>;
  manifest_path: string;
}>;

type FigureManifestResult = ToolResult<{
  figure_pages: number[];
  manifest_path: string;
}>;

type TechnicalResult = ToolResult<{
  total_score: number;
  evaluation_json_path: string;
}>;

type CollectedTurn = {
  finalResponse: string;
  usage: { input_tokens: number; cached_input_tokens: number; output_tokens: number } | null;
  events: ThreadEvent[];
  items: ThreadItem[];
};

export class BenchmarkRunner {
  private readonly bridge = new PythonBridge();
  private readonly codex: Codex;
  private readonly config: BenchmarkConfig;

  constructor(config: BenchmarkConfig) {
    this.config = config;
    this.codex = new Codex({
      config: {
        mcp_servers: {
          morpheus: {
            command: config.mcpCommand[0],
            args: config.mcpCommand.slice(1),
            env: {
              MORPHEUS_RUNS_DIR: config.resultsDir,
            },
          },
        },
        skills: {
          config: config.skillPaths.map((skillPath) => ({ path: skillPath, enabled: true })),
        },
      },
    });
  }

  async run(maxPapers?: number): Promise<BenchmarkSummary> {
    const papers = await this.discoverPapers(maxPapers);
    const results: PaperRunResult[] = [];

    for (const pdfPath of papers) {
      try {
        results.push(await this.processPaper(pdfPath));
      } catch (error) {
        const message = error instanceof Error ? error.message : String(error);
        results.push(
          failedResult(
            path.basename(pdfPath),
            pdfPath,
            `Unhandled runner error: ${message}`,
          ),
        );
      }
    }

    const completed = results.filter((result) => result.status === "completed").length;
    const technicalScores = results.flatMap((result) =>
      result.technicalScore === null ? [] : [result.technicalScore],
    );
    const reproductionScores = results.flatMap((result) =>
      result.reproductionScore === null ? [] : [result.reproductionScore],
    );

    const summary: BenchmarkSummary = {
      config: this.config,
      generatedAt: new Date().toISOString(),
      totalPapers: results.length,
      completedPapers: completed,
      failedPapers: results.length - completed,
      averageTechnicalScore: average(technicalScores),
      averageReproductionScore: average(reproductionScores),
      results,
    };

    const summaryPath = path.join(this.config.resultsDir, "benchmark_summary.json");
    await writeJson(summaryPath, summary);
    return summary;
  }

  async discoverPapers(maxPapers?: number): Promise<string[]> {
    const entries = await readdir(this.config.papersDir, { withFileTypes: true });
    const pdfs = entries
      .filter((entry) => entry.isFile() && entry.name.toLowerCase().endsWith(".pdf"))
      .map((entry) => path.join(this.config.papersDir, entry.name))
      .sort();
    return typeof maxPapers === "number" ? pdfs.slice(0, maxPapers) : pdfs;
  }

  private async processPaper(pdfPath: string): Promise<PaperRunResult> {
    const paper = path.basename(pdfPath);
    const paperStem = sanitizeStem(path.basename(pdfPath, path.extname(pdfPath)));

    const createRun = (await this.bridge.invoke<{
      run_id: string;
      run_dir: string;
      run_manifest_path: string;
    }>("create_run", { name: paperStem })) as CreateRunResult;
    if (!createRun.ok) {
      return failedResult(paper, pdfPath, `Failed to create run: ${createRun.error ?? "unknown error"}`);
    }

    const runId = createRun.run_id;
    const runDir = createRun.run_dir;
    await mkdir(path.join(runDir, "transcripts"), { recursive: true });

    const extract = (await this.bridge.invoke("extract_paper_text", {
      pdf_path: pdfPath,
      run_id: runId,
    })) as ExtractPaperResult;
    if (!extract.ok) {
      return failedResult(paper, pdfPath, `Failed to extract paper text: ${extract.error ?? "unknown error"}`, runId, runDir, createRun.run_manifest_path);
    }

    const figureManifest = (await this.bridge.invoke("list_paper_figures", {
      pdf_path: pdfPath,
      run_id: runId,
    })) as FigureManifestResult;
    if (!figureManifest.ok) {
      return failedResult(paper, pdfPath, `Failed to list PDF figures: ${figureManifest.error ?? "unknown error"}`, runId, runDir, createRun.run_manifest_path);
    }

    const threadOptions: ThreadOptions = {
      model: this.config.model,
      modelReasoningEffort: this.config.reasoningEffort,
      sandboxMode: "workspace-write",
      approvalPolicy: "never",
      workingDirectory: process.cwd(),
      additionalDirectories: [this.config.resultsDir],
      networkAccessEnabled: false,
      webSearchMode: "disabled",
    };
    const thread = this.codex.startThread(threadOptions);

    let technicalEvaluationPath: string | null = null;
    let pageManifestPath: string | null = null;
    let lastSummary: string | undefined;
    let finalCycle: AgentCycleResponse | null = null;
    let status: PaperRunResult["status"] = "max_turns";
    let completedCycles = 0;

    for (let cycle = 1; cycle <= this.config.maxTurnsPerPaper; cycle += 1) {
      const prompt = buildCyclePrompt({
        paperName: paper,
        pdfPath,
        runId,
        runDir,
        paperTextPath: extract.text_path,
        pageRenderDpi: this.config.pageRenderDpi,
        representativeOutputFrames: this.config.representativeOutputFrames,
        pageManifestPath,
        figureManifestPath: figureManifest.manifest_path,
        likelyFigurePages: figureManifest.figure_pages,
        cycle,
        previousSummary: lastSummary,
        technicalEvaluationPath,
        paperImagePaths: [],
        outputImagePaths: [],
        contactSheetPath: null,
      });

      const input = buildTurnInput(prompt, [], [], null);
      let turn: CollectedTurn;
      try {
        turn = await collectTurn(thread, input);
      } catch (error) {
        return failedResult(
          paper,
          pdfPath,
          `Failed during Codex turn: ${error instanceof Error ? error.message : String(error)}`,
          runId,
          runDir,
          createRun.run_manifest_path,
          thread.id,
        );
      }
      await writeTranscript(path.join(runDir, "transcripts", `cycle_${String(cycle).padStart(2, "0")}.jsonl`), turn.events);
      completedCycles = cycle;

      let cycleResponse: AgentCycleResponse;
      try {
        cycleResponse = parseCycleResponse(turn.finalResponse);
      } catch (error) {
        return failedResult(
          paper,
          pdfPath,
          `Codex returned invalid structured output: ${(error as Error).message}`,
          runId,
          runDir,
          createRun.run_manifest_path,
          thread.id,
        );
      }

      let latestInspection = collectInspectionArtifacts(turn.items, runDir);
      pageManifestPath = latestInspection.pageManifestPath ?? pageManifestPath;
      const reviewInspection = latestInspection;

      if (hasInspectionArtifacts(reviewInspection)) {
        const reviewPrompt = buildImageReviewPrompt({
          paperName: paper,
          runId,
          cycle,
          paperImagePaths: reviewInspection.paperImagePaths,
          outputImagePaths: reviewInspection.outputImagePaths,
          contactSheetPath: reviewInspection.contactSheetPath,
          technicalEvaluationPath,
        });

        const reviewInput = buildTurnInput(
          reviewPrompt,
          reviewInspection.paperImagePaths,
          reviewInspection.outputImagePaths,
          reviewInspection.contactSheetPath,
        );
        let reviewTurn: CollectedTurn;
        try {
          reviewTurn = await collectTurn(thread, reviewInput);
        } catch (error) {
          return failedResult(
            paper,
            pdfPath,
            `Failed during image review turn: ${error instanceof Error ? error.message : String(error)}`,
            runId,
            runDir,
            createRun.run_manifest_path,
            thread.id,
          );
        }
        await writeTranscript(
          path.join(runDir, "transcripts", `cycle_${String(cycle).padStart(2, "0")}_review.jsonl`),
          reviewTurn.events,
        );

        try {
          cycleResponse = parseCycleResponse(reviewTurn.finalResponse);
        } catch (error) {
          return failedResult(
            paper,
            pdfPath,
            `Codex returned invalid structured output after image review: ${(error as Error).message}`,
            runId,
            runDir,
            createRun.run_manifest_path,
            thread.id,
          );
        }

        latestInspection = collectInspectionArtifacts(reviewTurn.items, runDir);
        pageManifestPath = latestInspection.pageManifestPath ?? pageManifestPath;
      }

      finalCycle = cycleResponse;
      lastSummary = cycleResponse.summary;

      const technical = (await this.bridge.invoke("evaluate_technical_run", {
        run_id: runId,
      })) as TechnicalResult;
      if (technical.ok) {
        technicalEvaluationPath = technical.evaluation_json_path;
      }

      if (cycleResponse.status === "completed" && !cycleResponse.needsAnotherImageReview) {
        status = "completed";
        break;
      }

      if (cycleResponse.status === "failed") {
        status = "failed";
        break;
      }
    }

    const technical = (await this.bridge.invoke("evaluate_technical_run", {
      run_id: runId,
    })) as TechnicalResult;
    const technicalScore = technical.ok ? technical.total_score : null;
    const technicalPath = technical.ok ? technical.evaluation_json_path : technicalEvaluationPath;

    const reproductionPath = path.join(runDir, "reproduction_report.json");
    const reproductionScore = finalCycle?.reproduction?.total_score ?? null;
    await writeJson(reproductionPath, {
      paper,
      pdfPath,
      runId,
      generatedAt: new Date().toISOString(),
      status,
      reproduction: finalCycle?.reproduction ?? null,
      summary: finalCycle?.summary ?? "",
    });

    const result: PaperRunResult = {
      paper,
      pdfPath,
      runId,
      threadId: thread.id,
      status,
      cycles: completedCycles,
      technicalScore,
      reproductionScore,
      technicalEvaluationPath: technicalPath ?? null,
      reproductionReportPath: reproductionPath,
      runManifestPath: createRun.run_manifest_path,
      summary: finalCycle?.summary ?? "No final summary available.",
      error: status === "failed" ? finalCycle?.summary : undefined,
    };
    return result;
  }
}

function buildTurnInput(
  prompt: string,
  paperImagePaths: string[],
  outputImagePaths: string[],
  contactSheetPath: string | null,
): UserInput[] {
  const inputs: UserInput[] = [{ type: "text", text: prompt }];
  for (const imagePath of uniquePaths(paperImagePaths)) {
    inputs.push({ type: "local_image", path: imagePath });
  }
  for (const imagePath of uniquePaths(outputImagePaths)) {
    inputs.push({ type: "local_image", path: imagePath });
  }
  if (contactSheetPath) {
    inputs.push({ type: "local_image", path: contactSheetPath });
  }
  return inputs;
}

async function collectTurn(thread: Thread, input: UserInput[]): Promise<CollectedTurn> {
  const streamed = await thread.runStreamed(input, { outputSchema: FINAL_RESPONSE_SCHEMA });
  const events: ThreadEvent[] = [];
  const items = new Map<string, ThreadItem>();
  let usage: CollectedTurn["usage"] = null;
  let finalResponse = "";
  let turnCompleted = false;
  let turnFailedMessage: string | null = null;
  let recoverableStreamError: string | null = null;

  for await (const event of streamed.events) {
    events.push(event);
    if (event.type === "item.started" || event.type === "item.updated" || event.type === "item.completed") {
      items.set(event.item.id, event.item);
      if (event.item.type === "agent_message") {
        finalResponse = event.item.text;
      }
    }
    if (event.type === "turn.completed") {
      usage = event.usage;
      turnCompleted = true;
    }
    if (event.type === "turn.failed") {
      turnFailedMessage = event.error.message;
    }
    if (event.type === "error") {
      if (isRecoverableStreamError(event.message)) {
        recoverableStreamError = event.message;
        continue;
      }
      throw new Error(event.message);
    }
  }

  if (turnFailedMessage) {
    throw new Error(turnFailedMessage);
  }

  if (!turnCompleted) {
    throw new Error(
      recoverableStreamError
        ? `Turn stream ended before completion after transient stream errors: ${recoverableStreamError}`
        : "Turn stream ended before completion.",
    );
  }

  return {
    finalResponse,
    usage,
    events,
    items: [...items.values()],
  };
}

function sanitizeStem(value: string): string {
  return value.replace(/[^a-zA-Z0-9_-]+/g, "_");
}

function isRecoverableStreamError(message: string): boolean {
  const normalized = message.toLowerCase();
  return (
    normalized.includes("reconnecting") ||
    normalized.includes("stream disconnected before completion") ||
    normalized.includes("websocket closed by server")
  );
}

function average(values: number[]): number {
  if (values.length === 0) {
    return 0;
  }
  return Number((values.reduce((sum, value) => sum + value, 0) / values.length).toFixed(2));
}

function hasInspectionArtifacts(value: InspectionArtifacts): boolean {
  return (
    value.paperImagePaths.length > 0 ||
    value.outputImagePaths.length > 0 ||
    value.contactSheetPath !== null
  );
}

function uniquePaths(values: string[]): string[] {
  return [...new Set(values)];
}

function collectInspectionArtifacts(items: ThreadItem[], runDir: string): InspectionArtifacts {
  const paperImagePaths = new Set<string>();
  const outputImagePaths = new Set<string>();
  let contactSheetPath: string | null = null;
  let pageManifestPath: string | null = null;

  for (const item of items) {
    const toolItem = item as any;
    if (toolItem.type !== "mcp_tool_call" || toolItem.status !== "completed" || !toolItem.result) {
      continue;
    }

    const payload =
      toolItem.result?.structured_content?.result ??
      toolItem.result?.structuredContent?.result ??
      null;
    if (!payload || payload.ok === false) {
      continue;
    }

    if (toolItem.tool === "render_pdf_pages" && Array.isArray(payload.pages)) {
      for (const page of payload.pages) {
        if (typeof page?.path === "string") {
          paperImagePaths.add(resolveArtifactPath(runDir, page.path));
        }
      }
      if (typeof payload.manifest_path === "string") {
        pageManifestPath = resolveArtifactPath(runDir, payload.manifest_path);
      }
    }

    if (toolItem.tool === "sample_output_images") {
      if (Array.isArray(payload.selected_images)) {
        for (const imagePath of payload.selected_images) {
          if (typeof imagePath === "string") {
            outputImagePaths.add(resolveArtifactPath(runDir, imagePath));
          }
        }
      }
      if (typeof payload.contact_sheet_path === "string" && payload.contact_sheet_path.length > 0) {
        contactSheetPath = resolveArtifactPath(runDir, payload.contact_sheet_path);
      }
    }
  }

  return {
    paperImagePaths: [...paperImagePaths],
    outputImagePaths: [...outputImagePaths],
    contactSheetPath,
    pageManifestPath,
  };
}

function resolveArtifactPath(runDir: string, value: string): string {
  return path.isAbsolute(value) ? value : path.join(runDir, value);
}

async function writeTranscript(outputPath: string, events: ThreadEvent[]): Promise<void> {
  const content = `${events.map((event) => JSON.stringify(event)).join("\n")}\n`;
  await writeFile(outputPath, content, "utf8");
}

async function writeJson(outputPath: string, payload: unknown): Promise<void> {
  await mkdir(path.dirname(outputPath), { recursive: true });
  await writeFile(outputPath, JSON.stringify(payload, null, 2), "utf8");
}

function failedResult(
  paper: string,
  pdfPath: string,
  error: string,
  runId = "",
  runDir = "",
  runManifestPath: string | null = null,
  threadId: string | null = null,
): PaperRunResult {
  return {
    paper,
    pdfPath,
    runId,
    threadId,
    status: "failed",
    cycles: 0,
    technicalScore: null,
    reproductionScore: null,
    technicalEvaluationPath: null,
    reproductionReportPath: null,
    runManifestPath,
    summary: error,
    error,
  };
}
