"""
QABot — File Scanner
Filtros e metadados dos arquivos que entram na análise.

A varredura de pasta local saiu quando o envio passou a ser por upload:
num app publicado, ler um caminho do disco leria o disco do SERVIDOR, não
o do usuário.
"""

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
