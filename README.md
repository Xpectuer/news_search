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
# 添加RSS源
news-agent config add-rss "https://rss.cnn.com/rss/edition.rss"

# 启用Google搜索（可选）
news-agent config enable-google
news-agent config set-google-proxy http://127.0.0.1:7890

# 获取新闻
news-agent fetch -k "人工智能" -s rss
news-agent fetch -k "Python" -s google --recent-days 7
```

## 命令参考

```bash
# 基础命令
news-agent --help              # 查看帮助
news-agent demo               # 查看演示
news-agent config show        # 查看配置

# RSS配置
news-agent config add-rss <URL>     # 添加RSS源
news-agent config list-rss          # 列出RSS源

# Google搜索配置
news-agent config enable-google     # 启用Google搜索
news-agent config set-google-proxy <URL>  # 设置代理
news-agent config set-google-delay <秒>   # 设置延时

# 获取新闻
news-agent fetch -k "关键词" -s rss|google
news-agent fetch -k "关键词" -s google --sites example.com --recent-days 7
news-agent fetch -k "关键词" -f csv -o "output.csv"

# 定时任务
news-agent schedule add -k "关键词" -i "6h"
news-agent schedule start
```

## 注意事项

- 中国大陆用户使用Google搜索需配置代理
- 建议设置3-5秒延时避免被封禁
- 遵守相关服务条款
