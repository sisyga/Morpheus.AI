# Morpheus Model Corpus

This folder is for large, local, on-demand Morpheus example corpora.

The recommended layout is:

```text
corpus/
  model-repo/                 # local clone of https://gitlab.com/morpheus.lab/model-repo
  morpheus-model-index.sqlite # optional generated index/cache
```

`model-repo/` is intentionally gitignored. It is a local clone/cache, not benchmark output and not prompt context.

The MCP server reads this corpus when available and falls back to `references/model_repository.txt` when the clone is missing.
