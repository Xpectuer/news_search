
import requests
from bs4 import BeautifulSoup
import time
import random
from urllib.parse import quote_plus
import itertools

class GoogleSearchScraper:
    def __init__(self, proxies=None, proxy_auth=None):
        """
        初始化爬虫
        
        Args:
            proxies: 代理列表，格式如 ['ip:port', '127.0.0.1:8080']
            proxy_auth: 代理认证信息，格式如 {'username': 'user', 'password': 'pass'}
        """
        # 常见的User-Agent列表，随机选择
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        ]
        
        # 基本请求头
        self.base_headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0'
        }
        
        # 代理设置
        self.proxies = proxies or []
        self.proxy_auth = proxy_auth
        self.proxy_cycle = itertools.cycle(self.proxies) if self.proxies else None
        self.failed_proxies = set()  # 记录失败的代理
        
        # 创建session
        self.session = requests.Session()
        
        # 如果有代理认证，设置认证
        if self.proxy_auth:
            self.session.auth = (proxy_auth['username'], proxy_auth['password'])
    
    def get_headers(self):
        """获取随机User-Agent的请求头"""
        headers = self.base_headers.copy()
        headers['User-Agent'] = random.choice(self.user_agents)
        return headers
    
    def get_proxy_config(self):
        """获取代理配置"""
        if not self.proxy_cycle:
            return None
        
        # 获取下一个可用代理
        max_attempts = len(self.proxies)
        for _ in range(max_attempts):
            proxy = next(self.proxy_cycle)
            if proxy not in self.failed_proxies:
                # 支持HTTP和SOCKS代理
                if proxy.startswith('socks'):
                    return {
                        'http': proxy,
                        'https': proxy
                    }
                else:
                    # 默认为HTTP代理
                    return {
                        'http': f'http://{proxy}',
                        'https': f'http://{proxy}'
                    }
        
        # 如果所有代理都失败了，清空失败列表重新开始
        if len(self.failed_proxies) == len(self.proxies):
            print("所有代理都失败，重置代理状态...")
            self.failed_proxies.clear()
            proxy = next(self.proxy_cycle)
            return {
                'http': f'http://{proxy}',
                'https': f'http://{proxy}'
            }
        
        return None
    
    def test_proxy(self, proxy_config):
        """测试代理是否可用"""
        try:
            test_url = "https://httpbin.org/ip"
            response = requests.get(
                test_url,
                proxies=proxy_config,
                headers=self.get_headers(),
                timeout=10
            )
            if response.status_code == 200:
                print(f"代理测试成功: {proxy_config}")
                return True
        except:
            pass
        return False
    
    def search(self, query, num_results=10, lang='zh-cn', max_retries=3):
        """
        搜索Google并返回结果
        
        Args:
            query: 搜索关键词
            num_results: 返回结果数量
            lang: 语言设置
            max_retries: 最大重试次数
        """
        # URL编码搜索词
        encoded_query = quote_plus(query)
        
        # 构造Google搜索URL
        search_url = f"https://www.google.com/search?q={encoded_query}&num={num_results}&hl={lang}"
        
        for attempt in range(max_retries + 1):
            try:
                # 获取代理配置
                proxy_config = self.get_proxy_config()
                
                # 随机延迟避免被检测
                time.sleep(random.uniform(1, 3))
                
                # 发送请求
                response = self.session.get(
                    search_url,
                    headers=self.get_headers(),
                    proxies=proxy_config,
                    timeout=15
                )
                
                # 检查响应状态
                response.raise_for_status()
                
                # 检查是否被Google阻止
                if "unusual traffic" in response.text.lower() or response.status_code == 429:
                    raise requests.RequestException("被Google检测到异常流量")
                
                # 解析HTML
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # 提取搜索结果
                results = self.parse_results(soup)
                
                if results:  # 如果成功获取到结果
                    print(f"搜索成功，使用代理: {proxy_config}")
                    return results
                else:
                    raise Exception("未找到搜索结果")
                
            except requests.RequestException as e:
                print(f"请求错误 (尝试 {attempt + 1}/{max_retries + 1}): {e}")
                
                # 如果是代理相关错误，标记代理为失败
                if proxy_config:
                    failed_proxy = list(proxy_config.values())[0]
                    self.failed_proxies.add(failed_proxy.replace('http://', ''))
                    print(f"标记代理失败: {failed_proxy}")
                
                if attempt == max_retries:
                    return []
                    
            except Exception as e:
                print(f"解析错误 (尝试 {attempt + 1}/{max_retries + 1}): {e}")
                if attempt == max_retries:
                    return []
        
        return []
    
    def parse_results(self, soup):
        """解析搜索结果页面"""
        results = []
        
        # Google搜索结果的主要容器选择器
        result_containers = soup.find_all('a')
        
        print(len(result_containers))
        breakpoint()
        # for container in result_containers:
        #     try:
        #         # 提取标题和链接
        #         title_element = container.find('h3')
        #         if not title_element:
        #             continue
                    
        #         link_element = title_element.find_parent('a')
        #         if not link_element:
        #             continue
                
        #         title = title_element.get_text(strip=True)
        #         link = link_element.get('href', '')
                
        #         # 提取描述
        #         desc_element = container.find('div', class_=['VwiC3b', 's3v9rd'])
        #         description = desc_element.get_text(strip=True) if desc_element else ''
                
        #         # 提取显示URL
        #         cite_element = container.find('cite')
        #         display_url = cite_element.get_text(strip=True) if cite_element else ''
                
        #         if title and link:
        #             results.append({
        #                 'title': title,
        #                 'link': link,
        #                 'description': description,
        #                 'display_url': display_url
        #             })
                    
        #     except Exception as e:
        #         print(f"解析单个结果时出错: {e}")
        #         continue
        
        return results
    
    def add_proxy(self, proxy):
        """添加新代理"""
        if proxy not in self.proxies:
            self.proxies.append(proxy)
            self.proxy_cycle = itertools.cycle(self.proxies)
            print(f"添加代理: {proxy}")
    
    def remove_proxy(self, proxy):
        """移除代理"""
        if proxy in self.proxies:
            self.proxies.remove(proxy)
            self.proxy_cycle = itertools.cycle(self.proxies) if self.proxies else None
            print(f"移除代理: {proxy}")
    
    def get_proxy_status(self):
        """获取代理状态"""
        total = len(self.proxies)
        failed = len(self.failed_proxies)
        active = total - failed
        return {
            'total': total,
            'active': active,
            'failed': failed,
            'failed_list': list(self.failed_proxies)
        }

def main():
    """示例使用"""
    # 代理列表示例 (请替换为真实可用的代理)
    proxy_list = [
        '127.0.0.1:7892',
        # '127.0.0.1:8081',
        # 'socks5://127.0.0.1:1080',  # SOCKS代理示例
    ]
    
    # 代理认证示例 (如果需要)
    proxy_auth = {
        'username': 'your_username',
        'password': 'your_password'
    }
    
    # 创建爬虫实例
    # 不使用代理
    # scraper = GoogleSearchScraper()
    
    # 使用代理（无认证）
    scraper = GoogleSearchScraper(proxies=proxy_list)
    
    # 使用代理（带认证）
    # scraper = GoogleSearchScraper(proxies=proxy_list, proxy_auth=proxy_auth)
    
    # 显示代理状态
    status = scraper.get_proxy_status()
    print(f"代理状态: 总计{status['total']}, 可用{status['active']}, 失败{status['failed']}")
    
    # 搜索示例
    query = "Python爬虫教程"
    print(f"\n搜索关键词: {query}")
    print("-" * 50)
    
    results = scraper.search(query, num_results=5)
    
    if results:
        for i, result in enumerate(results, 1):
            print(f"结果 {i}:")
            print(f"标题: {result['title']}")
            print(f"链接: {result['link']}")
            print(f"描述: {result['description']}")
            print(f"显示URL: {result['display_url']}")
            print("-" * 50)
    else:
        print("未找到搜索结果或请求失败")
    
    # 显示最终代理状态
    final_status = scraper.get_proxy_status()
    print(f"\n最终代理状态: 总计{final_status['total']}, 可用{final_status['active']}, 失败{final_status['failed']}")
    if final_status['failed_list']:
        print(f"失败的代理: {final_status['failed_list']}")

if __name__ == "__main__":
    main()
