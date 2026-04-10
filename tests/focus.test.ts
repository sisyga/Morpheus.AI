import assert from "node:assert/strict";
import path from "node:path";
import test from "node:test";

import { loadPaperFocus } from "../src/benchmark/focus.js";

test("loadPaperFocus reads focus text matching the PDF stem", async () => {
  const focus = await loadPaperFocus(
    path.resolve("benchmark_focus"),
    path.resolve("benchmark_papers/ten_Berkhout2025_clean.pdf"),
  );

  assert.equal(focus, "WT Fig.1 and Fig.2");
});

test("loadPaperFocus treats missing focus files as optional", async () => {
  const focus = await loadPaperFocus(path.resolve("benchmark_focus"), "benchmark_papers/missing.pdf");
  assert.equal(focus, null);
});
