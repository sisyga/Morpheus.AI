# Morpheus.AI

Morpheus.AI is a skill-first Morpheus modeling repo with two public surfaces:

- a TypeScript benchmark runner built on the Codex SDK;
- a thin Python MCP server for deterministic Morpheus, PDF, and artifact utilities.

The benchmark flow is no longer centered on Anthropic prompts or a benchmark-specific state machine. The reusable interface is the Morpheus skill in `.agents/skills/morpheus/`, with the MCP server as a companion for tools that are easier to expose deterministically.

## What is in this repo

- `benchmark_papers/`
  Benchmark input PDFs.
- `references/`
  Raw Morpheus examples and assets.
- `.agents/skills/morpheus/`
  The publishable Morpheus skill and its markdown-grounded reference set.
- `src/benchmark/`
  The Codex SDK benchmark runner.
- `server.py`
  Entry point for the thin MCP server.
- `morpheus_mcp_server.py`
  Python utility implementation used by the MCP server.
- `morpheus_tools_cli.py`
  JSON-over-stdin bridge used by the benchmark runner between Codex turns.

## Quick start

### 1. Install Python dependencies

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Install Node dependencies

```powershell
npm install
```

### 3. Verify Morpheus and Codex

```powershell
morpheus --help
codex login status
```

### 4. Run the benchmark

```powershell
npm run benchmark -- -- --max-papers 1
```

The default configuration lives in `benchmark.config.json`.

## Benchmark runner

The benchmark runner uses the local Codex SDK and the repo skill to process papers one at a time. Each paper gets its own run directory under `benchmark_runs/` by default.

Per paper, the runner:

1. creates a run directory;
2. stages the paper as extracted text, page-rendered PNGs, and a figure manifest;
3. starts a Codex thread with the Morpheus skill enabled;
4. lets the agent ground itself in references, write Morpheus XML, run Morpheus, and inspect outputs;
5. writes:
   - `run_manifest.json`
   - `technical_evaluation.json`
   - `technical_evaluation.txt`
   - `reproduction_report.json`
   - per-cycle transcript JSONL files

The benchmark keeps the legacy 0-7 technical score and adds a second reproduction score with four 0-2 criteria:

- `source_coverage`
- `mechanism_mapping`
- `observable_alignment`
- `parameter_plausibility`

## MCP server

Start the server with:

```powershell
python server.py
```

The intended public tool surface is:

- `extract_paper_text`
- `render_pdf_pages`
- `list_paper_figures`
- `list_references`
- `read_reference`
- `validate_model_xml`
- `write_model_xml`
- `run_morpheus_model`
- `summarize_morpheus_run`
- `sample_output_images`
- `evaluate_technical_run`

These tools are stateless apart from the explicit run directory they write into.

## Skill-first workflow

The Morpheus skill is the main reusable interface. It is designed for:

- recreating published models in Morpheus;
- translating mathematical or biological descriptions into MorpheusML;
- hypothesis-driven Morpheus modeling;
- inspecting Morpheus output images and logs.

The benchmark runner enables the skill explicitly and the repo now ships a real `AGENTS.md` so Codex can discover the workflow locally.

## Configuration

`benchmark.config.json` supports:

- `papersDir`
- `resultsDir`
- `model`
- `reasoningEffort`
- `maxTurnsPerPaper`
- `pageRenderDpi`
- `representativeOutputFrames`
- `mcpCommand`
- `skillPaths`

Default values are tuned for the current Codex setup:

- `model = "gpt-5.4"`
- `reasoningEffort = "xhigh"`
- `maxTurnsPerPaper = 30`
- `pageRenderDpi = 150`
- `representativeOutputFrames = 5`

## Testing

TypeScript:

```powershell
npm run typecheck
npm run test:ts
```

Python:

```powershell
python -m unittest test_morpheus_mcp_server.py
```

## Legacy note

The old Anthropic benchmark scripts and prompt files are still present for historical comparison, but they are no longer the primary workflow and the README/SETUP no longer document them as the supported path.
