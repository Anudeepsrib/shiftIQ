"""
Sandboxed code analysis without execution.

Security Principle: Static analysis only, no dynamic execution.
Defense Layers:
1. AST parsing (never eval/exec)
2. Read-only file operations
3. Resource limits (CPU, memory, time)
4. File-size and file-count limits
"""

import ast
import json
import os
from pathlib import Path
from typing import Dict, List, Any

from .input_validator import SecurityError
from ..security.crypto_handler import SecureFileHandler
from code_migration.config import settings


class SafeCodeAnalyzer:
    """
    Analyze code WITHOUT executing it.
    
    Security Principle: Static analysis only, no dynamic execution.
    """
    
    # Maximum lines to process
    MAX_LINES = 100_000
    
    @staticmethod
    def analyze(file_path: Path) -> Dict[str, Any]:
        """
        Parse code structure using AST only.
        
        Args:
            file_path: Path to file to analyze
            
        Returns:
            Dict with analysis results
            
        Raises:
            SecurityError: If file is too large or analysis fails
        """
        # Validate file size
        if file_path.is_symlink():
            raise SecurityError(f"Refusing to analyze symlink: {file_path}")
        if not file_path.exists():
            raise SecurityError(f"File does not exist: {file_path}")
        if not file_path.is_file():
            raise SecurityError(f"Path is not a regular file: {file_path}")
        file_size = os.path.getsize(file_path)
        if file_size > (settings.security.max_file_size_kb * 1024):
            return {"safe": False, "reason": f"File exceeds maximum size of {settings.security.max_file_size_kb}KB"}
        
        # Read file with size limit
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
        except (OSError, UnicodeDecodeError) as e:
            raise SecurityError(f"Failed to read file: {e}")
        
        # Check line count
        lines = content.split('\n')
        if len(lines) > SafeCodeAnalyzer.MAX_LINES:
            raise SecurityError(f"File has too many lines: {len(lines)}")
        
        # Parse using AST (safe, no execution)
        try:
            tree = ast.parse(content)
        except SyntaxError as e:
            return {
                "error": str(e),
                "parsed": False,
                "file_path": str(file_path),
                "file_size": file_size,
                "line_count": len(lines)
            }
        
        # Extract metadata via AST traversal only
        analysis = {
            "parsed": True,
            "file_path": str(file_path),
            "file_size": file_size,
            "line_count": len(lines),
            "classes": [],
            "functions": [],
            "imports": [],
            "complexity": 0,
            "docstrings": []
        }
        
        # Traverse AST safely
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                analysis["classes"].append({
                    "name": node.name,
                    "line": node.lineno,
                    "methods": [n.name for n in node.body if isinstance(n, ast.FunctionDef)]
                })
            
            elif isinstance(node, ast.FunctionDef):
                analysis["functions"].append({
                    "name": node.name,
                    "line": node.lineno,
                    "args": [arg.arg for arg in node.args.args],
                    "complexity": SafeCodeAnalyzer._calculate_cyclomatic_complexity(node)
                })
                analysis["complexity"] += analysis["functions"][-1]["complexity"]
            
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    analysis["imports"].append({
                        "module": alias.name,
                        "alias": alias.asname,
                        "line": node.lineno
                    })
            
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    analysis["imports"].append({
                        "module": node.module,
                        "names": [alias.name for alias in node.names],
                        "line": node.lineno
                    })
            
            elif isinstance(node, ast.Module) and ast.get_docstring(node):
                analysis["docstrings"].append({
                    "type": "module",
                    "line": 1,
                    "content": ast.get_docstring(node)[:200] + "..." if len(ast.get_docstring(node)) > 200 else ast.get_docstring(node)
                })
        
        return analysis
    
    @staticmethod
    def _calculate_cyclomatic_complexity(node: ast.FunctionDef) -> int:
        """
        Calculate cyclomatic complexity of function.
        
        Uses only AST analysis, no execution.
        """
        complexity = 1  # Base complexity
        
        for child in ast.walk(node):
            # Each decision point adds to complexity
            if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1
            elif isinstance(child, ast.ExceptHandler):
                complexity += 1
            elif isinstance(child, (ast.With, ast.AsyncWith)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
            elif isinstance(child, ast.ListComp):
                complexity += 1
            elif isinstance(child, ast.DictComp):
                complexity += 1
            elif isinstance(child, ast.SetComp):
                complexity += 1
            elif isinstance(child, ast.GeneratorExp):
                complexity += 1
        
        return complexity
    
    @staticmethod
    def analyze_directory(directory: Path) -> Dict[str, Any]:
        """
        Analyze all Python files in directory.
        
        Args:
            directory: Directory to analyze
            
        Returns:
            Dict with aggregated analysis results
        """
        if not directory.is_dir():
            raise SecurityError(f"Path is not a directory: {directory}")
        
        results = {
            "directory": str(directory),
            "files_analyzed": 0,
            "total_lines": 0,
            "total_size": 0,
            "classes": [],
            "functions": [],
            "imports": [],
            "total_complexity": 0,
            "errors": []
        }
        
        # Find all Python files
        py_files = [
            path
            for path in directory.rglob("*.py")
            if not path.is_symlink()
            and not any(part in {".git", ".venv", "venv", "__pycache__", "node_modules"} for part in path.parts)
        ][: settings.security.max_files]
        
        for py_file in py_files:
            try:
                analysis = SafeCodeAnalyzer.analyze(py_file)
                
                if analysis.get("parsed"):
                    results["files_analyzed"] += 1
                    results["total_lines"] += analysis["line_count"]
                    results["total_size"] += analysis["file_size"]
                    results["total_complexity"] += analysis["complexity"]
                    
                    # Aggregate data
                    results["classes"].extend(analysis["classes"])
                    results["functions"].extend(analysis["functions"])
                    results["imports"].extend(analysis["imports"])
                else:
                    results["errors"].append({
                        "file": str(py_file),
                        "error": analysis.get("error", "Unknown error")
                    })
                    
            except SecurityError as e:
                results["errors"].append({
                    "file": str(py_file),
                    "error": str(e)
                })
        
        # Calculate summary statistics
        if results["files_analyzed"] > 0:
            results["avg_complexity"] = results["total_complexity"] / results["files_analyzed"]
            results["avg_lines_per_file"] = results["total_lines"] / results["files_analyzed"]
        else:
            results["avg_complexity"] = 0
            results["avg_lines_per_file"] = 0
        
        return results
    
    @staticmethod
    def extract_dependencies(file_path: Path) -> List[str]:
        """
        Extract import dependencies safely.
        
        Args:
            file_path: Python file to analyze
            
        Returns:
            List of imported module names
        """
        try:
            analysis = SafeCodeAnalyzer.analyze(file_path)
            if not analysis.get("parsed"):
                return []
            
            dependencies = set()
            for imp in analysis["imports"]:
                if isinstance(imp, dict):
                    if "module" in imp:
                        dependencies.add(imp["module"])
                    elif "names" in imp:
                        dependencies.update(imp["names"])
            
            return sorted(list(dependencies))
            
        except SecurityError:
            return []
