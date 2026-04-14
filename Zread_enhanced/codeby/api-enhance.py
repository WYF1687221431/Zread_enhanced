#!/usr/bin/env python3
"""zread API 增强后处理器"""
import sys
from pathlib import Path

# 将 codeby/ 的父目录加入 sys.path（支持 codeby 作为顶级包导入）
sys.path.insert(0, str(Path(__file__).parent.parent))

import argparse
from extractors.api_extractor import ApiExtractor
from generators.api_generator import ApiGenerator
from mergers.wiki_merger import WikiMerger
from extractors.api_database import ApiDatabase
from extractors.api_enricher import enrich_api_descriptions


def find_version_dir(base_dir: Path, version_id: str) -> Path:
    """查找版本目录"""
    versions_dir = base_dir / '.zread' / 'wiki' / 'versions'
    if version_id and (versions_dir / version_id).exists():
        return versions_dir / version_id
    # 尝试找最新的版本
    if versions_dir.exists():
        candidates = sorted(versions_dir.iterdir(), reverse=True)
        for d in candidates:
            if d.is_dir():
                return d
    return None


def main():
    parser = argparse.ArgumentParser(description='zread API 增强后处理器')
    parser.add_argument('--version', help='zread wiki 版本目录名（不指定则自动选择最新）')
    parser.add_argument('--src-dir', default='ORB_SLAM2_modified', help='源码目录（相对于当前目录）')
    parser.add_argument('--no-llm', action='store_true', help='跳过 LLM 说明生成')
    parser.add_argument('--project-name', default='', help='项目名称（用于数据库追踪）')
    parser.add_argument('--base-dir', default=None, help='项目根目录（默认为当前目录）')
    args = parser.parse_args()

    # 项目根目录（默认为当前目录）
    base_dir = Path(args.base_dir) if args.base_dir else Path('.')

    # 获取项目名（用于数据库追踪）
    project_name = args.project_name or base_dir.name

    # 查找版本目录
    version_dir = find_version_dir(base_dir, args.version)
    if not version_dir:
        print(f"Error: 未找到 wiki 版本目录。请先运行 zread generate。")
        return 1

    print(f"使用版本目录: {version_dir.name}")

    wiki_json_path = version_dir / 'wiki.json'
    if not wiki_json_path.exists():
        print(f"Error: wiki.json 不存在: {wiki_json_path}")
        return 1

    # API 文件直接放在版本目录根目录
    api_dir = version_dir

    # 1. 读取 wiki.json
    merger = WikiMerger()
    wiki_json = merger.load_wiki_json(wiki_json_path)
    print(f"Loaded wiki.json with {len(wiki_json['pages'])} pages")

    # 2. 扫描源码提取 API
    src_dir = base_dir / args.src_dir
    if not src_dir.exists():
        print(f"Error: 源码目录不存在: {src_dir}")
        return 1

    extractor = ApiExtractor()
    api_data = extractor.extract_from_directory(src_dir, project_name=project_name)
    print(f"Extracted APIs from {len(api_data)} libraries: {list(api_data.keys())}")

    if not api_data:
        print("No APIs found.")
        return 0

    total_apis = sum(len(v) for v in api_data.values())
    print(f"Total API calls: {total_apis}")

    # 3. 初始化数据库并补充 API 说明
    db = ApiDatabase()

    if not args.no_llm:
        api_data = enrich_api_descriptions(api_data, db)
    else:
        print("Skipping LLM description generation (--no-llm specified)")

    # 4. 生成 API 页面
    generator = ApiGenerator(api_dir)
    pages = generator.generate(api_data, db)
    print(f"Generated {len(pages)} API pages: {[p['filename'] for p in pages]}")

    # 5. 生成 API 索引并合并到 wiki.json
    api_index = merger.generate_api_index(pages)
    merged = merger.merge(wiki_json, api_index)
    merger.save_wiki_json(wiki_json_path, merged)
    print(f"Updated wiki.json with {len(api_index)} API pages")

    print("Done!")
    print(f"\nRun 'zread browse' to view the documentation.")
    return 0


if __name__ == '__main__':
    exit(main())
