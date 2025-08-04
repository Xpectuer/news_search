# News Agent - 新闻收集器

智能新闻收集工具，支持RSS和Google搜索，提供多格式存储和定时任务功能。

## 🚀 功能特性

- **📰 RSS订阅**: 支持多RSS源自动采集
- **🔍 Google搜索**: 基于Playwright的智能搜索（支持代理）
- **💾 多格式存储**: JSON/CSV/Parquet格式输出
- **⏰ 定时任务**: 自动化新闻收集
- **🎯 智能过滤**: 关键词匹配和去重
- **🌐 代理支持**: 支持HTTP/SOCKS5代理

## 📦 安装

```bash
# 安装依赖
pip install -e .

# 安装Google搜索依赖（可选）
playwright install chromium
```

## ⚡ 快速开始

### 1. 配置RSS源

```bash
news-agent config add-rss "https://rss.cnn.com/rss/edition.rss"
news-agent config add-rss "https://feeds.bbci.co.uk/news/rss.xml"
```

### 2. 启用Google搜索（可选）

```bash
# 启用Google搜索
news-agent config enable-google

# 配置代理（中国大陆用户）
news-agent config set-google-proxy http://127.0.0.1:7890

# 设置搜索参数
news-agent config set-google-delay 5
```

### 3. 获取新闻

```bash
# RSS搜索
news-agent fetch -k "人工智能" -k "AI" -s rss

# Google搜索
news-agent fetch -k "Python" -s google --recent-days 7

# 高级Google搜索
news-agent fetch -k "机器学习" -s google \
  --sites arxiv.org --sites nature.com \
  --after 2024-01-01 --exclude "广告"

# 指定输出格式
news-agent fetch -k "科技" -f csv -o "tech_news.csv"
```

## 📋 命令参考

### 基础命令

```bash
# 查看帮助
news-agent --help
news-agent demo

# 查看配置
news-agent config show

# 列出文件
news-agent list-files
```

### RSS配置

```bash
news-agent config add-rss <URL>          # 添加RSS源
news-agent config remove-rss <URL>       # 移除RSS源
news-agent config list-rss               # 列出RSS源
```

### Google搜索配置

```bash
news-agent config enable-google                    # 启用Google搜索
news-agent config disable-google                   # 禁用Google搜索
news-agent config set-google-proxy <PROXY_URL>     # 设置代理
news-agent config disable-google-proxy             # 禁用代理
news-agent config set-google-delay <SECONDS>       # 设置延时
news-agent config set-google-sites <SITE1> <SITE2> # 设置默认网站
```

### 搜索选项

```bash
# 基础选项
-k, --keywords    # 搜索关键词（可多个）
-s, --source     # 数据源（rss/google）
-f, --format     # 输出格式（json/csv/parquet）
-o, --output     # 输出文件名

# Google搜索选项
--sites          # 限制搜索网站
--after          # 日期之后 (YYYY-MM-DD)
--before         # 日期之前 (YYYY-MM-DD)
--recent-days    # 最近N天
--exclude        # 排除关键词
```

### 定时任务

```bash
news-agent schedule add -k "新闻" -i "6h"    # 添加定时任务
news-agent schedule list                    # 列出任务
news-agent schedule start                   # 启动调度器
news-agent schedule stop                    # 停止调度器
news-agent schedule clear                   # 清除所有任务
```

## 🔧 高级用法

### Google搜索语法

支持完整的Google搜索操作符：

- `site:example.com` - 限制网站
- `after:2024-01-01` - 日期范围
- `intitle:"关键词"` - 标题匹配
- `inurl:关键词` - URL匹配
- `filetype:pdf` - 文件类型
- `-排除词` - 排除关键词

### 关键词匹配模式

```bash
# 普通匹配
news-agent fetch -k "python"

# 精确匹配
news-agent fetch -k '"机器学习"'

# 排除词
news-agent fetch -k "新闻" -k "-广告"

# 组合使用
news-agent fetch -k "AI" -k '"深度学习"' -k "-推广"
```

### 代理配置

```bash
# HTTP代理
news-agent config set-google-proxy http://127.0.0.1:7890

# SOCKS5代理
news-agent config set-google-proxy socks5://127.0.0.1:1080

# 带认证的代理
news-agent config set-google-proxy http://proxy.com:8080 \
  --username user --password pass
```

## 📁 项目结构

```text
src/news_agent/
├── core/                    # 核心模块
│   ├── config.py           # 配置管理
│   ├── scheduler.py        # 定时任务
│   └── data_sources/       # 数据源
│       ├── base.py         # 基础类
│       ├── rss.py          # RSS数据源
│       └── google_search.py # Google搜索
├── storage/                # 存储模块
│   ├── manager.py          # 存储管理器
│   ├── json_storage.py     # JSON存储
│   ├── csv_storage.py      # CSV存储
│   └── parquet_storage.py  # Parquet存储
└── cli/                    # 命令行接口
    ├── main.py             # 入口文件
    └── commands.py         # 命令实现
```

## ⚙️ 配置文件

配置文件位于 `config/` 目录：

- `default.yaml` - 默认配置
- `user_config.yaml` - 用户自定义配置

示例配置：

```yaml
data_sources:
  rss:
    enabled: true
    sources:
      - "https://rss.cnn.com/rss/edition.rss"
  google_search:
    enabled: true
    delay: 5
    proxy:
      enabled: true
      server: "http://127.0.0.1:7890"

storage:
  format: "json"
  directory: "data"
```

## 🔍 使用示例

### 科技新闻收集

```bash
# 收集科技新闻（RSS）
news-agent fetch -k "人工智能" -k "机器学习" -s rss -f csv

# 搜索最新AI论文（Google）
news-agent fetch -k "artificial intelligence" -s google \
  --sites arxiv.org --recent-days 7 -o "ai_papers.json"
```

### 财经新闻追踪

```bash
# 设置财经网站
news-agent config set-google-sites bloomberg.com reuters.com cnbc.com

# 收集财经新闻
news-agent fetch -k "股市" -k "经济" -s google --recent-days 1
```

### 定时新闻收集

```bash
# 每6小时收集一次科技新闻
news-agent schedule add -k "科技" -k "AI" -i "6h"

# 每天8点收集财经新闻
news-agent schedule add -k "财经" -t "08:00"

# 启动定时任务
news-agent schedule start
```

## ⚠️ 注意事项

### Google搜索

- 🌍 中国大陆用户需要配置代理
- ⏱️ 建议设置3-5秒延时避免封禁
- 🔄 合理使用频率
- 📜 遵守Google服务条款

### RSS订阅

- 📡 某些RSS源可能不稳定
- 🔄 建议添加多个RSS源
- ⚡ RSS获取速度较快

## 🐛 故障排除

### 常见问题

1. **Google搜索超时**

   ```bash
   news-agent config set-google-delay 8
   ```

2. **代理连接失败**
   - 确认代理服务运行
   - 检查代理地址和端口

3. **RSS源访问失败**
   - 检查网络连接
   - 尝试其他RSS源

4. **模块导入错误**
   ```bash
   pip install -e .
   playwright install chromium
   ```

### 测试

```bash
# 运行测试脚本
python test_google_proxy.py

# 检查配置
news-agent config show

# 查看演示
news-agent demo
```

## 📄 许可证

MIT License

## 🤝 贡献

欢迎提交Issue和Pull Request！

---

**开始使用**: `news-agent demo` 查看完整使用示例