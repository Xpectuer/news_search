import pandas as pd
from typing import List
from datetime import datetime

from .base import StorageBackend
from ..core.data_sources.base import NewsItem


class ParquetStorage(StorageBackend):
    def save(self, news_items: List[NewsItem], filename: str) -> str:
        file_path = self.get_file_path(filename)
        
        # 转换为DataFrame
        data = []
        for item in news_items:
            row = {
                'title': item.title,
                'content': item.content,
                'url': item.url,
                'published_date': item.published_date,
                'source': item.source,
                'author': item.author or '',
                'summary': item.summary or '',
                'keywords': '|'.join(item.keywords) if item.keywords else ''
            }
            data.append(row)
        
        df = pd.DataFrame(data)
        
        # 确保发布时间是datetime类型
        df['published_date'] = pd.to_datetime(df['published_date'])
        
        df.to_parquet(file_path, index=False)
        
        return str(file_path)
    
    def load(self, filename: str) -> List[NewsItem]:
        file_path = self.get_file_path(filename)
        
        if not file_path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")
        
        df = pd.read_parquet(file_path)
        
        news_items = []
        for _, row in df.iterrows():
            keywords = row['keywords'].split('|') if row['keywords'] else []
            
            news_item = NewsItem(
                title=row['title'],
                content=row['content'],
                url=row['url'],
                published_date=row['published_date'].to_pydatetime(),
                source=row['source'],
                author=row['author'] if pd.notna(row['author']) and row['author'] else None,
                summary=row['summary'] if pd.notna(row['summary']) and row['summary'] else None,
                keywords=keywords
            )
            news_items.append(news_item)
        
        return news_items
    
    def get_file_extension(self) -> str:
        return "parquet"