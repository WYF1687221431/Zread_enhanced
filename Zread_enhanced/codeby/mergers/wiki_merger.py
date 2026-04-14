"""wiki.json 合并器"""
import json
from pathlib import Path
from typing import List, Dict


class WikiMerger:
    """将 API 页面元数据合并到 wiki.json"""

    def merge(self, wiki_json: dict, api_pages: List[Dict]) -> dict:
        """合并 API 页面到 wiki.json，自动去重"""
        result = wiki_json.copy()

        # 提取现有的非 API 页面
        original_pages = [p for p in result['pages'] if not p['slug'].startswith('api-')]

        # 添加新的 API 页面
        result['pages'] = original_pages + api_pages
        return result

    def load_wiki_json(self, path: Path) -> dict:
        """加载 wiki.json"""
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def save_wiki_json(self, path: Path, data: dict):
        """保存 wiki.json"""
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def generate_api_index(self, pages: List[Dict]) -> List[Dict]:
        """生成 API 页面的 wiki.json 条目"""
        api_index = []
        for page in pages:
            slug = f"api-{page['lib'].lower().replace(' ', '_')}"
            api_index.append({
                'slug': slug,
                'title': f"{page['lib']} API 速查",
                'file': page['filename'],  # 关键！zread browse 需要这个
                'group': 'API 速查'
            })
        return api_index