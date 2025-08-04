from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class NewsItem:
    title: str
    content: str
    url: str
    published_date: datetime
    source: str
    author: Optional[str] = None
    summary: Optional[str] = None
    keywords: List[str] = None
    
    def __post_init__(self):
        if self.keywords is None:
            self.keywords = []
    
    def __hash__(self):
        # 使用URL和标题的组合作为唯一标识
        return hash((self.url, self.title.strip().lower()))
    
    def __eq__(self, other):
        if not isinstance(other, NewsItem):
            return False
        # 基于URL和标题判断是否为同一条新闻
        return (self.url == other.url and 
                self.title.strip().lower() == other.title.strip().lower())
    
    def get_content_hash(self) -> str:
        """获取内容哈希，用于更精确的去重"""
        import hashlib
        content_str = f"{self.title.strip().lower()}{self.content[:500].strip().lower()}"
        return hashlib.md5(content_str.encode()).hexdigest()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'title': self.title,
            'content': self.content,
            'url': self.url,
            'published_date': self.published_date.isoformat(),
            'source': self.source,
            'author': self.author,
            'summary': self.summary,
            'keywords': self.keywords
        }


class DataSource(ABC):
    def __init__(self, name: str):
        self.name = name
    
    @abstractmethod
    def fetch_news(self, keywords: List[str] = None, **kwargs) -> List[NewsItem]:
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        pass
    
    def get_source_info(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'available': self.is_available()
        }