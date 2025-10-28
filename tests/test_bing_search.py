#!/usr/bin/env python3
"""
测试Bing搜索接口功能
"""
import sys
import os
from datetime import datetime

# 添加项目路径到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from news_agent.core.data_sources.bing_search import BingSearchSource, BingSearchOptions


def test_bing_search():
    """测试Bing搜索功能"""
    print("=" * 60)
    print("测试Bing搜索接口 - 关键词: 'trump'")
    print("=" * 60)
    
    # 创建Bing搜索实例（不使用API key，使用HTTP备用方案）
    bing_source = BingSearchSource(delay=1, max_results=10)
    
    # 检查服务可用性
    print(f"服务可用性: {bing_source.is_available()}")
    print(f"数据源信息: {bing_source.get_source_info()}")
    print()
    
    # 测试基础搜索
    print("1. 基础搜索测试:")
    print("-" * 40)
    try:
        results = bing_source.fetch_news(keywords=["trump"])
        print(f"搜索结果数量: {len(results)}")
        
        for i, news in enumerate(results[:3], 1):  # 只显示前3个结果
            print(f"\n结果 {i}:")
            print(f"  标题: {news.title}")
            print(f"  URL: {news.url}")
            print(f"  来源: {news.source}")
            print(f"  发布时间: {news.published_date}")
            print(f"  摘要: {news.summary[:100]}...")
            
    except Exception as e:
        print(f"基础搜索失败: {e}")
    
    # 测试高级搜索选项
    print("\n\n2. 高级搜索测试 (限制新闻网站):")
    print("-" * 40)
    try:
        search_options = BingSearchOptions.news_sites(['cnn.com', 'bbc.com', 'reuters.com'])
        results = bing_source.fetch_news(
            keywords=["trump"], 
            search_options=search_options
        )
        print(f"限制网站搜索结果数量: {len(results)}")
        
        for i, news in enumerate(results[:2], 1):  # 只显示前2个结果
            print(f"\n结果 {i}:")
            print(f"  标题: {news.title}")
            print(f"  URL: {news.url}")
            print(f"  来源: {news.source}")
            
    except Exception as e:
        print(f"高级搜索失败: {e}")
    
    # 测试排除词功能
    print("\n\n3. 排除词测试:")
    print("-" * 40)
    try:
        search_options = BingSearchOptions.exclude_terms(['election'])
        results = bing_source.fetch_news(
            keywords=["trump"], 
            search_options=search_options
        )
        print(f"排除'election'词的搜索结果数量: {len(results)}")
        
        for i, news in enumerate(results[:2], 1):
            print(f"\n结果 {i}:")
            print(f"  标题: {news.title}")
            print(f"  是否包含'election': {'election' in news.title.lower()}")
            
    except Exception as e:
        print(f"排除词搜索失败: {e}")


def test_bing_search_with_api():
    """测试使用API key的Bing搜索（如果有的话）"""
    print("\n\n" + "=" * 60)
    print("测试Bing搜索API接口")
    print("=" * 60)
    
    # 尝试从环境变量获取API key
    api_key = os.getenv('BING_SEARCH_API_KEY')
    
    if not api_key:
        print("未找到BING_SEARCH_API_KEY环境变量，跳过API测试")
        print("如需测试API功能，请设置环境变量:")
        print("export BING_SEARCH_API_KEY='your_api_key'")
        return
    
    bing_api_source = BingSearchSource(api_key=api_key, delay=1, max_results=5)
    
    try:
        print("使用API key进行搜索...")
        results = bing_api_source.fetch_news(keywords=["trump"])
        print(f"API搜索结果数量: {len(results)}")
        
        for i, news in enumerate(results, 1):
            print(f"\nAPI结果 {i}:")
            print(f"  标题: {news.title}")
            print(f"  URL: {news.url}")
            print(f"  来源: {news.source}")
            print(f"  发布时间: {news.published_date}")
            
    except Exception as e:
        print(f"API搜索失败: {e}")


if __name__ == "__main__":
    try:
        test_bing_search()
        test_bing_search_with_api()
        
        print("\n\n" + "=" * 60)
        print("测试完成")
        print("=" * 60)
        
    except KeyboardInterrupt:
        print("\n测试被用户中断")
    except Exception as e:
        print(f"\n测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()