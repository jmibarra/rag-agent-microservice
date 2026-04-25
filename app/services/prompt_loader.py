"""
Módulo utilitario para cargar y renderizar templates de prompts
desde archivos .md externos ubicados en app/prompts/.
"""

from pathlib import Path
from collections import defaultdict

# Directorio raíz de los templates de prompts
PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"


def load_prompt(filename: str) -> str:
    """
    Carga un archivo de template desde el directorio de prompts
    y retorna su contenido como string sin espacios sobrantes.

    Args:
        filename: Nombre del archivo (ej: 'system_prompt.md')

    Returns:
        Contenido del archivo como string.

    Raises:
        FileNotFoundError: Si el archivo no existe en el directorio de prompts.
    """
    filepath = PROMPTS_DIR / filename
    if not filepath.exists():
        raise FileNotFoundError(
            f"Template de prompt no encontrado: {filepath}"
        )
    return filepath.read_text(encoding="utf-8").strip()


def render_prompt(filename: str, **kwargs) -> str:
    """
    Carga un template y reemplaza los placeholders {variable}
    con los valores proporcionados.

    Usa defaultdict para que placeholders sin valor asignado
    queden como texto literal en vez de lanzar KeyError.

    Args:
        filename: Nombre del archivo template.
        **kwargs: Pares clave-valor para reemplazar placeholders.

    Returns:
        String del prompt con los placeholders reemplazados.
    """
    template = load_prompt(filename)

    # defaultdict retorna el placeholder original si no se provee valor
    safe_kwargs = defaultdict(lambda: "{key_not_found}", kwargs)
    return template.format_map(safe_kwargs)
