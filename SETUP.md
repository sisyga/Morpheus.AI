# Setup

This guide is written for someone who has not worked with this repository before. If your goal is simply to verify that the benchmark runs, follow the sections in order and start with a one-paper smoke test before attempting the full benchmark.

## 1. What you need

Required:

- Python 3.10 or newer
- Node.js 18 or newer
- Morpheus installed and runnable from the command line
- Codex CLI installed and authenticated locally

Optional but recommended:

- Poppler tools on `PATH`
  - `pdftotext`
  - `pdftoppm`
  - `pdfimages`

If Poppler is not installed, the repository falls back to Python PDF tooling. The benchmark should still run, but PDF staging may be slower or less complete.

## 2. Create a Python environment

From the repository root:

```powershell
python -m venv .venv
```

Activate it.

PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

If PowerShell blocks the script with an execution policy error, use:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.venv\Scripts\Activate.ps1
```

Command Prompt:

```cmd
.venv\Scripts\activate.bat
```

macOS or Linux:

```bash
source .venv/bin/activate
```

Install Python dependencies:

```powershell
pip install -r requirements.txt
```

The Python side provides the MCP server and the deterministic utilities for PDF staging, XML handling, Morpheus execution, and output evaluation.

## 3. Install Node dependencies

From the repository root:

```powershell
npm install
```

This installs the TypeScript benchmark runner and the local `@openai/codex-sdk` dependency used by the harness.

## 4. Install and log into Codex CLI

As of March 16, 2026, OpenAI's Codex CLI documentation describes installation via npm. If `codex` is not already installed on your machine, install it with:

```powershell
npm install -g @openai/codex
```

Then authenticate:

```powershell
codex login
```

Confirm that the CLI is authenticated:

```powershell
codex login status
```

This repository expects a locally authenticated Codex CLI and is set up for OpenAI OAuth-style local login rather than direct benchmark-side API key handling.

## 5. Verify Morpheus

Check that Morpheus is available:

```powershell
morpheus --help
```

If that command fails but Morpheus is installed elsewhere, point the repo to the executable by setting `MORPHEUS_BIN`.

PowerShell:

```powershell
$env:MORPHEUS_BIN = "D:\Programs\Morpheus\morpheus.exe"
```

macOS or Linux:

```bash
export MORPHEUS_BIN=/path/to/morpheus
```

Then rerun:

```powershell
morpheus --help
```

## 6. Optional: install Poppler

Poppler is not required, but it improves PDF staging.

Typical installation routes are:

- macOS: `brew install poppler`
- Ubuntu or Debian: `sudo apt-get install poppler-utils`
- Windows: install a Poppler build and add its `bin` directory to `PATH`

After installation, these commands should resolve:

```powershell
pdftotext -h
pdftoppm -h
pdfimages -h
```

## 7. Verify the repository before running the benchmark

These checks are fast and catch most setup problems:

```powershell
npm run typecheck
python -m unittest test_morpheus_mcp_server.py
```

You do not need to start `server.py` manually for the benchmark. The benchmark runner starts the MCP server automatically from `benchmark.config.json`.

## 8. Run a one-paper smoke test

This is the recommended first run:

```powershell
npm run benchmark -- --max-papers 1
```

This command scans `benchmark_papers/`, takes the first PDF in sorted order, and creates one run directory under `benchmark_runs/`.

If the smoke test works, you should see:

- a new paper-specific folder under `benchmark_runs/`;
- `paper.txt`, `paper_page_manifest.json`, and `paper_figure_manifest.json`;
- a generated `model.xml`;
- Morpheus logs in `stdout.log` and `stderr.log`;
- `technical_evaluation.json`;
- `reproduction_report.json`;
- transcript files under `transcripts/`;
- `benchmark_runs/benchmark_summary.json`.

## 9. Run the full benchmark

Once the smoke test succeeds:

```powershell
npm run benchmark
```

Useful variants:

```powershell
npm run benchmark -- --help
npm run benchmark -- --max-papers 3
npm run benchmark -- --max-turns 8
npm run benchmark -- --results-dir benchmark_runs_review
npm run benchmark -- --model gpt-5.4 --reasoning-effort xhigh
```

The runner processes one paper at a time. Full runs can take a while because each paper may require multiple agent/Morpheus cycles.

## 10. Understand the configuration

The default configuration is stored in `benchmark.config.json`:

```json
{
  "papersDir": "benchmark_papers",
  "resultsDir": "benchmark_runs",
  "model": "gpt-5.4",
  "reasoningEffort": "xhigh",
  "maxTurnsPerPaper": 5,
  "pageRenderDpi": 150,
  "representativeOutputFrames": 5,
  "mcpCommand": ["python", "server.py"],
  "skillPaths": [".agents/skills/morpheus/SKILL.md"]
}
```

Important fields:

- `papersDir`
  Folder scanned for benchmark PDFs.
- `resultsDir`
  Folder where run directories and `benchmark_summary.json` are written.
- `maxTurnsPerPaper`
  Upper bound on the host-controlled review/revision cycles for a single paper.
  One turn is one full Codex cycle for that paper, not one MCP tool call.
- `pageRenderDpi`
  Preferred resolution used when the agent requests specific paper pages for rendering.
- `representativeOutputFrames`
  Preferred number of Morpheus output images the agent should sample when it asks for visual inspection.
- `mcpCommand`
  Command used to start the MCP server.
- `skillPaths`
  Skills enabled for the Codex run.

## 11. Read the outputs

The main files to inspect are:

- `benchmark_runs/benchmark_summary.json`
  Aggregate result across all processed papers.
- `benchmark_runs/<run_dir>/run_manifest.json`
  File map for that paper run.
- `benchmark_runs/<run_dir>/model.xml`
  Final Morpheus model produced for the paper.
- `benchmark_runs/<run_dir>/technical_evaluation.json`
  Legacy 0-7 executability score.
- `benchmark_runs/<run_dir>/reproduction_report.json`
  Structured 0-8 reproduction rubric.
- `benchmark_runs/<run_dir>/stdout.log`
  Morpheus standard output.
- `benchmark_runs/<run_dir>/stderr.log`
  Morpheus errors and warnings.
- `benchmark_runs/<run_dir>/transcripts/`
  Per-cycle structured Codex output.

The benchmark is text-first. It does not attach all page images or all Morpheus output images up front. Instead:

- the agent reads `paper.txt` first;
- if it needs figures, it requests specific pages with `render_pdf_pages`;
- if it needs Morpheus visual output, it requests sampled images with `sample_output_images`;
- the runner then provides those images in an immediate follow-up review turn within the same host cycle.

## 12. Common setup failures

PowerShell says running scripts is disabled when activating `.venv`:

- Run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` in that shell.
- Then activate with `.venv\Scripts\Activate.ps1`.

`codex` command not found:

- Install Codex CLI, then rerun `codex login`.

`codex login status` shows that you are not authenticated:

- Run `codex login` and complete the local login flow.

`morpheus` command not found:

- Install Morpheus or set `MORPHEUS_BIN` to the executable path.

The benchmark starts but fails while staging PDFs:

- Install Poppler if possible.
- If Poppler is unavailable, confirm that the Python environment is active and `pip install -r requirements.txt` completed successfully.

The benchmark creates a run folder but Morpheus does not complete:

- Inspect `stdout.log`, `stderr.log`, and `technical_evaluation.json` in that run directory.
- Check whether the generated `model.xml` is syntactically valid and whether Morpheus reported XML or runtime errors.

The smoke test works but the full benchmark is slow:

- That is expected. Each paper can trigger several agent/revision cycles.
- Use `--max-papers` first to measure behavior on your machine before running the full set.

## 13. What you do not need to do

- You do not need to move files around before running the benchmark.
- You do not need to launch `server.py` separately for the benchmark path.
- You do not need to use anything in `Archive/` for the current workflow.

`Archive/` contains the older Anthropic-based setup and historical outputs. The supported path is the Codex SDK benchmark runner at the repository root.
