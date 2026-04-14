"""API 页面生成器"""
from pathlib import Path
from typing import List, Dict, Optional
from extractors.api_database import ApiDatabase


class ApiGenerator:
    """生成 API Markdown 页面"""

    def __init__(self, output_dir: Path):
        self.output_dir = output_dir

    def generate(self, api_data: dict, db: Optional[ApiDatabase] = None) -> List[Dict]:
        """根据 API 数据生成 Markdown 文件"""
        pages = []
        for lib_name, apis in api_data.items():
            if lib_name == 'Unknown' or not apis:
                continue
            filename = f"api-{lib_name.lower().replace(' ', '_')}.md"
            content = self._generate_page_content(lib_name, apis, db)
            filepath = self.output_dir / filename
            filepath.write_text(content, encoding='utf-8')
            pages.append({
                'filename': filename,
                'content': content,
                'lib': lib_name
            })
        return pages

    def _generate_page_content(self, lib_name: str, apis: list,
                               db: Optional[ApiDatabase] = None) -> str:
        """生成单个库的 API 页面内容，按函数名分组"""
        lines = [f"# {lib_name} API 速查\n"]
        lines.append(f"本文页面列出代码中使用的所有 {lib_name} API 调用。\n")

        # 按 func 分组：func -> [api条目列表]
        grouped = {}
        for api in apis:
            func = api['func']
            if func not in grouped:
                grouped[func] = []
            grouped[func].append(api)

        for func, items in grouped.items():
            lines.append(f"## {func}")

            # 从数据库获取说明
            desc = ''
            if db:
                desc = db.get_description(func) or ''
            if not desc:
                desc = '（待补充）'

            lines.append(f"**说明：** {desc}")
            lines.append("")

            # 显示参数信息
            if items[0].get('params'):
                params = items[0]['params']
                if params:
                    params_preview = ', '.join(params[:5])
                    if len(params) > 5:
                        params_preview += ', ...'
                    lines.append(f"**参数：** {params_preview}")
                    lines.append("")

            # 列出所有调用位置
            locations = []
            for item in items:
                loc = f"`{item['file']}#{item['line']}`"
                locations.append(loc)
            lines.append(f"**调用位置：** {' | '.join(locations)}")
            lines.append("")

            # 显示一个典型示例（第一个）
            example = items[0]['code']
            lang = self._detect_language(example)
            lines.append(f"```{lang}")
            lines.append(example)
            lines.append("```")
            lines.append("")

        return "\n".join(lines)

    def _detect_language(self, code: str) -> str:
        """根据代码内容检测语言"""
        if '::' in code and '(' in code:
            return 'cpp'
        if 'import ' in code or 'from ' in code or 'def ' in code:
            return 'python'
        if 'function' in code or 'const ' in code or 'let ' in code or 'var ' in code:
            return 'javascript'
        if '#include' in code:
            return 'cpp'
        return 'cpp'  # 默认为 C++
