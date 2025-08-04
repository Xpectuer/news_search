#!/usr/bin/env python3
"""
调试Bing搜索HTML解析
"""
import requests
from urllib.parse import quote_plus
from bs4 import BeautifulSoup
import sys
import os

# 添加项目路径到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))


def debug_bing_news_parsing():
    """调试Bing新闻HTML解析"""
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8"
    }
    
    # 构建搜索URL
    query = "trump news"
    encoded_query = quote_plus(query)
    search_url = f"https://www.bing.com/news/search?q={encoded_query}&qft=interval%3D%227%22&form=PTFTNR"
    
    print(f"请求URL: {search_url}")
    print()
    
    try:
        # 发送请求
        response = requests.get(search_url, headers=headers, timeout=30)
        
        if response.status_code == 200:
            html = response.text
            soup = BeautifulSoup(html, 'html.parser')
            
            print("尝试不同的选择器来找到新闻条目:")
            print("=" * 50)
            
            # 尝试多种选择器
            selectors = [
                'div.news-card',
                'div.newsitem',
                'div[class*="news"]',
                'div[class*="card"]',
                'article',
                '.title',
                'h2 a',
                'h3 a',
                'a[href*="http"]'
            ]
            
            for selector in selectors:
                elements = soup.select(selector)
                print(f"选择器 '{selector}': 找到 {len(elements)} 个元素")
                
                if elements and len(elements) > 0:
                    print("  前3个元素内容:")
                    for i, elem in enumerate(elements[:3], 1):
                        text = elem.get_text(strip=True)[:100]
                        href = elem.get('href', 'N/A')
                        print(f"    {i}. {text}...")
                        if href != 'N/A':
                            print(f"       链接: {href[:60]}...")
                    print()
            
            # 尝试查找所有包含链接和文本的元素
            print("\n查找所有包含链接的元素:")
            print("-" * 30)
            
            all_links = soup.find_all('a', href=True)
            news_links = []
            
            for link in all_links:
                href = link.get('href', '')
                text = link.get_text(strip=True)
                
                # 过滤出可能是新闻链接的元素
                if (text and len(text) > 10 and 
                    ('http' in href or href.startswith('/')) and
                    'trump' in text.lower()):
                    news_links.append((text, href))
            
            print(f"找到 {len(news_links)} 个可能的新闻链接:")
            for i, (text, href) in enumerate(news_links[:5], 1):
                print(f"{i}. {text[:80]}...")
                print(f"   {href[:80]}...")
                print()
                
        else:
            print(f"请求失败，状态码: {response.status_code}")
            
    except Exception as e:
        print(f"请求异常: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    debug_bing_news_parsing()