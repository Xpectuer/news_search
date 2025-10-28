#!/usr/bin/env python3
"""
测试Bing代理功能
"""
import sys
import os

# 添加项目路径到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from news_agent.core.data_sources.bing_search import BingSearchSource


def test_bing_proxy():
    """测试Bing代理功能"""
    
    print("=" * 60)
    print("测试Bing搜索代理功能")
    print("=" * 60)
    
    # 测试无代理
    print("\n1. 无代理配置测试:")
    bing_no_proxy = BingSearchSource(market="en-US", delay=1, max_results=3)
    
    info = bing_no_proxy.get_source_info()
    print(f"代理启用: {info['proxy_enabled']}")
    print(f"代理服务器: {info['proxy_server']}")
    
    proxies = bing_no_proxy._get_proxies()
    print(f"requests代理配置: {proxies}")
    
    # 测试有代理
    print("\n2. 有代理配置测试:")
    proxy_config = {
        'enabled': True,
        'server': 'http://127.0.0.1:7890'
    }
    
    bing_with_proxy = BingSearchSource(
        market="en-US", 
        delay=1, 
        max_results=3,
        proxy_config=proxy_config
    )
    
    info = bing_with_proxy.get_source_info()
    print(f"代理启用: {info['proxy_enabled']}")
    print(f"代理服务器: {info['proxy_server']}")
    
    proxies = bing_with_proxy._get_proxies()
    print(f"requests代理配置: {proxies}")
    
    # 测试带用户名密码的代理
    print("\n3. 带认证的代理配置测试:")
    proxy_config_auth = {
        'enabled': True,
        'server': 'http://127.0.0.1:7890',
        'username': 'testuser',
        'password': 'testpass'
    }
    
    bing_with_auth_proxy = BingSearchSource(
        market="en-US", 
        delay=1, 
        max_results=3,
        proxy_config=proxy_config_auth
    )
    
    proxies = bing_with_auth_proxy._get_proxies()
    print(f"requests代理配置: {proxies}")
    
    # 测试可用性检查
    print("\n4. 服务可用性测试:")
    print(f"无代理可用性: {bing_no_proxy.is_available()}")
    print(f"有代理可用性: {bing_with_proxy.is_available()}")  # 这个可能会失败，因为代理地址不存在
    
    print("\n" + "=" * 60)
    print("代理功能测试完成")
    print("=" * 60)


if __name__ == "__main__":
    test_bing_proxy()