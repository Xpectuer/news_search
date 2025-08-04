import json
from typing import List
from datetime import datetime

from .base import StorageBackend
from ..core.data_sources.base import NewsItem


class JSONStorage(StorageBackend):
    def save(self, news_items: List[NewsItem], filename: str) -> str:
        file_path = self.get_file_path(filename)
        
        data = {
            'metadata': {
                'count': len(news_items),
                'saved_at': datetime.now().isoformat(),
                'format': 'json'
            },
            'news': [item.to_dict() for item in news_items]
        }
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        return str(file_path)
    
    def load(self, filename: str) -> List[NewsItem]:
        file_path = self.get_file_path(filename)
        
        if not file_path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        news_items = []
        for item_data in data.get('news', []):
            news_item = NewsItem(
                title=item_data.get('title', ''),
                content=item_data.get('content', ''),
                url=item_data.get('url', ''),
                published_date=datetime.fromisoformat(item_data.get('published_date')),
                source=item_data.get('source', ''),
                author=item_data.get('author'),
                summary=item_data.get('summary'),
                keywords=item_data.get('keywords', [])
            )
            news_items.append(news_item)
        
        return news_items
    
    def get_file_extension(self) -> str:
        return "json"