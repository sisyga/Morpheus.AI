import { spawn } from "node:child_process";
import path from "node:path";
import process from "node:process";

import type { ToolResult } from "./types.js";

type PythonToolName =
  | "create_run"
  | "extract_paper_text"
  | "render_pdf_pages"
  | "list_paper_figures"
  | "list_references"
  | "read_reference"
  | "read_file_text"
  | "validate_model_xml"
  | "write_model_xml"
  | "run_morpheus_model"
  | "summarize_morpheus_run"
  | "sample_output_images"
  | "evaluate_technical_run";

export class PythonBridge {
  private readonly pythonExecutable: string;
  private readonly cliPath: string;
  private readonly runsDir: string | undefined;

  constructor() {
    this.pythonExecutable = process.env.PYTHON_EXECUTABLE ?? "python";
    this.cliPath = path.resolve(process.cwd(), "morpheus_tools_cli.py");
    this.runsDir = process.env.MORPHEUS_RUNS_DIR;
  }

  invoke<T extends Record<string, unknown>>(command: PythonToolName, payload: Record<string, unknown>): Promise<ToolResult<T>> {
    return new Promise((resolve, reject) => {
      const child = spawn(this.pythonExecutable, [this.cliPath, command], {
        cwd: process.cwd(),
        stdio: ["pipe", "pipe", "pipe"],
        env: {
          ...process.env,
          ...(this.runsDir ? { MORPHEUS_RUNS_DIR: this.runsDir } : {}),
        },
      });

      let stdout = "";
      let stderr = "";

      child.stdout.setEncoding("utf8");
      child.stderr.setEncoding("utf8");
      child.stdout.on("data", (chunk) => {
        stdout += chunk;
      });
      child.stderr.on("data", (chunk) => {
        stderr += chunk;
      });

      child.on("error", (error) => reject(error));
      child.on("close", (code) => {
        const cleaned = stdout.trim();
        if (!cleaned) {
          reject(new Error(`Python tool ${command} returned no JSON. stderr: ${stderr}`));
          return;
        }
        try {
          const parsed = JSON.parse(cleaned) as ToolResult<T>;
          if (!parsed.ok && !parsed.error && stderr.trim()) {
            parsed.error = stderr.trim();
          }
          if (code !== 0 && parsed.ok) {
            parsed.ok = false;
            parsed.error = parsed.error ?? stderr.trim() ?? `Python tool ${command} failed`;
          }
          resolve(parsed);
        } catch (error) {
          reject(
            new Error(
              `Failed to parse Python tool output for ${command}: ${(error as Error).message}\nstdout: ${stdout}\nstderr: ${stderr}`,
            ),
          );
        }
      });

      child.stdin.write(JSON.stringify(payload));
      child.stdin.end();
    });
  }
}
