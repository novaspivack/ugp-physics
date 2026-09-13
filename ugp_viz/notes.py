"""
Notes module — markdown-backed annotations that travel with runs and configs.

A "notes" payload is human-authored markdown plus a small metadata envelope
(title, created, modified). Notes can live either embedded in a YAML
experiment config / run JSON, or in standalone ``.md`` / ``.notes.json``
files alongside the artifacts they describe.

Use cases
---------
- Document the purpose of an experiment before running it (YAML field).
- Annotate a finished run with observations + conclusions.
- Distribute a notes file alongside a saved-run bundle so a future reader
  knows what it is.
- Externally authored markdown files (e.g. lab notebook entries) can be
  loaded into the GUI without ever opening a YAML file.

The rendering helpers in this module are deliberately dependency-free.
For full HTML rendering install a markdown library; for the in-app Tk
preview we ship a minimal segmenter that converts the most common
markdown constructs into Tk-friendly ``(text, tags)`` tuples.
"""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable


@dataclass
class Notes:
    """Markdown-backed notes attached to a run or experiment config."""

    title: str = ""
    text: str = ""            # markdown source
    created: str = ""         # ISO-8601 timestamp
    modified: str = ""        # ISO-8601 timestamp
    author: str = ""          # optional free-form author tag
    tags: list[str] = field(default_factory=list)

    @classmethod
    def empty(cls, title: str = "") -> "Notes":
        now = datetime.now().isoformat(timespec="seconds")
        return cls(title=title, text="", created=now, modified=now)

    def touch(self) -> None:
        self.modified = datetime.now().isoformat(timespec="seconds")
        if not self.created:
            self.created = self.modified

    def is_empty(self) -> bool:
        return not (self.text.strip() or self.title.strip())

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> "Notes":
        if not data:
            return cls.empty()
        return cls(
            title=str(data.get("title", "")),
            text=str(data.get("text", "")),
            created=str(data.get("created", "")),
            modified=str(data.get("modified", "")),
            author=str(data.get("author", "")),
            tags=list(data.get("tags", []) or []),
        )


# ─────────────────────────────────────────────────────────────────────────
# File I/O — supports both ``.md`` (raw markdown with optional YAML front
# matter) and ``.notes.json`` (the dataclass envelope).
# ─────────────────────────────────────────────────────────────────────────

def load_notes(path: str | Path) -> Notes:
    """Load notes from a ``.md`` or ``.notes.json`` file.

    ``.md`` files may optionally start with a YAML front-matter block
    delimited by ``---`` lines. Recognized keys: ``title``, ``author``,
    ``tags``, ``created``, ``modified``. Anything else is ignored.
    """
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"notes file not found: {p}")
    if p.suffix.lower() == ".json":
        return Notes.from_dict(json.loads(p.read_text()))
    text = p.read_text()
    front, body = _split_front_matter(text)
    n = Notes(text=body)
    for key, val in front.items():
        if hasattr(n, key):
            if key == "tags" and isinstance(val, str):
                val = [t.strip() for t in val.split(",") if t.strip()]
            setattr(n, key, val)
    if not n.created:
        n.created = datetime.fromtimestamp(p.stat().st_mtime).isoformat(
            timespec="seconds")
        n.modified = n.created
    if not n.title:
        stem = p.stem
        if stem.endswith(".notes"):
            stem = stem[: -len(".notes")]
        n.title = stem
    return n


def save_notes(path: str | Path, notes: Notes,
               *, fmt: str | None = None) -> Path:
    """Save notes to ``path``.

    ``fmt`` is "md" or "json". When omitted it is inferred from the
    suffix; unknown suffixes default to markdown with YAML front matter
    so the file remains human-readable.
    """
    p = Path(path)
    notes.touch()
    suffix = (fmt or p.suffix.lstrip(".") or "md").lower()
    if suffix == "json":
        p.write_text(json.dumps(notes.to_dict(), indent=2))
        return p
    front = {
        "title": notes.title,
        "author": notes.author,
        "tags": notes.tags,
        "created": notes.created,
        "modified": notes.modified,
    }
    front_yaml = "\n".join(
        f"{k}: {_yaml_scalar(v)}" for k, v in front.items() if v
    )
    blob = f"---\n{front_yaml}\n---\n\n{notes.text}\n" if front_yaml else notes.text
    p.write_text(blob)
    return p


def _yaml_scalar(v: Any) -> str:
    if isinstance(v, list):
        return "[" + ", ".join(str(x) for x in v) + "]"
    s = str(v)
    if any(c in s for c in ":#-{}[]"):
        return json.dumps(s)
    return s


_FRONT_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)


def _split_front_matter(text: str) -> tuple[dict[str, Any], str]:
    m = _FRONT_RE.match(text)
    if not m:
        return {}, text
    block = m.group(1)
    out: dict[str, Any] = {}
    for line in block.splitlines():
        if ":" not in line:
            continue
        k, v = line.split(":", 1)
        out[k.strip()] = _parse_scalar(v.strip())
    return out, text[m.end():]


def _parse_scalar(v: str) -> Any:
    if v.startswith("[") and v.endswith("]"):
        inner = v[1:-1]
        return [x.strip() for x in inner.split(",") if x.strip()]
    if (v.startswith('"') and v.endswith('"')) or (
            v.startswith("'") and v.endswith("'")):
        return v[1:-1]
    return v


# ─────────────────────────────────────────────────────────────────────────
# Plain-text and Tk segment rendering. Used by the GUI's notes preview.
# ─────────────────────────────────────────────────────────────────────────

def markdown_to_plain(md: str) -> str:
    """Strip markup leaving readable plain text (best-effort)."""
    lines = []
    for line in md.splitlines():
        s = line
        s = re.sub(r"^#{1,6}\s*", "", s)
        s = re.sub(r"\*\*(.+?)\*\*", r"\1", s)
        s = re.sub(r"\*(.+?)\*", r"\1", s)
        s = re.sub(r"_(.+?)_", r"\1", s)
        s = re.sub(r"`(.+?)`", r"\1", s)
        s = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r"\1 (\2)", s)
        lines.append(s)
    return "\n".join(lines)


def markdown_to_tk_segments(md: str) -> list[tuple[str, tuple[str, ...]]]:
    """Convert markdown to a list of ``(text, tag_tuple)`` segments.

    The GUI's Tk Text widget configures these tags:
      ``h1``, ``h2``, ``h3``, ``bold``, ``italic``, ``code``, ``codeblock``,
      ``bullet``, ``link``, ``quote``, ``hr``, ``normal``.
    Each segment is appended sequentially with the listed tags applied.
    Newlines are produced explicitly so the renderer never breaks lines
    inside a styled span.
    """
    out: list[tuple[str, tuple[str, ...]]] = []
    lines = md.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.strip().startswith("```"):
            block: list[str] = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith("```"):
                block.append(lines[i])
                i += 1
            i += 1  # skip closing fence
            out.append(("\n".join(block) + "\n", ("codeblock",)))
            continue
        h = re.match(r"^(#{1,6})\s+(.*)$", line)
        if h:
            level = len(h.group(1))
            tag = f"h{min(level, 3)}"
            out.append((h.group(2) + "\n", (tag,)))
            i += 1
            continue
        if line.strip() == "" or set(line.strip()) == {"-"} and len(line.strip()) >= 3:
            if set(line.strip()) == {"-"} and len(line.strip()) >= 3:
                out.append(("─" * 40 + "\n", ("hr",)))
            else:
                out.append(("\n", ("normal",)))
            i += 1
            continue
        if line.lstrip().startswith(("-", "*", "+")) and line.lstrip()[1:2] == " ":
            out.append(("  • ", ("bullet",)))
            _append_inline(out, line.lstrip()[2:])
            out.append(("\n", ("normal",)))
            i += 1
            continue
        if line.lstrip().startswith(">"):
            out.append(("  │ ", ("quote",)))
            _append_inline(out, line.lstrip()[1:].lstrip())
            out.append(("\n", ("quote",)))
            i += 1
            continue
        _append_inline(out, line)
        out.append(("\n", ("normal",)))
        i += 1
    return out


_INLINE_RE = re.compile(
    r"(\*\*(?P<b>[^*]+)\*\*)"
    r"|(\*(?P<i>[^*]+)\*)"
    r"|(`(?P<c>[^`]+)`)"
    r"|(\[(?P<link>[^\]]+)\]\((?P<href>[^)]+)\))",
)


def _append_inline(out: list[tuple[str, tuple[str, ...]]], text: str) -> None:
    pos = 0
    for m in _INLINE_RE.finditer(text):
        if m.start() > pos:
            out.append((text[pos:m.start()], ("normal",)))
        if m.group("b"):
            out.append((m.group("b"), ("bold",)))
        elif m.group("i"):
            out.append((m.group("i"), ("italic",)))
        elif m.group("c"):
            out.append((m.group("c"), ("code",)))
        elif m.group("link"):
            out.append((m.group("link"), ("link",)))
            out.append((f" ({m.group('href')})", ("normal",)))
        pos = m.end()
    if pos < len(text):
        out.append((text[pos:], ("normal",)))


def render_html(md: str) -> str:
    """Render markdown to a self-contained HTML fragment.

    Uses the ``markdown`` package if installed; otherwise falls back to a
    minimal converter that handles headers, bold, italic, code, code
    blocks, bullet lists, blockquotes, and paragraphs. Adequate for
    embedded previews and external export.
    """
    try:
        import markdown as _md  # type: ignore[import-not-found]
        return _md.markdown(md, extensions=["fenced_code", "tables"])
    except Exception:
        return _minimal_html(md)


def _minimal_html(md: str) -> str:
    out_lines: list[str] = []
    in_code = False
    in_list = False
    for raw in md.splitlines():
        line = raw.rstrip()
        if line.startswith("```"):
            if in_code:
                out_lines.append("</code></pre>")
                in_code = False
            else:
                out_lines.append("<pre><code>")
                in_code = True
            continue
        if in_code:
            out_lines.append(_html_escape(line))
            continue
        h = re.match(r"^(#{1,6})\s+(.*)$", line)
        if h:
            if in_list:
                out_lines.append("</ul>")
                in_list = False
            level = len(h.group(1))
            out_lines.append(f"<h{level}>{_inline_html(h.group(2))}</h{level}>")
            continue
        if line.lstrip().startswith(("-", "*", "+")) and line.lstrip()[1:2] == " ":
            if not in_list:
                out_lines.append("<ul>")
                in_list = True
            out_lines.append(f"<li>{_inline_html(line.lstrip()[2:])}</li>")
            continue
        if in_list:
            out_lines.append("</ul>")
            in_list = False
        if not line.strip():
            out_lines.append("")
            continue
        out_lines.append(f"<p>{_inline_html(line)}</p>")
    if in_list:
        out_lines.append("</ul>")
    if in_code:
        out_lines.append("</code></pre>")
    return "\n".join(out_lines)


def _html_escape(text: str) -> str:
    return (text.replace("&", "&amp;").replace("<", "&lt;")
                .replace(">", "&gt;"))


def _inline_html(text: str) -> str:
    s = _html_escape(text)
    s = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"\*([^*]+)\*", r"<em>\1</em>", s)
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    s = re.sub(
        r"\[([^\]]+)\]\(([^)]+)\)",
        r'<a href="\2">\1</a>', s)
    return s


__all__ = [
    "Notes",
    "load_notes",
    "save_notes",
    "markdown_to_plain",
    "markdown_to_tk_segments",
    "render_html",
]
