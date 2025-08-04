import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field


@dataclass
class DataSourceConfig:
    rss_enabled: bool = True
    rss_sources: List[str] = field(default_factory=list)
    rss_timeout: int = 30
    
    news_api_enabled: bool = False
    news_api_key: str = ""
    
    google_search_enabled: bool = False
    google_search_delay: int = 3
    google_search_max_results: int = 50
    google_search_headless: bool = True
    google_search_default_sites: List[str] = field(default_factory=list)
    google_search_proxy_enabled: bool = False
    google_search_proxy_server: str = ""
    google_search_proxy_username: str = ""
    google_search_proxy_password: str = ""
    
    search_engine_enabled: bool = False
    search_engines: List[str] = field(default_factory=lambda: ["google", "bing"])
    search_delay: int = 2


@dataclass
class StorageConfig:
    format: str = "json"
    directory: str = "data"
    filename_template: str = "news_{date}_{keyword}.{format}"


@dataclass
class SchedulerConfig:
    enabled: bool = True
    default_interval: str = "24h"
    daily_time: str = "00:00"
    hourly_minute: int = 0


@dataclass
class SearchConfig:
    default_keywords: List[str] = field(default_factory=list)
    max_results: int = 100


@dataclass
class LoggingConfig:
    level: str = "INFO"
    file: str = "logs/news_agent.log"
    max_size: str = "10MB"
    backup_count: int = 5


class ConfigManager:
    def __init__(self, config_dir: Optional[str] = None):
        self.config_dir = Path(config_dir) if config_dir else Path("config")
        self.default_config_path = self.config_dir / "default.yaml"
        self.user_config_path = self.config_dir / "user_config.yaml"
        
        self._config: Dict[str, Any] = {}
        self._load_config()
    
    def _load_config(self):
        # 加载默认配置
        if self.default_config_path.exists():
            with open(self.default_config_path, 'r', encoding='utf-8') as f:
                self._config = yaml.safe_load(f) or {}
        
        # 加载用户配置并覆盖默认配置
        if self.user_config_path.exists():
            with open(self.user_config_path, 'r', encoding='utf-8') as f:
                user_config = yaml.safe_load(f) or {}
                self._merge_config(self._config, user_config)
    
    def _merge_config(self, base: Dict[str, Any], override: Dict[str, Any]):
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._merge_config(base[key], value)
            else:
                base[key] = value
    
    def get(self, key: str, default=None):
        keys = key.split('.')
        value = self._config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set_user_config(self, key: str, value: Any):
        if not self.user_config_path.exists():
            self.user_config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.user_config_path, 'w', encoding='utf-8') as f:
                yaml.dump({}, f)
        
        # 读取现有用户配置
        with open(self.user_config_path, 'r', encoding='utf-8') as f:
            user_config = yaml.safe_load(f) or {}
        
        # 设置新值
        keys = key.split('.')
        current = user_config
        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]
        current[keys[-1]] = value
        
        # 保存配置
        with open(self.user_config_path, 'w', encoding='utf-8') as f:
            yaml.dump(user_config, f, default_flow_style=False, allow_unicode=True)
        
        # 重新加载配置
        self._load_config()
    
    @property
    def data_sources(self) -> DataSourceConfig:
        ds_config = self.get('data_sources', {})
        rss_config = ds_config.get('rss', {})
        api_config = ds_config.get('news_api', {})
        google_config = ds_config.get('google_search', {})
        search_config = ds_config.get('search_engine', {})
        
        return DataSourceConfig(
            rss_enabled=rss_config.get('enabled', True),
            rss_sources=rss_config.get('sources', []),
            rss_timeout=rss_config.get('timeout', 30),
            news_api_enabled=api_config.get('enabled', False),
            news_api_key=api_config.get('api_key', ''),
            google_search_enabled=google_config.get('enabled', False),
            google_search_delay=google_config.get('delay', 3),
            google_search_max_results=google_config.get('max_results', 50),
            google_search_headless=google_config.get('headless', True),
            google_search_default_sites=google_config.get('default_sites', []),
            google_search_proxy_enabled=google_config.get('proxy', {}).get('enabled', False),
            google_search_proxy_server=google_config.get('proxy', {}).get('server', ''),
            google_search_proxy_username=google_config.get('proxy', {}).get('username', ''),
            google_search_proxy_password=google_config.get('proxy', {}).get('password', ''),
            search_engine_enabled=search_config.get('enabled', False),
            search_engines=search_config.get('engines', ['google', 'bing']),
            search_delay=search_config.get('delay', 2)
        )
    
    @property
    def storage(self) -> StorageConfig:
        storage_config = self.get('storage', {})
        return StorageConfig(
            format=storage_config.get('format', 'json'),
            directory=storage_config.get('directory', 'data'),
            filename_template=storage_config.get('filename_template', 'news_{date}_{keyword}.{format}')
        )
    
    @property
    def scheduler(self) -> SchedulerConfig:
        scheduler_config = self.get('scheduler', {})
        time_patterns = scheduler_config.get('time_patterns', {})
        
        return SchedulerConfig(
            enabled=scheduler_config.get('enabled', True),
            default_interval=scheduler_config.get('default_interval', '24h'),
            daily_time=time_patterns.get('daily', '00:00'),
            hourly_minute=int(time_patterns.get('hourly', '0'))
        )
    
    @property
    def search(self) -> SearchConfig:
        search_config = self.get('search', {})
        return SearchConfig(
            default_keywords=search_config.get('default_keywords', []),
            max_results=search_config.get('max_results', 100)
        )
    
    @property
    def logging(self) -> LoggingConfig:
        logging_config = self.get('logging', {})
        return LoggingConfig(
            level=logging_config.get('level', 'INFO'),
            file=logging_config.get('file', 'logs/news_agent.log'),
            max_size=logging_config.get('max_size', '10MB'),
            backup_count=logging_config.get('backup_count', 5)
        )


# 全局配置实例
config = ConfigManager()