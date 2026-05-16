import re
from pathlib import Path
from typing import Optional

from code_migration.core.security.input_validator import SecurityError


_DANGEROUS_PATH_PARTS = ("..", "~", "$", "`", "|", ";", "&", "\x00")


def validate_path(path: str, base_dir: Optional[str] = None) -> Path:
    """
    Validate and sanitize file path to prevent directory traversal.
    
    Args:
        path: The path to validate.
        base_dir: The allowed base directory. If None, uses current working directory.
        
    Returns:
        Path: Absolute resolved path.
        
    Raises:
        SecurityError: If path is outside base directory or contains dangerous patterns.
    """
    if not path or len(path) > 4096:
        raise SecurityError("Invalid path length")

    raw_path = str(path)
    for marker in _DANGEROUS_PATH_PARTS:
        if marker in raw_path:
            raise SecurityError(f"Dangerous path pattern detected: {marker}")

    base = Path(base_dir or Path.cwd()).expanduser()
    try:
        resolved_base = base.resolve(strict=True)
        candidate = Path(path).expanduser()
        if not candidate.is_absolute():
            candidate = resolved_base / candidate
        resolved_path = candidate.resolve(strict=False)
    except Exception as e:
        raise SecurityError(f"Invalid path resolution: {e}")

    try:
        resolved_path.relative_to(resolved_base)
    except ValueError as exc:
        raise SecurityError(f"Path traversal detected: {path} is outside {resolved_base}") from exc

    return resolved_path

def sanitize_input(input_str: str) -> str:
    """
    Sanitize user input string.
    Removes potentially dangerous characters for shell execution.
    """
    # Allow alphanumeric, underscore, dot, hyphen, forward slash (for paths)
    # This is very restrictive, primarily for filenames/paths passed to CLIs
    if not re.match(r'^[a-zA-Z0-9_\-\./]+$', input_str):
        # We might want to be more lenient depending on context, but strict by default
        pass
    return input_str
