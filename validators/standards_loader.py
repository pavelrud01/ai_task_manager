# validators/standards_loader.py
from __future__ import annotations
from pathlib import Path
from typing import Dict, Optional, Tuple, List
import re
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


def validate_interview_guide(guide_md: str) -> Tuple[bool, List[str]]:
    """
    Минимальная проверка стандарта интервью:
    - отсутствие тайм-меток в тексте
    - наличие write_to у вопросов
    - проверяемые {подстановки}
    """
    errors = []
    
    # Проверка на тайм-метки (например, "10:30", "2 минуты")
    time_patterns = [
        r'\d{1,2}:\d{2}',  # 10:30
        r'\d+\s*(минут|минуты|минуту|час|часа|часов)',  # 2 минуты
        r'\d+\s*(min|mins|hour|hours)',  # 2 min
    ]
    
    for pattern in time_patterns:
        if re.search(pattern, guide_md, re.IGNORECASE):
            errors.append(f"Found time markers in guide: {pattern}")
    
    # Проверка на наличие write_to в вопросах
    if "write_to" not in guide_md.lower():
        errors.append("No 'write_to' found in questions")
    
    # Проверка на подстановки {variable}
    substitution_pattern = r'\{[^}]+\}'
    substitutions = re.findall(substitution_pattern, guide_md)
    if not substitutions:
        errors.append("No variable substitutions found (e.g., {product_name})")
    
    # Проверка на наличие основных секций
    required_sections = ["Core Questions", "Evidence Tags", "Output Contract"]
    for section in required_sections:
        if section not in guide_md:
            errors.append(f"Missing required section: {section}")
    
    return len(errors) == 0, errors


def contracts_dir() -> Path:
    return CONTRACTS_DIR

def guides_dir() -> Path:
    return GLOBAL_GUIDES_DIR


# NEW: загрузка всех .md стандартов (проектовые перекрывают глобальные)
def load_md_standards(project_dir: Optional[Path] = None) -> Dict[str, str]:
    return load_core_standards(project_dir)


# NEW: загрузка всех JSON-схем контрактов
def load_contract_schemas() -> Dict[str, dict]:
    import json
    result: Dict[str, dict] = {}
    if CONTRACTS_DIR.exists():
        for p in CONTRACTS_DIR.glob("*.schema.json"):
            try:
                result[p.stem] = json.loads(p.read_text(encoding="utf-8")) or {}
            except Exception:
                result[p.stem] = {}
    return result


# NEW: загрузка орг-контекста (CompanyCard/MarketCard/Lessons + Knowledge Bank)
def load_organizational_context() -> Dict[str, str]:
    ctx_dir = REPO_ROOT / "prompts" / "context"
    def read_or_empty(name: str) -> str:
        p = ctx_dir / name
        return p.read_text(encoding="utf-8") if p.exists() else ""
    
    # Базовые контекстные файлы
    result = {
        "CompanyCard.md": read_or_empty("CompanyCard.md"),
        "MarketCard.md": read_or_empty("MarketCard.md"),
        "Lessons.md": read_or_empty("Lessons.md"),
    }
    
    # Загружаем Knowledge Bank
    knowledge_bank = load_knowledge_bank()
    result.update(knowledge_bank)
    
    return result


def load_knowledge_bank() -> Dict[str, str]:
    """
    Загружает все файлы из Knowledge Bank (prompts/context/knowledge/).
    Возвращает словарь {relative_path: content} для всех .md файлов.
    """
    knowledge_dir = REPO_ROOT / "prompts" / "context" / "knowledge"
    result = {}
    
    if not knowledge_dir.exists():
        return result
    
    # Рекурсивно обходим все подпапки
    for md_file in knowledge_dir.rglob("*.md"):
        try:
            # Получаем относительный путь от knowledge_dir
            relative_path = md_file.relative_to(knowledge_dir)
            # Используем forward slashes для консистентности
            key = str(relative_path).replace("\\", "/")
            
            content = md_file.read_text(encoding="utf-8")
            result[key] = content
            
        except Exception as e:
            print(f"Warning: Could not load knowledge file {md_file}: {e}")
            continue
    
    return result


# NEW: короткое резюме понимания для step_00_understanding.md
def summarize_understanding(context: dict) -> str:
    md = ["# STEP-00 — Understanding",
          "## Inputs",
          f"- Company: {context.get('input',{}).get('company_name','N/A')}",
          f"- Landing URL: {context.get('input',{}).get('landing_url','N/A')}",
          f"- Products: {context.get('input',{}).get('products',[])}",
          "",
          "## Standards loaded",
          ", ".join(sorted((context.get('md_standards') or {}).keys())) or "-",
          "",
          "## Schemas loaded", 
          ", ".join(sorted((context.get('schemas') or {}).keys())) or "-",
          "",
          "## Knowledge Bank loaded",
          _format_knowledge_bank_summary(context.get('org_context') or {}),
          "",
          "## Org Context Preview"]
    # форматируем короткий превью контекста
    org = context.get("org_context") or {}
    for name, content in org.items():
        if content and len(content.strip()) > 10:
            md.append(f"### {name}\n{content[:500]}...\n")
    return "\n".join(md)


def _format_knowledge_bank_summary(org_context: Dict[str, str]) -> str:
    """Форматирует краткое резюме загруженных файлов Knowledge Bank."""
    knowledge_files = []
    for key in org_context.keys():
        if "/" in key:  # Файлы из knowledge bank имеют путь с "/"
            knowledge_files.append(key)
    
    if not knowledge_files:
        return "-"
    
    return ", ".join(sorted(knowledge_files))


def get_standard_for_step(step_name: str, project_dir: Optional[Path], md_standards: Dict[str, str]) -> str:
    """
    Получает стандарт для конкретного шага.
    Ищет в md_standards по имени файла, соответствующему шагу.
    """
    # Маппинг имен шагов на имена файлов стандартов
    step_to_standard = {
        "step_05_segments": "segmentation.md",
        "step_06_decision_mapping": "decision_mapping.md", 
        "step_12_funnel_design": "funnel_design.md",
        "step_04_jtbd": "jtbd.md",
        "step_03_interview_collect": "interview_ajtbd.md",
        "step_02a_guide_compile": "guide_standard.md"
    }
    
    standard_file = step_to_standard.get(step_name)
    if standard_file and standard_file in md_standards:
        return md_standards[standard_file]
    
    # Если не найден, возвращаем пустую строку
    return ""
