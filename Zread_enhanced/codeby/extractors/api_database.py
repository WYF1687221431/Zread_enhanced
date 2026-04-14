"""API 数据库：使用 SQLite 存储已知 API 的说明"""
import sqlite3
import json
from pathlib import Path
from typing import Dict, List, Optional, Set
from dataclasses import dataclass


@dataclass
class ApiInfo:
    """API 信息"""
    func: str           # 函数名，如 cv::imread
    library: str        # 库名，如 OpenCV
    description: str    # 说明
    params: str         # 参数描述（可选）
    source: str         # 来源：manual/llm/cache
    call_locations: List[dict]  # 调用位置 [{project, file, line}]


class ApiDatabase:
    """SQLite API 数据库"""

    def __init__(self, db_path: Optional[Path] = None):
        if db_path is None:
            db_path = Path(__file__).parent / 'api_database.db'
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """初始化数据库表"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS apis (
                    func TEXT PRIMARY KEY,
                    library TEXT DEFAULT '',
                    description TEXT DEFAULT '',
                    params TEXT DEFAULT '',
                    source TEXT DEFAULT 'cache',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.execute('''
                CREATE TABLE IF NOT EXISTS call_locations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    func TEXT NOT NULL,
                    project TEXT DEFAULT '',
                    file TEXT NOT NULL,
                    line INTEGER NOT NULL,
                    code TEXT DEFAULT '',
                    FOREIGN KEY (func) REFERENCES apis(func)
                )
            ''')
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_call_locations_func
                ON call_locations(func)
            ''')
            conn.commit()

    def get_description(self, func: str) -> Optional[str]:
        """获取 API 说明"""
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.execute(
                'SELECT description FROM apis WHERE func = ?', (func,)
            )
            row = cur.fetchone()
            return row[0] if row and row[0] else None

    def has_description(self, func: str) -> bool:
        """检查 API 是否有说明"""
        desc = self.get_description(func)
        return bool(desc and desc.strip())

    def add_api(self, func: str, description: str, library: str = '',
                params: str = '', source: str = 'llm'):
        """添加或更新 API 说明"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT INTO apis (func, library, description, params, source, updated_at)
                VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(func) DO UPDATE SET
                    description = excluded.description,
                    library = COALESCE(excluded.library, apis.library),
                    params = COALESCE(excluded.params, apis.params),
                    source = excluded.source,
                    updated_at = CURRENT_TIMESTAMP
            ''', (func, library, description, params, source))
            conn.commit()

    def get_apis_without_description(self) -> List[str]:
        """获取所有缺少说明的 API"""
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.execute(
                "SELECT func FROM apis WHERE description = '' OR description IS NULL"
            )
            return [row[0] for row in cur.fetchall()]

    def add_call_location(self, func: str, project: str, file: str,
                          line: int, code: str = ''):
        """添加调用位置"""
        with sqlite3.connect(self.db_path) as conn:
            # 检查是否已存在
            cur = conn.execute(
                '''SELECT id FROM call_locations
                   WHERE func = ? AND file = ? AND line = ?''',
                (func, file, line)
            )
            if cur.fetchone():
                return  # 已存在则跳过
            conn.execute(
                '''INSERT INTO call_locations (func, project, file, line, code)
                   VALUES (?, ?, ?, ?, ?)''',
                (func, project, file, line, code)
            )
            conn.commit()

    def get_call_locations(self, func: str) -> List[dict]:
        """获取 API 的所有调用位置"""
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.execute(
                '''SELECT project, file, line, code FROM call_locations
                   WHERE func = ? ORDER BY project, file, line''',
                (func,)
            )
            return [
                {'project': row[0], 'file': row[1], 'line': row[2], 'code': row[3]}
                for row in cur.fetchall()
            ]

    def get_all_apis(self) -> List[ApiInfo]:
        """获取所有 API 列表"""
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.execute(
                '''SELECT func, library, description, params, source
                   FROM apis ORDER BY library, func'''
            )
            return [
                ApiInfo(
                    func=row[0], library=row[1] or '', description=row[2] or '',
                    params=row[3] or '', source=row[4],
                    call_locations=self.get_call_locations(row[0])
                )
                for row in cur.fetchall()
            ]

    def search_apis(self, keyword: str) -> List[ApiInfo]:
        """搜索 API"""
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.execute(
                '''SELECT func, library, description, params, source
                   FROM apis
                   WHERE func LIKE ? OR description LIKE ? OR library LIKE ?
                   ORDER BY func''',
                (f'%{keyword}%', f'%{keyword}%', f'%{keyword}%')
            )
            return [
                ApiInfo(
                    func=row[0], library=row[1] or '', description=row[2] or '',
                    params=row[3] or '', source=row[4],
                    call_locations=self.get_call_locations(row[0])
                )
                for row in cur.fetchall()
            ]

    def import_from_cache(self, cache: Dict[str, str]):
        """从旧版缓存 JSON 导入"""
        for func, description in cache.items():
            if not self.has_description(func):
                self.add_api(func, description, source='cache')

    def export_json(self) -> Dict[str, str]:
        """导出为 JSON 格式（供 LLM 使用）"""
        result = {}
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.execute(
                'SELECT func, description FROM apis WHERE description != ""'
            )
            for row in cur.fetchall():
                result[row[0]] = row[1]
        return result
