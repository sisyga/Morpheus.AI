from __future__ import annotations

import json
import sys
from typing import Any, Callable, Dict

from morpheus_mcp_server import (
    create_run,
    evaluate_technical_run,
    extract_paper_text,
    get_model_example_corpus_status,
    list_paper_figures,
    list_model_example_assets,
    list_references,
    read_file_text,
    read_model_example,
    read_model_example_section,
    read_reference,
    render_pdf_pages,
    run_morpheus_model,
    sample_output_images,
    search_model_examples,
    suggest_model_examples_for_paper,
    summarize_morpheus_run,
    validate_model_xml,
    write_model_xml,
)

COMMANDS: Dict[str, Callable[..., Dict[str, Any]]] = {
    "create_run": create_run,
    "extract_paper_text": extract_paper_text,
    "render_pdf_pages": render_pdf_pages,
    "list_paper_figures": list_paper_figures,
    "get_model_example_corpus_status": get_model_example_corpus_status,
    "search_model_examples": search_model_examples,
    "suggest_model_examples_for_paper": suggest_model_examples_for_paper,
    "read_model_example": read_model_example,
    "read_model_example_section": read_model_example_section,
    "list_model_example_assets": list_model_example_assets,
    "list_references": list_references,
    "read_reference": read_reference,
    "read_file_text": read_file_text,
    "validate_model_xml": validate_model_xml,
    "write_model_xml": write_model_xml,
    "run_morpheus_model": run_morpheus_model,
    "summarize_morpheus_run": summarize_morpheus_run,
    "sample_output_images": sample_output_images,
    "evaluate_technical_run": evaluate_technical_run,
}


def main() -> int:
    if len(sys.argv) != 2 or sys.argv[1] not in COMMANDS:
        available = ", ".join(sorted(COMMANDS))
        print(
            json.dumps(
                {
                    "ok": False,
                    "error": f"Usage: python morpheus_tools_cli.py <command>. Available: {available}",
                }
            )
        )
        return 1

    raw_payload = sys.stdin.read().strip()
    payload = json.loads(raw_payload) if raw_payload else {}
    try:
        result = COMMANDS[sys.argv[1]](**payload)
    except Exception as exc:
        result = {"ok": False, "error": str(exc)}
    print(json.dumps(result))
    return 0 if result.get("ok", True) else 1


if __name__ == "__main__":
    raise SystemExit(main())
