from typing import List, Dict, Any
from .base import StorageBackend
from .json_storage import JSONStorage
from .csv_storage import CSVStorage
from .parquet_storage import ParquetStorage
from ..core.data_sources.base import NewsItem


class StorageManager:
    def __init__(self, storage_dir: str = "data"):
        self.storage_dir = storage_dir
        self._backends: Dict[str, StorageBackend] = {
            'json': JSONStorage(storage_dir),
            'csv': CSVStorage(storage_dir),
            'parquet': ParquetStorage(storage_dir)
        }
    
    def get_backend(self, format_name: str) -> StorageBackend:
        if format_name not in self._backends:
            raise ValueError(f"不支持的存储格式: {format_name}. 支持的格式: {list(self._backends.keys())}")
        return self._backends[format_name]
    
    def save_news(self, news_items: List[NewsItem], keywords: List[str] = None, 
                  format_name: str = "json", filename: str = None) -> str:
        backend = self.get_backend(format_name)
        
        if filename is None:
            filename = backend.generate_filename(keywords or [])
        
        return backend.save(news_items, filename)
    
    def load_news(self, filename: str, format_name: str = None) -> List[NewsItem]:
        # 如果没有指定格式，从文件扩展名推断
        if format_name is None:
            for fmt, backend in self._backends.items():
                if filename.endswith(f".{backend.get_file_extension()}"):
                    format_name = fmt
                    break
            
            if format_name is None:
                raise ValueError(f"无法从文件名推断格式: {filename}")
        
        backend = self.get_backend(format_name)
        return backend.load(filename)
    
    def list_files(self, format_name: str = None) -> Dict[str, List[str]]:
        if format_name:
            backend = self.get_backend(format_name)
            return {format_name: backend.list_files()}
        
        result = {}
        for fmt, backend in self._backends.items():
            result[fmt] = backend.list_files()
        
        return result
    
    def get_supported_formats(self) -> List[str]:
        return list(self._backends.keys())