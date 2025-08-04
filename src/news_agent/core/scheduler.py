import schedule
import time
import threading
from typing import List, Callable, Dict, Any
from datetime import datetime, timedelta

from .config import config
from .data_sources.rss import RSSSource
from ..storage.manager import StorageManager


class NewsScheduler:
    def __init__(self):
        self.jobs: List[Dict[str, Any]] = []
        self.running = False
        self.thread = None
        self.storage_manager = StorageManager(config.storage.directory)
    
    def add_rss_job(self, keywords: List[str], interval: str = None, time_pattern: str = None):
        """添加RSS收集任务"""
        scheduler_config = config.scheduler
        
        if not scheduler_config.enabled:
            raise Exception("调度器未启用")
        
        # 解析间隔配置
        interval = interval or scheduler_config.default_interval
        
        job_config = {
            'type': 'rss',
            'keywords': keywords,
            'interval': interval,
            'time_pattern': time_pattern,
            'last_run': None
        }
        
        # 创建任务函数
        def job_func():
            self._run_rss_job(keywords)
        
        # 根据间隔类型调度任务
        if interval.endswith('h'):  # 小时间隔
            hours = int(interval[:-1])
            schedule.every(hours).hours.do(job_func)
        elif interval.endswith('d'):  # 天间隔
            days = int(interval[:-1])
            schedule.every(days).days.do(job_func)
        elif time_pattern:  # 特定时间
            schedule.every().day.at(time_pattern).do(job_func)
        else:
            # 默认每24小时
            schedule.every(24).hours.do(job_func)
        
        self.jobs.append(job_config)
        return len(self.jobs) - 1  # 返回任务ID
    
    def _run_rss_job(self, keywords: List[str]):
        """执行RSS收集任务"""
        try:
            print(f"[{datetime.now()}] 开始执行RSS收集任务，关键词: {keywords}")
            
            # 获取RSS配置
            ds_config = config.data_sources
            if not ds_config.rss_sources:
                print("警告: 未配置RSS源")
                return
            
            # 创建RSS数据源
            rss_source = RSSSource(ds_config.rss_sources, ds_config.rss_timeout)
            
            # 获取新闻
            news_items = rss_source.fetch_news(keywords)
            
            if news_items:
                # 保存数据
                storage_config = config.storage
                saved_path = self.storage_manager.save_news(
                    news_items, keywords, storage_config.format
                )
                print(f"找到 {len(news_items)} 条新闻，已保存至: {saved_path}")
            else:
                print("未找到相关新闻")
                
        except Exception as e:
            print(f"执行RSS任务时出错: {e}")
    
    def start(self):
        """启动调度器"""
        if self.running:
            print("调度器已在运行")
            return
        
        self.running = True
        
        def run_scheduler():
            while self.running:
                schedule.run_pending()
                time.sleep(1)
        
        self.thread = threading.Thread(target=run_scheduler, daemon=True)
        self.thread.start()
        print("调度器已启动")
    
    def stop(self):
        """停止调度器"""
        self.running = False
        if self.thread:
            self.thread.join()
        print("调度器已停止")
    
    def list_jobs(self) -> List[Dict[str, Any]]:
        """列出所有任务"""
        return self.jobs.copy()
    
    def clear_jobs(self):
        """清除所有任务"""
        schedule.clear()
        self.jobs.clear()
        print("已清除所有任务")
    
    def get_next_run_time(self) -> str:
        """获取下次运行时间"""
        next_run = schedule.next_run()
        if next_run:
            return next_run.strftime("%Y-%m-%d %H:%M:%S")
        return "无计划任务"


# 全局调度器实例
scheduler = NewsScheduler()