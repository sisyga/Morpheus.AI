from __future__ import annotations

import json
import shutil
import unittest
import uuid
from pathlib import Path
from unittest.mock import patch

import morpheus_mcp_server as server


def minimal_xml(stop_time: str = "500", with_model_graph: bool = True) -> str:
    model_graph = '<ModelGraph include-tags="#untagged" format="dot" reduced="false"/>' if with_model_graph else ""
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<MorpheusModel version="4">
  <Description>
    <Title>Test Model</Title>
  </Description>
  <Space>
    <Lattice class="square">
      <Neighborhood><Order>1</Order></Neighborhood>
      <Size symbol="size" value="20,20,0"/>
    </Lattice>
    <SpaceSymbol symbol="space"/>
  </Space>
  <Time>
    <StartTime value="0"/>
    <StopTime value="{stop_time}"/>
    <TimeSymbol symbol="time"/>
  </Time>
  <Analysis>
    {model_graph}
    <Gnuplotter time-step="100">
      <Terminal name="png"/>
      <Plot><Cells value="cell.id"/></Plot>
    </Gnuplotter>
    <Logger time-step="100">
      <Input><Symbol symbol-ref="time"/></Input>
      <Output><TextOutput/></Output>
    </Logger>
  </Analysis>
</MorpheusModel>
"""


class MorpheusMcpServerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.local_tmp_root = Path.cwd() / ".tmp_test_runs"
        self.local_tmp_root.mkdir(parents=True, exist_ok=True)
        self.original_runs_root = server.RUNS_ROOT
        self.test_runs_root = self.local_tmp_root / f"runs_{uuid.uuid4().hex[:8]}"
        self.test_runs_root.mkdir(parents=True, exist_ok=True)
        server.RUNS_ROOT = self.test_runs_root
        server.RUNS_ROOT.mkdir(parents=True, exist_ok=True)

    def tearDown(self) -> None:
        server.RUNS_ROOT = self.original_runs_root
        shutil.rmtree(self.test_runs_root, ignore_errors=True)

    def test_render_pdf_pages_fails_when_requested_pages_are_all_out_of_range(self) -> None:
        pdf_path = Path("benchmark_papers/1_Szabo2010_clean.pdf").resolve()
        with patch.object(server, "_parse_pdf_page_count", return_value=7):
            result = server.render_pdf_pages(
                pdf_path=str(pdf_path),
                run_id="run_render",
                pages=[9999],
                dpi=72,
            )

        self.assertFalse(result["ok"])
        self.assertEqual(result["requested_pages"], [9999])
        self.assertEqual(result["selected_pages"], [])
        self.assertGreater(result["total_pages"], 0)
        self.assertTrue(result["warnings"])

    def test_list_paper_figures_uses_fallback_detection_when_pdfimages_is_unavailable(self) -> None:
        pdf_path = Path("benchmark_papers/1_Szabo2010_clean.pdf").resolve()
        with patch.object(server, "_list_pdf_figures", return_value=[]), patch.object(
            server,
            "_list_pdf_figures_with_pymupdf",
            return_value=([{"page": 2, "num": 1, "type": "heuristic_page"}], ["fallback used"]),
        ):
            result = server.list_paper_figures(pdf_path=str(pdf_path), run_id="run_figures")

        self.assertTrue(result["ok"])
        self.assertEqual(result["detection_method"], "pymupdf_heuristic")
        self.assertEqual(result["figure_pages"], [2])
        self.assertEqual(result["warnings"], ["fallback used"])

    def test_latest_attempt_controls_summary_and_sampling(self) -> None:
        run_id = "run_attempts"
        run_path = server._run_dir(run_id)
        (run_path / "model.xml").write_text(minimal_xml(stop_time="500"), encoding="utf-8")
        server._merge_manifest(run_id, {"latest_attempt_id": "attempt_002"})

        attempt_one = server._attempt_dir(run_path, "attempt_001")
        attempt_one.mkdir(parents=True, exist_ok=True)
        (attempt_one / "stdout.log").write_text("Time: 0\nTime: 800\n", encoding="utf-8")
        (attempt_one / "plot_00800.png").write_bytes(b"old")
        (attempt_one / "logger_plot_time_00800.png").write_bytes(b"old")
        (attempt_one / "logger.csv").write_text("time\n800\n", encoding="utf-8")

        attempt_two = server._attempt_dir(run_path, "attempt_002")
        attempt_two.mkdir(parents=True, exist_ok=True)
        (attempt_two / "stdout.log").write_text("Time: 0\nTime: 500\n", encoding="utf-8")
        (attempt_two / "stderr.log").write_text("", encoding="utf-8")
        (attempt_two / "plot_00500.png").write_bytes(b"new")
        (attempt_two / "logger_plot_time_00500.png").write_bytes(b"new")
        (attempt_two / "logger.csv").write_text("time\n500\n", encoding="utf-8")

        summary = server.summarize_morpheus_run(run_id=run_id)
        sample = server.sample_output_images(run_id=run_id, limit=5)
        latest_primary_plot = Path(summary["key_outputs"]["latest_primary_plot"]).as_posix()
        selected_images = [Path(value).as_posix() for value in sample["selected_images"]]

        self.assertTrue(summary["ok"])
        self.assertEqual(summary["attempt_id"], "attempt_002")
        self.assertEqual(summary["time_progress"]["last_time_value"], 500.0)
        self.assertEqual(latest_primary_plot, "attempts/attempt_002/plot_00500.png")
        self.assertNotIn("plot_00800.png", json.dumps(summary))

        self.assertTrue(sample["ok"])
        self.assertEqual(sample["attempt_id"], "attempt_002")
        self.assertEqual(selected_images, ["attempts/attempt_002/plot_00500.png", "attempts/attempt_002/logger_plot_time_00500.png"])

    def test_evaluate_technical_run_uses_latest_attempt_only_and_flags_graph_mismatch(self) -> None:
        run_id = "run_eval"
        run_path = server._run_dir(run_id)
        (run_path / "model.xml").write_text(minimal_xml(stop_time="500", with_model_graph=False), encoding="utf-8")

        attempt_one = server._attempt_dir(run_path, "attempt_001")
        attempt_one.mkdir(parents=True, exist_ok=True)
        (attempt_one / "stdout.log").write_text("Time: 0\nTime: 800\n", encoding="utf-8")
        (attempt_one / "plot_00800.png").write_bytes(b"old")
        (attempt_one / "logger.csv").write_text("time\n800\n", encoding="utf-8")

        attempt_two = server._attempt_dir(run_path, "attempt_002")
        attempt_two.mkdir(parents=True, exist_ok=True)
        (attempt_two / "stdout.log").write_text("Time: 0\nTime: 500\n", encoding="utf-8")
        (attempt_two / "stderr.log").write_text("", encoding="utf-8")
        (attempt_two / "plot_00500.png").write_bytes(b"new")
        (attempt_two / "logger_plot_time_00500.png").write_bytes(b"new")
        (attempt_two / "logger.csv").write_text("time\n500\n", encoding="utf-8")
        (attempt_two / "model_graph.dot").write_text("digraph G {}", encoding="utf-8")
        server._merge_manifest(run_id, {"latest_attempt_id": "attempt_002"})

        evaluation = server.evaluate_technical_run(run_id=run_id)
        latest_primary_plot = Path(evaluation["breakdown"]["latest_primary_plot"]).as_posix()

        self.assertTrue(evaluation["ok"])
        self.assertEqual(evaluation["attempt_id"], "attempt_002")
        self.assertEqual(latest_primary_plot, "attempts/attempt_002/plot_00500.png")
        self.assertTrue(evaluation["breakdown"]["model_graph_present"])
        self.assertFalse(evaluation["breakdown"]["model_graph_matches_xml"])
        self.assertEqual(evaluation["breakdown"]["model_graph_score"], 0)

    def test_capture_model_xml_version_creates_host_snapshot_for_external_edits(self) -> None:
        run_id = "run_capture"
        write_result = server.write_model_xml(xml_content=minimal_xml(stop_time="100"), run_id=run_id)
        self.assertTrue(write_result["ok"])

        run_path = server._run_dir(run_id)
        (run_path / "model.xml").write_text(minimal_xml(stop_time="200"), encoding="utf-8")

        capture = server.capture_model_xml_version(run_id=run_id, reason="cycle_01_main_turn")
        manifest = json.loads((run_path / "run_manifest.json").read_text(encoding="utf-8"))

        self.assertTrue(capture["ok"])
        self.assertTrue(capture["snapshot_created"])
        self.assertEqual(capture["xml_version_count"], 2)
        self.assertTrue((run_path / "xml_versions" / "model_v002.xml").exists())
        self.assertEqual(manifest["last_host_captured_xml_version"]["reason"], "cycle_01_main_turn")
        self.assertEqual(len(manifest["host_captured_xml_versions"]), 1)


if __name__ == "__main__":
    unittest.main()
