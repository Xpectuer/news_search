# News Agent

智能新闻收集工具，支持RSS和Google搜索，提供多格式存储和定时任务。

## 功能特性

- RSS订阅采集
- Google搜索（支持代理）
- 多格式输出（JSON/CSV/Parquet）
- 定时任务
- 关键词过滤

## 安装

```bash
pip install -e .
playwright install chromium  # Google搜索可选
```

## 快速开始

```bash

# 启用Google搜索（可选）
news-agent config enable-google
news-agent config set-google-proxy http://127.0.0.1:7890

# 获取新闻
news-agent fetch -k "人工智能" -s rss
news-agent fetch -k "Python" -s google --recent-days 7
```

