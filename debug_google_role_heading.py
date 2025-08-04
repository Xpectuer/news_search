#!/usr/bin/env python3
"""
调试Google搜索role="heading"属性解析
"""
import requests
import random
from bs4 import BeautifulSoup
from urllib.parse import quote_plus

def debug_role_heading():
    """调试role='heading'属性的解析"""
    
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ]
    
    headers = {
        "User-Agent": random.choice(user_agents),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Cache-Control": "max-age=0",
        "DNT": "1"
    }
    
    # 测试新闻搜索
    query = "trump"
    encoded_query = quote_plus(query)
    search_url = f"https://www.google.com/search?q={encoded_query}&tbm=nws&hl=en&gl=us"
    
    print(f"测试URL: {search_url}")
    print("="*60)
    
    proxies = {'http': 'http://127.0.0.1:7892', 'https': 'http://127.0.0.1:7892'}
    
    try:
        response = requests.get(search_url, headers=headers, proxies=proxies, timeout=30)
        print(f"状态码: {response.status_code}")
        print(f"最终URL: {response.url}")
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 查找role="heading"元素
            heading_elements = soup.find_all(attrs={"role": "heading"})
            print(f"\n找到 {len(heading_elements)} 个role='heading'元素")
            
            if heading_elements:
                for i, heading in enumerate(heading_elements[:5], 1):  # 只看前5个
                    print(f"\n--- Heading {i} ---")
                    title = heading.get_text(strip=True)
                    print(f"标题: {title}")
                    print(f"标签: {heading.name}")
                    print(f"属性: {dict(heading.attrs)}")
                    
                    # 查找链接
                    url = ""
                    if heading.name == 'a' and heading.get('href'):
                        url = heading.get('href')
                        print(f"自身链接: {url}")
                    else:
                        # 查找内部链接
                        inner_link = heading.find('a', href=True)
                        if inner_link:
                            url = inner_link.get('href')
                            print(f"内部链接: {url}")
                        else:
                            # 查找父级链接
                            parent = heading.find_parent('a', href=True)
                            if parent:
                                url = parent.get('href')
                                print(f"父级链接: {url}")
                            else:
                                # 查找容器中的链接
                                container = heading.find_parent(['div', 'article', 'section'])
                                if container:
                                    nearby_links = container.find_all('a', href=True)
                                    for link in nearby_links:
                                        href = link.get('href', '')
                                        if href.startswith('http') or href.startswith('/url?q='):
                                            url = href
                                            print(f"容器链接: {url}")
                                            break
                    
                    # 查找摘要
                    container = heading.find_parent(['div', 'article', 'section'])
                    if container:
                        print(f"容器标签: {container.name}")
                        
                        # 查找兄弟元素中的文本
                        siblings = container.find_all(['div', 'span', 'p'])
                        print(f"兄弟元素数量: {len(siblings)}")
                        
                        for j, sibling in enumerate(siblings[:3]):  # 只看前3个兄弟元素
                            text = sibling.get_text(strip=True)
                            if len(text) > 20:
                                print(f"  兄弟元素{j+1}: {text[:100]}...")
                    
                    print("-" * 50)
            
            # 额外检查：查找所有可能的新闻相关元素
            print(f"\n=== 额外检查 ===")
            
            # 检查其他可能的标题元素
            other_selectors = [
                'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
                '[role="link"]',
                'a[href*="http"]',
                'div[data-ved]',
                '.g', '.tF2Cxc'
            ]
            
            for selector in other_selectors:
                elements = soup.select(selector)
                if elements:
                    print(f"{selector}: {len(elements)} 个")
                    if selector == 'a[href*="http"]':
                        # 显示前几个外部链接
                        for i, elem in enumerate(elements[:3], 1):
                            href = elem.get('href', '')
                            text = elem.get_text(strip=True)[:50]
                            print(f"  {i}. {text}... -> {href[:60]}...")
                            
        else:
            print(f"请求失败，状态码: {response.status_code}")
            
    except Exception as e:
        print(f"请求异常: {e}")


if __name__ == "__main__":
    debug_role_heading()