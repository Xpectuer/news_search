import feedparser
from typing import List, Dict, Any, Optional
from datetime import datetime
import time
import re
import html
import requests
from urllib.parse import urlparse
import socket

from .base import DataSource, NewsItem


class RSSSource(DataSource):
    def __init__(self, rss_urls: List[str], timeout: int = 30, max_retries: int = 3):
        super().__init__("RSS")
        self.rss_urls = rss_urls
        self.timeout = timeout
        self.max_retries = max_retries
    
    def fetch_news(self, keywords: List[str] = None, **kwargs) -> List[NewsItem]:
        all_news = []
        
        for url in self.rss_urls:
            try:
                news_items = self._fetch_from_url(url, keywords)
                all_news.extend(news_items)
            except Exception as e:
                print(f"警告: 无法获取RSS源 {url} 的数据: {e}")
                continue
        
        # 去重 - 使用set自动去重，依赖NewsItem的__hash__和__eq__方法
        unique_news = list(set(all_news))
        
        # 如果需要更精确的去重，使用内容哈希
        if len(unique_news) != len(all_news):
            content_hashes = set()
            final_news = []
            for item in unique_news:
                content_hash = item.get_content_hash()
                if content_hash not in content_hashes:
                    content_hashes.add(content_hash)
                    final_news.append(item)
            unique_news = final_news
        
        # 按发布时间排序
        unique_news.sort(key=lambda x: x.published_date, reverse=True)
        return unique_news
    
    def _fetch_from_url(self, url: str, keywords: List[str] = None) -> List[NewsItem]:
        """带重试机制的RSS获取"""
        last_exception = None
        
        for attempt in range(self.max_retries):
            try:
                # 验证URL格式
                parsed_url = urlparse(url)
                if not parsed_url.scheme or not parsed_url.netloc:
                    raise ValueError(f"无效的URL格式: {url}")
                
                # 设置feedparser的超时和用户代理
                feedparser.USER_AGENT = "News Agent 1.0 (https://github.com/example/news-agent)"
                
                # 解析RSS
                feed = feedparser.parse(url, resolve_relative_uris=False, sanitize_html=False)
                
                # 检查网络错误
                if hasattr(feed, 'status'):
                    if feed.status >= 400:
                        raise requests.exceptions.HTTPError(f"HTTP {feed.status}")
                
                # 检查解析错误
                if feed.bozo and hasattr(feed, 'bozo_exception'):
                    # 严重错误：完全无法解析
                    if not hasattr(feed, 'entries') or len(feed.entries) == 0:
                        error_msg = str(feed.bozo_exception)
                        if "timed out" in error_msg.lower():
                            raise socket.timeout(f"请求超时: {url}")
                        elif "connection" in error_msg.lower():
                            raise requests.exceptions.ConnectionError(f"连接错误: {error_msg}")
                        else:
                            raise Exception(f"RSS解析错误: {error_msg}")
                    else:
                        # 轻微错误：有内容但有警告
                        print(f"RSS警告 (尝试 {attempt + 1}/{self.max_retries}) - {url}: {feed.bozo_exception}")
                
                # 成功获取，跳出重试循环
                break
                
            except (socket.timeout, requests.exceptions.Timeout, 
                    requests.exceptions.ConnectionError, OSError) as e:
                last_exception = e
                if attempt < self.max_retries - 1:
                    wait_time = 2 ** attempt  # 指数退避
                    print(f"网络错误，{wait_time}秒后重试 (尝试 {attempt + 1}/{self.max_retries}): {e}")
                    time.sleep(wait_time)
                    continue
                else:
                    raise Exception(f"网络连接失败，已重试{self.max_retries}次: {e}")
            
            except Exception as e:
                # 非网络错误，不重试
                raise e
        
        news_items = []
        
        for entry in feed.entries:
            # 提取基本信息
            title = getattr(entry, 'title', '')
            content = self._extract_content(entry)
            link = getattr(entry, 'link', '')
            author = getattr(entry, 'author', None)
            
            # 解析发布时间
            published_date = self._parse_date(entry)
            
            # 获取RSS源名称
            feed_title = getattr(feed.feed, 'title', url)
            
            # 关键词过滤
            if keywords and not self._match_keywords(title + ' ' + content, keywords):
                continue
            
            # 提取摘要
            summary = getattr(entry, 'summary', '')[:500] + '...' if len(getattr(entry, 'summary', '')) > 500 else getattr(entry, 'summary', '')
            
            news_item = NewsItem(
                title=title,
                content=content,
                url=link,
                published_date=published_date,
                source=feed_title,
                author=author,
                summary=summary,
                keywords=keywords or []
            )
            
            news_items.append(news_item)
        
        return news_items
    
    def _extract_content(self, entry) -> str:
        # 尝试多种内容字段
        content_fields = ['content', 'summary', 'description']
        
        for field in content_fields:
            if hasattr(entry, field):
                content = getattr(entry, field)
                if isinstance(content, list) and len(content) > 0:
                    content = content[0]
                    if hasattr(content, 'value'):
                        return self._clean_html(content.value)
                elif isinstance(content, str):
                    return self._clean_html(content)
        
        return ""
    
    def _clean_html(self, text: str) -> str:
        # 简单的HTML标签清理
        import re
        clean = re.compile('<.*?>')
        return re.sub(clean, '', text)
    
    def _parse_date(self, entry) -> datetime:
        # 尝试解析多种时间格式
        date_fields = ['published_parsed', 'updated_parsed']
        
        for field in date_fields:
            if hasattr(entry, field):
                time_struct = getattr(entry, field)
                if time_struct:
                    return datetime.fromtimestamp(time.mktime(time_struct))
        
        # 如果无法解析，使用当前时间
        return datetime.now()
    
    def _match_keywords(self, text: str, keywords: List[str]) -> bool:
        """增强的关键词匹配，支持多种匹配模式"""
        if not keywords:
            return True
        
        text_lower = text.lower()
        
        for keyword in keywords:
            keyword_lower = keyword.lower().strip()
            
            # 1. 精确匹配（引号包围）
            if keyword_lower.startswith('"') and keyword_lower.endswith('"'):
                exact_keyword = keyword_lower[1:-1]
                if exact_keyword in text_lower:
                    return True
                continue
            
            # 2. 排除关键词（负号开头）
            if keyword_lower.startswith('-'):
                exclude_keyword = keyword_lower[1:]
                if exclude_keyword in text_lower:
                    return False
                continue
            
            # 3. 短语匹配（包含空格）
            if ' ' in keyword_lower:
                if keyword_lower in text_lower:
                    return True
                continue
            
            # 4. 普通包含匹配
            if keyword_lower in text_lower:
                return True
        
        # 如果有排除关键词但没有匹配的正向关键词，返回False
        has_positive_keywords = any(not k.strip().startswith('-') for k in keywords)
        return not has_positive_keywords
    
    def is_available(self) -> bool:
        return len(self.rss_urls) > 0
    
    def add_rss_url(self, url: str):
        if url not in self.rss_urls:
            self.rss_urls.append(url)
    
    def remove_rss_url(self, url: str):
        if url in self.rss_urls:
            self.rss_urls.remove(url)
    
    def get_source_info(self) -> Dict[str, Any]:
        info = super().get_source_info()
        info.update({
            'rss_urls': self.rss_urls,
            'url_count': len(self.rss_urls),
            'timeout': self.timeout
        })
        return info