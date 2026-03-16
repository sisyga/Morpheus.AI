# Setup

This repo now has three installable layers:

1. the Python Morpheus utility layer and MCP server;
2. the local Codex SDK benchmark runner;
3. the Morpheus skill and repo `AGENTS.md`.

## Prerequisites

- Python 3.10+
- Node.js 18+
- Morpheus installed and available on `PATH`
- Codex CLI logged in with OpenAI OAuth or otherwise configured locally

Optional but recommended:

- Poppler tools on `PATH`
  - `pdftotext`
  - `pdftoppm`
  - `pdfimages`

If Poppler is not available, the Python utilities fall back to `pypdf` and `PyMuPDF` for PDF processing.

## Python installation

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

The Python dependency set now includes:

- `mcp`
- `python-dotenv`
- `pypdf`
- `PyMuPDF`
- `Pillow`

## Node installation

```powershell
npm install
```

The benchmark runner depends on:

- `@openai/codex-sdk`
- `typescript`
- `tsx`

## Morpheus verification

```powershell
morpheus --help
```

If Morpheus is not on `PATH`, set:

```powershell
$env:MORPHEUS_BIN = "D:\Programs\Morpheus\morpheus.exe"
```

## Codex verification

```powershell
codex login status
```

The current benchmark defaults assume the local Codex configuration uses:

- `model = "gpt-5.4"`
- `model_reasoning_effort = "xhigh"`

## Benchmark configuration

The benchmark uses `benchmark.config.json`.

Default fields:

```json
{
  "papersDir": "benchmark_papers",
  "resultsDir": "benchmark_runs",
  "model": "gpt-5.4",
  "reasoningEffort": "xhigh",
  "maxTurnsPerPaper": 30,
  "pageRenderDpi": 150,
  "representativeOutputFrames": 5,
  "mcpCommand": ["python", "server.py"],
  "skillPaths": [".agents/skills/morpheus/SKILL.md"]
}
```

## Running the benchmark

Run the default benchmark:

```powershell
npm run benchmark
```

Override common settings:

```powershell
npm run benchmark -- -- --max-papers 1
npm run benchmark -- -- --papers-dir benchmark_papers --results-dir benchmark_runs
npm run benchmark -- -- --model gpt-5.4 --reasoning-effort xhigh
```

## Running the MCP server directly

```powershell
python server.py
```

The benchmark runner injects the MCP server into Codex automatically from `mcpCommand`, but the server is also usable on its own.

## Output structure

Each paper creates a run directory under `benchmark_runs/` by default:

```text
benchmark_runs/
  20260316_183403_my_paper/
    paper.txt
    paper_page_manifest.json
    paper_figure_manifest.json
    model.xml
    xml_versions/
    stdout.log
    stderr.log
    technical_evaluation.json
    technical_evaluation.txt
    reproduction_report.json
    sample_contact_sheet.png
    transcripts/
```

## Tests

TypeScript:

```powershell
npm run typecheck
npm run test:ts
```

Python:

```powershell
python -m unittest test_morpheus_mcp_server.py
```

## Legacy files

The legacy Anthropic benchmark scripts remain in the repo for reference, but they are not part of the supported install path anymore.
