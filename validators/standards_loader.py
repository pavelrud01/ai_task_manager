# validators/standards_loader.py
from __future__ import annotations
from pathlib import Path
from typing import Dict, Optional, Tuple
from pathlib import Path
import re
import yaml


# NB: для чтения YAML front-matter вам понадобится PyYAML
# добавьте в requirements.txt: PyYAML>=6.0.1
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
GLOBAL_STANDARDS_DIR = REPO_ROOT / "prompts" / "standards"
GLOBAL_GUIDES_DIR = REPO_ROOT / "prompts" / "guides"
CONTRACTS_DIR = REPO_ROOT / "contracts"


def _read_text(p: Path) -> str:
    return p.read_text(encoding="utf-8") if p.exists() else ""


def load_core_standards(project_dir: Optional[Path] = None) -> Dict[str, str]:
    """
    Загружает стандарты (.md) с приоритетом проекта:
    1) projects/<NAME>/standards/*.md (если есть)
    2) prompts/standards/*.md (глобальные)
    Возвращает dict {filename: content}
    """
    result: Dict[str, str] = {}

    # проектные стандарты
    if project_dir:
        proj_std_dir = project_dir / "standards"
        if proj_std_dir.exists():
            for md in proj_std_dir.glob("*.md"):
                result[md.name] = _read_text(md)

    # глобальные стандарты (не перезаписывают уже загруженные проектные)
    if GLOBAL_STANDARDS_DIR.exists():
        for md in GLOBAL_STANDARDS_DIR.glob("*.md"):
            result.setdefault(md.name, _read_text(md))

    return result


def resolve_guide_path(guide_path_or_name: str, project_dir: Optional[Path] = None) -> Path:
    """
    Находит путь к гайду. Приоритет:
    1) Абсолютный/относительный путь (как есть)
    2) projects/<NAME>/guides/<name>.md
    3) prompts/guides/<name>.md
    """
    p = Path(guide_path_or_name)
    if p.exists():
        return p

    if project_dir:
        candidate = project_dir / "guides" / guide_path_or_name
        if candidate.exists():
            return candidate

    candidate = GLOBAL_GUIDES_DIR / guide_path_or_name
    if candidate.exists():
        return candidate

    # если передали просто имя без .md
    if not guide_path_or_name.endswith(".md"):
        if project_dir:
            candidate = project_dir / "guides" / f"{guide_path_or_name}.md"
            if candidate.exists():
                return candidate
        candidate = GLOBAL_GUIDES_DIR / f"{guide_path_or_name}.md"
        if candidate.exists():
            return candidate

    # последний шанс — вернём как есть (пусть упадёт выше по стеку с понятной ошибкой)
    return Path(guide_path_or_name)


def load_guide_markdown(guide_path_or_name: str, project_dir: Optional[Path] = None) -> str:
    """
    Возвращает сырой Markdown гайда (с YAML front-matter вверху).
    """
    path = resolve_guide_path(guide_path_or_name, project_dir)
    if not path.exists():
        raise FileNotFoundError(f"Guide file not found: {path}")
    return _read_text(path)


def parse_guide_markdown(md_text: str) -> Tuple[dict, dict]:
    """
    Быстрый разбор front-matter + секций Markdown.
    Возвращает (meta:dict, sections:dict).
    Примечание: секции остаются текстовыми; структурирование вопросов
    под JSON-схему делаем уже на шаге интервью (через LLM).
    """
    meta: dict = {}
    body = md_text

    # YAML front-matter между --- ... ---
    if md_text.startswith("---"):
        parts = md_text.split("\n---", 1)
        if len(parts) == 2:
            fm = parts[0].lstrip("-\n")
            body = parts[1].lstrip("\n")
            try:
                meta = yaml.safe_load(fm) or {}
            except Exception:
                meta = {}

    # Простое разбиение по заголовкам второго уровня "## "
    sections: dict = {}
    current = None
    lines = body.splitlines()
    buf = []
    for line in lines:
        if line.strip().startswith("## "):
            if current:
                sections[current] = "\n".join(buf).strip()
                buf = []
            current = line.strip()[3:]  # после "## "
        else:
            buf.append(line)
    if current:
        sections[current] = "\n".join(buf).strip()

    return meta, sections


def contracts_dir() -> Path:
    return CONTRACTS_DIR

def contracts_dir() -> Path:
    return Path(__file__).resolve().parents[1] / "contracts"

def guides_dir() -> Path:
    return Path(__file__).resolve().parents[1] / "prompts" / "guides"

def load_guide_markdown(guide_path: str, project_dir: Path | None) -> str:
    """
    Резолвит путь к гайду:
    1) Абсолютный — читаем как есть.
    2) Относительный + project_dir — ищем внутри проекта.
    3) Иначе — ищем в prompts/guides/.
    """
    p = Path(guide_path)
    candidates = []
    if p.is_absolute():
        candidates.append(p)
    if project_dir:
        candidates.append(Path(project_dir) / guide_path)
    candidates.append(guides_dir() / guide_path)

    for c in candidates:
        if c.exists():
            return c.read_text(encoding="utf-8")
    raise FileNotFoundError(f"Guide not found by paths: {', '.join(map(str, candidates))}")

_HEADER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)

def parse_guide_markdown(md: str) -> tuple[dict, dict]:
    """
    Поддерживает YAML-фронтматтер между --- --- и секции вида:
    ## Intro
    ## Core Questions
    ## Deepening (5 Whys)
    ## Branching Rules
    ## Output Contract Hints
    ## Safety & Ethics
    ## Stop Conditions
    Возвращает (meta_dict, sections_dict)
    """
    meta = {}
    m = _HEADER_RE.match(md)
    body = md
    if m:
        try:
            meta = yaml.safe_load(m.group(1)) or {}
        except Exception:
            meta = {}
        body = md[m.end():]

    sections = {}
    current = None
    lines = []
    for line in body.splitlines():
        if line.startswith("## "):
            if current:
                sections[current] = "\n".join(lines).strip()
                lines = []
            current = line.replace("## ", "").strip()
        else:
            lines.append(line)
    if current:
        sections[current] = "\n".join(lines).strip()

    return meta, sections
