from __future__ import annotations

import json
import math
import os
import re
import shutil
import subprocess
import uuid
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple

from dotenv import load_dotenv

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

REFERENCES_ROOT = REPO_ROOT / "references"
REFERENCE_CATEGORIES = {
    "CPM": REFERENCES_ROOT / "CPM",
    "PDE": REFERENCES_ROOT / "PDE",
    "ODE": REFERENCES_ROOT / "ODE",
    "Multiscale": REFERENCES_ROOT / "Multiscale",
    "Miscellaneous": REFERENCES_ROOT / "Miscellaneous",
}
CORPUS_ROOT = REPO_ROOT / "corpus"
MODEL_REPO_DIR = Path(os.getenv("MORPHEUS_MODEL_REPO_DIR", str(CORPUS_ROOT / "model-repo"))).expanduser()
if not MODEL_REPO_DIR.is_absolute():
    MODEL_REPO_DIR = (REPO_ROOT / MODEL_REPO_DIR).resolve()
PACKED_MODEL_REPO_PATH = Path(
    os.getenv("MORPHEUS_MODEL_REPO_TXT", str(REFERENCES_ROOT / "model_repository.txt"))
).expanduser()
if not PACKED_MODEL_REPO_PATH.is_absolute():
    PACKED_MODEL_REPO_PATH = (REPO_ROOT / PACKED_MODEL_REPO_PATH).resolve()

MODEL_REPO_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".svg", ".tif", ".tiff", ".gif"}
MODEL_REPO_VIDEO_EXTENSIONS = {".mp4", ".webm", ".mov"}
MODEL_REPO_ASSET_EXTENSIONS = MODEL_REPO_IMAGE_EXTENSIONS | MODEL_REPO_VIDEO_EXTENSIONS | {".zip"}
MODEL_REPO_TEXT_EXTENSIONS = {".md", ".xml", ".txt"}
MAX_MODEL_EXAMPLE_READ_CHARS = 250_000
MAX_MODEL_EXAMPLE_SECTION_CHARS = 40_000
MODEL_EXAMPLE_RESULT_LIMIT = 20
MODEL_EXAMPLE_STOPWORDS = {
    "about",
    "after",
    "also",
    "and",
    "are",
    "based",
    "between",
    "both",
    "can",
    "cell",
    "cells",
    "data",
    "during",
    "each",
    "figure",
    "from",
    "has",
    "have",
    "into",
    "model",
    "models",
    "not",
    "paper",
    "results",
    "show",
    "shows",
    "simulation",
    "the",
    "their",
    "this",
    "that",
    "using",
    "with",
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


def _safe_model_file_name(file_name: str) -> str:
    candidate = Path(file_name)
    if candidate.name != file_name or candidate.is_absolute() or file_name in {"", ".", ".."}:
        raise ValueError("file_name must be a simple file name inside the run directory, e.g. model.xml")
    return file_name


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


def _merge_manifest(run_id: str, updates: Dict[str, Any]) -> Path:
    manifest_path = _run_dir(run_id) / "run_manifest.json"
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    else:
        manifest = {
            "run_id": run_id,
            "run_dir": str(_run_dir(run_id)),
            "created_at": _now_iso(),
        }
    manifest.update(updates)
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


def _time_progress_summary(stdout_text: str) -> Dict[str, Any]:
    time_lines, time_values = _count_time_lines(stdout_text)
    return {
        "time_lines_count": time_lines,
        "first_time_value": time_values[0] if time_values else None,
        "last_time_value": time_values[-1] if time_values else None,
    }


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


def _normalize_repo_relpath(path: Path | str) -> str:
    return str(path).replace("\\", "/")


def _parse_scalar_metadata(value: str) -> Any:
    value = value.strip()
    if not value:
        return ""
    if value.startswith("[") and value.endswith("]"):
        inner = value[1:-1].strip()
        if not inner:
            return []
        return [item.strip().strip("\"'") for item in inner.split(",") if item.strip()]
    return value.strip("\"'")


def _parse_markdown_front_matter(text: str) -> Tuple[Dict[str, Any], str]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, text

    metadata: Dict[str, Any] = {}
    current_key: Optional[str] = None
    body_start = 0
    for index, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            body_start = index + 1
            break

        key_match = re.match(r"^([A-Za-z0-9_-]+):\s*(.*)$", line)
        if key_match:
            key = key_match.group(1)
            raw_value = key_match.group(2)
            parsed_value = _parse_scalar_metadata(raw_value)
            metadata[key] = parsed_value
            current_key = key
            continue

        list_match = re.match(r"^\s*-\s+(.+)$", line)
        if list_match and current_key:
            existing = metadata.get(current_key)
            if not isinstance(existing, list):
                existing = []
                metadata[current_key] = existing
            existing.append(list_match.group(1).strip().strip("\"'"))

    if body_start == 0:
        return metadata, text
    return metadata, "\n".join(lines[body_start:])


def _strip_markup(text: str, max_chars: int = 800) -> str:
    text = re.sub(r"```.*?```", " ", text, flags=re.DOTALL)
    text = re.sub(r"!\[[^\]]*\]\([^)]+\)", " ", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"[#*_`>{}|]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:max_chars]


def _extract_xml_title(xml_text: str) -> Optional[str]:
    match = re.search(r"<Title\b[^>]*>(.*?)</Title>", xml_text, flags=re.IGNORECASE | re.DOTALL)
    if not match:
        return None
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", match.group(1))).strip() or None


def _extract_xml_details(xml_text: str, max_chars: int = 800) -> str:
    match = re.search(r"<Details\b[^>]*>(.*?)</Details>", xml_text, flags=re.IGNORECASE | re.DOTALL)
    if not match:
        return ""
    return _strip_markup(match.group(1), max_chars=max_chars)


def _extract_model_id(*texts: str) -> Optional[str]:
    for text in texts:
        match = re.search(r"\b(M\d{4,})\b", text, flags=re.IGNORECASE)
        if match:
            return match.group(1).upper()
    return None


def _extract_xml_tags(xml_text: str, limit: int = 80) -> List[str]:
    tags: List[str] = []
    seen: Set[str] = set()
    for match in re.finditer(r"<\s*/?\s*([A-Za-z_][A-Za-z0-9_.:-]*)\b", xml_text):
        tag = match.group(1)
        if tag.startswith("?") or tag.startswith("!"):
            continue
        if tag not in seen:
            tags.append(tag)
            seen.add(tag)
        if len(tags) >= limit:
            break
    return tags


def _asset_kind(path: str) -> str:
    suffix = Path(path).suffix.lower()
    if suffix in MODEL_REPO_IMAGE_EXTENSIONS:
        return "image"
    if suffix in MODEL_REPO_VIDEO_EXTENSIONS:
        return "video"
    return "asset"


def _extract_markdown_assets(
    markdown_text: str,
    model_dir: Optional[Path] = None,
) -> List[Dict[str, Any]]:
    assets: List[Dict[str, Any]] = []
    seen: Set[str] = set()

    patterns = [
        re.compile(r"!\[[^\]]*\]\(([^)\s]+)(?:\s+\"([^\"]*)\")?\)"),
        re.compile(r"\bsrc=\"([^\"]+)\""),
    ]
    for pattern in patterns:
        for match in pattern.finditer(markdown_text):
            rel = match.group(1).strip()
            if not rel or rel.startswith(("http://", "https://", "#")):
                continue
            suffix = Path(rel.split("#", 1)[0]).suffix.lower()
            if suffix not in MODEL_REPO_ASSET_EXTENSIONS:
                continue
            caption = match.group(2).strip() if len(match.groups()) > 1 and match.group(2) else ""
            local_path = model_dir / rel if model_dir else None
            key = str(local_path.resolve()) if local_path and local_path.exists() else rel
            if key in seen:
                continue
            seen.add(key)
            assets.append(
                {
                    "kind": _asset_kind(rel),
                    "relative_path": _normalize_repo_relpath(rel),
                    "path": str(local_path.resolve()) if local_path and local_path.exists() else None,
                    "exists": bool(local_path and local_path.exists()),
                    "caption": caption,
                    "referenced_in_markdown": True,
                }
            )

    return assets


def _list_local_model_assets(model_dir: Path, existing: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
    assets = list(existing)
    seen = {asset.get("path") or asset.get("relative_path") for asset in assets}
    for path in sorted(model_dir.iterdir()):
        if not path.is_file() or path.suffix.lower() not in MODEL_REPO_ASSET_EXTENSIONS:
            continue
        resolved = str(path.resolve())
        if resolved in seen:
            continue
        seen.add(resolved)
        assets.append(
            {
                "kind": _asset_kind(path.name),
                "relative_path": path.name,
                "path": resolved,
                "exists": True,
                "caption": "",
                "referenced_in_markdown": False,
            }
        )
    return assets


def _model_types_from_record(path_text: str, tags: Sequence[str], plugins: Sequence[str]) -> List[str]:
    metadata_haystack = " ".join([path_text, *tags]).lower()
    plugin_haystack = " ".join(plugins).lower()
    model_types: List[str] = []

    has_cpm = (
        "cellular potts" in metadata_haystack
        or _text_contains_term(metadata_haystack, "cpm")
        or _text_contains_term(plugin_haystack, "cpm")
    )
    has_pde = (
        "partial differential" in metadata_haystack
        or _text_contains_term(metadata_haystack, "pde")
        or _text_contains_term(plugin_haystack, "diffusion")
    )
    has_ode = "ordinary differential" in metadata_haystack or _text_contains_term(metadata_haystack, "ode")
    has_multiscale = _text_contains_term(metadata_haystack, "multiscale") or (has_cpm and (has_pde or has_ode))

    if has_cpm:
        model_types.append("CPM")
    if has_pde:
        model_types.append("PDE")
    if has_ode:
        model_types.append("ODE")
    if has_multiscale:
        model_types.append("Multiscale")
    return model_types


def _asset_counts(assets: Sequence[Dict[str, Any]]) -> Dict[str, int]:
    counts = Counter(asset.get("kind", "asset") for asset in assets)
    return {
        "images": int(counts.get("image", 0)),
        "videos": int(counts.get("video", 0)),
        "other_assets": int(sum(count for kind, count in counts.items() if kind not in {"image", "video"})),
    }


def _text_contains_term(text: str, term: str) -> bool:
    if re.fullmatch(r"[A-Za-z0-9]+", term) and len(term) <= 3:
        return re.search(rf"(?<![A-Za-z0-9]){re.escape(term)}(?![A-Za-z0-9])", text) is not None
    return term in text


def _record_search_text(record: Dict[str, Any], xml_text: str) -> str:
    return " ".join(
        [
            str(record.get("title", "")),
            str(record.get("example_id", "")),
            str(record.get("category", "")),
            " ".join(record.get("tags", [])),
            " ".join(record.get("model_types", [])),
            " ".join(record.get("plugins", [])),
            str(record.get("summary", "")),
            _extract_xml_details(xml_text, max_chars=1_500),
        ]
    ).lower()


def _make_model_record(
    *,
    source: str,
    example_id: str,
    rel_path: str,
    xml_text: str,
    index_markdown: str = "",
    model_markdown: str = "",
    model_dir: Optional[Path] = None,
    xml_abs_path: Optional[Path] = None,
    index_abs_path: Optional[Path] = None,
    model_abs_path: Optional[Path] = None,
) -> Dict[str, Any]:
    metadata, index_body = _parse_markdown_front_matter(index_markdown)
    model_metadata, model_body = _parse_markdown_front_matter(model_markdown)
    tags = metadata.get("tags") or model_metadata.get("tags") or []
    if isinstance(tags, str):
        tags = [tags]

    title = metadata.get("title") or model_metadata.get("title") or _extract_xml_title(xml_text) or Path(rel_path).stem
    model_id = (
        metadata.get("MorpheusModelID")
        or model_metadata.get("MorpheusModelID")
        or _extract_model_id(index_markdown, model_markdown, xml_text)
    )
    contributors = metadata.get("contributors") or model_metadata.get("contributors") or metadata.get("authors") or []
    if isinstance(contributors, str):
        contributors = [contributors]

    rel_parts = rel_path.split("/")
    category = rel_parts[0] if rel_parts else ""
    subcategory = "/".join(rel_parts[:2]) if len(rel_parts) >= 2 else category
    model_name = rel_parts[-2] if len(rel_parts) >= 2 else Path(rel_path).stem
    plugins = _extract_xml_tags(xml_text)
    summary = _strip_markup(index_body or model_body or _extract_xml_details(xml_text), max_chars=1_000)
    markdown_assets = _extract_markdown_assets("\n\n".join([index_markdown, model_markdown]), model_dir=model_dir)
    assets = _list_local_model_assets(model_dir, markdown_assets) if model_dir and model_dir.exists() else markdown_assets

    record: Dict[str, Any] = {
        "example_id": example_id,
        "source": source,
        "model_id": str(model_id) if model_id else None,
        "title": str(title),
        "model_name": model_name,
        "category": category,
        "subcategory": subcategory,
        "repo_path": rel_path,
        "tags": [str(tag) for tag in tags],
        "contributors": [str(contributor) for contributor in contributors],
        "plugins": plugins,
        "model_types": _model_types_from_record(rel_path, [str(tag) for tag in tags], plugins),
        "summary": summary,
        "asset_counts": _asset_counts(assets),
        "sample_assets": assets[:5],
        "_assets": assets,
        "_xml_content": xml_text if source == "packed_txt" else None,
        "_xml_abs_path": str(xml_abs_path.resolve()) if xml_abs_path else None,
        "_index_content": index_markdown if source == "packed_txt" else None,
        "_model_content": model_markdown if source == "packed_txt" else None,
        "_index_abs_path": str(index_abs_path.resolve()) if index_abs_path else None,
        "_model_abs_path": str(model_abs_path.resolve()) if model_abs_path else None,
    }
    record["_search_text"] = _record_search_text(record, xml_text)
    return record


def _load_model_repo_dir_records(model_repo_dir: Path) -> List[Dict[str, Any]]:
    if not model_repo_dir.exists() or not model_repo_dir.is_dir():
        return []
    records: List[Dict[str, Any]] = []
    for xml_path in sorted(model_repo_dir.rglob("*.xml")):
        if ".git" in xml_path.parts:
            continue
        rel_path = _normalize_repo_relpath(xml_path.resolve().relative_to(model_repo_dir.resolve()))
        model_dir = xml_path.parent
        index_path = model_dir / "index.md"
        model_path = model_dir / "model.md"
        xml_text = _read_text(xml_path, max_chars=1_000_000)
        index_markdown = _read_text(index_path, max_chars=100_000) if index_path.exists() else ""
        model_markdown = _read_text(model_path, max_chars=100_000) if model_path.exists() else ""
        records.append(
            _make_model_record(
                source="model_repo_dir",
                example_id=rel_path,
                rel_path=rel_path,
                xml_text=xml_text,
                index_markdown=index_markdown,
                model_markdown=model_markdown,
                model_dir=model_dir,
                xml_abs_path=xml_path,
                index_abs_path=index_path if index_path.exists() else None,
                model_abs_path=model_path if model_path.exists() else None,
            )
        )
    return records


def _parse_packed_model_repo(path: Path) -> Dict[str, str]:
    if not path.exists():
        return {}
    text = _read_text(path, max_chars=20_000_000)
    files: Dict[str, str] = {}
    matches = list(re.finditer(r"^## File:\s+(.+)$", text, flags=re.MULTILINE))
    for index, match in enumerate(matches):
        rel_path = match.group(1).strip()
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        block = text[start:end].strip()
        fence_match = re.match(r"````[A-Za-z0-9_-]*\s*\n(.*)\n````\s*$", block, flags=re.DOTALL)
        files[_normalize_repo_relpath(rel_path)] = fence_match.group(1) if fence_match else block
    return files


def _load_packed_model_repo_records(path: Path) -> List[Dict[str, Any]]:
    packed_files = _parse_packed_model_repo(path)
    records: List[Dict[str, Any]] = []
    for rel_path, xml_text in sorted(packed_files.items()):
        if not rel_path.endswith(".xml"):
            continue
        model_dir = _normalize_repo_relpath(Path(rel_path).parent)
        index_markdown = packed_files.get(f"{model_dir}/index.md", "")
        model_markdown = packed_files.get(f"{model_dir}/model.md", "")
        records.append(
            _make_model_record(
                source="packed_txt",
                example_id=rel_path,
                rel_path=rel_path,
                xml_text=xml_text,
                index_markdown=index_markdown,
                model_markdown=model_markdown,
                model_dir=None,
            )
        )
    return records


def _load_model_example_records() -> Tuple[str, List[Dict[str, Any]]]:
    records = _load_model_repo_dir_records(MODEL_REPO_DIR)
    if records:
        return "model_repo_dir", records
    records = _load_packed_model_repo_records(PACKED_MODEL_REPO_PATH)
    if records:
        return "packed_txt", records
    return "missing", []


def _public_model_record(record: Dict[str, Any], include_assets: bool = False) -> Dict[str, Any]:
    public = {key: value for key, value in record.items() if not key.startswith("_")}
    if include_assets:
        public["assets"] = record.get("_assets", [])
    return public


def _tokenize_model_query(text: str, limit: int = 80) -> List[str]:
    terms = [
        term.lower()
        for term in re.findall(r"[A-Za-z0-9_.+-]+", text)
        if len(term) > 2 and term.lower() not in MODEL_EXAMPLE_STOPWORDS
    ]
    if len(terms) <= limit:
        return terms
    counts = Counter(terms)
    return [term for term, _count in counts.most_common(limit)]


def _score_model_example(record: Dict[str, Any], terms: Sequence[str]) -> float:
    if not terms:
        return 0.0
    title = str(record.get("title", "")).lower()
    tags = " ".join(record.get("tags", [])).lower()
    plugins = " ".join(record.get("plugins", [])).lower()
    path = str(record.get("repo_path", "")).lower()
    summary = str(record.get("summary", "")).lower()
    search_text = str(record.get("_search_text", "")).lower()

    score = 0.0
    for term in terms:
        if _text_contains_term(title, term):
            score += 6
        if _text_contains_term(tags, term):
            score += 5
        if _text_contains_term(plugins, term):
            score += 4
        if _text_contains_term(path, term):
            score += 3
        if _text_contains_term(summary, term):
            score += 2
        if _text_contains_term(search_text, term):
            score += 1
    return score


def _find_model_record(example_id: str) -> Tuple[Optional[Dict[str, Any]], str, List[Dict[str, Any]]]:
    source, records = _load_model_example_records()
    normalized = _normalize_repo_relpath(example_id).strip("/")
    for record in records:
        if record.get("example_id") == normalized or record.get("model_id") == normalized.upper():
            return record, source, records
    return None, source, records


def _read_model_record_xml(record: Dict[str, Any], max_chars: int = MAX_MODEL_EXAMPLE_READ_CHARS) -> str:
    xml_path = record.get("_xml_abs_path")
    if xml_path:
        return _read_text(Path(str(xml_path)), max_chars=max_chars)
    return str(record.get("_xml_content") or "")[:max_chars]


def _read_model_record_markdown(record: Dict[str, Any], key: str, max_chars: int = 100_000) -> str:
    path_key = f"_{key}_abs_path"
    content_key = f"_{key}_content"
    markdown_path = record.get(path_key)
    if markdown_path:
        return _read_text(Path(str(markdown_path)), max_chars=max_chars)
    return str(record.get(content_key) or "")[:max_chars]


def _extract_xml_section(xml_text: str, section: str) -> Tuple[str, int]:
    section = section.strip()
    if section.lower() in {"full", "xml", "model"}:
        return xml_text, 1 if xml_text else 0
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_.:-]*", section):
        raise ValueError("section must be an XML tag name such as Analysis, CPM, Global, or CellTypes")

    pattern = re.compile(
        rf"<{re.escape(section)}\b[^>]*>.*?</{re.escape(section)}>",
        flags=re.IGNORECASE | re.DOTALL,
    )
    matches = pattern.findall(xml_text)
    if not matches:
        self_closing = re.compile(rf"<{re.escape(section)}\b[^>]*/>", flags=re.IGNORECASE | re.DOTALL)
        matches = self_closing.findall(xml_text)
    return "\n\n".join(matches), len(matches)


def _search_model_example_records(
    *,
    query: str = "",
    model_type: Optional[str] = None,
    category: Optional[str] = None,
    tags: Optional[Sequence[str]] = None,
    limit: int = 5,
) -> Dict[str, Any]:
    source, records = _load_model_example_records()
    limit = max(1, min(limit, MODEL_EXAMPLE_RESULT_LIMIT))
    terms = _tokenize_model_query(query)
    required_tags = [tag.lower() for tag in (tags or []) if tag]
    model_type_l = model_type.lower() if model_type else None
    category_l = category.lower() if category else None

    ranked: List[Tuple[float, Dict[str, Any]]] = []
    for record in records:
        haystack = " ".join(
            [
                str(record.get("category", "")),
                str(record.get("subcategory", "")),
                str(record.get("repo_path", "")),
                " ".join(record.get("tags", [])),
                " ".join(record.get("model_types", [])),
                " ".join(record.get("plugins", [])),
                str(record.get("_search_text", "")),
            ]
        ).lower()
        if category_l and category_l not in haystack:
            continue
        if model_type_l and not _text_contains_term(haystack, model_type_l):
            continue
        if required_tags and not all(_text_contains_term(haystack, tag) for tag in required_tags):
            continue

        score = _score_model_example(record, terms)
        if not terms:
            score += 1
        if model_type_l:
            score += 8
        if category_l:
            score += 4
        if required_tags:
            score += 4 * len(required_tags)
        ranked.append((score, record))

    ranked.sort(key=lambda item: (-item[0], str(item[1].get("repo_path", ""))))
    return {
        "ok": True,
        "source": source,
        "model_repo_dir": str(MODEL_REPO_DIR),
        "packed_model_repo_path": str(PACKED_MODEL_REPO_PATH),
        "record_count": len(records),
        "query_terms": terms,
        "results": [
            {**_public_model_record(record), "score": score}
            for score, record in ranked[:limit]
        ],
    }


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
    pngs = sorted(run_path.rglob("*.png"))
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
    selected_pages = pages or list(range(1, total_pages + 1))
    selected_pages = [page for page in selected_pages if 1 <= page <= total_pages]
    if max_pages is not None:
        selected_pages = selected_pages[:max_pages]

    try:
        rendered_paths = _render_pdf_pages(pdf_file, out_dir, selected_pages, dpi)
    except Exception as exc:
        return {"ok": False, "error": str(exc)}

    page_entries = [
        {"page": page, "path": _relative_to_run(run_path, path)}
        for page, path in zip(selected_pages, rendered_paths)
    ]
    manifest_path = run_path / "paper_page_manifest.json"
    _write_json(
        manifest_path,
        {
            "pdf_path": str(pdf_file),
            "dpi": dpi,
            "pages": page_entries,
            "generated_at": _now_iso(),
        },
    )
    _merge_manifest(
        run_id,
        {
            "paper_page_manifest_path": str(manifest_path),
            "paper_page_image_count": len(page_entries),
        },
    )

    return {
        "ok": True,
        "run_id": run_id,
        "pdf_path": str(pdf_file),
        "dpi": dpi,
        "pages": page_entries,
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

    figures = _list_pdf_figures(pdf_file)
    figure_pages = sorted({figure["page"] for figure in figures if isinstance(figure.get("page"), int)})
    manifest_path = run_path / "paper_figure_manifest.json"
    _write_json(
        manifest_path,
        {
            "pdf_path": str(pdf_file),
            "generated_at": _now_iso(),
            "figure_count": len(figures),
            "figure_pages": figure_pages,
        },
    )
    _merge_manifest(
        run_id,
        {
            "paper_figure_manifest_path": str(manifest_path),
            "paper_figure_count": len(figures),
        },
    )

    return {
        "ok": True,
        "run_id": run_id,
        "pdf_path": str(pdf_file),
        "figure_count": len(figures),
        "figure_pages": figure_pages,
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
def get_model_example_corpus_status() -> Dict[str, Any]:
    """Report which Morpheus example corpus source is active."""
    source, records = _load_model_example_records()
    category_counts = Counter(str(record.get("category", "")) for record in records)
    type_counts = Counter(
        model_type
        for record in records
        for model_type in record.get("model_types", [])
    )
    asset_totals = {
        "images": sum(record.get("asset_counts", {}).get("images", 0) for record in records),
        "videos": sum(record.get("asset_counts", {}).get("videos", 0) for record in records),
        "other_assets": sum(record.get("asset_counts", {}).get("other_assets", 0) for record in records),
    }
    return {
        "ok": True,
        "source": source,
        "record_count": len(records),
        "model_repo_dir": str(MODEL_REPO_DIR),
        "model_repo_dir_exists": MODEL_REPO_DIR.exists(),
        "packed_model_repo_path": str(PACKED_MODEL_REPO_PATH),
        "packed_model_repo_path_exists": PACKED_MODEL_REPO_PATH.exists(),
        "category_counts": dict(sorted(category_counts.items())),
        "model_type_counts": dict(sorted(type_counts.items())),
        "asset_totals": asset_totals,
    }


@mcp.tool()
def search_model_examples(
    query: str = "",
    model_type: Optional[str] = None,
    category: Optional[str] = None,
    tags: Optional[List[str]] = None,
    limit: int = 5,
) -> Dict[str, Any]:
    """
    Search the large local Morpheus model corpus and return compact example cards.

    Use read_model_example or read_model_example_section to load selected XML only after search.
    """
    return _search_model_example_records(
        query=query,
        model_type=model_type,
        category=category,
        tags=tags,
        limit=limit,
    )


@mcp.tool()
def suggest_model_examples_for_paper(run_id: str, limit: int = 5) -> Dict[str, Any]:
    """Suggest model examples from the local corpus based on the extracted paper text."""
    try:
        run_id = _coerce_run_id(run_id)
        paper_path = _run_dir(run_id) / "paper.txt"
    except ValueError as exc:
        return {"ok": False, "error": str(exc)}
    if not paper_path.exists():
        return {"ok": False, "error": "paper.txt not found for this run"}

    text = _read_text(paper_path, 50_000)
    reference_categories = _infer_reference_categories_from_text(text)
    query_terms = _tokenize_model_query(text, limit=80)
    search_query = " ".join(query_terms)
    results = _search_model_example_records(query=search_query, limit=limit)
    return {
        **results,
        "run_id": run_id,
        "reference_category_suggestions": reference_categories,
    }


@mcp.tool()
def read_model_example(
    example_id: str,
    max_chars: int = MAX_MODEL_EXAMPLE_READ_CHARS,
    include_markdown: bool = True,
    include_assets: bool = True,
) -> Dict[str, Any]:
    """Read a selected Morpheus model example XML from the local corpus."""
    record, source, records = _find_model_record(example_id)
    if not record:
        return {
            "ok": False,
            "error": f"Model example not found: {example_id}",
            "source": source,
            "record_count": len(records),
        }
    max_chars = max(1_000, min(max_chars, MAX_MODEL_EXAMPLE_READ_CHARS))
    xml_text = _read_model_record_xml(record, max_chars=max_chars)
    payload: Dict[str, Any] = {
        "ok": True,
        "source": source,
        "example": _public_model_record(record, include_assets=include_assets),
        "xml": xml_text,
        "xml_truncated": len(_read_model_record_xml(record, max_chars=MAX_MODEL_EXAMPLE_READ_CHARS)) > len(xml_text),
        "validation": _validate_xml_completeness(xml_text),
    }
    if include_markdown:
        payload["index_markdown"] = _read_model_record_markdown(record, "index", max_chars=50_000)
        payload["model_markdown"] = _read_model_record_markdown(record, "model", max_chars=50_000)
    return payload


@mcp.tool()
def read_model_example_section(
    example_id: str,
    section: str,
    max_chars: int = MAX_MODEL_EXAMPLE_SECTION_CHARS,
) -> Dict[str, Any]:
    """Read one XML section, e.g. Analysis, CPM, Global, CellTypes, Space, or Time."""
    record, source, records = _find_model_record(example_id)
    if not record:
        return {
            "ok": False,
            "error": f"Model example not found: {example_id}",
            "source": source,
            "record_count": len(records),
        }
    try:
        xml_text = _read_model_record_xml(record, max_chars=MAX_MODEL_EXAMPLE_READ_CHARS)
        section_text, match_count = _extract_xml_section(xml_text, section)
    except ValueError as exc:
        return {"ok": False, "error": str(exc)}
    max_chars = max(1_000, min(max_chars, MAX_MODEL_EXAMPLE_SECTION_CHARS))
    truncated = len(section_text) > max_chars
    return {
        "ok": True,
        "source": source,
        "example": _public_model_record(record),
        "section": section,
        "match_count": match_count,
        "content": section_text[:max_chars],
        "truncated": truncated,
    }


@mcp.tool()
def list_model_example_assets(example_id: str) -> Dict[str, Any]:
    """List image/video assets available next to a selected model example."""
    record, source, records = _find_model_record(example_id)
    if not record:
        return {
            "ok": False,
            "error": f"Model example not found: {example_id}",
            "source": source,
            "record_count": len(records),
        }
    return {
        "ok": True,
        "source": source,
        "example": _public_model_record(record),
        "asset_counts": record.get("asset_counts", {}),
        "assets": record.get("_assets", []),
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
        file_name = _safe_model_file_name(file_name)
        run_path = _run_dir(run_id)
    except ValueError as exc:
        return {"ok": False, "error": str(exc)}

    xml_path = run_path / file_name
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
def run_morpheus_model(
    xml_path: str,
    run_id: Optional[str] = None,
    threads: Optional[int] = None,
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

    command = [MORPHEUS_BIN, "-f", str(xml_file), "--outdir", str(run_path)]
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

    stdout_path = run_path / "stdout.log"
    stderr_path = run_path / "stderr.log"
    _write_text(stdout_path, result["stdout"])
    _write_text(stderr_path, result["stderr"])

    outputs = _list_outputs(run_path)
    primary_pngs = [path for path in outputs["png"] if Path(path).name.startswith("plot_")]
    logger_pngs = [path for path in outputs["png"] if Path(path).name.startswith("logger_")]
    stdout_summary = _time_progress_summary(result["stdout"])
    manifest_path = _merge_manifest(
        run_id,
        {
            "last_run_at": _now_iso(),
            "last_run_command": command,
            "stdout_log_path": str(stdout_path),
            "stderr_log_path": str(stderr_path),
            "last_run_returncode": result["returncode"],
            "last_run_png_count": len(outputs["png"]),
            "last_run_csv_count": len(outputs["csv"]),
        },
    )

    ok = result["returncode"] == 0
    return {
        "ok": ok,
        "run_id": run_id,
        "xml_path": _relative_to_run(run_path, xml_file),
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
def summarize_morpheus_run(run_id: str) -> Dict[str, Any]:
    try:
        run_id = _coerce_run_id(run_id)
        run_path = _run_dir(run_id)
    except ValueError as exc:
        return {"ok": False, "error": str(exc)}
    outputs = _list_outputs(run_path)
    stdout_path = run_path / "stdout.log"
    stderr_path = run_path / "stderr.log"
    xml_path = run_path / "model.xml"
    primary_pngs = [path for path in outputs["png"] if Path(path).name.startswith("plot_")]
    logger_pngs = [path for path in outputs["png"] if Path(path).name.startswith("logger_")]
    stdout_text = _read_text_tail(stdout_path) if stdout_path.exists() else ""
    stderr_text = _read_text_tail(stderr_path) if stderr_path.exists() else ""

    return {
        "ok": True,
        "run_id": run_id,
        "run_dir": str(run_path),
        "xml_path": _relative_to_run(run_path, xml_path) if xml_path.exists() else None,
        "stdout_path": _relative_to_run(run_path, stdout_path) if stdout_path.exists() else None,
        "stderr_path": _relative_to_run(run_path, stderr_path) if stderr_path.exists() else None,
        "output_counts": {
            **_output_counts(outputs),
            "primary_plot_count": len(primary_pngs),
            "logger_plot_count": len(logger_pngs),
        },
        "key_outputs": {
            "latest_primary_plot": _last_relative(run_path, primary_pngs),
            "latest_logger_plot": _last_relative(run_path, logger_pngs),
            "latest_csv": _last_relative(run_path, outputs["csv"]),
            "sample_output_paths": _sample_paths(run_path, outputs["png"]),
        },
        "time_progress": _time_progress_summary(stdout_text),
        "stdout_tail": stdout_text,
        "stderr_tail": stderr_text,
    }


@mcp.tool()
def sample_output_images(
    run_id: str,
    limit: int = 5,
    create_contact_sheet: bool = False,
) -> Dict[str, Any]:
    try:
        run_id = _coerce_run_id(run_id)
        run_path = _run_dir(run_id)
    except ValueError as exc:
        return {"ok": False, "error": str(exc)}
    sample = _sample_run_images(run_path, limit)
    selected_paths = [_relative_to_run(run_path, path) for path in sample["selected"]]
    contact_sheet_path: Optional[str] = None

    if create_contact_sheet and sample["selected"]:
        output_path = run_path / "sample_contact_sheet.png"
        created = _create_contact_sheet(sample["selected"], output_path)
        if created:
            contact_sheet_path = _relative_to_run(run_path, created)

    return {
        "ok": True,
        "run_id": run_id,
        "selected_images": selected_paths,
        "primary_plot_count": sample["primary_plot_count"],
        "logger_plot_count": sample["logger_plot_count"],
        "all_png_count": sample["all_png_count"],
        "contact_sheet_path": contact_sheet_path,
    }


@mcp.tool()
def evaluate_technical_run(run_id: str) -> Dict[str, Any]:
    try:
        run_id = _coerce_run_id(run_id)
        run_path = _run_dir(run_id)
    except ValueError as exc:
        return {"ok": False, "error": str(exc)}
    xml_path = run_path / "model.xml"
    stdout_path = run_path / "stdout.log"
    stderr_path = run_path / "stderr.log"
    evaluation_json = run_path / "technical_evaluation.json"
    evaluation_txt = run_path / "technical_evaluation.txt"

    xml_text = _read_text(xml_path, max_chars=1_000_000)
    stdout_text = _read_text(stdout_path, max_chars=1_000_000)
    stderr_text = _read_text(stderr_path, max_chars=1_000_000)
    outputs = _list_outputs(run_path)
    validation = _validate_xml_completeness(xml_text) if xml_text else {}

    error_count = _count_error_lines(stderr_text)
    model_graph_present = any(Path(path).name == "model_graph.dot" for path in outputs["dot"])
    time_lines, time_values = _count_time_lines(stdout_text)
    time_score = _calculate_time_score(time_lines)
    stop_time = _extract_stop_time(xml_text) if xml_text else None
    last_time = time_values[-1] if time_values else None
    stop_time_match = stop_time is not None and last_time is not None and abs(stop_time - last_time) < 1e-6
    png_count = len(outputs["png"])
    csv_count = len(outputs["csv"])
    results_score = 1 if (png_count > 0 or csv_count > 0) else 0
    bonus_many_results = 1 if png_count >= 10 else 0

    raw_score = (
        -error_count
        + (1 if model_graph_present else 0)
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
        "model_graph_score": 1 if model_graph_present else 0,
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
        "xml_validation": validation,
    }
    payload = {
        "ok": True,
        "run_id": run_id,
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
                f"Model graph: {1 if model_graph_present else 0}/1",
                f"Time progression: {time_score}/3",
                f"StopTime match: {1 if stop_time_match else 0}/1",
                f"Result files: {results_score}/1",
                f"Bonus (10+ PNGs): {bonus_many_results}/1",
                "",
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
        },
    )
    return payload


@mcp.tool()
def read_file_text(path: str, max_chars: int = MAX_READ_CHARS) -> Dict[str, Any]:
    file_path = Path(path).expanduser().resolve()
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
    model_examples = suggest_model_examples_for_paper(extracted["run_id"], limit=5)
    return {
        "ok": True,
        "run_id": extracted["run_id"],
        "run_dir": extracted["run_dir"],
        "pdf_path": extracted["pdf_path"],
        "paper_text": extracted["text_path"],
        "paper_text_preview": extracted["text_preview"],
        "suggested_reference_categories": refs.get("suggested_categories", []),
        "available_references": refs.get("available_references", {}),
        "suggested_model_examples": model_examples.get("results", []),
        "next_steps": [
            "Use search_model_examples() or suggested_model_examples to choose relevant corpus examples.",
            "Use read_model_example_section(example_id, section) before reading full XML.",
            "Use list_references(category) and read_reference(category, name) only as the legacy curated fallback.",
            "Use write_model_xml() to save Morpheus XML.",
            "Use run_morpheus_model() and evaluate_technical_run() after writing the model.",
        ],
    }


if __name__ == "__main__":
    mcp.run(transport="stdio")
