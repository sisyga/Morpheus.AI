from __future__ import annotations

import json
import math
import os
import re
import shutil
import subprocess
import uuid
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

try:
    from dotenv import load_dotenv
except ImportError:
    def load_dotenv(*args: Any, **kwargs: Any) -> bool:
        return False

try:
    from mcp.server.fastmcp import FastMCP
except ImportError:
    class FastMCP:  # type: ignore[override]
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            self.args = args
            self.kwargs = kwargs

        def tool(self):
            def decorator(func):
                return func

            return decorator

        def run(self, *args: Any, **kwargs: Any) -> None:
            raise RuntimeError("mcp is not installed. Install requirements before running the MCP server.")

load_dotenv()

REPO_ROOT = Path(__file__).resolve().parent
RUNS_ROOT = Path(os.getenv("MORPHEUS_RUNS_DIR", REPO_ROOT / "runs")).expanduser()
RUNS_ROOT.mkdir(parents=True, exist_ok=True)
ACTIVE_RUN_ID_ENV = "MORPHEUS_ACTIVE_RUN_ID"

MORPHEUS_BIN = os.getenv("MORPHEUS_BIN", "morpheus")
MAX_TEXT_PREVIEW = 1_000
MAX_READ_CHARS = 50_000
MAX_REFERENCE_READ_CHARS = 250_000
MAX_LOG_PREVIEW_CHARS = 1_500
MAX_OUTPUT_PATHS = 6
RUN_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]+$")
ATTEMPT_ID_PATTERN = re.compile(r"^attempt_(\d{3})$")
FIGURE_CAPTION_PATTERN = re.compile(r"\bfig(?:ure)?\.?\s*[A-Za-z]?\s*\d+", re.IGNORECASE)

REFERENCES_ROOT = REPO_ROOT / "references"
REFERENCE_CATEGORIES = {
    "CPM": REFERENCES_ROOT / "CPM",
    "PDE": REFERENCES_ROOT / "PDE",
    "ODE": REFERENCES_ROOT / "ODE",
    "Multiscale": REFERENCES_ROOT / "Multiscale",
    "Miscellaneous": REFERENCES_ROOT / "Miscellaneous",
}

mcp = FastMCP(
    name="morpheus-mcp",
    host="0.0.0.0",
    port=0,
    stateless_http=True,
)


def _now_iso() -> str:
    return datetime.now().isoformat()


def _now_stamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def _new_run_id() -> str:
    return f"{_now_stamp()}_{uuid.uuid4().hex[:8]}"


def _active_run_id() -> Optional[str]:
    run_id = os.getenv(ACTIVE_RUN_ID_ENV, "").strip()
    return run_id or None


def _sanitize_run_name(name: str) -> str:
    sanitized = re.sub(r"[^A-Za-z0-9_-]+", "_", name).strip("_")
    return sanitized or "run"


def _validate_run_id(run_id: str) -> str:
    if not RUN_ID_PATTERN.fullmatch(run_id):
        raise ValueError(
            f"Invalid run_id {run_id!r}. Run IDs may only contain letters, numbers, underscores, and hyphens."
        )
    return run_id


def _coerce_run_id(run_id: Optional[str]) -> str:
    active_run_id = _active_run_id()
    if active_run_id:
        _validate_run_id(active_run_id)
        if run_id and run_id != active_run_id:
            raise ValueError(
                f"Active benchmark run is {active_run_id!r}; received run_id {run_id!r}. "
                "Use the active run_id exactly and do not create paper-specific output folders."
            )
        return active_run_id

    if run_id is None:
        return _new_run_id()
    return _validate_run_id(run_id)


def _run_dir(run_id: str) -> Path:
    run_id = _validate_run_id(run_id)
    run_path = (RUNS_ROOT / run_id).resolve()
    runs_root = RUNS_ROOT.resolve()
    if run_path != runs_root and runs_root not in run_path.parents:
        raise ValueError(f"Resolved run directory escapes the configured runs root: {run_path}")
    run_path.mkdir(parents=True, exist_ok=True)
    return run_path


def _is_within(root: Path, target: Path) -> bool:
    try:
        target.resolve().relative_to(root.resolve())
        return True
    except Exception:
        return False


def _resolve_run_file_path(run_path: Path, requested_path: str) -> Path:
    if not requested_path or not requested_path.strip():
        raise ValueError("file_name must not be empty")

    raw_path = Path(requested_path).expanduser()
    resolved = raw_path.resolve() if raw_path.is_absolute() else (run_path / raw_path).resolve()
    if not _is_within(run_path, resolved):
        raise ValueError("file_name must stay within the run directory")
    if resolved.exists() and resolved.is_dir():
        raise ValueError("file_name must point to a file, not a directory")
    return resolved


def _allowed_read_roots() -> List[Path]:
    return [RUNS_ROOT.resolve(), REFERENCES_ROOT.resolve()]


def _resolve_allowed_read_path(requested_path: str) -> Path:
    if not requested_path or not requested_path.strip():
        raise ValueError("path must not be empty")

    raw_path = Path(requested_path).expanduser()
    candidates = [raw_path.resolve()] if raw_path.is_absolute() else [
        (REPO_ROOT / raw_path).resolve(),
        (RUNS_ROOT / raw_path).resolve(),
        (REFERENCES_ROOT / raw_path).resolve(),
    ]

    for candidate in candidates:
        if any(_is_within(root, candidate) for root in _allowed_read_roots()):
            return candidate

    allowed_roots = ", ".join(str(root) for root in _allowed_read_roots())
    raise ValueError(
        f"Invalid path: {requested_path}. read_file_text only allows files inside {allowed_roots}"
    )


def _ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def _write_text(path: Path, text: str) -> None:
    _ensure_parent(path)
    path.write_text(text, encoding="utf-8", errors="ignore")


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    _ensure_parent(path)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _read_text(path: Path, max_chars: int = MAX_READ_CHARS) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="ignore")[:max_chars]


def _read_text_tail(path: Path, max_chars: int = MAX_LOG_PREVIEW_CHARS) -> str:
    if not path.exists():
        return ""
    text = path.read_text(encoding="utf-8", errors="ignore")
    if len(text) <= max_chars:
        return text
    return text[-max_chars:]


def _read_text_full(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="ignore")


def _manifest_path(run_id: str) -> Path:
    return _run_dir(run_id) / "run_manifest.json"


def _load_manifest(run_id: str) -> Dict[str, Any]:
    manifest_path = _manifest_path(run_id)
    if manifest_path.exists():
        return json.loads(manifest_path.read_text(encoding="utf-8"))
    return {
        "run_id": run_id,
        "run_dir": str(_run_dir(run_id)),
        "created_at": _now_iso(),
    }


def _merge_manifest(run_id: str, updates: Dict[str, Any]) -> Path:
    manifest_path = _manifest_path(run_id)
    manifest = _load_manifest(run_id)
    manifest.update(updates)
    _write_json(manifest_path, manifest)
    return manifest_path


def _append_manifest_event(run_id: str, key: str, entry: Dict[str, Any]) -> Path:
    manifest_path = _manifest_path(run_id)
    manifest = _load_manifest(run_id)
    existing = manifest.get(key)
    if not isinstance(existing, list):
        existing = []
    existing.append(entry)
    manifest[key] = existing
    _write_json(manifest_path, manifest)
    return manifest_path


def _list_outputs(run_path: Path) -> Dict[str, List[str]]:
    return {
        "png": sorted(str(path) for path in run_path.rglob("*.png")),
        "csv": sorted(str(path) for path in run_path.rglob("*.csv")),
        "xml": sorted(str(path) for path in run_path.rglob("*.xml")),
        "dot": sorted(str(path) for path in run_path.rglob("*.dot")),
        "log": sorted(str(path) for path in run_path.rglob("*.log")),
    }


def _relative_to_run(run_path: Path, target: Path) -> str:
    try:
        return str(target.resolve().relative_to(run_path.resolve()))
    except Exception:
        return str(target)


def _sample_paths(run_path: Path, paths: Sequence[str], limit: int = MAX_OUTPUT_PATHS) -> List[str]:
    sampled = [Path(path) for path in paths[:limit]]
    return [_relative_to_run(run_path, path) for path in sampled]


def _last_relative(run_path: Path, paths: Sequence[str]) -> Optional[str]:
    if not paths:
        return None
    return _relative_to_run(run_path, Path(paths[-1]))


def _output_counts(outputs: Dict[str, List[str]]) -> Dict[str, int]:
    return {key: len(value) for key, value in outputs.items()}


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _time_progress_summary(stdout_text: str) -> Dict[str, Any]:
    time_lines, time_values = _count_time_lines(stdout_text)
    return {
        "time_lines_count": time_lines,
        "first_time_value": time_values[0] if time_values else None,
        "last_time_value": time_values[-1] if time_values else None,
    }


def _validate_attempt_id(attempt_id: str) -> str:
    if not ATTEMPT_ID_PATTERN.fullmatch(attempt_id):
        raise ValueError("attempt_id must match attempt_###, for example attempt_001")
    return attempt_id


def _attempts_root(run_path: Path) -> Path:
    attempts_root = run_path / "attempts"
    attempts_root.mkdir(parents=True, exist_ok=True)
    return attempts_root


def _existing_attempt_ids(run_path: Path) -> List[str]:
    attempts_root = _attempts_root(run_path)
    attempts = [
        path.name
        for path in attempts_root.iterdir()
        if path.is_dir() and ATTEMPT_ID_PATTERN.fullmatch(path.name)
    ]
    return sorted(attempts)


def _next_attempt_id(run_path: Path) -> str:
    indices = [
        int(match.group(1))
        for attempt_id in _existing_attempt_ids(run_path)
        if (match := ATTEMPT_ID_PATTERN.fullmatch(attempt_id))
    ]
    next_index = (max(indices) if indices else 0) + 1
    return f"attempt_{next_index:03d}"


def _attempt_dir(run_path: Path, attempt_id: str) -> Path:
    attempt_id = _validate_attempt_id(attempt_id)
    attempt_path = (_attempts_root(run_path) / attempt_id).resolve()
    attempts_root = _attempts_root(run_path).resolve()
    if attempt_path != attempts_root and attempts_root not in attempt_path.parents:
        raise ValueError(f"Resolved attempt directory escapes the attempts root: {attempt_path}")
    return attempt_path


def _latest_attempt_id(run_id: str, run_path: Optional[Path] = None) -> Optional[str]:
    run_path = run_path or _run_dir(run_id)
    manifest = _load_manifest(run_id)
    latest_attempt_id = manifest.get("latest_attempt_id")
    if isinstance(latest_attempt_id, str):
        attempt_path = _attempt_dir(run_path, latest_attempt_id)
        if attempt_path.is_dir():
            return latest_attempt_id
    existing = _existing_attempt_ids(run_path)
    return existing[-1] if existing else None


def _resolve_attempt(run_id: str, run_path: Path, attempt_id: Optional[str]) -> Tuple[Optional[str], Optional[Path]]:
    resolved_attempt_id = _validate_attempt_id(attempt_id) if attempt_id else _latest_attempt_id(run_id, run_path)
    if not resolved_attempt_id:
        return None, None
    attempt_path = _attempt_dir(run_path, resolved_attempt_id)
    if not attempt_path.exists():
        return None, None
    return resolved_attempt_id, attempt_path


def _non_contact_sheet_pngs(paths: Sequence[str]) -> List[str]:
    return [path for path in paths if Path(path).name != "sample_contact_sheet.png"]


def _which(command: str) -> Optional[str]:
    return shutil.which(command)


def _run_cmd(
    command: Sequence[str],
    cwd: Optional[Path] = None,
    timeout_s: Optional[int] = None,
) -> Dict[str, Any]:
    completed = subprocess.run(
        list(command),
        cwd=str(cwd) if cwd else None,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="ignore",
        timeout=timeout_s,
    )
    return {
        "returncode": completed.returncode,
        "stdout": completed.stdout or "",
        "stderr": completed.stderr or "",
        "command": list(command),
    }


def _sanitize_xml(xml: str) -> str:
    xml = xml.strip()
    xml = re.sub(r"^\s*```xml\s*", "", xml, flags=re.IGNORECASE)
    xml = re.sub(r"\s*```\s*$", "", xml)
    return xml.strip()


def _looks_like_morpheus_xml(xml: str) -> bool:
    return "<MorpheusModel" in xml and "</MorpheusModel>" in xml


def _poppler_extract_text(pdf_path: Path) -> Optional[str]:
    if not _which("pdftotext"):
        return None
    result = _run_cmd(["pdftotext", "-layout", str(pdf_path), "-"])
    if result["returncode"] != 0 or not result["stdout"].strip():
        return None
    return result["stdout"]


def _python_extract_text(pdf_path: Path) -> str:
    try:
        from pypdf import PdfReader  # type: ignore
    except ImportError as exc:
        raise RuntimeError(
            "Could not extract PDF text. Install pypdf or provide Poppler's pdftotext."
        ) from exc

    reader = PdfReader(str(pdf_path))
    chunks: List[str] = []
    for page in reader.pages:
        try:
            chunks.append(page.extract_text() or "")
        except Exception:
            continue
    return "\n\n".join(chunks).strip()


def _extract_pdf_text(pdf_path: Path) -> str:
    text = _poppler_extract_text(pdf_path)
    if text is not None:
        return text.strip()
    return _python_extract_text(pdf_path)


def _render_with_poppler(
    pdf_path: Path,
    out_dir: Path,
    pages: Sequence[int],
    dpi: int,
) -> List[Path]:
    rendered: List[Path] = []
    if not _which("pdftoppm"):
        return rendered

    for page in pages:
        prefix = out_dir / f"page_{page:04d}"
        result = _run_cmd(
            [
                "pdftoppm",
                "-f",
                str(page),
                "-l",
                str(page),
                "-r",
                str(dpi),
                "-png",
                str(pdf_path),
                str(prefix),
            ]
        )
        if result["returncode"] != 0:
            continue
        candidates = sorted(out_dir.glob(f"{prefix.name}*.png"))
        if candidates:
            target = out_dir / f"page_{page:04d}.png"
            if candidates[0] != target:
                candidates[0].replace(target)
                for extra in candidates[1:]:
                    extra.unlink(missing_ok=True)
            rendered.append(target)
    return rendered


def _render_with_pymupdf(
    pdf_path: Path,
    out_dir: Path,
    pages: Sequence[int],
    dpi: int,
) -> List[Path]:
    try:
        import fitz  # type: ignore
    except ImportError as exc:
        raise RuntimeError(
            "Could not render PDF pages. Install PyMuPDF or provide Poppler's pdftoppm."
        ) from exc

    doc = fitz.open(str(pdf_path))
    scale = dpi / 72.0
    matrix = fitz.Matrix(scale, scale)
    rendered: List[Path] = []
    for page_num in pages:
        pix = doc.load_page(page_num - 1).get_pixmap(matrix=matrix, alpha=False)
        out_path = out_dir / f"page_{page_num:04d}.png"
        pix.save(str(out_path))
        rendered.append(out_path)
    return rendered


def _render_pdf_pages(
    pdf_path: Path,
    out_dir: Path,
    pages: Sequence[int],
    dpi: int,
) -> List[Path]:
    rendered = _render_with_poppler(pdf_path, out_dir, pages, dpi)
    if rendered:
        return rendered
    return _render_with_pymupdf(pdf_path, out_dir, pages, dpi)


def _parse_pdf_page_count(pdf_path: Path) -> int:
    if _which("pdfinfo"):
        result = _run_cmd(["pdfinfo", str(pdf_path)])
        if result["returncode"] == 0:
            for line in result["stdout"].splitlines():
                if line.startswith("Pages:"):
                    return int(line.split(":", 1)[1].strip())
    try:
        from pypdf import PdfReader  # type: ignore
    except ImportError as exc:
        raise RuntimeError(
            "Could not determine PDF page count. Install pypdf or provide Poppler's pdfinfo."
        ) from exc
    return len(PdfReader(str(pdf_path)).pages)


def _parse_pdfimages_output(raw_output: str) -> List[Dict[str, Any]]:
    figures: List[Dict[str, Any]] = []
    lines = [line for line in raw_output.splitlines() if line.strip()]
    for line in lines[2:]:
        parts = re.split(r"\s+", line.strip())
        if len(parts) < 16:
            continue
        figures.append(
            {
                "page": int(parts[0]),
                "num": int(parts[1]),
                "type": parts[2],
                "width": int(parts[3]),
                "height": int(parts[4]),
                "color": parts[5],
                "encoding": parts[8],
                "object_id": f"{parts[10]} {parts[11]}",
                "x_ppi": int(parts[12]),
                "y_ppi": int(parts[13]),
                "size": parts[14],
                "ratio": parts[15],
            }
        )
    return figures


def _list_pdf_figures(pdf_path: Path) -> List[Dict[str, Any]]:
    if not _which("pdfimages"):
        return []
    result = _run_cmd(["pdfimages", "-list", str(pdf_path)])
    if result["returncode"] != 0:
        return []
    return _parse_pdfimages_output(result["stdout"])


def _list_pdf_figures_with_pymupdf(pdf_path: Path) -> Tuple[List[Dict[str, Any]], List[str]]:
    try:
        import fitz  # type: ignore
    except ImportError:
        return [], ["PyMuPDF is not installed, so figure-page heuristic detection is unavailable."]

    warnings = [
        "pdfimages is unavailable or returned no figures; used PyMuPDF figure-page heuristics based on captions and page graphics."
    ]
    figures: List[Dict[str, Any]] = []
    doc = fitz.open(str(pdf_path))
    try:
        for page_index in range(doc.page_count):
            page = doc.load_page(page_index)
            text = page.get_text("text") or ""
            caption_matches = FIGURE_CAPTION_PATTERN.findall(text)
            image_count = len(page.get_images(full=True))
            try:
                drawing_count = len(page.get_drawings())
            except Exception:
                drawing_count = 0
            has_figure_caption = len(caption_matches) > 0
            has_page_graphics = image_count > 0 or drawing_count > 0
            if not has_figure_caption or not has_page_graphics:
                continue
            figures.append(
                {
                    "page": page_index + 1,
                    "num": len(figures) + 1,
                    "type": "heuristic_page",
                    "width": page.rect.width,
                    "height": page.rect.height,
                    "caption_matches": caption_matches[:5],
                    "image_count": image_count,
                    "drawing_count": drawing_count,
                }
            )
    finally:
        doc.close()
    if not figures:
        warnings.append("No figure pages matched the fallback caption-and-graphics heuristic.")
    return figures, warnings


def _infer_reference_categories_from_text(text: str) -> Dict[str, Any]:
    lower = text.lower()
    scores = {"CPM": 0, "PDE": 0, "ODE": 0, "Multiscale": 0}

    cpm_keywords = [
        "cellular potts",
        "cpm",
        "adhesion",
        "contact energy",
        "surface constraint",
        "cell sorting",
        "motility",
    ]
    pde_keywords = [
        "reaction-diffusion",
        "diffusion",
        "morphogen",
        "concentration field",
        "gradient",
    ]
    ode_keywords = [
        "ode",
        "ordinary differential equation",
        "kinetic model",
        "gene regulatory",
        "signaling network",
    ]
    multiscale_keywords = [
        "multiscale",
        "hybrid",
        "cellular potts model",
        "chemokine",
        "feedback loop",
    ]

    scores["CPM"] += sum(keyword in lower for keyword in cpm_keywords)
    scores["PDE"] += sum(keyword in lower for keyword in pde_keywords)
    scores["ODE"] += sum(keyword in lower for keyword in ode_keywords)
    scores["Multiscale"] += sum(keyword in lower for keyword in multiscale_keywords)

    selected = [name for name, score in scores.items() if score > 0]
    if not selected:
        selected = ["Miscellaneous"]

    return {"scores": scores, "selected_categories": selected}


def _validate_xml_completeness(xml: str) -> Dict[str, Any]:
    cleaned = _sanitize_xml(xml)
    has_png_terminal = re.search(r"<Terminal\b[^>]*\bname\s*=\s*['\"]png['\"]", cleaned) is not None
    checks = {
        "has_root": "<MorpheusModel" in cleaned and "</MorpheusModel>" in cleaned,
        "has_description": "<Description>" in cleaned and "</Description>" in cleaned,
        "has_space": "<Space>" in cleaned and "</Space>" in cleaned,
        "has_time": "<Time>" in cleaned and "</Time>" in cleaned,
        "has_analysis": "<Analysis>" in cleaned and "</Analysis>" in cleaned,
        "has_gnuplotter": "<Gnuplotter" in cleaned and has_png_terminal,
        "has_logger": "<Logger" in cleaned and "<TextOutput" in cleaned,
        "has_model_graph": "<ModelGraph" in cleaned,
        "has_version": 'version="4"' in cleaned or "version='4'" in cleaned,
    }

    errors: List[str] = []
    warnings: List[str] = []
    if not checks["has_root"]:
        errors.append("Missing MorpheusModel root element")
    if not checks["has_description"]:
        warnings.append("Missing Description section")
    if not checks["has_space"]:
        warnings.append("Missing Space section")
    if not checks["has_time"]:
        warnings.append("Missing Time section")
    if not checks["has_analysis"]:
        warnings.append("Missing Analysis section")
    if checks["has_analysis"] and not checks["has_gnuplotter"]:
        warnings.append("Analysis section is missing Gnuplotter PNG output")
    if checks["has_analysis"] and not checks["has_logger"]:
        warnings.append("Analysis section is missing Logger CSV output")
    if checks["has_analysis"] and not checks["has_model_graph"]:
        warnings.append("Analysis section is missing ModelGraph output")
    if checks["has_root"] and not checks["has_version"]:
        warnings.append("MorpheusModel is not version 4")

    return {
        **checks,
        "valid": checks["has_root"],
        "graph_generation_ready": checks["has_analysis"] and checks["has_gnuplotter"],
        "errors": errors,
        "warnings": warnings,
    }


def _extract_stop_time(xml_text: str) -> Optional[float]:
    patterns = [
        r'<StopTime\b[^>]*\bvalue\s*=\s*["\']?([\d.eE+-]+)["\']?[^>]*/?>',
        r'<StopTime[^>]*>([\d.eE+-]+)</StopTime>',
    ]
    for pattern in patterns:
        match = re.search(pattern, xml_text, re.IGNORECASE)
        if match:
            try:
                return float(match.group(1))
            except ValueError:
                continue
    return None


def _count_time_lines(stdout_text: str) -> Tuple[int, List[float]]:
    time_values: List[float] = []
    pattern = re.compile(r"^Time:\s*<?([\d.eE+-]+)>?", re.IGNORECASE)
    for line in stdout_text.splitlines():
        match = pattern.match(line.strip())
        if not match:
            continue
        try:
            time_values.append(float(match.group(1)))
        except ValueError:
            continue
    return len(time_values), time_values


def _calculate_time_score(time_line_count: int) -> int:
    if time_line_count == 0:
        return 0
    if time_line_count == 1:
        return 1
    if 1 < time_line_count < 101:
        return 2
    return 3


def _count_error_lines(stderr_text: str) -> int:
    stderr_text = stderr_text.strip()
    if not stderr_text:
        return 0
    count = 0
    patterns = [r"\[ERROR\]", r"\[FATAL\]", r"Error:", r"error:", r"Exception"]
    for line in stderr_text.splitlines():
        if not line.strip():
            continue
        if any(re.search(pattern, line) for pattern in patterns):
            count += 1
    return count if count > 0 else len([line for line in stderr_text.splitlines() if line.strip()])


def _extract_time_from_png_name(path_value: Optional[str]) -> Optional[float]:
    if not path_value:
        return None
    match = re.search(r"_(\d+(?:\.\d+)?)\.png$", Path(path_value).name)
    if not match:
        return None
    try:
        return float(match.group(1))
    except ValueError:
        return None


def _pick_evenly_spaced(items: Sequence[Path], limit: int) -> List[Path]:
    if not items or limit <= 0:
        return []
    if len(items) <= limit:
        return list(items)
    if limit == 1:
        return [items[0]]

    indices = [0]
    for step in range(1, limit - 1):
        ratio = step / (limit - 1)
        indices.append(round(ratio * (len(items) - 1)))
    indices.append(len(items) - 1)

    ordered = sorted(set(indices))
    return [items[index] for index in ordered][:limit]


def _create_contact_sheet(image_paths: Sequence[Path], output_path: Path) -> Optional[Path]:
    if not image_paths:
        return None
    try:
        from PIL import Image, ImageOps  # type: ignore
    except ImportError:
        return None

    thumbs: List[Any] = []
    for path in image_paths:
        try:
            image = Image.open(path).convert("RGB")
            image.thumbnail((320, 320))
            thumbs.append(ImageOps.pad(image, (320, 320), color="white"))
        except Exception:
            continue

    if not thumbs:
        return None

    columns = min(3, len(thumbs))
    rows = math.ceil(len(thumbs) / columns)
    sheet = Image.new("RGB", (columns * 320, rows * 320), color="white")
    for index, thumb in enumerate(thumbs):
        x = (index % columns) * 320
        y = (index // columns) * 320
        sheet.paste(thumb, (x, y))
    _ensure_parent(output_path)
    sheet.save(output_path)
    return output_path


def _sample_run_images(run_path: Path, limit: int) -> Dict[str, Any]:
    pngs = sorted(path for path in run_path.rglob("*.png") if path.name != "sample_contact_sheet.png")
    primary = [path for path in pngs if path.name.startswith("plot_")]
    logger = [path for path in pngs if path.name.startswith("logger_")]

    selected_primary = _pick_evenly_spaced(primary, limit)
    selected_logger: List[Path] = []
    if logger:
        selected_logger.append(logger[0])
        if logger[-1] != logger[0]:
            selected_logger.append(logger[-1])

    selected = selected_primary + [path for path in selected_logger if path not in selected_primary]
    return {
        "all_png_count": len(pngs),
        "primary_plot_count": len(primary),
        "logger_plot_count": len(logger),
        "selected": selected,
    }


@mcp.tool()
def create_run(name: Optional[str] = None) -> Dict[str, Any]:
    active_run_id = _active_run_id()
    if active_run_id:
        run_id = _validate_run_id(active_run_id)
        run_path = _run_dir(run_id)
        manifest_path = _merge_manifest(
            run_id,
            {
                "run_id": run_id,
                "run_dir": str(run_path),
                "runs_root": str(RUNS_ROOT),
            },
        )
        return {
            "ok": True,
            "run_id": run_id,
            "run_dir": str(run_path),
            "runs_root": str(RUNS_ROOT),
            "run_manifest_path": str(manifest_path),
            "note": "Using the active benchmark run; create_run is a no-op inside benchmark cycles.",
        }

    if name:
        sanitized_name = _sanitize_run_name(name)
        existing_path = RUNS_ROOT / sanitized_name
        run_id = sanitized_name if existing_path.is_dir() else f"{_now_stamp()}_{sanitized_name}"
    else:
        run_id = _new_run_id()

    run_path = _run_dir(run_id)
    manifest_path = _merge_manifest(
        run_id,
        {
            "run_id": run_id,
            "run_dir": str(run_path),
            "created_at": _now_iso(),
            "runs_root": str(RUNS_ROOT),
        },
    )
    return {
        "ok": True,
        "run_id": run_id,
        "run_dir": str(run_path),
        "runs_root": str(RUNS_ROOT),
        "run_manifest_path": str(manifest_path),
    }


@mcp.tool()
def extract_paper_text(pdf_path: str, run_id: Optional[str] = None) -> Dict[str, Any]:
    pdf_file = Path(pdf_path).expanduser().resolve()
    if not pdf_file.exists():
        return {"ok": False, "error": f"PDF not found: {pdf_path}"}

    try:
        run_id = _coerce_run_id(run_id)
        run_path = _run_dir(run_id)
    except ValueError as exc:
        return {"ok": False, "error": str(exc)}

    try:
        text = _extract_pdf_text(pdf_file)
    except Exception as exc:
        return {"ok": False, "error": str(exc)}

    if not text.strip():
        return {"ok": False, "error": "No text could be extracted from PDF"}

    text_path = run_path / "paper.txt"
    _write_text(text_path, text)

    page_count = _parse_pdf_page_count(pdf_file)
    suggestions = _infer_reference_categories_from_text(text[:50_000])
    manifest_path = _merge_manifest(
        run_id,
        {
            "paper_pdf_path": str(pdf_file),
            "paper_text_path": str(text_path),
            "paper_page_count": page_count,
            "reference_suggestions": suggestions,
        },
    )

    return {
        "ok": True,
        "run_id": run_id,
        "run_dir": str(run_path),
        "pdf_path": str(pdf_file),
        "text_path": str(text_path),
        "page_count": page_count,
        "text_preview": text[:MAX_TEXT_PREVIEW],
        "reference_suggestions": suggestions,
        "run_manifest_path": str(manifest_path),
    }


def _normalize_page_request(
    total_pages: int,
    pages: Optional[List[int]],
    max_pages: Optional[int],
) -> Tuple[Optional[List[int]], List[int], List[str]]:
    warnings: List[str] = []
    requested_pages = list(pages) if pages is not None else None
    selected_pages = requested_pages or list(range(1, total_pages + 1))
    out_of_range_pages = [page for page in selected_pages if page < 1 or page > total_pages]
    if out_of_range_pages:
        warnings.append(
            f"Ignored out-of-range pages: {', '.join(str(page) for page in sorted(set(out_of_range_pages)))}."
        )
    selected_pages = [page for page in selected_pages if 1 <= page <= total_pages]
    if max_pages is not None and len(selected_pages) > max_pages:
        warnings.append(f"Truncated page render request to max_pages={max_pages}.")
        selected_pages = selected_pages[:max_pages]
    return requested_pages, selected_pages, warnings


@mcp.tool()
def render_pdf_pages(
    pdf_path: str,
    run_id: Optional[str] = None,
    pages: Optional[List[int]] = None,
    dpi: int = 150,
    max_pages: Optional[int] = None,
) -> Dict[str, Any]:
    pdf_file = Path(pdf_path).expanduser().resolve()
    if not pdf_file.exists():
        return {"ok": False, "error": f"PDF not found: {pdf_path}"}

    try:
        run_id = _coerce_run_id(run_id)
        run_path = _run_dir(run_id)
    except ValueError as exc:
        return {"ok": False, "error": str(exc)}
    out_dir = run_path / "paper_pages"
    out_dir.mkdir(parents=True, exist_ok=True)

    total_pages = _parse_pdf_page_count(pdf_file)
    requested_pages, selected_pages, warnings = _normalize_page_request(total_pages, pages, max_pages)
    if requested_pages is not None and not selected_pages:
        return {
            "ok": False,
            "error": f"None of the requested pages are within the PDF page range 1..{total_pages}.",
            "run_id": run_id,
            "pdf_path": str(pdf_file),
            "total_pages": total_pages,
            "requested_pages": requested_pages,
            "selected_pages": selected_pages,
            "warnings": warnings,
        }

    try:
        rendered_paths = _render_pdf_pages(pdf_file, out_dir, selected_pages, dpi)
    except Exception as exc:
        return {"ok": False, "error": str(exc)}

    page_entries = [
        {"page": page, "path": _relative_to_run(run_path, path)}
        for page, path in zip(selected_pages, rendered_paths)
    ]
    manifest_path = run_path / "paper_page_manifest.json"
    if selected_pages and len(page_entries) != len(selected_pages):
        warnings.append(
            f"Only rendered {len(page_entries)} of {len(selected_pages)} requested page(s)."
        )
    _write_json(
        manifest_path,
        {
            "pdf_path": str(pdf_file),
            "dpi": dpi,
            "total_pages": total_pages,
            "requested_pages": requested_pages,
            "selected_pages": selected_pages,
            "pages": page_entries,
            "warnings": warnings,
            "generated_at": _now_iso(),
        },
    )
    _merge_manifest(
        run_id,
        {
            "paper_page_manifest_path": str(manifest_path),
            "paper_page_image_count": len(page_entries),
            "paper_page_warnings": warnings,
        },
    )

    return {
        "ok": True,
        "run_id": run_id,
        "pdf_path": str(pdf_file),
        "dpi": dpi,
        "total_pages": total_pages,
        "requested_pages": requested_pages,
        "selected_pages": selected_pages,
        "pages": page_entries,
        "warnings": warnings,
        "manifest_path": _relative_to_run(run_path, manifest_path),
    }


@mcp.tool()
def list_paper_figures(pdf_path: str, run_id: Optional[str] = None) -> Dict[str, Any]:
    pdf_file = Path(pdf_path).expanduser().resolve()
    if not pdf_file.exists():
        return {"ok": False, "error": f"PDF not found: {pdf_path}"}

    try:
        run_id = _coerce_run_id(run_id)
        run_path = _run_dir(run_id)
    except ValueError as exc:
        return {"ok": False, "error": str(exc)}

    warnings: List[str] = []
    figures = _list_pdf_figures(pdf_file)
    detection_method = "pdfimages"
    if not figures:
        detection_method = "pymupdf_heuristic"
        figures, warnings = _list_pdf_figures_with_pymupdf(pdf_file)
    figure_pages = sorted({figure["page"] for figure in figures if isinstance(figure.get("page"), int)})
    manifest_path = run_path / "paper_figure_manifest.json"
    _write_json(
        manifest_path,
        {
            "pdf_path": str(pdf_file),
            "generated_at": _now_iso(),
            "figure_count": len(figures),
            "figure_pages": figure_pages,
            "detection_method": detection_method,
            "warnings": warnings,
        },
    )
    _merge_manifest(
        run_id,
        {
            "paper_figure_manifest_path": str(manifest_path),
            "paper_figure_count": len(figures),
            "paper_figure_detection_method": detection_method,
            "paper_figure_warnings": warnings,
        },
    )

    return {
        "ok": True,
        "run_id": run_id,
        "pdf_path": str(pdf_file),
        "figure_count": len(figures),
        "figure_pages": figure_pages,
        "detection_method": detection_method,
        "warnings": warnings,
        "manifest_path": _relative_to_run(run_path, manifest_path),
        "note": "Likely pages containing figures. Render only specific pages when visual inspection is needed.",
    }


@mcp.tool()
def list_references(category: Optional[str] = None) -> Dict[str, Any]:
    categories = {category: REFERENCE_CATEGORIES.get(category)} if category else REFERENCE_CATEGORIES
    results: Dict[str, List[str]] = {}
    for name, directory in categories.items():
        if not directory or not directory.exists():
            continue
        results[name] = sorted(
            path.name
            for path in directory.iterdir()
            if path.is_file() and path.suffix in {".xml", ".txt", ".tif", ".tiff"}
        )
    return {"ok": True, "categories": results}


@mcp.tool()
def read_reference(category: str, name: str, max_chars: int = MAX_REFERENCE_READ_CHARS) -> Dict[str, Any]:
    directory = REFERENCE_CATEGORIES.get(category)
    if not directory:
        return {
            "ok": False,
            "error": f"Unknown category: {category}. Valid categories: {list(REFERENCE_CATEGORIES)}",
        }
    path = (directory / name).resolve()
    if not path.exists() or not path.is_file():
        return {"ok": False, "error": f"Reference not found: {category}/{name}"}
    if directory not in path.parents:
        return {"ok": False, "error": "Invalid reference path"}

    content = _read_text(path, max_chars)
    return {
        "ok": True,
        "category": category,
        "name": name,
        "path": str(path),
        "content": content,
        "validation": _validate_xml_completeness(content) if path.suffix == ".xml" else None,
    }


@mcp.tool()
def validate_model_xml(xml_content: str) -> Dict[str, Any]:
    validation = _validate_xml_completeness(xml_content)
    return {"ok": validation["valid"], **validation}


@mcp.tool()
def write_model_xml(
    xml_content: str,
    run_id: Optional[str] = None,
    file_name: str = "model.xml",
) -> Dict[str, Any]:
    cleaned = _sanitize_xml(xml_content)
    if not _looks_like_morpheus_xml(cleaned):
        return {
            "ok": False,
            "error": "Provided XML does not look like a MorpheusModel document",
        }

    try:
        run_id = _coerce_run_id(run_id)
        run_path = _run_dir(run_id)
        xml_path = _resolve_run_file_path(run_path, file_name)
    except ValueError as exc:
        return {"ok": False, "error": str(exc)}
    version_dir = run_path / "xml_versions"
    version_dir.mkdir(parents=True, exist_ok=True)

    existing_versions = sorted(version_dir.glob("model_v*.xml"))
    version_index = len(existing_versions) + 1
    version_path = version_dir / f"model_v{version_index:03d}.xml"

    _write_text(xml_path, cleaned)
    _write_text(version_path, cleaned)

    validation = _validate_xml_completeness(cleaned)
    manifest_path = _merge_manifest(
        run_id,
        {
            "current_model_xml_path": str(xml_path),
            "latest_xml_version_path": str(version_path),
            "xml_version_count": version_index,
            "last_xml_validation": validation,
        },
    )

    return {
        "ok": True,
        "run_id": run_id,
        "xml_path": str(xml_path),
        "version_path": str(version_path),
        "validation": validation,
        "run_manifest_path": str(manifest_path),
    }


@mcp.tool()
def capture_model_xml_version(run_id: str, reason: str = "host_captured") -> Dict[str, Any]:
    try:
        run_id = _coerce_run_id(run_id)
        run_path = _run_dir(run_id)
    except ValueError as exc:
        return {"ok": False, "error": str(exc)}

    xml_path = run_path / "model.xml"
    if not xml_path.exists():
        return {
            "ok": True,
            "run_id": run_id,
            "model_present": False,
            "snapshot_created": False,
            "reason": reason,
        }

    current_text = _read_text_full(xml_path)
    current_hash = _sha256_text(current_text)
    version_dir = run_path / "xml_versions"
    version_dir.mkdir(parents=True, exist_ok=True)
    existing_versions = sorted(version_dir.glob("model_v*.xml"))
    latest_version_path = existing_versions[-1] if existing_versions else None
    latest_hash = _sha256_text(_read_text_full(latest_version_path)) if latest_version_path else None
    if latest_hash == current_hash:
        manifest_path = _merge_manifest(
            run_id,
            {
                "current_model_xml_path": str(xml_path),
                "current_model_xml_sha256": current_hash,
                "latest_xml_version_path": str(latest_version_path) if latest_version_path else None,
                "xml_version_count": len(existing_versions),
            },
        )
        return {
            "ok": True,
            "run_id": run_id,
            "model_present": True,
            "snapshot_created": False,
            "current_model_sha256": current_hash,
            "latest_version_path": str(latest_version_path) if latest_version_path else None,
            "xml_version_count": len(existing_versions),
            "run_manifest_path": str(manifest_path),
            "reason": reason,
        }

    version_index = len(existing_versions) + 1
    version_path = version_dir / f"model_v{version_index:03d}.xml"
    _write_text(version_path, current_text)
    validation = _validate_xml_completeness(current_text)
    manifest_path = _merge_manifest(
        run_id,
        {
            "current_model_xml_path": str(xml_path),
            "current_model_xml_sha256": current_hash,
            "latest_xml_version_path": str(version_path),
            "xml_version_count": version_index,
            "last_xml_validation": validation,
            "last_host_captured_xml_version": {
                "timestamp": _now_iso(),
                "reason": reason,
                "version_path": str(version_path),
                "sha256": current_hash,
            },
        },
    )
    _append_manifest_event(
        run_id,
        "host_captured_xml_versions",
        {
            "timestamp": _now_iso(),
            "reason": reason,
            "version_path": str(version_path),
            "sha256": current_hash,
        },
    )
    return {
        "ok": True,
        "run_id": run_id,
        "model_present": True,
        "snapshot_created": True,
        "current_model_sha256": current_hash,
        "version_path": str(version_path),
        "xml_version_count": version_index,
        "validation": validation,
        "run_manifest_path": str(manifest_path),
        "reason": reason,
    }


@mcp.tool()
def run_morpheus_model(
    xml_path: str,
    run_id: Optional[str] = None,
    threads: Optional[int] = None,
    attempt_id: Optional[str] = None,
) -> Dict[str, Any]:
    xml_file = Path(xml_path).expanduser().resolve()
    if not xml_file.exists():
        return {"ok": False, "error": f"XML not found: {xml_path}"}

    try:
        inferred_run_id = None if _active_run_id() else xml_file.parent.name
        run_id = _coerce_run_id(run_id or inferred_run_id)
        run_path = _run_dir(run_id)
    except ValueError as exc:
        return {"ok": False, "error": str(exc)}

    if _active_run_id():
        try:
            xml_file.relative_to(run_path)
        except ValueError:
            return {
                "ok": False,
                "error": f"XML path must be inside the active benchmark run directory: {run_path}",
            }

    resolved_attempt_id = _validate_attempt_id(attempt_id) if attempt_id else _next_attempt_id(run_path)
    attempt_path = _attempt_dir(run_path, resolved_attempt_id)
    if attempt_path.exists() and any(attempt_path.iterdir()):
        return {
            "ok": False,
            "error": f"Attempt directory already exists and is not empty: {resolved_attempt_id}",
        }
    attempt_path.mkdir(parents=True, exist_ok=True)
    executed_xml_path = attempt_path / "model.xml"
    shutil.copy2(xml_file, executed_xml_path)

    command = [MORPHEUS_BIN, "-f", str(xml_file), "--outdir", str(attempt_path)]
    if threads:
        command.extend(["--num-threads", str(threads)])

    try:
        result = _run_cmd(command, cwd=xml_file.parent, timeout_s=None)
    except FileNotFoundError:
        return {
            "ok": False,
            "error": f"Morpheus binary not found: {MORPHEUS_BIN}",
        }
    except Exception as exc:
        return {"ok": False, "error": str(exc)}

    stdout_path = attempt_path / "stdout.log"
    stderr_path = attempt_path / "stderr.log"
    _write_text(stdout_path, result["stdout"])
    _write_text(stderr_path, result["stderr"])

    outputs = _list_outputs(attempt_path)
    png_outputs = _non_contact_sheet_pngs(outputs["png"])
    primary_pngs = [path for path in png_outputs if Path(path).name.startswith("plot_")]
    logger_pngs = [path for path in png_outputs if Path(path).name.startswith("logger_")]
    stdout_summary = _time_progress_summary(result["stdout"])
    manifest_path = _merge_manifest(
        run_id,
        {
            "last_run_at": _now_iso(),
            "last_run_command": command,
            "last_run_returncode": result["returncode"],
            "last_run_png_count": len(png_outputs),
            "last_run_csv_count": len(outputs["csv"]),
            "latest_attempt_id": resolved_attempt_id,
            "latest_attempt_dir": str(attempt_path),
            "latest_attempt_xml_path": str(executed_xml_path),
            "latest_attempt_stdout_path": str(stdout_path),
            "latest_attempt_stderr_path": str(stderr_path),
            "latest_attempt_returncode": result["returncode"],
            "latest_attempt_png_count": len(png_outputs),
            "latest_attempt_csv_count": len(outputs["csv"]),
        },
    )
    _append_manifest_event(
        run_id,
        "attempt_history",
        {
            "attempt_id": resolved_attempt_id,
            "attempt_dir": str(attempt_path),
            "executed_xml_path": str(executed_xml_path),
            "command": command,
            "returncode": result["returncode"],
            "started_at": _now_iso(),
            "png_count": len(png_outputs),
            "csv_count": len(outputs["csv"]),
        },
    )

    ok = result["returncode"] == 0
    return {
        "ok": ok,
        "run_id": run_id,
        "attempt_id": resolved_attempt_id,
        "attempt_dir": _relative_to_run(run_path, attempt_path),
        "xml_path": _relative_to_run(run_path, xml_file),
        "executed_xml_path": _relative_to_run(run_path, executed_xml_path),
        "run_dir": str(run_path),
        "returncode": result["returncode"],
        "stdout_path": _relative_to_run(run_path, stdout_path),
        "stderr_path": _relative_to_run(run_path, stderr_path),
        "stdout_tail": _read_text_tail(stdout_path),
        "stderr_tail": _read_text_tail(stderr_path),
        "time_progress": stdout_summary,
        "output_counts": {
            **_output_counts(outputs),
            "primary_plot_count": len(primary_pngs),
            "logger_plot_count": len(logger_pngs),
        },
        "key_outputs": {
            "latest_primary_plot": _last_relative(run_path, primary_pngs),
            "latest_logger_plot": _last_relative(run_path, logger_pngs),
            "latest_csv": _last_relative(run_path, outputs["csv"]),
        },
        "run_manifest_path": _relative_to_run(run_path, manifest_path),
        "message": "Morpheus run completed" if ok else "Morpheus run failed",
    }


@mcp.tool()
def summarize_morpheus_run(run_id: str, attempt_id: Optional[str] = None) -> Dict[str, Any]:
    try:
        run_id = _coerce_run_id(run_id)
        run_path = _run_dir(run_id)
    except ValueError as exc:
        return {"ok": False, "error": str(exc)}
    resolved_attempt_id, attempt_path = _resolve_attempt(run_id, run_path, attempt_id)
    if not resolved_attempt_id or not attempt_path:
        return {"ok": False, "error": f"No Morpheus attempt exists yet for run_id={run_id}."}
    outputs = _list_outputs(attempt_path)
    png_outputs = _non_contact_sheet_pngs(outputs["png"])
    stdout_path = attempt_path / "stdout.log"
    stderr_path = attempt_path / "stderr.log"
    xml_path = run_path / "model.xml"
    executed_xml_path = attempt_path / "model.xml"
    primary_pngs = [path for path in png_outputs if Path(path).name.startswith("plot_")]
    logger_pngs = [path for path in png_outputs if Path(path).name.startswith("logger_")]
    stdout_text = _read_text_full(stdout_path) if stdout_path.exists() else ""
    stderr_text = _read_text_tail(stderr_path) if stderr_path.exists() else ""

    return {
        "ok": True,
        "run_id": run_id,
        "attempt_id": resolved_attempt_id,
        "attempt_dir": _relative_to_run(run_path, attempt_path),
        "run_dir": str(run_path),
        "xml_path": _relative_to_run(run_path, xml_path) if xml_path.exists() else None,
        "executed_xml_path": _relative_to_run(run_path, executed_xml_path) if executed_xml_path.exists() else None,
        "stdout_path": _relative_to_run(run_path, stdout_path) if stdout_path.exists() else None,
        "stderr_path": _relative_to_run(run_path, stderr_path) if stderr_path.exists() else None,
        "output_counts": {
            **{**_output_counts(outputs), "png": len(png_outputs)},
            "primary_plot_count": len(primary_pngs),
            "logger_plot_count": len(logger_pngs),
        },
        "key_outputs": {
            "latest_primary_plot": _last_relative(run_path, primary_pngs),
            "latest_logger_plot": _last_relative(run_path, logger_pngs),
            "latest_csv": _last_relative(run_path, outputs["csv"]),
            "sample_output_paths": _sample_paths(run_path, png_outputs),
        },
        "time_progress": _time_progress_summary(stdout_text),
        "stdout_tail": _read_text_tail(stdout_path) if stdout_path.exists() else "",
        "stderr_tail": stderr_text,
    }


@mcp.tool()
def sample_output_images(
    run_id: str,
    limit: int = 5,
    create_contact_sheet: bool = False,
    attempt_id: Optional[str] = None,
) -> Dict[str, Any]:
    try:
        run_id = _coerce_run_id(run_id)
        run_path = _run_dir(run_id)
    except ValueError as exc:
        return {"ok": False, "error": str(exc)}
    resolved_attempt_id, attempt_path = _resolve_attempt(run_id, run_path, attempt_id)
    if not resolved_attempt_id or not attempt_path:
        return {"ok": False, "error": f"No Morpheus attempt exists yet for run_id={run_id}."}
    sample = _sample_run_images(attempt_path, limit)
    selected_paths = [_relative_to_run(run_path, path) for path in sample["selected"]]
    contact_sheet_path: Optional[str] = None

    if create_contact_sheet and sample["selected"]:
        output_path = attempt_path / "sample_contact_sheet.png"
        created = _create_contact_sheet(sample["selected"], output_path)
        if created:
            contact_sheet_path = _relative_to_run(run_path, created)

    return {
        "ok": True,
        "run_id": run_id,
        "attempt_id": resolved_attempt_id,
        "attempt_dir": _relative_to_run(run_path, attempt_path),
        "selected_images": selected_paths,
        "primary_plot_count": sample["primary_plot_count"],
        "logger_plot_count": sample["logger_plot_count"],
        "all_png_count": sample["all_png_count"],
        "contact_sheet_path": contact_sheet_path,
    }


@mcp.tool()
def evaluate_technical_run(run_id: str, attempt_id: Optional[str] = None) -> Dict[str, Any]:
    try:
        run_id = _coerce_run_id(run_id)
        run_path = _run_dir(run_id)
    except ValueError as exc:
        return {"ok": False, "error": str(exc)}
    xml_path = run_path / "model.xml"
    evaluation_json = run_path / "technical_evaluation.json"
    evaluation_txt = run_path / "technical_evaluation.txt"
    resolved_attempt_id, attempt_path = _resolve_attempt(run_id, run_path, attempt_id)
    if not resolved_attempt_id or not attempt_path:
        return {"ok": False, "error": f"No Morpheus attempt exists yet for run_id={run_id}."}
    stdout_path = attempt_path / "stdout.log"
    stderr_path = attempt_path / "stderr.log"

    xml_text = _read_text(xml_path, max_chars=1_000_000)
    stdout_text = _read_text_full(stdout_path)
    stderr_text = _read_text_full(stderr_path)
    outputs = _list_outputs(attempt_path)
    png_outputs = _non_contact_sheet_pngs(outputs["png"])
    validation = _validate_xml_completeness(xml_text) if xml_text else {}

    error_count = _count_error_lines(stderr_text)
    model_graph_present = any(Path(path).name == "model_graph.dot" for path in outputs["dot"])
    model_graph_matches_xml = bool(validation.get("has_model_graph")) == bool(model_graph_present)
    time_lines, time_values = _count_time_lines(stdout_text)
    time_score = _calculate_time_score(time_lines)
    stop_time = _extract_stop_time(xml_text) if xml_text else None
    last_time = time_values[-1] if time_values else None
    stop_time_match = stop_time is not None and last_time is not None and abs(stop_time - last_time) < 1e-6
    png_count = len(png_outputs)
    csv_count = len(outputs["csv"])
    results_score = 1 if (png_count > 0 or csv_count > 0) else 0
    bonus_many_results = 1 if png_count >= 10 else 0
    model_graph_score = 1 if model_graph_present and bool(validation.get("has_model_graph")) else 0
    primary_pngs = [path for path in png_outputs if Path(path).name.startswith("plot_")]
    logger_pngs = [path for path in png_outputs if Path(path).name.startswith("logger_")]
    latest_primary_plot = _last_relative(run_path, primary_pngs)
    latest_logger_plot = _last_relative(run_path, logger_pngs)
    latest_primary_plot_time = _extract_time_from_png_name(latest_primary_plot)
    latest_logger_plot_time = _extract_time_from_png_name(latest_logger_plot)
    latest_primary_plot_within_last_time = (
        latest_primary_plot_time is None or last_time is None or latest_primary_plot_time <= last_time + 1e-6
    )
    latest_logger_plot_within_last_time = (
        latest_logger_plot_time is None or last_time is None or latest_logger_plot_time <= last_time + 1e-6
    )

    raw_score = (
        -error_count
        + model_graph_score
        + time_score
        + (1 if stop_time_match else 0)
        + results_score
        + bonus_many_results
    )
    total_score = max(0, min(7, raw_score))

    breakdown = {
        "xml_error_count": error_count,
        "xml_error_penalty": -error_count,
        "model_graph_present": model_graph_present,
        "model_graph_score": model_graph_score,
        "model_graph_matches_xml": model_graph_matches_xml,
        "time_lines_count": time_lines,
        "time_score": time_score,
        "time_values_sample": time_values[:5],
        "last_time_value": last_time,
        "stop_time": stop_time,
        "stop_time_match": stop_time_match,
        "stop_time_score": 1 if stop_time_match else 0,
        "results_generated": png_count > 0 or csv_count > 0,
        "png_count": png_count,
        "csv_count": csv_count,
        "results_score": results_score,
        "bonus_many_results": bonus_many_results,
        "latest_primary_plot": latest_primary_plot,
        "latest_primary_plot_time": latest_primary_plot_time,
        "latest_primary_plot_within_last_time": latest_primary_plot_within_last_time,
        "latest_logger_plot": latest_logger_plot,
        "latest_logger_plot_time": latest_logger_plot_time,
        "latest_logger_plot_within_last_time": latest_logger_plot_within_last_time,
        "xml_validation": validation,
    }
    payload = {
        "ok": True,
        "run_id": run_id,
        "attempt_id": resolved_attempt_id,
        "attempt_dir": _relative_to_run(run_path, attempt_path),
        "total_score": total_score,
        "max_possible_score": 7,
        "score_percentage": round((total_score / 7) * 100, 2),
        "breakdown": breakdown,
        "evaluation_json_path": str(evaluation_json),
        "evaluation_txt_path": str(evaluation_txt),
        "generated_at": _now_iso(),
    }
    _write_json(evaluation_json, payload)
    _write_text(
        evaluation_txt,
        "\n".join(
            [
                "============================================================",
                "MORPHEUS TECHNICAL EVALUATION",
                "============================================================",
                f"Run ID: {run_id}",
                f"Timestamp: {payload['generated_at']}",
                "",
                f"TOTAL SCORE: {total_score} / 7 ({payload['score_percentage']}%)",
                "",
                f"Error penalty: {-error_count}",
                f"Model graph: {model_graph_score}/1",
                f"Time progression: {time_score}/3",
                f"StopTime match: {1 if stop_time_match else 0}/1",
                f"Result files: {results_score}/1",
                f"Bonus (10+ PNGs): {bonus_many_results}/1",
                "",
                f"Attempt ID: {resolved_attempt_id}",
                f"PNG files: {png_count}",
                f"CSV files: {csv_count}",
            ]
        ),
    )
    _merge_manifest(
        run_id,
        {
            "technical_evaluation_json_path": str(evaluation_json),
            "technical_evaluation_txt_path": str(evaluation_txt),
            "technical_score": total_score,
            "technical_attempt_id": resolved_attempt_id,
            "technical_attempt_dir": str(attempt_path),
        },
    )
    return payload


@mcp.tool()
def read_file_text(path: str, max_chars: int = MAX_READ_CHARS) -> Dict[str, Any]:
    try:
        file_path = _resolve_allowed_read_path(path)
    except ValueError as exc:
        return {"ok": False, "error": str(exc)}
    if not file_path.exists() or not file_path.is_file():
        return {"ok": False, "error": f"File not found: {path}"}
    return {"ok": True, "path": str(file_path), "text": _read_text(file_path, max_chars)}


def read_pdf(pdf_path: str, run_id: Optional[str] = None) -> Dict[str, Any]:
    return extract_paper_text(pdf_path=pdf_path, run_id=run_id)


def suggest_references(run_id: str) -> Dict[str, Any]:
    paper_path = _run_dir(run_id) / "paper.txt"
    if not paper_path.exists():
        return {"ok": False, "error": "paper.txt not found for this run"}
    text = _read_text(paper_path, 50_000)
    suggestions = _infer_reference_categories_from_text(text)
    available = {
        category: sorted(path.name for path in REFERENCE_CATEGORIES[category].iterdir() if path.is_file())
        for category in suggestions["selected_categories"]
        if category in REFERENCE_CATEGORIES
    }
    return {
        "ok": True,
        "suggested_categories": suggestions["selected_categories"],
        "scores": suggestions["scores"],
        "available_references": available,
    }


def generate_xml_from_text(
    model_xml: str,
    run_id: Optional[str] = None,
    file_name: str = "model.xml",
) -> Dict[str, Any]:
    return write_model_xml(xml_content=model_xml, run_id=run_id, file_name=file_name)


def save_model_xml(
    xml_content: str,
    run_id: Optional[str] = None,
    file_name: str = "model.xml",
) -> Dict[str, Any]:
    return write_model_xml(xml_content=xml_content, run_id=run_id, file_name=file_name)


def run_morpheus(xml_path: str, run_id: Optional[str] = None) -> Dict[str, Any]:
    return run_morpheus_model(xml_path=xml_path, run_id=run_id)


def get_run_summary(run_id: str) -> Dict[str, Any]:
    return summarize_morpheus_run(run_id=run_id)


def evaluation(run_id: str) -> Dict[str, Any]:
    return evaluate_technical_run(run_id=run_id)


def auto_fix_and_rerun(run_id: str) -> Dict[str, Any]:
    run_path = _run_dir(run_id)
    xml_path = run_path / "model.xml"
    stderr_path = run_path / "stderr.log"
    stdout_path = run_path / "stdout.log"
    xml_text = _read_text(xml_path, max_chars=1_000_000)
    return {
        "ok": True,
        "run_id": run_id,
        "current_xml_path": str(xml_path) if xml_path.exists() else None,
        "current_xml": xml_text,
        "stderr": _read_text(stderr_path, max_chars=1_000_000),
        "stdout": _read_text(stdout_path, max_chars=1_000_000),
        "validation": _validate_xml_completeness(xml_text) if xml_text else None,
        "message": "Legacy compatibility helper only. Inspect the logs, update XML, and rerun manually.",
    }


def run_xml_once(xml_content: str) -> Dict[str, Any]:
    saved = write_model_xml(xml_content=xml_content)
    if not saved.get("ok"):
        return saved
    return run_morpheus_model(xml_path=saved["xml_path"], run_id=saved["run_id"])


def pdf_to_morpheus_pipeline(pdf_path: str) -> Dict[str, Any]:
    extracted = extract_paper_text(pdf_path=pdf_path)
    if not extracted.get("ok"):
        return extracted
    refs = suggest_references(extracted["run_id"])
    return {
        "ok": True,
        "run_id": extracted["run_id"],
        "run_dir": extracted["run_dir"],
        "pdf_path": extracted["pdf_path"],
        "paper_text": extracted["text_path"],
        "paper_text_preview": extracted["text_preview"],
        "suggested_reference_categories": refs.get("suggested_categories", []),
        "available_references": refs.get("available_references", {}),
        "next_steps": [
            "Use list_references(category) and read_reference(category, name) to study examples.",
            "Use write_model_xml() to save Morpheus XML.",
            "Use run_morpheus_model() and evaluate_technical_run() after writing the model.",
        ],
    }


if __name__ == "__main__":
    mcp.run(transport="stdio")
