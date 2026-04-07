from __future__ import annotations

import shutil
import unittest
import uuid
from unittest import mock
from pathlib import Path

import morpheus_mcp_server as server


class MorpheusMcpServerTests(unittest.TestCase):
    def setUp(self) -> None:
        temp_root = Path.cwd() / "runs" / "unit_tests"
        temp_root.mkdir(parents=True, exist_ok=True)
        server.RUNS_ROOT = temp_root / f"test_{uuid.uuid4().hex}"
        server.RUNS_ROOT.mkdir(parents=True, exist_ok=True)
        self.addCleanup(lambda: shutil.rmtree(server.RUNS_ROOT, ignore_errors=True))
        self.env_patch = mock.patch.dict("os.environ", {}, clear=False)
        self.env_patch.start()
        self.addCleanup(self.env_patch.stop)
        server.os.environ.pop(server.ACTIVE_RUN_ID_ENV, None)

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
        self.assertTrue(all(not Path(path).is_absolute() for path in result["selected_images"]))

    def test_extract_stop_time_accepts_nonfirst_value_attribute(self) -> None:
        xml = """
        <MorpheusModel version="4">
          <Time>
            <StopTime symbol="t_stop" value="40"/>
          </Time>
        </MorpheusModel>
        """
        self.assertEqual(server._extract_stop_time(xml), 40.0)

    def test_validation_accepts_single_quoted_png_terminal(self) -> None:
        validation = server._validate_xml_completeness(
            """
            <MorpheusModel version='4'>
              <Description><Title>Eval</Title></Description>
              <Space></Space>
              <Time></Time>
              <Analysis><Gnuplotter><Terminal name='png'/></Gnuplotter></Analysis>
            </MorpheusModel>
            """
        )
        self.assertTrue(validation["has_gnuplotter"])

    def test_create_run_reuses_existing_run_id_name(self) -> None:
        existing = server._run_dir("20260402_201012_ten_Berkhout2025_clean")
        result = server.create_run("20260402_201012_ten_Berkhout2025_clean")
        self.assertTrue(result["ok"])
        self.assertEqual(Path(result["run_dir"]), existing)
        self.assertEqual(result["run_id"], "20260402_201012_ten_Berkhout2025_clean")

    def test_active_run_forces_create_run_to_noop(self) -> None:
        server.os.environ[server.ACTIVE_RUN_ID_ENV] = "active_run"
        result = server.create_run("some_other_name")
        self.assertTrue(result["ok"])
        self.assertEqual(result["run_id"], "active_run")
        self.assertTrue((server.RUNS_ROOT / "active_run").exists())
        self.assertFalse((server.RUNS_ROOT / "some_other_name").exists())

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
