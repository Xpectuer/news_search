#!/usr/bin/env python3
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from src.news_agent.cli.commands import cli

def main():
    """CLI入口点"""
    cli()

if __name__ == '__main__':
    main()