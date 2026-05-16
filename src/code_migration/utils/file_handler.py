import os
import shutil
import tempfile
from pathlib import Path
from typing import Optional
from .logger import get_logger
logger = get_logger(__name__)
from .sanitizer import validate_path, SecurityError

def create_backup(file_path: Path, backup_dir: Path) -> Path:
    """
    Create a backup of the file before modification.
    """
    if not file_path.exists():
        return None
        
    backup_dir.mkdir(parents=True, exist_ok=True)
    
    # Create timestamped filename or just simple backup?
    # For now, let's keep it simple: original_filename.bak
    # In production, we might want versioning.
    backup_path = backup_dir / f"{file_path.name}.bak"
    shutil.copy2(file_path, backup_path)
    logger.debug(f"Backup created: {backup_path}")
    return backup_path

def safe_write_file(path: str, content: str, base_dir: Optional[str] = None) -> None:
    """
    Safely write content to a file using atomic write pattern.
    Verifies path security before writing.
    """
    try:
        raw_path = Path(path)
        if raw_path.is_symlink():
            raise SecurityError("Refusing to overwrite symlink targets")
        file_path = validate_path(path, base_dir)
    except SecurityError as e:
        logger.error("Security violation during write: %s", e)
        raise

    # Create backup
    # Check if we should backup (could be config driven, passing simplified logic for now)
    backup_dir = file_path.parent / ".migration-backups"
    create_backup(file_path, backup_dir)

    # Atomic write: write to temp -> fsync -> rename
    dir_name = file_path.parent
    dir_name.mkdir(parents=True, exist_ok=True)
    
    tmp_name = None
    try:
        with tempfile.NamedTemporaryFile("w", dir=dir_name, delete=False, encoding="utf-8", newline="") as tmp_file:
            tmp_file.write(content)
            tmp_file.flush()
            os.fsync(tmp_file.fileno())
            tmp_name = tmp_file.name

        if file_path.exists():
            try:
                shutil.copystat(file_path, tmp_name)
            except OSError:
                pass

        os.replace(tmp_name, file_path)
        logger.info("Successfully wrote to %s", file_path)
    except (OSError, IOError) as e:
        logger.error(f"Failed to write file {file_path}: {e}")
        if tmp_name and os.path.exists(tmp_name):
            os.remove(tmp_name)
        raise

def safe_read_file(path: str, base_dir: Optional[str] = None) -> str:
    """
    Safely read file content.
    """
    try:
        raw_path = Path(path)
        if raw_path.is_symlink():
            raise SecurityError("Refusing to read symlink targets")
        file_path = validate_path(path, base_dir)
        if not file_path.exists():
             raise FileNotFoundError(f"File not found: {path}")

        if not file_path.is_file():
            raise SecurityError(f"Path is not a regular file: {path}")

        with open(file_path, "r", encoding="utf-8", errors="strict", newline="") as f:
            return f.read()
    except SecurityError as e:
        logger.error("Security violation during read: %s", e)
        raise
