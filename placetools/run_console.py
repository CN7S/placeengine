#!/usr/bin/env python3
"""
Place Cell Engine Console 启动脚本
"""

import os
import sys

# 添加当前目录到 Python 路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

try:
    from console import PlaceEngineConsole
    print("正在启动 Place Cell Engine Console...")
    console = PlaceEngineConsole()
    console.cmdloop()
except ImportError as e:
    print(f"导入错误: {e}")
    print("请确保 place_engine.py 文件在同一目录下")
except Exception as e:
    print(f"启动失败: {e}")