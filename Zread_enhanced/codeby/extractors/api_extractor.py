"""API 提取器：扫描源码目录，提取所有 API 调用"""
from pathlib import Path
from collections import defaultdict
from typing import Dict, List
from codeby.extractors.code_parser import CodeParser


class ApiExtractor:
    """扫描源码目录，提取所有 API 调用（通用版）"""

    def __init__(self, use_hybrid: bool = True, use_llm: bool = True):
        """
        初始化提取器

        Args:
            use_hybrid: 是否使用混合解析器（默认 True）
            use_llm: 是否启用 LLM 验证（仅在 use_hybrid=True 时有效）
        """
        if use_hybrid:
            try:
                from codeby.extractors.llm_parser import HybridCodeParser
                self.parser = HybridCodeParser(use_llm_fallback=use_llm)
                self._parser_type = 'hybrid'
            except ImportError:
                # 如果混合解析器不可用，降级到正则解析器
                self.parser = CodeParser()
                self._parser_type = 'regex'
        else:
            self.parser = CodeParser()
            self._parser_type = 'regex'

        # 支持的文件扩展名
        self.source_extensions = {
            # C/C++
            '.cpp', '.cc', '.h', '.hpp', '.cxx', '.c', '.hxx',
            # Python
            '.py',
            # JavaScript/TypeScript
            '.js', '.ts', '.jsx', '.tsx', '.mjs', '.cjs',
            # Java
            '.java',
            # Go
            '.go',
            # Rust
            '.rs',
            # Ruby
            '.rb',
            # PHP
            '.php',
        }

    def extract_from_code(self, code: str, filename: str = '') -> list:
        """从代码字符串提取 API 调用"""
        return self.parser.extract_apis(code, filename)

    def extract_from_file(self, filepath: Path) -> list:
        """从文件提取 API 调用"""
        if filepath.suffix not in self.source_extensions:
            return []
        try:
            code = filepath.read_text(encoding='utf-8', errors='ignore')
            return self.parser.extract_apis(code, str(filepath))
        except Exception:
            return []

    def extract_from_directory(self, dirpath: Path, project_name: str = '') -> Dict[str, List]:
        """扫描目录，返回按库分类的 API 列表"""
        result = defaultdict(list)
        for filepath in dirpath.rglob('*'):
            if filepath.is_file() and filepath.suffix in self.source_extensions:
                apis = self.extract_from_file(filepath)
                for api in apis:
                    library = api.get('library', '')
                    api['project'] = project_name
                    result[library].append(api)
        return dict(result)
