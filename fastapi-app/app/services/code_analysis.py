"""
Code analysis service for extracting code metrics and information.
"""
import ast
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass

from ..core import logger, is_code_file


@dataclass
class CodeMetrics:
    """Data class for code metrics."""
    lines_of_code: int
    lines_of_comments: int
    functions_count: int
    classes_count: int
    complexity_score: int
    docstring_coverage: float
    naming_convention_score: float


class CodeAnalysisService:
    """Service for analyzing code quality and extracting metrics."""
    
    def __init__(self):
        self.supported_languages = {
            '.py': self._analyze_python,
            '.js': self._analyze_javascript,
            '.java': self._analyze_java,
            '.cpp': self._analyze_cpp,
            '.c': self._analyze_c,
        }
    
    def analyze_code_file(self, file_path: Path, content: str) -> CodeMetrics:
        """
        Analyze a code file and extract metrics.
        
        Args:
            file_path: Path to the code file
            content: File content
            
        Returns:
            CodeMetrics object with analysis results
        """
        file_extension = file_path.suffix.lower()
        
        if file_extension in self.supported_languages:
            analyzer = self.supported_languages[file_extension]
            return analyzer(content)
        else:
            # Generic analysis for unsupported languages
            return self._analyze_generic(content)
    
    def _analyze_python(self, content: str) -> CodeMetrics:
        """Analyze Python code."""
        try:
            tree = ast.parse(content)
        except SyntaxError:
            logger.warning("Failed to parse Python code due to syntax errors")
            return self._analyze_generic(content)
        
        lines = content.split('\n')
        lines_of_code = len([line for line in lines if line.strip() and not line.strip().startswith('#')])
        lines_of_comments = len([line for line in lines if line.strip().startswith('#')])
        
        functions_count = len([node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)])
        classes_count = len([node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)])
        
        # Calculate complexity (simplified)
        complexity_score = self._calculate_python_complexity(tree)
        
        # Calculate docstring coverage
        docstring_coverage = self._calculate_docstring_coverage(tree)
        
        # Calculate naming convention score
        naming_score = self._calculate_python_naming_convention(tree)
        
        return CodeMetrics(
            lines_of_code=lines_of_code,
            lines_of_comments=lines_of_comments,
            functions_count=functions_count,
            classes_count=classes_count,
            complexity_score=complexity_score,
            docstring_coverage=docstring_coverage,
            naming_convention_score=naming_score
        )
    
    def _analyze_javascript(self, content: str) -> CodeMetrics:
        """Analyze JavaScript code."""
        lines = content.split('\n')
        lines_of_code = len([line for line in lines if line.strip() and not line.strip().startswith('//')])
        lines_of_comments = len([line for line in lines if line.strip().startswith('//')])
        
        # Count functions (simplified regex approach)
        function_pattern = r'function\s+\w+\s*\(|const\s+\w+\s*=\s*\(|let\s+\w+\s*=\s*\(|var\s+\w+\s*=\s*\('
        functions_count = len(re.findall(function_pattern, content))
        
        # Count classes
        class_pattern = r'class\s+\w+'
        classes_count = len(re.findall(class_pattern, content))
        
        return CodeMetrics(
            lines_of_code=lines_of_code,
            lines_of_comments=lines_of_comments,
            functions_count=functions_count,
            classes_count=classes_count,
            complexity_score=0,  # Would need more sophisticated analysis
            docstring_coverage=0.0,  # Would need JSDoc analysis
            naming_convention_score=0.0  # Would need camelCase analysis
        )
    
    def _analyze_java(self, content: str) -> CodeMetrics:
        """Analyze Java code."""
        lines = content.split('\n')
        lines_of_code = len([line for line in lines if line.strip() and not line.strip().startswith('//')])
        lines_of_comments = len([line for line in lines if line.strip().startswith('//')])
        
        # Count methods
        method_pattern = r'(public|private|protected)?\s*(static)?\s*\w+\s+\w+\s*\('
        functions_count = len(re.findall(method_pattern, content))
        
        # Count classes
        class_pattern = r'class\s+\w+'
        classes_count = len(re.findall(class_pattern, content))
        
        return CodeMetrics(
            lines_of_code=lines_of_code,
            lines_of_comments=lines_of_comments,
            functions_count=functions_count,
            classes_count=classes_count,
            complexity_score=0,
            docstring_coverage=0.0,
            naming_convention_score=0.0
        )
    
    def _analyze_cpp(self, content: str) -> CodeMetrics:
        """Analyze C++ code."""
        lines = content.split('\n')
        lines_of_code = len([line for line in lines if line.strip() and not line.strip().startswith('//')])
        lines_of_comments = len([line for line in lines if line.strip().startswith('//')])
        
        # Count functions
        function_pattern = r'\w+\s+\w+\s*\([^)]*\)\s*\{'
        functions_count = len(re.findall(function_pattern, content))
        
        # Count classes
        class_pattern = r'class\s+\w+'
        classes_count = len(re.findall(class_pattern, content))
        
        return CodeMetrics(
            lines_of_code=lines_of_code,
            lines_of_comments=lines_of_comments,
            functions_count=functions_count,
            classes_count=classes_count,
            complexity_score=0,
            docstring_coverage=0.0,
            naming_convention_score=0.0
        )
    
    def _analyze_c(self, content: str) -> CodeMetrics:
        """Analyze C code."""
        lines = content.split('\n')
        lines_of_code = len([line for line in lines if line.strip() and not line.strip().startswith('//')])
        lines_of_comments = len([line for line in lines if line.strip().startswith('//')])
        
        # Count functions
        function_pattern = r'\w+\s+\w+\s*\([^)]*\)\s*\{'
        functions_count = len(re.findall(function_pattern, content))
        
        return CodeMetrics(
            lines_of_code=lines_of_code,
            lines_of_comments=lines_of_comments,
            functions_count=functions_count,
            classes_count=0,  # C doesn't have classes
            complexity_score=0,
            docstring_coverage=0.0,
            naming_convention_score=0.0
        )
    
    def _analyze_generic(self, content: str) -> CodeMetrics:
        """Generic analysis for unsupported languages."""
        lines = content.split('\n')
        lines_of_code = len([line for line in lines if line.strip()])
        lines_of_comments = 0
        
        # Try to detect comment patterns
        comment_patterns = ['//', '#', '/*', '--', ';']
        for line in lines:
            stripped = line.strip()
            if any(stripped.startswith(pattern) for pattern in comment_patterns):
                lines_of_comments += 1
        
        return CodeMetrics(
            lines_of_code=lines_of_code,
            lines_of_comments=lines_of_comments,
            functions_count=0,
            classes_count=0,
            complexity_score=0,
            docstring_coverage=0.0,
            naming_convention_score=0.0
        )
    
    def _calculate_python_complexity(self, tree: ast.AST) -> int:
        """Calculate cyclomatic complexity for Python code."""
        complexity = 1  # Base complexity
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1
            elif isinstance(node, ast.ExceptHandler):
                complexity += 1
            elif isinstance(node, ast.BoolOp):
                complexity += len(node.values) - 1
        
        return complexity
    
    def _calculate_docstring_coverage(self, tree: ast.AST) -> float:
        """Calculate docstring coverage for Python code."""
        functions_with_docstrings = 0
        total_functions = 0
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                total_functions += 1
                if ast.get_docstring(node):
                    functions_with_docstrings += 1
        
        if total_functions == 0:
            return 0.0
        
        return (functions_with_docstrings / total_functions) * 100
    
    def _calculate_python_naming_convention(self, tree: ast.AST) -> float:
        """Calculate naming convention score for Python code."""
        total_names = 0
        correct_names = 0
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Name):
                total_names += 1
                if self._is_valid_python_name(node.id):
                    correct_names += 1
            elif isinstance(node, ast.FunctionDef):
                total_names += 1
                if self._is_valid_python_function_name(node.name):
                    correct_names += 1
            elif isinstance(node, ast.ClassDef):
                total_names += 1
                if self._is_valid_python_class_name(node.name):
                    correct_names += 1
        
        if total_names == 0:
            return 0.0
        
        return (correct_names / total_names) * 100
    
    def _is_valid_python_name(self, name: str) -> bool:
        """Check if a Python name follows conventions."""
        return name.islower() and '_' in name or name.islower()
    
    def _is_valid_python_function_name(self, name: str) -> bool:
        """Check if a Python function name follows conventions."""
        return name.islower() and ('_' in name or name.islower())
    
    def _is_valid_python_class_name(self, name: str) -> bool:
        """Check if a Python class name follows conventions."""
        return name[0].isupper() and name[1:].islower()
    
    def get_code_summary(self, code_files: Dict[str, str]) -> Dict[str, Any]:
        """
        Get summary of code analysis for multiple files.
        
        Args:
            code_files: Dictionary mapping file paths to content
            
        Returns:
            Dictionary with summary statistics
        """
        total_metrics = CodeMetrics(0, 0, 0, 0, 0, 0.0, 0.0)
        file_metrics = {}
        
        for file_path, content in code_files.items():
            path = Path(file_path)
            metrics = self.analyze_code_file(path, content)
            file_metrics[file_path] = metrics
            
            # Aggregate metrics
            total_metrics.lines_of_code += metrics.lines_of_code
            total_metrics.lines_of_comments += metrics.lines_of_comments
            total_metrics.functions_count += metrics.functions_count
            total_metrics.classes_count += metrics.classes_count
            total_metrics.complexity_score += metrics.complexity_score
        
        # Calculate averages
        file_count = len(code_files)
        if file_count > 0:
            avg_complexity = total_metrics.complexity_score / file_count
            avg_docstring_coverage = sum(m.docstring_coverage for m in file_metrics.values()) / file_count
            avg_naming_score = sum(m.naming_convention_score for m in file_metrics.values()) / file_count
        else:
            avg_complexity = 0
            avg_docstring_coverage = 0
            avg_naming_score = 0
        
        return {
            "total_files": file_count,
            "total_lines_of_code": total_metrics.lines_of_code,
            "total_lines_of_comments": total_metrics.lines_of_comments,
            "total_functions": total_metrics.functions_count,
            "total_classes": total_metrics.classes_count,
            "average_complexity": avg_complexity,
            "average_docstring_coverage": avg_docstring_coverage,
            "average_naming_convention_score": avg_naming_score,
            "file_metrics": {k: {
                "lines_of_code": v.lines_of_code,
                "lines_of_comments": v.lines_of_comments,
                "functions_count": v.functions_count,
                "classes_count": v.classes_count,
                "complexity_score": v.complexity_score,
                "docstring_coverage": v.docstring_coverage,
                "naming_convention_score": v.naming_convention_score
            } for k, v in file_metrics.items()}
        }
