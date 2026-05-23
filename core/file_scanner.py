"""
QABot — File Scanner
Responsável por varrer pastas e ler arquivos do projeto do usuário.
"""

import pathlib

EXTENSIONS_ALLOWED = {
    ".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".cs",
    ".cpp", ".c", ".go", ".rb", ".php", ".html", ".css",
    ".json", ".yaml", ".yml", ".md", ".sql", ".sh"
}

DIRS_IGNORE = {
    "__pycache__", ".git", "node_modules", ".venv", "venv",
    "env", ".env", "dist", "build", ".idea", ".vscode",
    ".pytest_cache", ".mypy_cache"
}

MAX_FILE_SIZE_BYTES = 500_000  # 500 KB
MAX_CHARS_PER_FILE  = 8_000


def scan_project(folder_path: str) -> tuple[list, str | None]:
    """
    Varre a pasta informada e retorna lista de arquivos analisáveis.
    Retorna (files, error_message).
    """
    root = pathlib.Path(folder_path)

    if not root.exists():
        return [], "❌ Caminho não encontrado. Verifique se a pasta existe."
    if not root.is_dir():
        return [], "❌ O caminho informado não é uma pasta."

    files = []
    for path in sorted(root.rglob("*")):
        if any(d in path.parts for d in DIRS_IGNORE):
            continue
        if not path.is_file():
            continue
        if path.suffix.lower() not in EXTENSIONS_ALLOWED:
            continue
        try:
            if path.stat().st_size <= MAX_FILE_SIZE_BYTES:
                files.append(path)
        except OSError:
            pass

    return files, None


def read_file(path: pathlib.Path) -> str:
    """
    Lê o conteúdo de um arquivo com limite de caracteres.
    Retorna o conteúdo como string.
    """
    try:
        content = path.read_text(encoding="utf-8", errors="ignore")
        if len(content) > MAX_CHARS_PER_FILE:
            content = content[:MAX_CHARS_PER_FILE] + "\n\n[... arquivo truncado ...]"
        return content
    except Exception as e:
        return f"[Erro ao ler arquivo: {e}]"


def get_language_from_ext(ext: str) -> str:
    """Retorna o nome da linguagem para exibição e highlight."""
    mapping = {
        ".py": "python", ".js": "javascript", ".ts": "typescript",
        ".jsx": "javascript", ".tsx": "typescript", ".java": "java",
        ".cs": "csharp", ".cpp": "cpp", ".c": "c", ".go": "go",
        ".rb": "ruby", ".php": "php", ".html": "html", ".css": "css",
        ".json": "json", ".yaml": "yaml", ".yml": "yaml",
        ".md": "markdown", ".sql": "sql", ".sh": "bash",
    }
    return mapping.get(ext.lower(), "text")


def build_file_tree(files: list, root: str) -> list[dict]:
    """
    Retorna estrutura de árvore de arquivos para exibição.
    Cada item: {name, relative_path, ext, size_kb}
    """
    root_path = pathlib.Path(root)
    tree = []
    for f in files:
        try:
            rel = str(f.relative_to(root_path))
            size_kb = round(f.stat().st_size / 1024, 1)
            tree.append({
                "name": f.name,
                "relative_path": rel,
                "ext": f.suffix.lower(),
                "size_kb": size_kb,
                "depth": len(f.relative_to(root_path).parts) - 1,
            })
        except Exception:
            pass
    return tree
