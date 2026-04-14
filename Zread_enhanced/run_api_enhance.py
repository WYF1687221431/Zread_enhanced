#!/usr/bin/env python3
"""运行 api-enhance 的包装脚本"""
import sys
from pathlib import Path

# 将 Zread_enhanced 目录加入 sys.path
sys.path.insert(0, str(Path(__file__).parent))

# 切换到目标项目目录
import os
target_dir = Path(__file__).parent.parent / "ppt-master"
os.chdir(target_dir)

# 现在可以导入 api-enhance 模块（通过别名）
from api_enhance import main

if __name__ == '__main__':
    sys.exit(main())