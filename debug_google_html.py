#!/usr/bin/env python3
"""
调试Google搜索HTML结构
"""
import requests
import random
from bs4 import BeautifulSoup
from urllib.parse import quote_plus

def debug_google_html():
    """调试Google搜索返回的HTML结构"""
    
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ]
    
    headers = {
        "User-Agent": random.choice(user_agents),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Charset": "utf-8, iso-8859-1;q=0.5",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Cache-Control": "max-age=0"
    }
    
    # 测试普通搜索和新闻搜索
    queries = [
        ("trump", "https://www.google.com/search?q=trump&hl=zh-CN"),  # 普通搜索
        ("trump news", "https://www.google.com/search?q=trump&tbm=nws&hl=zh-CN")  # 新闻搜索
    ]
    
    proxies = {'http': 'http://127.0.0.1:7892', 'https': 'http://127.0.0.1:7892'}
    
    for query_name, url in queries:
        print(f"\n{'='*60}")
        print(f"测试: {query_name}")
        print(f"URL: {url}")
        print('='*60)
        
        try:
            response = requests.get(url, headers=headers, proxies=proxies, timeout=30)
            print(f"状态码: {response.status_code}")
            print(f"最终URL: {response.url}")
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # 保存HTML到文件供检查
                filename = f"google_{query_name.replace(' ', '_')}.html"
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(response.text)
                print(f"HTML已保存到: {filename}")
                
                # 分析HTML结构
                print(f"HTML长度: {len(response.text)}")
                
                # 查找各种可能的元素
                elements_to_check = [
                    ('h1', soup.find_all('h1')),
                    ('h2', soup.find_all('h2')),
                    ('h3', soup.find_all('h3')),
                    ('h4', soup.find_all('h4')),
                    ('a[href]', soup.find_all('a', href=True)),
                    ('div[data-ved]', soup.select('div[data-ved]')),
                    ('.g', soup.select('.g')),
                    ('.tF2Cxc', soup.select('.tF2Cxc')),
                    ('article', soup.find_all('article'))
                ]
                
                for element_name, elements in elements_to_check:
                    print(f"{element_name}: {len(elements)} 个")
                    
                    if elements and len(elements) > 0:
                        print(f"  前3个{element_name}的内容:")
                        for i, elem in enumerate(elements[:3], 1):
                            text = elem.get_text(strip=True)[:100]
                            href = elem.get('href', 'N/A') if elem.name == 'a' else 'N/A'
                            print(f"    {i}. {text}... | {href}")
                
                # 检查是否有验证页面标识
                page_text = response.text.lower()
                warnings = []
                if 'captcha' in page_text:
                    warnings.append("检测到CAPTCHA")
                if 'sorry' in page_text:
                    warnings.append("检测到Sorry页面")
                if 'unusual traffic' in page_text:
                    warnings.append("检测到异常流量警告")
                
                if warnings:
                    print(f"⚠️  警告: {', '.join(warnings)}")
                else:
                    print("✅ 页面正常")
                    
        except Exception as e:
            print(f"请求失败: {e}")

if __name__ == "__main__":
    debug_google_html()