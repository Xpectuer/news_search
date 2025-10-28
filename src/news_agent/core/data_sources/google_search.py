import asyncio
import re
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from urllib.parse import quote_plus, urljoin
import random
import sys
import requests

from playwright.async_api import async_playwright
from bs4 import BeautifulSoup

from .base import DataSource, NewsItem


class GoogleSearchSource(DataSource):
    """基于Playwright的Google搜索数据源
    
    支持Google高级搜索语法：
    - site:example.com - 限制搜索域名
    - intitle:"关键词" - 标题中包含关键词
    - inurl:关键词 - URL中包含关键词
    - "精确匹配" - 精确短语匹配
    - 关键词1 OR 关键词2 - 或关系
    - 关键词1 -排除词 - 排除特定词
    - after:2023-01-01 - 指定日期之后
    - before:2023-12-31 - 指定日期之前
    """
    
    def __init__(self, delay: int = 3, max_results: int = 50, headless: bool = True, 
                 proxy_config: Dict[str, Any] = None, use_requests: bool = True):
        super().__init__("Google Search")
        self.delay = delay  # 请求间隔，避免被封
        self.max_results = max_results
        self.headless = headless
        self.proxy_config = proxy_config or {}
        self.use_requests = use_requests  # 优先使用requests，失败时fallback到playwright
        
        # 用户代理池，模拟真实浏览器
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15"
        ]
    
    def fetch_news(self, keywords: List[str] = None, **kwargs) -> List[NewsItem]:
        """获取新闻数据"""
        if not keywords:
            return []
        
        # 构建搜索查询
        search_options = kwargs.get('search_options', {})
        query = self._build_search_query(keywords, search_options)
        
        if self.use_requests:
            try:
                # 优先使用requests方案
                print("使用requests方式进行Google搜索...")
                return self._search_with_requests(query)
            except Exception as e:
                print(f"requests搜索失败，fallback到playwright: {e}", file=sys.stderr)
                # fallback到playwright
                try:
                    return asyncio.run(self._search_async(query))
                except Exception as e2:
                    print(f"playwright搜索也失败: {e2}", file=sys.stderr)
                    return []
        else:
            try:
                # 直接使用playwright方案
                return asyncio.run(self._search_async(query))
            except Exception as e:
                print(f"Google搜索失败: {e}", file=sys.stderr)
                return []
    
    def _build_search_query(self, keywords: List[str], options: Dict[str, Any]) -> str:
        """构建Google搜索查询语句"""
        query_parts = []
        
        # 基础关键词
        for keyword in keywords:
            if keyword.strip():
                query_parts.append(keyword.strip())
        
        base_query = " ".join(query_parts)
        
        # 添加高级搜索选项
        advanced_parts = []
        
        # 网站限制
        if 'site' in options:
            sites = options['site'] if isinstance(options['site'], list) else [options['site']]
            site_queries = [f"site:{site}" for site in sites]
            if len(site_queries) == 1:
                advanced_parts.append(site_queries[0])
            else:
                advanced_parts.append(f"({' OR '.join(site_queries)})")
        
        # 日期限制
        if 'after' in options:
            advanced_parts.append(f"after:{options['after']}")
        if 'before' in options:
            advanced_parts.append(f"before:{options['before']}")
        
        # 标题限制
        if 'intitle' in options:
            titles = options['intitle'] if isinstance(options['intitle'], list) else [options['intitle']]
            for title in titles:
                advanced_parts.append(f'intitle:"{title}"')
        
        # URL限制
        if 'inurl' in options:
            urls = options['inurl'] if isinstance(options['inurl'], list) else [options['inurl']]
            for url in urls:
                advanced_parts.append(f"inurl:{url}")
        
        # 文件类型限制
        if 'filetype' in options:
            advanced_parts.append(f"filetype:{options['filetype']}")
        
        # 排除词
        if 'exclude' in options:
            excludes = options['exclude'] if isinstance(options['exclude'], list) else [options['exclude']]
            for exclude in excludes:
                advanced_parts.append(f"-{exclude}")
        
        # 组合查询
        if advanced_parts:
            full_query = f"{base_query} {' '.join(advanced_parts)}"
        else:
            full_query = base_query
        
        return full_query.strip()
    
    def _get_requests_headers(self) -> Dict[str, str]:
        """获取requests使用的请求头"""
        return {
            "User-Agent": random.choice(self.user_agents),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",  # 英文优先
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Cache-Control": "max-age=0",
            "DNT": "1"  # Do Not Track
        }
    
    def _get_requests_proxies(self) -> Dict[str, str]:
        """获取requests使用的代理配置"""
        if not self.proxy_config.get('enabled', False) or not self.proxy_config.get('server'):
            return {}
        
        proxy_server = self.proxy_config['server']
        username = self.proxy_config.get('username')
        password = self.proxy_config.get('password')
        
        # 如果有用户名密码，添加到URL中
        if username and password:
            if '://' in proxy_server:
                protocol, server_part = proxy_server.split('://', 1)
                proxy_url = f"{protocol}://{username}:{password}@{server_part}"
            else:
                proxy_url = f"http://{username}:{password}@{proxy_server}"
        else:
            proxy_url = proxy_server
        
        return {
            'http': proxy_url,
            'https': proxy_url
        }
    
    def _search_with_requests(self, query: str) -> List[NewsItem]:
        """使用requests进行Google搜索"""
        results = []
        
        headers = self._get_requests_headers()
        proxies = self._get_requests_proxies()
        
        session = requests.Session()
        session.headers.update(headers)
        session.proxies.update(proxies)
        
        try:
            page_num = 0
            while len(results) < self.max_results and page_num < 5:  # 最多5页
                search_url = self._build_search_url(query, page_num * 10)
                print(f"正在抓取第{page_num + 1}页: {search_url}")
                
                try:
                    response = session.get(search_url, timeout=30)
                    response.raise_for_status()
                    
                    # 检查是否被重定向到验证页面
                    if "sorry" in response.url.lower() or "captcha" in response.url.lower():
                        print("[WARNING] 检测到验证页面，请检查代理设置或稍后重试")
                        break
                    
                    # 解析HTML
                    soup = BeautifulSoup(response.text, 'html.parser')
                    page_results = self._parse_google_html(soup)
                    
                    if not page_results:
                        print(f"第{page_num + 1}页未找到结果")
                        break
                    
                    results.extend(page_results)
                    print(f"第{page_num + 1}页找到 {len(page_results)} 条结果")
                    
                    page_num += 1
                    
                    # 随机延时避免被封
                    if page_num < 5:  # 最后一页不延时
                        delay_time = self.delay + random.uniform(0.5, 2.0)
                        print(f"等待 {delay_time:.1f} 秒...")
                        time.sleep(delay_time)
                    
                except requests.exceptions.RequestException as e:
                    print(f"第{page_num + 1}页请求失败: {e}")
                    break
                    
        except Exception as e:
            print(f"requests搜索出错: {e}")
            
        return results[:self.max_results]
    
    def _parse_google_html(self, soup: BeautifulSoup) -> List[NewsItem]:
        """解析Google搜索结果HTML，使用role='heading'属性定位标题"""
        results = []
        
        heading_elements = []
        
        # 查找所有带有role="heading"属性的元素
        heading_elements.extend(soup.find_all(attrs={"role": "heading"}))
        
        print(f"找到 {len(heading_elements)} 个role='heading'元素")
        # 查找所有h3标签元素
        heading_elements.extend(soup.find_all('h3'))
        print(f"找到 {len(heading_elements)} 个h3元素")
        
        # find class ="LC20lb MBeuO DKV0Md"
        heading_elements.extend(soup.find_all(class_="LC20lb MBeuO DKV0Md"))
        
        for heading in heading_elements:
            try:
                # 获取标题文本
                title = heading.get_text(strip=True)
                if not title or len(title) < 5:
                    continue
                
                print(f"处理标题: {title[:50]}...")
                
                # 查找链接 - 先在heading元素本身查找
                link_element = None
                url = ""
                
                # 方法1: heading元素本身是链接
                if heading.name == 'a' and heading.get('href'):
                    link_element = heading
                    url = heading.get('href')
                
                # 方法2: heading内部包含链接
                if not link_element:
                    inner_link = heading.find('a', href=True)
                    if inner_link:
                        link_element = inner_link
                        url = inner_link.get('href')
                
                # 方法3: heading的父元素是链接
                if not link_element:
                    parent = heading.find_parent('a', href=True)
                    if parent:
                        link_element = parent
                        url = parent.get('href')
                
                # 方法4: 在同级或附近元素中查找链接
                if not link_element:
                    # 查找包含此heading的容器
                    container = heading.find_parent(['div', 'article', 'section'])
                    if container:
                        # 在容器中查找第一个有效链接
                        nearby_links = container.find_all('a', href=True)
                        for link in nearby_links:
                            href = link.get('href', '')
                            if href.startswith('http') or href.startswith('/url?q='):
                                link_element = link
                                url = href
                                break
                
                if not url:
                    print(f"  未找到链接，跳过")
                    continue
                
                # 清理Google重定向URL
                if url.startswith('/url?q='):
                    import urllib.parse
                    try:
                        url = urllib.parse.unquote(url.split('/url?q=')[1].split('&')[0])
                    except:
                        continue
                elif url.startswith('/search') or url.startswith('#') or 'google.com' in url:
                    print(f"  跳过内部链接: {url[:50]}")
                    continue
                
                if not url.startswith('http'):
                    print(f"  无效URL: {url[:50]}")
                    continue
                
                print(f"  找到URL: {url[:60]}...")
                
                # 查找摘要内容 - 在兄弟元素中查找
                summary = ""
                container = heading.find_parent(['div', 'article', 'section'])
                if container:
                    # 查找描述性文本，通常在heading之后的兄弟元素中
                    siblings = list(container.find_all(['div', 'span', 'p']))
                    
                    for sibling in siblings:
                        text = sibling.get_text(strip=True)
                        # 筛选合适的摘要文本
                        if (len(text) > 30 and len(text) < 500 and 
                            text != title and 
                            not text.startswith('http') and
                            '...' in text or len(text.split()) > 5):
                            summary = text
                            break
                    
                    # 如果还没有找到摘要，尝试查找任何包含足够文本的元素
                    if not summary:
                        all_text_elements = container.find_all(string=True)
                        for text_node in all_text_elements:
                            text = text_node.strip()
                            if (len(text) > 20 and len(text) < 300 and 
                                text != title and
                                not any(skip_word in text.lower() for skip_word in ['google', 'search', 'click', '搜索'])):
                                summary = text
                                break
                
                # 尝试提取来源信息 - 在兄弟元素中查找
                source = "Google News"
                if container:
                    # 查找包含域名或时间信息的元素
                    source_elements = container.find_all(['span', 'div', 'cite'])
                    for elem in source_elements:
                        text = elem.get_text(strip=True)
                        # 检查是否像是来源信息
                        if (len(text) > 3 and len(text) < 100 and
                            (any(domain in text.lower() for domain in ['.com', '.org', '.net', '.cn', '.co.uk']) or
                             any(time_word in text.lower() for time_word in ['ago', 'hours', 'minutes', '小时', '分钟']))):
                            source = text
                            break
                
                print(f"  摘要: {summary[:50]}...")
                print(f"  来源: {source}")
                
                # 创建NewsItem
                news_item = NewsItem(
                    title=title,
                    content=summary,
                    url=url,
                    published_date=datetime.now(),
                    source=source,
                    summary=summary[:200] + "..." if len(summary) > 200 else summary,
                    keywords=[]
                )
                
                results.append(news_item)
                
            except Exception as e:
                print(f"解析role='heading'元素时出错: {e}")
                continue
        
        print(f"成功解析 {len(results)} 条新闻")
        return results
    
    async def _search_async(self, query: str) -> List[NewsItem]:
        """异步执行Google搜索"""
        async with async_playwright() as p:
            # 启动浏览器 - 不在启动参数中设置代理，避免冲突
            launch_args = [
                '--no-sandbox',
                '--disable-blink-features=AutomationControlled',
                '--disable-web-security',
                '--disable-features=VizDisplayCompositor'
            ]
            
            browser = await p.chromium.launch(
                headless=self.headless,
                args=launch_args
            )
            
            try:
                # 创建浏览器上下文
                context_options = {
                    'user_agent': random.choice(self.user_agents),
                    'viewport': {'width': 1920, 'height': 1080}
                }
                
                # 添加代理配置
                if self.proxy_config.get('enabled') and self.proxy_config.get('server'):
                    proxy_config = {'server': self.proxy_config['server']}
                    if self.proxy_config.get('username') and self.proxy_config.get('password'):
                        proxy_config.update({
                            'username': self.proxy_config['username'],
                            'password': self.proxy_config['password']
                        })
                    context_options['proxy'] = proxy_config
                
                context = await browser.new_context(**context_options)
                page = await context.new_page()
                
                # 设置额外的反检测措施
                await page.add_init_script("""
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined,
                    });
                """)
                
                results = []
                page_num = 0
                
                while len(results) < self.max_results and page_num < 5:  # 最多爬5页
                    try:
                        # 构建搜索URL
                        search_url = self._build_search_url(query, page_num * 10)
                        print(f"正在访问页面: {search_url}")
                        # 访问搜索页面，添加重试机制
                        retry_count = 0
                        max_retries = 3
                        page_loaded = False
                        
                        while retry_count < max_retries and not page_loaded:
                            try:
                                await page.goto(search_url, wait_until='networkidle', timeout=60000)
                                print(f"页面{page_num} 已加载")
                                page_loaded = True
                            except Exception as e:
                                retry_count += 1
                                if retry_count < max_retries:
                                    await asyncio.sleep(2 + retry_count)  # 递增延时
                                else:
                                    break
                        
                        if not page_loaded:
                            page_num += 1
                            continue
                        
                        # 检查是否被重定向到验证页面
                        current_url = page.url
                        if "sorry" in current_url.lower() or "captcha" in current_url.lower():
                            print("[WARNING] 检测到验证页面，请检查代理设置。")
                            break
                        
                        # 等待搜索结果加载，尝试多个选择器
                        result_loaded = False
                        selectors_to_try = [
                            # 'div[data-ved]',  # 主要结果容器
                            'h3',  # 标题元素
                            # '.g',  # Google结果类
                            # '[data-content-feature]'  # 内容特征
                        ]
                        
                        for selector in selectors_to_try:
                            try:
                                await page.wait_for_selector(selector, timeout=30000)
                                result_loaded = True
                                break
                            except:
                                continue
                        
                        if not result_loaded:
                            pass  # 尝试继续解析已有内容
                        
                        # 解析搜索结果
                        page_results = await self._parse_search_results(page)
                        
                        if not page_results:
                            break
                        
                        results.extend(page_results)
                        page_num += 1
                        
                        # 随机延时，避免被检测
                        delay_time = self.delay + random.uniform(0.5, 2.0)
                        await asyncio.sleep(delay_time)
                        
                    except Exception as e:
                        break
                
                return results[:self.max_results]
                
            finally:
                await browser.close()
    
    def _build_search_url(self, query: str, start: int = 0) -> str:
        """构建Google搜索URL"""
        encoded_query = quote_plus(query)
        base_url = "https://www.google.com/search"
        params = [
            f"q={encoded_query}",
            f"start={start}",
            "tbm=nws",  # 搜索新闻
            "hl=en",  # 英文界面，避免重定向
            "gl=us"  # 美国地区
        ]
        return f"{base_url}?{'&'.join(params)}"
    
    async def _parse_search_results(self, page) -> List[NewsItem]:
        """解析Google搜索结果页面"""
        results = []
        
        # 获取页面HTML
        html = await page.content()
        soup = BeautifulSoup(html, 'html.parser')
        
        # 查找新闻结果，尝试多种选择器
        news_items = []
        
        # 尝试不同的结果选择器
        selectors = [
            'div[data-ved]',  # 主要结果
            '.g',  # 通用Google结果
            'article',  # 文章元素
            '.tF2Cxc'  # 新版Google结果
        ]
        
        for selector in selectors:
            items = soup.select(selector)
            if items:
                news_items = items
                break
        
        if not news_items:
            # 如果都找不到，尝试最宽泛的选择器
            news_items = soup.find_all('div')
        
        for item in news_items:
            try:
                # 提取标题和链接
                title_element = item.find('h3')
                if not title_element:
                    continue
                
                title = title_element.get_text(strip=True)
                if not title:
                    continue
                
                # 查找链接
                link_element = item.find('a', href=True)
                if not link_element:
                    continue
                
                url = link_element['href']
                if url.startswith('/url?q='):
                    # 提取真实URL
                    url = url.split('/url?q=')[1].split('&')[0]
                
                # 提取摘要
                summary_element = item.find('span', {'data-ved': True})
                summary = ""
                if summary_element:
                    summary = summary_element.get_text(strip=True)
                
                # 提取来源和日期
                source = "Google News"
                published_date = datetime.now()
                
                # 尝试提取更详细的来源信息
                source_elements = item.find_all('span')
                for span in source_elements:
                    text = span.get_text(strip=True)
                    if any(domain in text.lower() for domain in ['.com', '.org', '.net', '.cn']):
                        source = text
                        break
                
                # 创建NewsItem
                news_item = NewsItem(
                    title=title,
                    content=summary,
                    url=url,
                    published_date=published_date,
                    source=source,
                    summary=summary[:200] + "..." if len(summary) > 200 else summary,
                    keywords=[]
                )
                
                results.append(news_item)
                
            except Exception as e:
                continue
        
        return results
    
    def is_available(self) -> bool:
        """检查Google搜索是否可用"""
        try:
            # 简单的连通性检测
            import socket
            socket.create_connection(("www.google.com", 80), timeout=5)
            return True
        except:
            return False
    
    def get_source_info(self) -> Dict[str, Any]:
        """获取数据源信息"""
        info = super().get_source_info()
        info.update({
            'delay': self.delay,
            'max_results': self.max_results,
            'headless': self.headless,
            'supported_options': [
                'site', 'after', 'before', 'intitle', 
                'inurl', 'filetype', 'exclude'
            ]
        })
        return info


class GoogleSearchOptions:
    """Google搜索选项辅助类"""
    
    @staticmethod
    def news_sites(sites: List[str]) -> Dict[str, Any]:
        """限制搜索新闻网站"""
        return {'site': sites}
    
    @staticmethod
    def date_range(after: str = None, before: str = None) -> Dict[str, Any]:
        """设置日期范围 (格式: YYYY-MM-DD)"""
        options = {}
        if after:
            options['after'] = after
        if before:
            options['before'] = before
        return options
    
    @staticmethod
    def recent_days(days: int) -> Dict[str, Any]:
        """搜索最近N天的内容"""
        after_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        return {'after': after_date}
    
    @staticmethod
    def exclude_terms(terms: List[str]) -> Dict[str, Any]:
        """排除特定词汇"""
        return {'exclude': terms}
    
    @staticmethod
    def title_contains(terms: List[str]) -> Dict[str, Any]:
        """标题必须包含特定词汇"""
        return {'intitle': terms}