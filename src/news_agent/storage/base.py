from abc import ABC, abstractmethod
from typing import List, Dict, Any
from pathlib import Path
from datetime import datetime

from ..core.data_sources.base import NewsItem


class StorageBackend(ABC):
    def __init__(self, storage_dir: str = "data"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
    
    @abstractmethod
    def save(self, news_items: List[NewsItem], filename: str) -> str:
        pass
    
    @abstractmethod
    def load(self, filename: str) -> List[NewsItem]:
        pass
    
    @abstractmethod
    def get_file_extension(self) -> str:
        pass
    
    def generate_filename(self, keywords: List[str], template: str = None) -> str:
        if template is None:
            template = "news_{date}_{keyword}.{format}"
        
        date_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        keyword_str = "_".join(keywords) if keywords else "all"
        
        # 清理文件名中的特殊字符
        keyword_str = "".join(c for c in keyword_str if c.isalnum() or c in "._-")
        
        filename = template.format(
            date=date_str,
            keyword=keyword_str,
            format=self.get_file_extension()
        )
        
        return filename
    
    def get_file_path(self, filename: str) -> Path:
        return self.storage_dir / filename
    
    def file_exists(self, filename: str) -> bool:
        return self.get_file_path(filename).exists()
    
    def list_files(self) -> List[str]:
        pattern = f"*.{self.get_file_extension()}"
        return [f.name for f in self.storage_dir.glob(pattern)]