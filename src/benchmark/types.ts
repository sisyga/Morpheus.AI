export type ReasoningEffort = "minimal" | "low" | "medium" | "high" | "xhigh";

export type BenchmarkConfig = {
  papersDir: string;
  resultsDir: string;
  model: string;
  reasoningEffort: ReasoningEffort;
  maxTurnsPerPaper: number;
  pageRenderDpi: number;
  representativeOutputFrames: number;
  mcpCommand: string[];
  skillPaths: string[];
};

export type ToolResult<T = Record<string, unknown>> = T & {
  ok: boolean;
  error?: string;
};

export type ReproductionCriterion = {
  score: 0 | 1 | 2;
  evidence: string[];
  rationale: string;
};

export type ReproductionReport = {
  source_coverage: ReproductionCriterion;
  mechanism_mapping: ReproductionCriterion;
  observable_alignment: ReproductionCriterion;
  parameter_plausibility: ReproductionCriterion;
  total_score: number;
  summary: string;
};

export type AgentCycleResponse = {
  runId: string;
  status: "in_progress" | "completed" | "failed";
  summary: string;
  modelChanged: boolean;
  morpheusRan: boolean;
  needsAnotherImageReview: boolean;
  reproduction: ReproductionReport | null;
};

export type PaperRunResult = {
  paper: string;
  pdfPath: string;
  runId: string;
  threadId: string | null;
  status: "completed" | "failed" | "max_turns";
  cycles: number;
  technicalScore: number | null;
  reproductionScore: number | null;
  technicalEvaluationPath: string | null;
  reproductionReportPath: string | null;
  runManifestPath: string | null;
  summary: string;
  error?: string;
};

export type BenchmarkSummary = {
  config: BenchmarkConfig;
  generatedAt: string;
  totalPapers: number;
  completedPapers: number;
  failedPapers: number;
  averageTechnicalScore: number;
  averageReproductionScore: number;
  results: PaperRunResult[];
};
