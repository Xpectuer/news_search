#!/usr/bin/env python3
"""
调试Bing搜索HTTP请求
"""
import requests
from urllib.parse import quote_plus
import sys
import os

# 添加项目路径到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))


def debug_bing_http_request():
    """调试Bing HTTP请求"""
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json, text/html, */*",
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
        print(f"响应状态码: {response.status_code}")
        print(f"响应头部: {dict(response.headers)}")
        print()
        
        if response.status_code == 200:
            html = response.text
            print(f"HTML内容长度: {len(html)}")
            print("HTML前1000个字符:")
            print("-" * 50)
            print(html[:1000])
            print("-" * 50)
            
            # 检查是否包含新闻相关的关键词
            keywords = ['news-card', 'newsitem', 'cardcommon', 'title', 'href']
            for keyword in keywords:
                count = html.lower().count(keyword.lower())
                print(f"'{keyword}' 出现次数: {count}")
                
        else:
            print(f"请求失败，状态码: {response.status_code}")
            print(f"响应内容: {response.text[:500]}")
            
    except Exception as e:
        print(f"请求异常: {e}")


def test_simple_bing_search():
    """测试简单的Bing搜索页面"""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    }
    
    # 更简单的搜索URL
    query = "trump"
    encoded_query = quote_plus(query)
    search_url = f"https://www.bing.com/search?q={encoded_query}"
    
    print(f"\n测试简单搜索URL: {search_url}")
    
    try:
        response = requests.get(search_url, headers=headers, timeout=30)
        print(f"响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            html = response.text
            print(f"HTML内容长度: {len(html)}")
            
            # 查找常见的搜索结果元素
            import re
            
            # 查找链接和标题
            link_pattern = r'<a[^>]*href="([^"]*)"[^>]*>([^<]*)</a>'
            links = re.findall(link_pattern, html)
            print(f"找到链接数量: {len(links)}")
            
            if links:
                print("前5个链接:")
                for i, (url, title) in enumerate(links[:5], 1):
                    if title.strip() and 'trump' in title.lower():
                        print(f"  {i}. {title.strip()[:50]}...")
                        print(f"     {url[:80]}...")
                        
    except Exception as e:
        print(f"简单搜索异常: {e}")


if __name__ == "__main__":
    debug_bing_http_request()
    test_simple_bing_search()