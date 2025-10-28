#!/usr/bin/env python3
"""
Google搜索功能安装和测试脚本
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(command, description):
    """运行命令并处理输出"""
    print(f"\n[INFO] {description}")
    print(f"[CMD] {command}")
    
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"[SUCCESS] {description}")
            if result.stdout.strip():
                print(result.stdout)
        else:
            print(f"[ERROR] {description} 失败")
            print(result.stderr)
            return False
    except Exception as e:
        print(f"[ERROR] 执行命令失败: {e}")
        return False
    
    return True

def check_dependencies():
    """检查依赖是否已安装"""
    print("=== 检查依赖 ===")
    
    # 检查Python包
    required_packages = ['playwright', 'beautifulsoup4', 'rich']
    for package in required_packages:
        try:
            __import__(package)
            print(f"[OK] {package} 已安装")
        except ImportError:
            print(f"[MISSING] {package} 未安装")
            return False
    
    return True

def install_playwright_browsers():
    """安装Playwright浏览器"""
    print("\n=== 安装Playwright浏览器 ===")
    
    # 安装Chromium
    success = run_command(
        "python -m playwright install chromium",
        "安装Chromium浏览器"
    )
    
    if success:
        # 验证安装
        success = run_command(
            "python -m playwright install-deps chromium",
            "安装Chromium系统依赖"
        )
    
    return success

def test_google_search():
    """测试Google搜索功能"""
    print("\n=== 测试Google搜索功能 ===")
    
    try:
        # 导入模块
        sys.path.insert(0, str(Path(__file__).parent / "src"))
        from news_agent.core.data_sources.google_search import GoogleSearchSource
        
        print("[INFO] 正在测试Google搜索连接...")
        
        # 创建搜索实例
        search_source = GoogleSearchSource(delay=2, max_results=5, headless=True)
        
        # 检查可用性
        if not search_source.is_available():
            print("[ERROR] Google搜索不可用，请检查网络连接")
            return False
        
        print("[SUCCESS] Google搜索功能可用")
        
        # 进行简单测试搜索
        print("[INFO] 正在进行测试搜索...")
        results = search_source.fetch_news(
            keywords=["Python"],
            search_options={'site': ['stackoverflow.com'], 'after': '2024-01-01'}
        )
        
        if results:
            print(f"[SUCCESS] 测试搜索成功，找到 {len(results)} 条结果")
            print(f"[INFO] 第一条结果: {results[0].title[:50]}...")
        else:
            print("[WARNING] 测试搜索未找到结果，这可能是正常的")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] 测试失败: {e}")
        return False

def main():
    """主函数"""
    print("Google搜索功能安装和测试工具")
    print("=" * 50)
    
    # 检查依赖
    if not check_dependencies():
        print("\n[ERROR] 依赖检查失败，请先安装所需的Python包:")
        print("pip install playwright beautifulsoup4 rich")
        return 1
    
    # 安装浏览器
    if not install_playwright_browsers():
        print("\n[ERROR] 浏览器安装失败")
        return 1
    
    # 测试功能
    if not test_google_search():
        print("\n[ERROR] 功能测试失败")
        return 1
    
    print("\n" + "=" * 50)
    print("[SUCCESS] Google搜索功能安装和测试完成！")
    print("\n使用示例:")
    print("news-agent config enable-google")
    print('news-agent fetch -k "Python" -s google --recent-days 7')
    
    return 0

if __name__ == "__main__":
    sys.exit(main())