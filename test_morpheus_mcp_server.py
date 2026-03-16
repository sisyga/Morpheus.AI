from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import morpheus_mcp_server as server


class MorpheusMcpServerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tempdir.cleanup)
        server.RUNS_ROOT = Path(self.tempdir.name)
        server.RUNS_ROOT.mkdir(parents=True, exist_ok=True)

    def test_write_model_xml_creates_versioned_copies(self) -> None:
        result = server.write_model_xml(
            """
            <MorpheusModel version="4">
              <Description><Title>Test</Title></Description>
              <Space></Space>
              <Time></Time>
              <Analysis><Gnuplotter><Terminal name="png"/></Gnuplotter></Analysis>
            </MorpheusModel>
            """,
            run_id="run_xml",
        )
        self.assertTrue(result["ok"])
        self.assertTrue(Path(result["xml_path"]).exists())
        self.assertTrue(Path(result["version_path"]).exists())
        self.assertEqual(result["validation"]["has_root"], True)

    def test_sample_output_images_prefers_primary_frames(self) -> None:
        run_path = server._run_dir("run_images")
        for index in range(10):
            (run_path / f"plot_{index:05d}.png").write_text("x", encoding="utf-8")
        (run_path / "logger_plot_00000.png").write_text("x", encoding="utf-8")
        (run_path / "logger_plot_00009.png").write_text("x", encoding="utf-8")

        result = server.sample_output_images("run_images", limit=5)
        self.assertTrue(result["ok"])
        self.assertEqual(len(result["selected_images"]), 7)
        self.assertEqual(result["primary_plot_count"], 10)
        self.assertEqual(result["logger_plot_count"], 2)

    def test_evaluate_technical_run_preserves_legacy_score(self) -> None:
        run_path = server._run_dir("run_eval")
        (run_path / "model.xml").write_text(
            """
            <MorpheusModel version="4">
              <Description><Title>Eval</Title></Description>
              <Space></Space>
              <Time><StopTime value="1000"/></Time>
              <Analysis>
                <Gnuplotter><Terminal name="png"/></Gnuplotter>
                <Logger><Output><TextOutput/></Output></Logger>
                <ModelGraph/>
              </Analysis>
            </MorpheusModel>
            """,
            encoding="utf-8",
        )
        (run_path / "stdout.log").write_text(
            "\n".join(["Time: 0", "Time: 500", "Time: 1000"]),
            encoding="utf-8",
        )
        (run_path / "stderr.log").write_text("", encoding="utf-8")
        (run_path / "model_graph.dot").write_text("graph", encoding="utf-8")
        for index in range(10):
            (run_path / f"plot_{index:05d}.png").write_text("x", encoding="utf-8")
        (run_path / "logger.csv").write_text("x", encoding="utf-8")

        result = server.evaluate_technical_run("run_eval")
        self.assertTrue(result["ok"])
        self.assertEqual(result["total_score"], 6)
        self.assertEqual(result["breakdown"]["png_count"], 10)


if __name__ == "__main__":
    unittest.main()
