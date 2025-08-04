#!/usr/bin/env python3
"""
调试Bing英文搜索
"""
import requests
from urllib.parse import quote_plus
from bs4 import BeautifulSoup
import sys
import os

# 添加项目路径到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from news_agent.core.data_sources.bing_search import BingSearchSource


def debug_bing_english_search():
    """调试Bing英文搜索"""
    
    # 创建英文市场的Bing搜索实例
    bing_source = BingSearchSource(market="en-US", delay=1, max_results=10)
    
    print("=== Bing搜索配置信息 ===")
    print(f"市场设置: {bing_source.market}")
    print(f"Accept-Language: {bing_source.headers['Accept-Language']}")
    
    # 手动构建URL看看
    query = "trump"
    encoded_query = quote_plus(query)
    url_params = bing_source._get_url_params(encoded_query)
    search_url = f"https://www.bing.com/news/search?{url_params}"
    
    print(f"\n=== 构建的搜索URL ===")
    print(f"URL: {search_url}")
    
    # 发送请求查看响应
    try:
        response = requests.get(search_url, headers=bing_source.headers, timeout=30)
        print(f"\n=== HTTP响应信息 ===")
        print(f"状态码: {response.status_code}")
        print(f"最终URL: {response.url}")
        
        if response.status_code == 200:
            html = response.text
            soup = BeautifulSoup(html, 'html.parser')
            
            print(f"HTML长度: {len(html)}")
            
            # 查找.title元素
            title_elements = soup.select('.title')
            print(f"\n=== 找到的.title元素 ===")
            print(f"数量: {len(title_elements)}")
            
            for i, elem in enumerate(title_elements[:5], 1):
                link_elem = elem if elem.name == 'a' else elem.find('a', href=True)
                if link_elem:
                    title = link_elem.get_text(strip=True)
                    url = link_elem.get('href', '').strip()
                    print(f"\n{i}. {title[:60]}...")
                    print(f"   URL: {url[:80]}...")
                else:
                    print(f"\n{i}. 无有效链接")
            
            # 查找其他可能的新闻元素
            print(f"\n=== 尝试其他选择器 ===")
            selectors = [
                'div.news-card',
                'div.newsitem', 
                'h3 a',
                'a[href*="http"]'
            ]
            
            for selector in selectors:
                elements = soup.select(selector)
                print(f"{selector}: {len(elements)} 个元素")
                
                if elements and len(elements) > 0:
                    for i, elem in enumerate(elements[:2], 1):
                        text = elem.get_text(strip=True)[:50]
                        href = elem.get('href', 'N/A')[:50]
                        print(f"  {i}. {text}... | {href}...")
                    
    except Exception as e:
        print(f"请求异常: {e}")


def test_different_markets():
    """测试不同市场设置"""
    markets = ['zh-CN', 'en-US', 'en-GB']
    
    for market in markets:
        print(f"\n{'='*60}")
        print(f"测试市场: {market}")
        print('='*60)
        
        bing_source = BingSearchSource(market=market, delay=1, max_results=5)
        
        try:
            results = bing_source.fetch_news(keywords=["trump"])
            print(f"找到新闻数: {len(results)}")
            
            for i, news in enumerate(results[:2], 1):
                print(f"\n{i}. {news.title[:60]}...")
                print(f"   来源: {news.source}")
                print(f"   URL: {news.url[:80]}...")
                
        except Exception as e:
            print(f"搜索失败: {e}")


if __name__ == "__main__":
    debug_bing_english_search()
    test_different_markets()