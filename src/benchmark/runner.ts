import { mkdir, readFile, readdir, writeFile } from "node:fs/promises";
import path from "node:path";
import process from "node:process";
import { setTimeout as sleep } from "node:timers/promises";

import { Codex, type Thread, type ThreadEvent, type ThreadItem, type ThreadOptions, type UserInput } from "@openai/codex-sdk";

import {
  buildCyclePrompt,
  buildImageReviewPrompt,
  FINAL_RESPONSE_SCHEMA,
  parseCycleResponse,
} from "./prompt.js";
import { loadPaperFocus } from "./focus.js";
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
  total_pages?: number;
  requested_pages?: number[] | null;
  selected_pages?: number[];
  pages: Array<{ page: number; path: string }>;
  warnings?: string[];
  manifest_path: string;
}>;

type FigureManifestResult = ToolResult<{
  figure_pages: number[];
  detection_method?: string;
  warnings?: string[];
  manifest_path: string;
}>;

type TechnicalResult = ToolResult<{
  total_score: number;
  max_possible_score?: number;
  evaluation_json_path: string;
  attempt_id?: string;
  attempt_dir?: string;
  breakdown?: {
    model_graph_matches_xml?: boolean;
    latest_primary_plot_within_last_time?: boolean;
    latest_logger_plot_within_last_time?: boolean;
    latest_primary_plot?: string | null;
    latest_logger_plot?: string | null;
    last_time_value?: number | null;
  };
}>;

type CaptureModelVersionResult = ToolResult<{
  model_present: boolean;
  snapshot_created: boolean;
  version_path?: string;
  xml_version_count?: number;
  run_manifest_path?: string;
}>;

type CollectedTurn = {
  finalResponse: string;
  usage: { input_tokens: number; cached_input_tokens: number; output_tokens: number } | null;
  events: ThreadEvent[];
  items: ThreadItem[];
  error: string | null;
};

type QuotaFallbackOptions = {
  context: string;
  enabled: boolean;
  fallbackWaitMs: number;
  maxRetries: number;
  retryBufferMs: number;
};

const QUOTA_WAIT_PROGRESS_INTERVAL_MS = 60_000;
const DURATION_UNIT_PATTERN = "hours|hour|hrs|hr|h|minutes|minute|mins|min|m|seconds|second|secs|sec|s";

export class BenchmarkRunner {
  private readonly bridge: PythonBridge;
  private readonly config: BenchmarkConfig;

  constructor(config: BenchmarkConfig) {
    this.config = config;
    process.env.MORPHEUS_RUNS_DIR = config.resultsDir;
    this.bridge = new PythonBridge();
  }

  private createCodex(activeRunId?: string): Codex {
    return new Codex({
      config: {
        mcp_servers: {
          morpheus: {
            command: this.config.mcpCommand[0],
            args: this.config.mcpCommand.slice(1),
            env: {
              MORPHEUS_RUNS_DIR: this.config.resultsDir,
              ...(activeRunId ? { MORPHEUS_ACTIVE_RUN_ID: activeRunId } : {}),
            },
          },
        },
        skills: {
          config: this.config.skillPaths.map((skillPath) => ({ path: skillPath, enabled: true })),
        },
      },
    });
  }

  private quotaFallbackOptions(context: string): QuotaFallbackOptions {
    return {
      context,
      enabled: this.config.codexQuotaFallbackEnabled,
      fallbackWaitMs: minutesToMilliseconds(this.config.codexQuotaFallbackWaitMinutes),
      maxRetries: Math.floor(nonNegativeNumber(this.config.codexQuotaMaxRetries)),
      retryBufferMs: secondsToMilliseconds(this.config.codexQuotaRetryBufferSeconds),
    };
  }

  private captureCanonicalModelVersion(runId: string, reason: string): Promise<CaptureModelVersionResult> {
    return this.bridge.invoke("capture_model_xml_version", {
      run_id: runId,
      reason,
    }) as Promise<CaptureModelVersionResult>;
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
    const benchmarkFocus = await loadPaperFocus(this.config.benchmarkFocusDir, pdfPath);

    const createRun = (await this.bridge.invoke<{
      run_id: string;
      run_dir: string;
      run_manifest_path: string;
    }>("create_run", { name: paperStem })) as CreateRunResult;
    if (!createRun.ok) {
      return failedResult(
        paper,
        pdfPath,
        `Failed to create run: ${createRun.error ?? "unknown error"}`,
        "",
        "",
        null,
        null,
        benchmarkFocus,
      );
    }

    const runId = createRun.run_id;
    const runDir = createRun.run_dir;
    await mkdir(path.join(runDir, "transcripts"), { recursive: true });
    const codex = this.createCodex(runId);

    const extract = (await this.bridge.invoke("extract_paper_text", {
      pdf_path: pdfPath,
      run_id: runId,
    })) as ExtractPaperResult;
    if (!extract.ok) {
      return failedResult(
        paper,
        pdfPath,
        `Failed to extract paper text: ${extract.error ?? "unknown error"}`,
        runId,
        runDir,
        createRun.run_manifest_path,
        null,
        benchmarkFocus,
      );
    }

    const figureManifest = (await this.bridge.invoke("list_paper_figures", {
      pdf_path: pdfPath,
      run_id: runId,
    })) as FigureManifestResult;
    if (!figureManifest.ok) {
      return failedResult(
        paper,
        pdfPath,
        `Failed to list PDF figures: ${figureManifest.error ?? "unknown error"}`,
        runId,
        runDir,
        createRun.run_manifest_path,
        null,
        benchmarkFocus,
      );
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
    const thread = codex.startThread(threadOptions);

    let technicalEvaluationPath: string | null = null;
    let pageManifestPath: string | null = null;
    let lastSummary: string | undefined;
    let lastReproductionScore: number | null = null;
    let finalCycle: AgentCycleResponse | null = null;
    let status: PaperRunResult["status"] = "max_turns";
    let completedCycles = 0;
    let hostContinuationReason: string | undefined;
    let lastImageReviewOutcome: string | undefined;

    for (let cycle = 1; cycle <= this.config.maxTurnsPerPaper; cycle += 1) {
      const prompt = buildCyclePrompt({
        paperName: paper,
        pdfPath,
        focusText: benchmarkFocus,
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
        previousReproductionScore: lastReproductionScore,
        hostContinuationReason,
        technicalEvaluationPath,
        paperImagePaths: [],
        outputImagePaths: [],
        contactSheetPath: null,
      });

      const input = buildTurnInput(prompt, [], [], null);
      const turn = await collectTurnWithQuotaFallback(
        thread,
        input,
        this.quotaFallbackOptions(`${paper} cycle ${cycle}`),
      );
      await writeTranscript(path.join(runDir, "transcripts", `cycle_${String(cycle).padStart(2, "0")}.jsonl`), turn.events);
      if (turn.error) {
        return failedResult(
          paper,
          pdfPath,
          `Failed during Codex turn: ${turn.error}`,
          runId,
          runDir,
          createRun.run_manifest_path,
          thread.id,
          benchmarkFocus,
        );
      }
      const mainTurnVersion = await this.captureCanonicalModelVersion(runId, `cycle_${cycle}_main_turn`);
      if (!mainTurnVersion.ok) {
        return failedResult(
          paper,
          pdfPath,
          `Failed to capture canonical model provenance after cycle ${cycle}: ${mainTurnVersion.error ?? "unknown error"}`,
          runId,
          runDir,
          createRun.run_manifest_path,
          thread.id,
          benchmarkFocus,
        );
      }
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
          benchmarkFocus,
        );
      }

      let latestInspection = collectInspectionArtifacts(turn.items, runDir);
      pageManifestPath = latestInspection.pageManifestPath ?? pageManifestPath;
      const reviewInspection = latestInspection;
      const reviewRequired = hasInspectionArtifacts(reviewInspection);
      let reviewExecuted = false;
      let reviewTranscriptPath: string | null = null;

      if (reviewRequired) {
        const reviewPrompt = buildImageReviewPrompt({
          paperName: paper,
          focusText: benchmarkFocus,
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
        const reviewTurn = await collectTurnWithQuotaFallback(
          thread,
          reviewInput,
          this.quotaFallbackOptions(`${paper} cycle ${cycle} image review`),
        );
        reviewTranscriptPath = path.join(runDir, "transcripts", `cycle_${String(cycle).padStart(2, "0")}_review.jsonl`);
        await writeTranscript(reviewTranscriptPath, reviewTurn.events);
        if (reviewTurn.error) {
          return failedResult(
            paper,
            pdfPath,
            `Failed during image review turn: ${reviewTurn.error}`,
            runId,
            runDir,
            createRun.run_manifest_path,
            thread.id,
            benchmarkFocus,
          );
        }
        reviewExecuted = true;
        const reviewTurnVersion = await this.captureCanonicalModelVersion(runId, `cycle_${cycle}_review_turn`);
        if (!reviewTurnVersion.ok) {
          return failedResult(
            paper,
            pdfPath,
            `Failed to capture canonical model provenance after cycle ${cycle} image review: ${reviewTurnVersion.error ?? "unknown error"}`,
            runId,
            runDir,
            createRun.run_manifest_path,
            thread.id,
            benchmarkFocus,
          );
        }

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
            benchmarkFocus,
          );
        }

        latestInspection = collectInspectionArtifacts(reviewTurn.items, runDir);
        pageManifestPath = latestInspection.pageManifestPath ?? pageManifestPath;
        lastImageReviewOutcome = summarizeImageReviewOutcome(cycle, reviewInspection, cycleResponse.summary);
      }

      if (reviewRequired && !reviewExecuted) {
        return failedResult(
          paper,
          pdfPath,
          `Host expected an image review turn in cycle ${cycle}, but it did not run.`,
          runId,
          runDir,
          createRun.run_manifest_path,
          thread.id,
          benchmarkFocus,
        );
      }

      if (reviewRequired) {
        await appendImageReviewProvenance(createRun.run_manifest_path, {
          cycle,
          required: reviewRequired,
          executed: reviewExecuted,
          paperImagePaths: reviewInspection.paperImagePaths,
          outputImagePaths: reviewInspection.outputImagePaths,
          contactSheetPath: reviewInspection.contactSheetPath,
          pageManifestPath: reviewInspection.pageManifestPath,
          reviewTranscriptPath,
          reviewSummary: reviewExecuted ? cycleResponse.summary : null,
          recordedAt: new Date().toISOString(),
        });
      }

      finalCycle = cycleResponse;
      lastSummary = cycleResponse.summary;
      lastReproductionScore = cycleResponse.reproduction?.total_score ?? null;

      const technical = (await this.bridge.invoke("evaluate_technical_run", {
        run_id: runId,
      })) as TechnicalResult;
      if (technical.ok) {
        technicalEvaluationPath = technical.evaluation_json_path;
      }

      const continuation = decideContinuation({
        cycleResponse,
        technical,
        cycle,
        maxCycles: this.config.maxTurnsPerPaper,
        reviewRequired,
        reviewExecuted,
      });
      hostContinuationReason = combineContinuationReason(continuation.reason, lastImageReviewOutcome) ?? undefined;

      if (continuation.shouldContinue) {
        status = "max_turns";
        continue;
      }

      if (
        cycleResponse.status === "completed" &&
        !cycleResponse.needsAnotherCycle &&
        !cycleResponse.needsAnotherImageReview
      ) {
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

    const reproductionScore = finalCycle?.reproduction?.total_score ?? null;
    const reproductionPayload = {
      paper,
      pdfPath,
      runId,
      benchmarkFocus,
      generatedAt: new Date().toISOString(),
      status,
      reproduction: finalCycle?.reproduction ?? null,
      summary: finalCycle?.summary ?? "",
      technicalScore,
      technicalEvaluationPath: technicalPath ?? null,
      cycles: completedCycles,
    };
    const primaryReportDir = technicalPath ? path.dirname(technicalPath) : runDir;
    const reportDirectories = uniquePaths([primaryReportDir, runDir]);
    for (const reportDir of reportDirectories) {
      await writeJson(path.join(reportDir, "reproduction_report.json"), reproductionPayload);
      await writeText(
        path.join(reportDir, "reproduction_report.txt"),
        formatReproductionReportText(reproductionPayload),
      );
    }
    const reproductionPath = path.join(primaryReportDir, "reproduction_report.json");
    const reproductionTextPath = path.join(primaryReportDir, "reproduction_report.txt");

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
      reproductionReportTextPath: reproductionTextPath,
      runManifestPath: createRun.run_manifest_path,
      benchmarkFocus,
      summary: finalCycle?.summary ?? "No final summary available.",
      error: status === "failed" ? finalCycle?.summary : undefined,
    };
    return result;
  }
}

export function buildTurnInput(
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

async function collectTurnWithQuotaFallback(
  thread: Thread,
  input: UserInput[],
  options: QuotaFallbackOptions,
): Promise<CollectedTurn> {
  const cumulativeEvents: ThreadEvent[] = [];
  let retries = 0;

  while (true) {
    const turn = await collectTurn(thread, input);
    cumulativeEvents.push(...turn.events);

    if (
      !turn.error ||
      !options.enabled ||
      !isCodexQuotaLimitError(turn.error) ||
      retries >= options.maxRetries
    ) {
      return { ...turn, events: cumulativeEvents };
    }

    retries += 1;
    const waitMs = getCodexQuotaResetWaitMs(turn.error, {
      fallbackWaitMs: options.fallbackWaitMs,
      retryBufferMs: options.retryBufferMs,
    });
    const resetAt = new Date(Date.now() + waitMs).toISOString();
    const message = [
      `Benchmark host detected a Codex quota/rate limit during ${options.context}.`,
      `Waiting ${formatDuration(waitMs)} before retry ${retries}/${options.maxRetries}.`,
      `Approximate retry time: ${resetAt}.`,
    ].join(" ");
    cumulativeEvents.push({ type: "error", message });
    console.warn(message);
    await sleepWithProgress(waitMs, options.context);
  }
}

async function collectTurn(thread: Thread, input: UserInput[]): Promise<CollectedTurn> {
  const events: ThreadEvent[] = [];
  const items = new Map<string, ThreadItem>();
  let usage: CollectedTurn["usage"] = null;
  let finalResponse = "";
  let turnCompleted = false;
  let turnFailedMessage: string | null = null;
  let recoverableStreamError: string | null = null;

  try {
    const streamed = await thread.runStreamed(input, { outputSchema: FINAL_RESPONSE_SCHEMA });
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
        return { finalResponse, usage, events, items: [...items.values()], error: event.message };
      }
    }
  } catch (error) {
    return { finalResponse, usage, events, items: [...items.values()], error: stringifyError(error) };
  }

  if (turnFailedMessage) {
    return { finalResponse, usage, events, items: [...items.values()], error: turnFailedMessage };
  }

  if (!turnCompleted) {
    const error = recoverableStreamError
      ? `Turn stream ended before completion after transient stream errors: ${recoverableStreamError}`
      : "Turn stream ended before completion.";
    return { finalResponse, usage, events, items: [...items.values()], error };
  }

  return {
    finalResponse,
    usage,
    events,
    items: [...items.values()],
    error: null,
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

function stringifyError(error: unknown): string {
  if (error instanceof Error) {
    return error.message;
  }
  return String(error);
}

export function isCodexQuotaLimitError(message: string): boolean {
  const normalized = message.toLowerCase().replace(/[_-]+/g, " ");
  const quotaSignal =
    normalized.includes("quota") ||
    normalized.includes("usage limit") ||
    normalized.includes("rate limit") ||
    normalized.includes("too many requests") ||
    normalized.includes("429") ||
    normalized.includes("5h") ||
    normalized.includes("5 hour") ||
    normalized.includes("5-hour") ||
    normalized.includes("five hour") ||
    normalized.includes("five-hour") ||
    normalized.includes("weekly limit") ||
    normalized.includes("daily limit") ||
    normalized.includes("request limit");
  if (!quotaSignal) {
    return false;
  }

  return (
    normalized.includes("codex") ||
    normalized.includes("openai") ||
    normalized.includes("chatgpt") ||
    normalized.includes("try again") ||
    normalized.includes("retry") ||
    normalized.includes("reset") ||
    normalized.includes("exceeded") ||
    normalized.includes("reached")
  );
}

export function getCodexQuotaResetWaitMs(
  message: string,
  options: {
    fallbackWaitMs: number;
    retryBufferMs: number;
    now?: Date;
  },
): number {
  const now = options.now ?? new Date();
  const retryBufferMs = nonNegativeNumber(options.retryBufferMs);
  const relativeWaitMs = parseRelativeWaitMs(message);
  if (relativeWaitMs !== null) {
    return nonNegativeNumber(relativeWaitMs) + retryBufferMs;
  }

  const absoluteResetMs = parseAbsoluteResetMs(message, now);
  if (absoluteResetMs !== null) {
    return nonNegativeNumber(absoluteResetMs - now.getTime()) + retryBufferMs;
  }

  return nonNegativeNumber(options.fallbackWaitMs) + retryBufferMs;
}

function parseRelativeWaitMs(message: string): number | null {
  const durationPattern = new RegExp(
    `((?:\\d+(?:\\.\\d+)?\\s*(?:${DURATION_UNIT_PATTERN})\\s*(?:,?\\s*(?:and\\s*)?)?)+)`,
    "i",
  );
  const contextual = message.match(
    new RegExp(
      `(?:try again|retry|reset(?:s)?|available|quota|limit)[^\\n.]{0,120}\\bin\\s+${durationPattern.source}`,
      "i",
    ),
  );
  const fallback = message.match(new RegExp(`\\bin\\s+${durationPattern.source}`, "i"));
  const duration = contextual?.[1] ?? fallback?.[1];
  if (!duration) {
    return null;
  }

  let totalMs = 0;
  const partPattern = new RegExp(`(\\d+(?:\\.\\d+)?)\\s*(${DURATION_UNIT_PATTERN})`, "gi");
  for (const match of duration.matchAll(partPattern)) {
    const value = Number(match[1]);
    const unit = match[2].toLowerCase();
    if (!Number.isFinite(value)) {
      continue;
    }
    if (unit.startsWith("h")) {
      totalMs += value * 60 * 60 * 1000;
    } else if (unit.startsWith("m")) {
      totalMs += value * 60 * 1000;
    } else {
      totalMs += value * 1000;
    }
  }

  return totalMs > 0 ? totalMs : null;
}

function parseAbsoluteResetMs(message: string, now: Date): number | null {
  const isoMatch = message.match(
    /\b20\d{2}-\d{2}-\d{2}(?:[ T]\d{2}:\d{2}(?::\d{2}(?:\.\d{1,3})?)?(?:Z|[+-]\d{2}:?\d{2})?)?\b/,
  );
  if (isoMatch) {
    const parsed = Date.parse(isoMatch[0]);
    if (Number.isFinite(parsed)) {
      return parsed;
    }
  }

  const phraseMatch = message.match(
    /(?:try again|retry|reset(?:s)?|available|quota|limit)[^\n.]{0,120}\b(?:at|after|until)\s+([^\n.;)]+)/i,
  );
  if (phraseMatch) {
    const parsed = Date.parse(phraseMatch[1].trim());
    if (Number.isFinite(parsed)) {
      return parsed;
    }
  }

  const timeMatch = message.match(
    /(?:try again|retry|reset(?:s)?|available|quota|limit)[^\n.]{0,120}\b(?:at|after|until)\s+(\d{1,2})(?::(\d{2}))?\s*(am|pm)?\b/i,
  );
  if (!timeMatch) {
    return null;
  }

  let hour = Number(timeMatch[1]);
  const minute = timeMatch[2] ? Number(timeMatch[2]) : 0;
  const meridiem = timeMatch[3]?.toLowerCase();
  if (!Number.isFinite(hour) || !Number.isFinite(minute) || minute > 59) {
    return null;
  }
  if (meridiem === "pm" && hour < 12) {
    hour += 12;
  }
  if (meridiem === "am" && hour === 12) {
    hour = 0;
  }
  if (hour > 23) {
    return null;
  }

  const reset = new Date(now);
  reset.setHours(hour, minute, 0, 0);
  if (reset.getTime() <= now.getTime()) {
    reset.setDate(reset.getDate() + 1);
  }
  return reset.getTime();
}

async function sleepWithProgress(waitMs: number, context: string): Promise<void> {
  const startedAt = Date.now();
  const targetAt = startedAt + nonNegativeNumber(waitMs);
  let nextProgressAt = startedAt + QUOTA_WAIT_PROGRESS_INTERVAL_MS;

  while (Date.now() < targetAt) {
    const now = Date.now();
    const chunkMs = Math.min(targetAt - now, Math.max(1, nextProgressAt - now));
    await sleep(chunkMs);
    if (Date.now() >= nextProgressAt && Date.now() < targetAt) {
      console.warn(
        `Still waiting for Codex quota reset during ${context}; ${formatDuration(targetAt - Date.now())} remaining.`,
      );
      nextProgressAt += QUOTA_WAIT_PROGRESS_INTERVAL_MS;
    }
  }
}

function minutesToMilliseconds(minutes: number): number {
  return nonNegativeNumber(minutes) * 60_000;
}

function secondsToMilliseconds(seconds: number): number {
  return nonNegativeNumber(seconds) * 1000;
}

function nonNegativeNumber(value: number): number {
  return Number.isFinite(value) ? Math.max(0, value) : 0;
}

function formatDuration(milliseconds: number): string {
  const totalSeconds = Math.ceil(nonNegativeNumber(milliseconds) / 1000);
  const hours = Math.floor(totalSeconds / 3600);
  const minutes = Math.floor((totalSeconds % 3600) / 60);
  const seconds = totalSeconds % 60;
  const parts: string[] = [];
  if (hours > 0) {
    parts.push(`${hours}h`);
  }
  if (minutes > 0 || hours > 0) {
    parts.push(`${minutes}m`);
  }
  parts.push(`${seconds}s`);
  return parts.join(" ");
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

type ContinuationDecision = {
  shouldContinue: boolean;
  reason: string | null;
};

export function decideContinuation(params: {
  cycleResponse: AgentCycleResponse;
  technical: TechnicalResult;
  cycle: number;
  maxCycles: number;
  reviewRequired?: boolean;
  reviewExecuted?: boolean;
}): ContinuationDecision {
  if (params.cycle >= params.maxCycles || params.cycleResponse.status === "failed") {
    return { shouldContinue: false, reason: null };
  }

  if (params.reviewRequired && !params.reviewExecuted) {
    return {
      shouldContinue: true,
      reason: "Inspection artifacts were produced, but the host image-review turn did not run.",
    };
  }

  if (params.cycleResponse.needsAnotherCycle) {
    return { shouldContinue: true, reason: "The agent requested another benchmark cycle." };
  }

  if (params.cycleResponse.needsAnotherImageReview) {
    return { shouldContinue: true, reason: "The agent requested another image-review cycle." };
  }

  if (params.cycleResponse.status !== "completed") {
    return {
      shouldContinue: true,
      reason: `The agent returned status=${params.cycleResponse.status}.`,
    };
  }

  if (!params.cycleResponse.morpheusRan) {
    return { shouldContinue: true, reason: "Morpheus has not run successfully in the agent response." };
  }

  const reproduction = params.cycleResponse.reproduction;
  if (!reproduction) {
    return { shouldContinue: true, reason: "The reproduction rubric is missing." };
  }

  if (!isFlawlessReproduction(reproduction)) {
    return {
      shouldContinue: true,
      reason: `The reproduction rubric is ${reproduction.total_score}/8; continue until all criteria are 2/2.`,
    };
  }

  if (!params.technical.ok) {
    return {
      shouldContinue: true,
      reason: `The host technical evaluation failed: ${params.technical.error ?? "unknown error"}.`,
    };
  }

  if (params.technical.breakdown?.model_graph_matches_xml === false) {
    return {
      shouldContinue: true,
      reason: "The technical evaluation found a ModelGraph mismatch between the canonical XML and the latest attempt outputs.",
    };
  }

  if (params.technical.breakdown?.latest_primary_plot_within_last_time === false) {
    return {
      shouldContinue: true,
      reason: `The latest primary plot (${params.technical.breakdown.latest_primary_plot ?? "unknown"}) exceeds the latest simulated time.`,
    };
  }

  if (params.technical.breakdown?.latest_logger_plot_within_last_time === false) {
    return {
      shouldContinue: true,
      reason: `The latest logger plot (${params.technical.breakdown.latest_logger_plot ?? "unknown"}) exceeds the latest simulated time.`,
    };
  }

  const maxTechnicalScore = params.technical.max_possible_score ?? 7;
  if (params.technical.total_score < maxTechnicalScore) {
    return {
      shouldContinue: true,
      reason: `The technical score is ${params.technical.total_score}/${maxTechnicalScore}; continue until it reaches the maximum.`,
    };
  }

  return { shouldContinue: false, reason: null };
}

function isFlawlessReproduction(reproduction: NonNullable<AgentCycleResponse["reproduction"]>): boolean {
  return (
    reproduction.total_score >= 8 &&
    reproduction.source_coverage.score === 2 &&
    reproduction.mechanism_mapping.score === 2 &&
    reproduction.observable_alignment.score === 2 &&
    reproduction.parameter_plausibility.score === 2
  );
}

function uniquePaths(values: string[]): string[] {
  return [...new Set(values)];
}

function unwrapStructuredToolPayload(result: unknown): Record<string, unknown> | null {
  const structured = (result as { structured_content?: unknown } | null)?.structured_content;
  if (!structured || typeof structured !== "object") {
    return null;
  }
  const maybeNested = structured as { result?: unknown; ok?: boolean };
  if (maybeNested.ok === false) {
    return null;
  }
  if (maybeNested.result && typeof maybeNested.result === "object") {
    const nestedResult = maybeNested.result as { ok?: boolean };
    if (nestedResult.ok === false) {
      return null;
    }
    return maybeNested.result as Record<string, unknown>;
  }
  return structured as Record<string, unknown>;
}

export function collectInspectionArtifacts(items: ThreadItem[], runDir: string): InspectionArtifacts {
  const paperImagePaths = new Set<string>();
  const outputImagePaths = new Set<string>();
  let contactSheetPath: string | null = null;
  let pageManifestPath: string | null = null;

  for (const item of items) {
    const toolItem = item as any;
    if (toolItem.type !== "mcp_tool_call" || toolItem.status !== "completed" || !toolItem.result) {
      continue;
    }

    const payload = unwrapStructuredToolPayload(toolItem.result);
    if (!payload) {
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

function combineContinuationReason(reason: string | null, reviewOutcome?: string): string | null {
  if (reason && reviewOutcome) {
    return `${reason} Prior image review outcome: ${reviewOutcome}`;
  }
  return reason ?? reviewOutcome ?? null;
}

function summarizeImageReviewOutcome(cycle: number, artifacts: InspectionArtifacts, summary: string): string {
  const paperCount = artifacts.paperImagePaths.length;
  const outputCount = artifacts.outputImagePaths.length;
  const contactSheetNote = artifacts.contactSheetPath ? " plus a contact sheet" : "";
  return `Cycle ${cycle} image review inspected ${paperCount} paper image(s) and ${outputCount} output image(s)${contactSheetNote}. Agent summary: ${summary}`;
}

async function appendImageReviewProvenance(runManifestPath: string, entry: Record<string, unknown>): Promise<void> {
  const manifest = (await readJson(runManifestPath)) as Record<string, unknown>;
  const existing = Array.isArray(manifest.image_review_history)
    ? (manifest.image_review_history as Record<string, unknown>[])
    : [];
  manifest.image_review_history = [...existing, entry];
  manifest.latest_image_review = entry;
  await writeJson(runManifestPath, manifest);
}

async function readJson(inputPath: string): Promise<unknown> {
  try {
    const content = await readFile(inputPath, "utf8");
    return JSON.parse(content);
  } catch {
    return {};
  }
}

async function writeTranscript(outputPath: string, events: ThreadEvent[]): Promise<void> {
  await mkdir(path.dirname(outputPath), { recursive: true });
  const content = events.length > 0 ? `${events.map((event) => JSON.stringify(event)).join("\n")}\n` : "";
  await writeFile(outputPath, content, "utf8");
}

async function writeJson(outputPath: string, payload: unknown): Promise<void> {
  await mkdir(path.dirname(outputPath), { recursive: true });
  await writeFile(outputPath, JSON.stringify(payload, null, 2), "utf8");
}

async function writeText(outputPath: string, content: string): Promise<void> {
  await mkdir(path.dirname(outputPath), { recursive: true });
  await writeFile(outputPath, content, "utf8");
}

function formatReproductionReportText(payload: {
  paper: string;
  pdfPath: string;
  runId: string;
  benchmarkFocus: string | null;
  generatedAt: string;
  status: PaperRunResult["status"];
  reproduction: AgentCycleResponse["reproduction"];
  summary: string;
  technicalScore: number | null;
  technicalEvaluationPath: string | null;
  cycles: number;
}): string {
  const lines = [
    "============================================================",
    "MORPHEUS REPRODUCTION REPORT",
    "============================================================",
    `Paper: ${payload.paper}`,
    `PDF Path: ${payload.pdfPath}`,
    `Benchmark Focus: ${payload.benchmarkFocus ?? "n/a"}`,
    `Run ID: ${payload.runId}`,
    `Timestamp: ${payload.generatedAt}`,
    `Status: ${payload.status}`,
    `Cycles: ${payload.cycles}`,
    `Technical Score: ${payload.technicalScore ?? "n/a"}`,
    `Technical Evaluation: ${payload.technicalEvaluationPath ?? "n/a"}`,
    "",
    `SUMMARY: ${payload.summary || "No summary available."}`,
  ];

  if (!payload.reproduction) {
    lines.push("", "No reproduction rubric was returned.");
    return lines.join("\n");
  }

  lines.push(
    "",
    `TOTAL REPRODUCTION SCORE: ${payload.reproduction.total_score} / 8`,
    `REPRODUCTION SUMMARY: ${payload.reproduction.summary}`,
  );

  type ReproductionCriterionKey =
    | "source_coverage"
    | "mechanism_mapping"
    | "observable_alignment"
    | "parameter_plausibility";
  const sections: Array<[string, ReproductionCriterionKey]> = [
    ["Source Coverage", "source_coverage"],
    ["Mechanism Mapping", "mechanism_mapping"],
    ["Observable Alignment", "observable_alignment"],
    ["Parameter Plausibility", "parameter_plausibility"],
  ];

  for (const [title, key] of sections) {
    const criterion = payload.reproduction[key];
    lines.push("", `${title}: ${criterion.score} / 2`, `Rationale: ${criterion.rationale}`, "Evidence:");
    if (criterion.evidence.length === 0) {
      lines.push("- None provided");
      continue;
    }
    for (const evidence of criterion.evidence) {
      lines.push(`- ${evidence}`);
    }
  }

  return lines.join("\n");
}

function failedResult(
  paper: string,
  pdfPath: string,
  error: string,
  runId = "",
  runDir = "",
  runManifestPath: string | null = null,
  threadId: string | null = null,
  benchmarkFocus: string | null = null,
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
    reproductionReportTextPath: null,
    runManifestPath,
    benchmarkFocus,
    summary: error,
    error,
  };
}
