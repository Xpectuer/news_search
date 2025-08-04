# Google搜索功能设置指南

## 概述

News Agent现在支持基于Playwright的Google搜索功能，可以直接搜索Google获取最新新闻。此功能特别适合中国大陆用户，支持代理配置。

## 功能特性

- ✅ 完整的Google搜索支持
- ✅ 丰富的搜索语法（site、after、before、exclude等）
- ✅ 代理支持（HTTP/SOCKS5）
- ✅ 反爬虫机制
- ✅ 可配置的延时和结果数量
- ✅ 美观的CLI交互界面

## 安装依赖

如果你还没有安装Playwright，请运行：

```bash
pip install playwright beautifulsoup4
playwright install chromium
```

## 基础配置

### 1. 启用Google搜索功能

```bash
news-agent config enable-google
```

### 2. 配置代理（中国大陆用户必需）

#### HTTP代理
```bash
news-agent config set-google-proxy http://127.0.0.1:7890
```

#### SOCKS5代理
```bash
news-agent config set-google-proxy socks5://127.0.0.1:1080
```

#### 带用户名密码的代理
```bash
news-agent config set-google-proxy http://proxy.example.com:8080 --username myuser --password mypass
```

### 3. 其他配置选项

```bash
# 设置搜索延时（推荐3-5秒）
news-agent config set-google-delay 5

# 设置默认搜索网站
news-agent config set-google-sites cnn.com bbc.com reuters.com

# 查看当前配置
news-agent config show
```

## 使用方法

### 基础搜索

```bash
# 简单关键词搜索
news-agent fetch -k "人工智能" -s google

# 多关键词搜索
news-agent fetch -k "Python" -k "机器学习" -s google
```

### 高级搜索选项

#### 网站限制
```bash
# 只搜索特定网站
news-agent fetch -k "AI" -s google --sites openai.com --sites techcrunch.com
```

#### 日期范围
```bash
# 搜索特定日期范围
news-agent fetch -k "ChatGPT" -s google --after 2024-01-01 --before 2024-12-31

# 搜索最近N天
news-agent fetch -k "新闻" -s google --recent-days 7
```

#### 排除关键词
```bash
# 排除特定词汇
news-agent fetch -k "技术新闻" -s google --exclude "广告" --exclude "推广"
```

#### 组合使用
```bash
# 复杂搜索示例
news-agent fetch -k "机器学习" -s google \
  --sites arxiv.org --sites nature.com \
  --after 2024-01-01 \
  --exclude "广告" \
  --recent-days 30 \
  -f csv -o "ml_research.csv"
```

## Google搜索语法支持

News Agent支持以下Google搜索操作符：

- `site:example.com` - 限制搜索特定网站
- `after:2024-01-01` - 搜索指定日期之后的内容
- `before:2024-12-31` - 搜索指定日期之前的内容
- `intitle:"关键词"` - 标题中必须包含关键词
- `inurl:关键词` - URL中必须包含关键词
- `filetype:pdf` - 搜索特定文件类型
- `-排除词` - 排除特定关键词

## 常见问题

### Q: 搜索时出现"搜索结果加载超时"
A: 这通常是网络问题或Google反爬机制。建议：
- 检查代理设置是否正确
- 增加延时间隔：`news-agent config set-google-delay 8`
- 确保代理服务正常运行

### Q: 提示"需要验证"或"captcha"
A: Google检测到自动化访问。建议：
- 降低搜索频率
- 更换代理IP
- 增加延时间隔

### Q: 搜索结果为空
A: 可能的原因：
- 关键词过于具体
- 网站限制过于严格
- 日期范围问题
- 网络连接问题

### Q: 代理连接失败
A: 检查代理配置：
- 确保代理服务正在运行
- 验证代理地址和端口
- 检查用户名密码（如果需要）

## 配置文件

Google搜索配置保存在 `config/user_config.yaml` 中：

```yaml
data_sources:
  google_search:
    enabled: true
    delay: 5
    proxy:
      enabled: true
      server: http://127.0.0.1:7890
      username: ""
      password: ""
```

## 性能建议

1. **延时设置**: 建议设置3-5秒延时，避免被Google封禁
2. **结果数量**: 默认最多50条结果，可根据需要调整
3. **批量搜索**: 避免短时间内大量搜索
4. **代理轮换**: 如有多个代理，可以手动切换使用

## 法律声明

请注意：
- 仅用于个人学习和研究目的
- 遵守Google服务条款
- 合理使用，避免对Google服务造成负担
- 尊重网站的robots.txt规则

## 故障排除

如果遇到问题，请按以下顺序检查：

1. 运行测试脚本：`python test_google_proxy.py`
2. 检查Playwright安装：`playwright --version`
3. 测试代理连接：使用浏览器验证代理是否能访问Google
4. 查看详细日志：使用 `--verbose` 选项

## 技术支持

如需技术支持，请提供：
- 错误信息截图
- 配置文件内容（隐藏敏感信息）
- 系统环境信息
- 复现步骤