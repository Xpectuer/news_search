#!/usr/bin/env python3
"""
测试Google搜索的requests改进方案
"""
import sys
import os
from datetime import datetime

# 添加项目路径到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from news_agent.core.data_sources.google_search import GoogleSearchSource, GoogleSearchOptions


def test_google_requests():
    """测试Google搜索requests方案"""
    print("=" * 60)
    print("测试Google搜索requests方案")
    print("=" * 60)
    
    # 创建使用requests的Google搜索实例
    google_source = GoogleSearchSource(
        delay=2,
        max_results=10,
        use_requests=True,  # 使用requests方案
        proxy_config={'enabled': True, 'server': 'http://127.0.0.1:7892'}  # 根据你的代理配置调整
    )
    
    print(f"使用requests: {google_source.use_requests}")
    print(f"服务可用性: {google_source.is_available()}")
    print()
    
    # 测试基础搜索
    print("1. 基础搜索测试 (关键词: trump):")
    print("-" * 40)
    try:
        results = google_source.fetch_news(keywords=["trump"])
        print(f"搜索结果数量: {len(results)}")
        
        for i, news in enumerate(results[:3], 1):  # 只显示前3个结果
            print(f"\n结果 {i}:")
            print(f"  标题: {news.title}")
            print(f"  URL: {news.url}")
            print(f"  来源: {news.source}")
            print(f"  摘要: {news.summary[:100]}...")
            
    except Exception as e:
        print(f"基础搜索失败: {e}")
    
    # 测试带site限制的搜索
    print("\n\n2. 网站限制搜索测试:")
    print("-" * 40)
    try:
        search_options = GoogleSearchOptions.news_sites(['cnn.com', 'bbc.com'])
        results = google_source.fetch_news(
            keywords=["AI"], 
            search_options=search_options
        )
        print(f"限制网站搜索结果数量: {len(results)}")
        
        for i, news in enumerate(results[:2], 1):
            print(f"\n结果 {i}:")
            print(f"  标题: {news.title}")
            print(f"  URL: {news.url}")
            print(f"  来源: {news.source}")
            
    except Exception as e:
        print(f"网站限制搜索失败: {e}")


def test_google_playwright_fallback():
    """测试playwright fallback机制"""
    print("\n\n" + "=" * 60)
    print("测试Playwright fallback机制")
    print("=" * 60)
    
    # 创建一个会失败的requests配置，测试fallback
    google_source = GoogleSearchSource(
        delay=1,
        max_results=3,
        use_requests=True,
        proxy_config={'enabled': True, 'server': 'http://invalid-proxy:9999'}  # 无效代理
    )
    
    try:
        print("使用无效代理测试fallback...")
        results = google_source.fetch_news(keywords=["test"])
        print(f"fallback结果数量: {len(results)}")
        
    except Exception as e:
        print(f"fallback测试失败: {e}")


def compare_requests_vs_playwright():
    """对比requests和playwright方案"""
    print("\n\n" + "=" * 60) 
    print("对比requests vs playwright方案")
    print("=" * 60)
    
    keywords = ["AI technology"]
    
    # 测试requests方案
    print("测试requests方案...")
    google_requests = GoogleSearchSource(delay=1, max_results=3, use_requests=True)
    
    start_time = datetime.now()
    try:
        results_requests = google_requests.fetch_news(keywords=keywords)
        requests_time = (datetime.now() - start_time).total_seconds()
        print(f"requests方案: {len(results_requests)} 条结果, 耗时 {requests_time:.2f} 秒")
    except Exception as e:
        print(f"requests方案失败: {e}")
        results_requests = []
        requests_time = 0
    
    # 测试playwright方案
    print("\n测试playwright方案...")
    google_playwright = GoogleSearchSource(delay=1, max_results=3, use_requests=False)
    
    start_time = datetime.now()
    try:
        results_playwright = google_playwright.fetch_news(keywords=keywords)
        playwright_time = (datetime.now() - start_time).total_seconds()
        print(f"playwright方案: {len(results_playwright)} 条结果, 耗时 {playwright_time:.2f} 秒")
    except Exception as e:
        print(f"playwright方案失败: {e}")
        results_playwright = []
        playwright_time = 0
    
    # 对比结果
    print(f"\n对比结果:")
    print(f"requests:   {len(results_requests)} 条结果, {requests_time:.2f} 秒")
    print(f"playwright: {len(results_playwright)} 条结果, {playwright_time:.2f} 秒")
    
    if requests_time > 0 and playwright_time > 0:
        speed_improvement = ((playwright_time - requests_time) / playwright_time) * 100
        print(f"速度提升: {speed_improvement:.1f}%")


if __name__ == "__main__":
    try:
        test_google_requests()
        test_google_playwright_fallback()
        compare_requests_vs_playwright()
        
        print("\n\n" + "=" * 60)
        print("测试完成")
        print("=" * 60)
        
    except KeyboardInterrupt:
        print("\n测试被用户中断")
    except Exception as e:
        print(f"\n测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()