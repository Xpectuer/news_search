import requests
import json
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from urllib.parse import quote_plus
import re

from .base import DataSource, NewsItem


class BingSearchSource(DataSource):
    """基于Bing搜索API的新闻数据源
    
    支持Bing搜索语法：
    - site:example.com - 限制搜索域名
    - intitle:"关键词" - 标题中包含关键词
    - "精确匹配" - 精确短语匹配
    - 关键词1 OR 关键词2 - 或关系
    - 关键词1 -排除词 - 排除特定词
    """
    
    def __init__(self, api_key: str = None, delay: int = 1, max_results: int = 50, 
                 market: str = "zh-CN", safe_search: str = "Moderate", 
                 proxy_config: Dict[str, Any] = None):
        super().__init__("Bing Search")
        self.api_key = api_key
        self.delay = delay
        self.max_results = max_results
        self.market = market  # 市场设置，影响搜索结果的语言和地区
        self.safe_search = safe_search  # Off, Moderate, Strict
        self.proxy_config = proxy_config or {}  # 代理配置
        
        # Bing搜索API端点
        self.search_url = "https://api.bing.microsoft.com/v7.0/search"
        self.news_search_url = "https://api.bing.microsoft.com/v7.0/news/search"
        
        # HTTP请求头 - 根据市场设置动态调整语言
        accept_language = self._get_accept_language_header()
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json",
            "Accept-Language": accept_language
        }
        
        if self.api_key:
            self.headers["Ocp-Apim-Subscription-Key"] = self.api_key
    
    def _get_accept_language_header(self) -> str:
        """根据市场设置生成Accept-Language头"""
        if self.market.startswith('zh'):
            return "zh-CN,zh;q=0.9,en;q=0.8"
        elif self.market.startswith('en'):
            return "en-US,en;q=0.9"
        elif self.market.startswith('ja'):
            return "ja-JP,ja;q=0.9,en;q=0.8"
        elif self.market.startswith('ko'):
            return "ko-KR,ko;q=0.9,en;q=0.8"
        elif self.market.startswith('fr'):
            return "fr-FR,fr;q=0.9,en;q=0.8"
        elif self.market.startswith('de'):
            return "de-DE,de;q=0.9,en;q=0.8"
        else:
            return "en-US,en;q=0.9"
    
    def _get_url_params(self, encoded_query: str) -> str:
        """根据市场设置生成URL参数"""
        params = [
            f"q={encoded_query}",
            "qft=interval%3D%227%22",  # 最近7天
            "form=PTFTNR"
        ]
        
        # 根据市场设置添加语言和地区参数
        if self.market.startswith('zh'):
            params.extend([
                "cc=CN",  # 国家/地区
                "setlang=zh-CN"  # 界面语言
            ])
        elif self.market.startswith('en-US'):
            params.extend([
                "cc=US",
                "setlang=en-US"
            ])
        elif self.market.startswith('en-GB'):
            params.extend([
                "cc=GB", 
                "setlang=en-GB"
            ])
        elif self.market.startswith('ja'):
            params.extend([
                "cc=JP",
                "setlang=ja-JP"
            ])
        elif self.market.startswith('ko'):
            params.extend([
                "cc=KR",
                "setlang=ko-KR"
            ])
        elif self.market.startswith('fr'):
            params.extend([
                "cc=FR",
                "setlang=fr-FR"
            ])
        elif self.market.startswith('de'):
            params.extend([
                "cc=DE",
                "setlang=de-DE"
            ])
        else:
            # 默认英文
            params.extend([
                "cc=US",
                "setlang=en-US"
            ])
        
        return "&".join(params)
    
    def _get_proxies(self) -> Dict[str, str]:
        """获取requests库使用的代理配置"""
        if not self.proxy_config.get('enabled', False) or not self.proxy_config.get('server'):
            return {}
        
        proxy_server = self.proxy_config['server']
        username = self.proxy_config.get('username')
        password = self.proxy_config.get('password')
        
        # 如果有用户名密码，添加到URL中
        if username and password:
            # 解析代理服务器URL
            if '://' in proxy_server:
                protocol, server_part = proxy_server.split('://', 1)
                proxy_url = f"{protocol}://{username}:{password}@{server_part}"
            else:
                proxy_url = f"http://{username}:{password}@{proxy_server}"
        else:
            proxy_url = proxy_server
        
        # requests库的代理格式
        return {
            'http': proxy_url,
            'https': proxy_url
        }
    
    def fetch_news(self, keywords: List[str] = None, **kwargs) -> List[NewsItem]:
        """获取新闻数据"""
        if not keywords:
            return []
        
        # 构建搜索查询
        search_options = kwargs.get('search_options', {})
        query = self._build_search_query(keywords, search_options)
        
        try:
            if self.api_key:
                # 使用官方API
                return self._search_with_api(query)
            else:
                # 使用HTTP请求方式（备用方案）
                return self._search_with_http(query)
        except Exception as e:
            print(f"Bing搜索失败: {e}")
            return []
    
    def _build_search_query(self, keywords: List[str], options: Dict[str, Any]) -> str:
        """构建Bing搜索查询语句"""
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
        
        # 标题限制
        if 'intitle' in options:
            titles = options['intitle'] if isinstance(options['intitle'], list) else [options['intitle']]
            for title in titles:
                advanced_parts.append(f'intitle:"{title}"')
        
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
    
    def _search_with_api(self, query: str) -> List[NewsItem]:
        """使用Bing官方API搜索新闻"""
        results = []
        offset = 0
        
        while len(results) < self.max_results:
            params = {
                'q': query,
                'mkt': self.market,
                'safeSearch': self.safe_search,
                'count': min(50, self.max_results - len(results)),  # 每次最多50条
                'offset': offset,
                'sortBy': 'Date',  # 按日期排序
                'freshness': 'Week'  # 最近一周的新闻
            }
            
            try:
                # 获取代理配置
                proxies = self._get_proxies()
                response = requests.get(
                    self.news_search_url, 
                    headers=self.headers, 
                    params=params,
                    proxies=proxies,
                    timeout=30
                )
                response.raise_for_status()
                
                data = response.json()
                news_items = data.get('value', [])
                
                if not news_items:
                    break
                
                for item in news_items:
                    try:
                        # 解析发布时间
                        published_date = datetime.now()
                        if 'datePublished' in item:
                            try:
                                published_date = datetime.fromisoformat(
                                    item['datePublished'].replace('Z', '+00:00')
                                ).replace(tzinfo=None)
                            except:
                                pass
                        
                        # 提取关键信息
                        title = item.get('name', '').strip()
                        description = item.get('description', '').strip()
                        url = item.get('url', '').strip()
                        
                        if not title or not url:
                            continue
                        
                        # 提取来源
                        source = "Bing News"
                        if 'provider' in item and item['provider']:
                            provider = item['provider'][0] if isinstance(item['provider'], list) else item['provider']
                            source = provider.get('name', source)
                        
                        # 创建NewsItem
                        news_item = NewsItem(
                            title=title,
                            content=description,
                            url=url,
                            published_date=published_date,
                            source=source,
                            summary=description[:200] + "..." if len(description) > 200 else description,
                            keywords=[]
                        )
                        
                        results.append(news_item)
                        
                    except Exception as e:
                        continue
                
                offset += len(news_items)
                
                # 延时避免过于频繁的请求
                if self.delay > 0:
                    time.sleep(self.delay)
                
            except requests.exceptions.RequestException as e:
                print(f"Bing API请求失败: {e}")
                break
        
        return results[:self.max_results]
    
    def _search_with_http(self, query: str) -> List[NewsItem]:
        """使用HTTP请求方式搜索（无API key时的备用方案）"""
        results = []
        
        try:
            # 构建搜索URL - 使用新闻搜索，根据市场设置调整语言参数
            encoded_query = quote_plus(query)
            url_params = self._get_url_params(encoded_query)
            search_url = f"https://www.bing.com/news/search?{url_params}"
            
            # 发送请求（使用代理配置）
            proxies = self._get_proxies()
            response = requests.get(
                search_url, 
                headers=self.headers, 
                proxies=proxies, 
                timeout=30
            )
            response.raise_for_status()
            
            # 使用BeautifulSoup解析HTML
            from bs4 import BeautifulSoup
            html = response.text
            soup = BeautifulSoup(html, 'html.parser')
            
            # 查找新闻条目 - 基于调试结果使用.title选择器
            news_items = soup.select('.title')
            
            for item in news_items[:self.max_results]:
                try:
                    # 获取链接元素
                    link_elem = item if item.name == 'a' else item.find('a', href=True)
                    if not link_elem:
                        continue
                    
                    # 提取标题和URL
                    title = link_elem.get_text(strip=True)
                    url = link_elem.get('href', '').strip()
                    
                    if not title or not url or len(title) < 5:
                        continue
                    
                    # 查找父级元素获取更多信息
                    parent_item = item.find_parent('div', class_=['news-card', 'newsitem'])
                    
                    # 提取摘要/描述
                    summary = ""
                    if parent_item:
                        # 查找描述元素
                        desc_elem = parent_item.find('div', class_=['snippet', 'content'])
                        if not desc_elem:
                            # 尝试其他可能的描述元素
                            desc_elem = parent_item.find('p')
                        if desc_elem:
                            summary = desc_elem.get_text(strip=True)
                    
                    # 提取来源信息
                    source = "Bing News"
                    if parent_item:
                        source_elem = parent_item.find('span', class_=['source', 'attribution'])
                        if source_elem:
                            source = source_elem.get_text(strip=True)
                    
                    # 提取时间信息
                    published_date = datetime.now()
                    if parent_item:
                        time_elem = parent_item.find('span', class_=['time', 'timestamp'])
                        if time_elem:
                            time_text = time_elem.get_text(strip=True)
                            # 简单的时间解析
                            if '小时' in time_text:
                                try:
                                    hours = int(time_text.split('小时')[0].strip())
                                    published_date = datetime.now() - timedelta(hours=hours)
                                except:
                                    pass
                    
                    # 创建NewsItem
                    news_item = NewsItem(
                        title=title,
                        content=summary if summary else title,
                        url=url,
                        published_date=published_date,
                        source=source,
                        summary=summary[:200] + "..." if len(summary) > 200 else summary,
                        keywords=[]
                    )
                    
                    results.append(news_item)
                    
                except Exception as e:
                    continue
            
        except Exception as e:
            print(f"Bing HTTP搜索失败: {e}")
        
        return results
    
    def is_available(self) -> bool:
        """检查Bing搜索是否可用"""
        try:
            # 获取代理配置
            proxies = self._get_proxies()
            
            if self.api_key:
                # 测试API连接
                test_params = {
                    'q': 'test',
                    'count': 1,
                    'mkt': self.market
                }
                response = requests.get(
                    self.news_search_url, 
                    headers=self.headers, 
                    params=test_params,
                    proxies=proxies,
                    timeout=10
                )
                return response.status_code == 200
            else:
                # 测试HTTP连接
                response = requests.get(
                    "https://www.bing.com", 
                    proxies=proxies, 
                    timeout=10
                )
                return response.status_code == 200
        except:
            return False
    
    def get_source_info(self) -> Dict[str, Any]:
        """获取数据源信息"""
        info = super().get_source_info()
        info.update({
            'has_api_key': bool(self.api_key),
            'delay': self.delay,
            'max_results': self.max_results,
            'market': self.market,
            'safe_search': self.safe_search,
            'proxy_enabled': self.proxy_config.get('enabled', False),
            'proxy_server': self.proxy_config.get('server', None),
            'supported_options': [
                'site', 'intitle', 'exclude'
            ]
        })
        return info


class BingSearchOptions:
    """Bing搜索选项辅助类"""
    
    @staticmethod
    def news_sites(sites: List[str]) -> Dict[str, Any]:
        """限制搜索新闻网站"""
        return {'site': sites}
    
    @staticmethod
    def exclude_terms(terms: List[str]) -> Dict[str, Any]:
        """排除特定词汇"""
        return {'exclude': terms}
    
    @staticmethod
    def title_contains(terms: List[str]) -> Dict[str, Any]:
        """标题必须包含特定词汇"""
        return {'intitle': terms}
    
    @staticmethod
    def combine_options(*options_list: Dict[str, Any]) -> Dict[str, Any]:
        """组合多个搜索选项"""
        combined = {}
        for options in options_list:
            combined.update(options)
        return combined