"""LLM 代码解析器：使用 AI 理解代码结构，精确提取 API 调用"""
import os
import json
from typing import List, Dict, Set, Optional
from pathlib import Path


class LlmCodeParser:
    """使用 LLM 解析代码，精确提取 API 调用"""

    def __init__(self):
        self._api_key = os.environ.get('MINIMAX_API_KEY') or os.environ.get('ANTHROPIC_AUTH_TOKEN')
        self._base_url = os.environ.get('MINIMAX_BASE_URL', 'https://api.minimax.com/v1')

    def extract_apis(self, code: str, filename: str = '', language_hint: str = '') -> List[Dict]:
        """使用 LLM 提取代码中的 API 调用"""
        if not self._api_key:
            print("Warning: LLM_API_KEY not set, falling back to regex parser")
            return None  # 返回 None 表示需要 fallback

        # 检测语言
        if not language_hint:
            language_hint = self._detect_language(code)

        # 构建 prompt
        prompt = self._build_prompt(code, language_hint)

        # 调用 LLM
        result = self._call_llm(prompt)

        if not result:
            return None

        # 解析结果
        return self._parse_result(result, filename, code)

    def _detect_language(self, code: str) -> str:
        """根据代码内容检测语言"""
        if '::' in code and ('#include' in code or 'namespace' in code):
            return 'cpp'
        if '#include' in code:
            return 'cpp'
        if 'import ' in code or 'from ' in code or 'def ' in code:
            return 'python'
        if 'function' in code or 'const ' in code or 'let ' in code:
            return 'javascript'
        if 'func ' in code or 'package ' in code:
            return 'go'
        if 'fn ' in code and '->' in code:
            return 'rust'
        return 'unknown'

    def _build_prompt(self, code: str, language: str) -> str:
        """构建 LLM prompt"""
        return f"""你是一个专业的代码分析助手。请从以下 {language} 代码中提取所有 API 函数调用。

要求：
1. 只提取真正的 API 调用，不提取：
   - 注释中的代码
   - 字符串中的内容
   - 类型声明（如 `cv::Mat` 是类型，不是 API）
   - 变量赋值（如 `obj.property = x` 是赋值，不是调用）
2. 对于每个 API 调用，提取：
   - func: 函数全名（如 `cv::imread`, `np.array`, `console.log`）
   - library: 所属库名（如 `OpenCV`, `NumPy`, `JavaScript`）
3. 以 JSON 数组格式返回，示例：
   [{{"func": "cv::imread", "library": "OpenCV"}}, {{"func": "np.array", "library": "NumPy"}}]

代码：
```{language}
{code}
```

只返回 JSON 数组，不要有其他文字："""

    def _call_llm(self, prompt: str) -> Optional[Dict]:
        """调用 LLM API"""
        import urllib.request
        import urllib.error

        payload = json.dumps({
            'model': 'MiniMax-M2.7',
            'messages': [
                {'role': 'user', 'content': prompt}
            ],
            'max_tokens': 4096,
            'temperature': 0.1
        }).encode('utf-8')

        req = urllib.request.Request(
            f'{self._base_url}/chat/completions',
            data=payload,
            headers={
                'Authorization': f'Bearer {self._api_key}',
                'Content-Type': 'application/json'
            },
            method='POST'
        )

        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                response_body = resp.read().decode('utf-8')
                if not response_body.strip():
                    return None
                result = json.loads(response_body)
                content = result['choices'][0]['message']['content']

                content = content.strip()
                think_marker = '</think>'
                if think_marker in content:
                    parts = content.split(think_marker)
                    content = parts[-1].strip()

                if content.startswith('```'):
                    lines = content.split('\n')
                    content = '\n'.join(lines[1:-1])

                return json.loads(content)
        except Exception as e:
            print(f"Warning: LLM call failed: {type(e).__name__}: {e}")
            return None

    def _parse_result(self, llm_result: List[Dict], filename: str, code: str) -> List[Dict]:
        """解析 LLM 返回结果，添加位置信息"""
        results = []
        for item in llm_result:
            func = item.get('func', '')
            library = item.get('library', '')

            line_num = self._find_line_number(code, func)

            results.append({
                'func': func,
                'library': library,
                'params': [],
                'params_str': '',
                'file': filename,
                'line': line_num,
                'code': f"{func}()",
                'source': 'llm'
            })

        return results

    def _find_line_number(self, code: str, func: str) -> int:
        """查找函数在代码中的行号"""
        lines = code.split('\n')
        for i, line in enumerate(lines):
            if func in line:
                return i + 1
        return 1


class HybridCodeParser:
    """混合解析器：先用正则快速提取，再用 LLM 精确验证"""

    def __init__(self, use_llm_fallback: bool = True):
        from extractors.code_parser import CodeParser
        self._regex_parser = CodeParser()
        self._llm_parser = LlmCodeParser()
        self._use_llm_fallback = use_llm_fallback

    def extract_apis(self, code: str, filename: str = '') -> List[Dict]:
        """提取 API 调用"""
        results = self._regex_parser.extract_apis(code, filename)

        if not self._use_llm_fallback:
            return results

        llm_results = self._llm_parser.extract_apis(code, filename)

        if llm_results is None:
            return results

        return self._merge_results(results, llm_results)

    def _merge_results(self, regex_results: List[Dict], llm_results: List[Dict]) -> List[Dict]:
        """合并正则和 LLM 的结果"""
        seen = set()
        merged = []

        for item in llm_results:
            func = item['func']
            if func not in seen:
                seen.add(func)
                merged.append(item)

        for item in regex_results:
            func = item['func']
            if func not in seen:
                if not self._is_likely_false_positive(item, llm_results):
                    seen.add(func)
                    merged.append(item)

        merged.sort(key=lambda x: (x['file'], x['line']))
        return merged

    def _is_likely_false_positive(self, item: Dict, llm_results: List[Dict]) -> bool:
        """检查正则结果是否是可能的误识别"""
        llm_funcs = [r['func'] for r in llm_results]
        return item['func'] not in llm_funcs
