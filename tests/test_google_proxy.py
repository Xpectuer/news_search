#!/usr/bin/env python3
"""
Google搜索代理功能测试脚本
"""

import sys
import os
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_proxy_config():
    """测试代理配置功能"""
    print("=== 测试代理配置功能 ===")
    
    try:
        from news_agent.core.config import config
        
        # 检查配置是否正确加载
        ds_config = config.data_sources
        
        print(f"Google搜索启用: {ds_config.google_search_enabled}")
        print(f"代理启用: {ds_config.google_search_proxy_enabled}")
        print(f"代理服务器: {ds_config.google_search_proxy_server}")
        
        # 测试代理配置构建
        proxy_config = {}
        if ds_config.google_search_proxy_enabled and ds_config.google_search_proxy_server:
            proxy_config = {
                'enabled': True,
                'server': ds_config.google_search_proxy_server,
                'username': ds_config.google_search_proxy_username,
                'password': ds_config.google_search_proxy_password
            }
            print(f"代理配置: {proxy_config}")
        
        print("[SUCCESS] 配置加载成功")
        return True
        
    except Exception as e:
        print(f"[ERROR] 配置测试失败: {e}")
        return False

def test_google_source_creation():
    """测试Google搜索源创建"""
    print("\n=== 测试Google搜索源创建 ===")
    
    try:
        from news_agent.core.data_sources.google_search import GoogleSearchSource
        from news_agent.core.config import config
        
        ds_config = config.data_sources
        
        # 准备代理配置
        proxy_config = {}
        if ds_config.google_search_proxy_enabled and ds_config.google_search_proxy_server:
            proxy_config = {
                'enabled': True,
                'server': ds_config.google_search_proxy_server,
                'username': ds_config.google_search_proxy_username,
                'password': ds_config.google_search_proxy_password
            }
        
        # 创建Google搜索源
        google_source = GoogleSearchSource(
            delay=ds_config.google_search_delay,
            max_results=5,  # 测试用小数量
            headless=True,
            proxy_config=proxy_config
        )
        
        print(f"Google搜索源创建成功")
        print(f"延时: {google_source.delay}秒")
        print(f"最大结果: {google_source.max_results}")
        print(f"代理配置: {google_source.proxy_config}")
        
        # 测试可用性检查
        is_available = google_source.is_available()
        print(f"Google连接可用性: {is_available}")
        
        print("[SUCCESS] Google搜索源创建成功")
        return True
        
    except Exception as e:
        print(f"[ERROR] Google搜索源创建失败: {e}")
        return False

def test_search_query_building():
    """测试搜索查询构建"""
    print("\n=== 测试搜索查询构建 ===")
    
    try:
        from news_agent.core.data_sources.google_search import GoogleSearchSource, GoogleSearchOptions
        
        google_source = GoogleSearchSource()
        
        # 测试基础查询
        query1 = google_source._build_search_query(["Python"], {})
        print(f"基础查询: {query1}")
        
        # 测试网站限制
        query2 = google_source._build_search_query(
            ["AI"], 
            GoogleSearchOptions.news_sites(["stackoverflow.com", "github.com"])
        )
        print(f"网站限制查询: {query2}")
        
        # 测试日期范围
        query3 = google_source._build_search_query(
            ["机器学习"], 
            GoogleSearchOptions.date_range("2024-01-01", "2024-12-31")
        )
        print(f"日期范围查询: {query3}")
        
        # 测试排除词
        query4 = google_source._build_search_query(
            ["新闻"], 
            GoogleSearchOptions.exclude_terms(["广告", "推广"])
        )
        print(f"排除词查询: {query4}")
        
        print("[SUCCESS] 搜索查询构建测试成功")
        return True
        
    except Exception as e:
        print(f"[ERROR] 搜索查询构建测试失败: {e}")
        return False

def main():
    """主函数"""
    print("Google搜索代理功能测试")
    print("=" * 50)
    
    success_count = 0
    total_tests = 3
    
    # 测试配置
    if test_proxy_config():
        success_count += 1
    
    # 测试Google搜索源创建
    if test_google_source_creation():
        success_count += 1
    
    # 测试搜索查询构建
    if test_search_query_building():
        success_count += 1
    
    print("\n" + "=" * 50)
    print(f"测试完成: {success_count}/{total_tests} 通过")
    
    if success_count == total_tests:
        print("[SUCCESS] 所有测试通过！")
        print("\n使用说明:")
        print("1. 确保代理服务正在运行（如果需要）")
        print("2. 使用 news-agent fetch -k 'Python' -s google 进行实际搜索测试")
        return 0
    else:
        print("[ERROR] 部分测试失败")
        return 1

if __name__ == "__main__":
    sys.exit(main())