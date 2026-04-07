# Morpheus.AI

This repository accompanies the Morpheus.AI benchmark study and also serves as a general-purpose Morpheus modeling toolkit. The current workflow uses the Codex SDK, a reusable Morpheus skill, and a thin Python MCP server for deterministic tasks such as PDF staging, XML writing, Morpheus execution, and output inspection.

At the repository level there are two main pieces:

- a benchmark runner that tests whether an agent can recreate Morpheus models from published papers;
- a reusable Morpheus skill and MCP tool layer that can also be used for broader modeling tasks beyond benchmarking.

## Installation

The repository does not include a `.venv/` directory. That environment is created locally after cloning.

Minimal setup from the repository root:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
npm install
```

If PowerShell blocks the activation script, run:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.venv\Scripts\Activate.ps1
```

For shell-specific activation instructions and the full benchmark setup, see [SETUP.md](SETUP.md).

## Quick start

1. Create and activate `.venv`, then install Python and Node dependencies.
2. Confirm that `codex login status` and `morpheus --help` both work.
3. Run `npm run benchmark -- --max-papers 1`.
4. Inspect the new folder under `benchmark_runs/` and the aggregate file `benchmark_runs/benchmark_summary.json`.

## What the benchmark does

For each PDF in `benchmark_papers/`, the runner:

1. creates a dedicated run directory;
2. extracts the paper text;
3. detects likely figure pages but does not attach page images up front;
4. exposes the Morpheus skill and MCP tools to Codex;
5. lets the agent write MorpheusML, run Morpheus, request specific paper pages or sampled output images only when needed, and revise if needed;
6. records technical and reproduction-oriented evaluation files.

Two score tracks are written for each paper:

- `technical_evaluation.json`: the legacy 0-7 executability score.
- `reproduction_report.json`: a structured 0-8 reproduction assessment with four 0-2 criteria:
  - `source_coverage`
  - `mechanism_mapping`
  - `observable_alignment`
  - `parameter_plausibility`

The benchmark runner processes papers one at a time and writes all paper-specific artifacts inside the run directory. It does not modify the source PDFs or the reference corpus.

## Repository layout

- `benchmark_papers/`
  Benchmark inputs. The runner scans this folder for PDF files.
- `benchmark_focus/`
  Optional per-paper focus prompts. A file named like the PDF stem, for example `ten_Berkhout2025_clean.txt`, is appended to that paper's benchmark prompt.
- `references/`
  Morpheus examples and raw reference assets. These help the agent understand Morpheus, but they are not benchmark targets.
- `.agents/skills/morpheus/`
  The publishable Morpheus skill used by the benchmark and intended for general Morpheus modeling tasks beyond paper recreation.
- `src/benchmark/`
  TypeScript benchmark runner built on the Codex SDK.
- `server.py`
  MCP server entry point.
- `morpheus_mcp_server.py`
  Python implementation of the deterministic Morpheus and PDF utilities.
- `morpheus_tools_cli.py`
  JSON bridge used by the benchmark runner.
- `benchmark.config.json`
  Default benchmark configuration.
- `Archive/`
  Legacy Anthropic-era prompts, runners, servers, and historical outputs retained for reference only.

## Minimal benchmark run

Start with one paper instead of the full benchmark:

```powershell
npm run benchmark -- --max-papers 1
```

If that succeeds, you should see:

- a new run folder under `benchmark_runs/`;
- a `model.xml` generated for that paper;
- `stdout.log` and `stderr.log` from Morpheus;
- `technical_evaluation.json`;
- `reproduction_report.json`;
- transcript files under `transcripts/`;
- an updated `benchmark_runs/benchmark_summary.json`.

To run the full benchmark set:

```powershell
npm run benchmark
```

To see available CLI options:

```powershell
npm run benchmark -- --help
```

The benchmark default is now `maxTurnsPerPaper = 5`. This can be overridden on the command line:

```powershell
npm run benchmark -- --max-turns 8
```

## Reading the outputs

Inside a paper run directory you will typically find:

- `run_manifest.json`
  Paths and metadata for the staged inputs and run outputs.
- `paper.txt`
  Extracted text from the benchmark PDF.
- `paper_page_manifest.json`
  The page images rendered on demand for multimodal inspection.
- `paper_figure_manifest.json`
  A lightweight index of likely figure pages in the PDF.
- `model.xml`
  The most recent Morpheus model produced by the agent.
- `xml_versions/`
  Earlier model revisions.
- `stdout.log` and `stderr.log`
  Morpheus run logs.
- `technical_evaluation.json`
  Executability score and breakdown.
- `reproduction_report.json`
  The structured reproduction rubric returned by the agent.
- `transcripts/`
  Per-cycle Codex interaction logs.

At the benchmark root, `benchmark_summary.json` aggregates the run status and scores across all processed papers.

## Benchmark behavior

- The benchmark uses local Codex authentication. It is intended to run with a locally authenticated Codex CLI rather than direct API-key billing in the harness.
- Live web search is disabled during benchmark runs. The agent works from the staged paper assets, the local Morpheus reference material, and the Morpheus outputs generated in the run directory.
- The agent is given paper text up front. Paper page images are not attached by default; instead, the agent can request only the specific figure pages it wants to inspect.
- If `benchmark_focus/<paper-stem>.txt` exists, the runner tells the agent to prioritize that target when the paper contains multiple models or figures.
- The agent can also request representative Morpheus output images. When it does so, the runner attaches those images in an immediate follow-up review turn within the same host cycle.
- A turn is one full host-controlled agent cycle for a paper, not one tool call. Within a single turn, Codex can read references, write XML, run Morpheus, inspect outputs, and return a structured decision about whether another cycle is needed.
- Images are not automatically reattached in later cycles. If the agent still needs them, it must request them again.
- The technical score is deterministic, but the reproduction report is a structured qualitative assessment returned by the agent from the staged evidence.
- Results can vary between runs because the benchmark depends on an LLM-driven modeling loop. In practice, a one-paper smoke test is the best first check, and repeated full runs should be interpreted as distributions rather than perfectly fixed outputs.

## Supported workflow vs. legacy material

The supported workflow is the Codex SDK benchmark runner plus the Morpheus skill and thin MCP server in the repository root.

Everything under `Archive/` is historical material from the earlier Anthropic-based setup. It is kept for comparison, not for routine use.
