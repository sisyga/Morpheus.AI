# Morpheus.AI Agents

## Available skill
- `morpheus`: `.agents/skills/morpheus/SKILL.md`

## Default workflow
- Use the `morpheus` skill for MorpheusML authoring, model debugging, simulation execution, and image inspection.
- Prefer the skill's markdown reference set before falling back to raw files in `references/`.
- Treat `benchmark_papers/` as benchmark inputs and `references/` as Morpheus examples, not benchmark targets.

## Repo expectations
- Keep benchmark orchestration in the TypeScript runner.
- Keep reusable deterministic utilities in the Python MCP server and CLI bridge.
- Write paper-specific outputs only inside the configured run directory.
- Do not edit benchmark source PDFs or the reference corpus during benchmark runs.
