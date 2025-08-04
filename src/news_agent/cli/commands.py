import click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.panel import Panel
from rich.table import Table

from ..core.config import config
from ..core.data_sources.rss import RSSSource
from ..core.data_sources.google_search import GoogleSearchSource, GoogleSearchOptions
from ..core.data_sources.bing_search import BingSearchSource, BingSearchOptions
from ..core.scheduler import scheduler
from ..storage.manager import StorageManager

console = Console()


@click.group()
@click.version_option(version="1.0.0")
def cli():
    """新闻收集器CLI工具"""
    pass


@cli.command()
@click.option('--keywords', '-k', multiple=True, help='搜索关键词（支持多种模式：普通匹配、"精确匹配"、-排除词、短语匹配）')
@click.option('--format', '-f', default=None, help='输出格式（json/csv/parquet）')
@click.option('--output', '-o', help='输出文件名')
@click.option('--source', '-s', default='rss', help='数据源类型（rss/google/bing）')
@click.option('--sites', multiple=True, help='Google搜索限制网站 (例如: --sites cnn.com --sites bbc.com)')
@click.option('--after', help='Google搜索日期限制，之后 (格式: YYYY-MM-DD)')
@click.option('--before', help='Google搜索日期限制，之前 (格式: YYYY-MM-DD)')
@click.option('--exclude', multiple=True, help='Google搜索排除词')
@click.option('--recent-days', type=int, help='搜索最近N天的内容')
def fetch(keywords, format, output, source, sites, after, before, exclude, recent_days):
    """获取新闻数据"""
    if not keywords:
        console.print("[red]错误: 请至少指定一个关键词[/red]")
        return
    
    keywords_list = list(keywords)
    
    # 显示任务信息面板
    info_panel = Panel(
        f"[bold cyan]关键词:[/bold cyan] {', '.join(keywords_list)}\n"
        f"[bold cyan]数据源:[/bold cyan] {source}\n"
        f"[bold cyan]输出格式:[/bold cyan] {format or config.storage.format}",
        title="[bold green]新闻获取任务[/bold green]",
        border_style="blue"
    )
    console.print(info_panel)
    
    # 获取配置
    storage_config = config.storage
    format_name = format or storage_config.format
    
    # 初始化存储管理器
    storage_manager = StorageManager(storage_config.directory)
    
    if source == 'rss':
        # 检查RSS配置
        ds_config = config.data_sources
        if not ds_config.rss_sources:
            console.print("[red]错误: 未配置RSS源，请先使用 'news-agent config add-rss' 添加RSS源[/red]")
            return
        
        # 创建RSS数据源
        rss_source = RSSSource(ds_config.rss_sources, ds_config.rss_timeout)
        
        try:
            # 使用进度条显示获取进度
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TaskProgressColumn(),
                console=console
            ) as progress:
                
                # 创建主任务
                main_task = progress.add_task(
                    f"正在从 {len(ds_config.rss_sources)} 个RSS源获取新闻...", 
                    total=len(ds_config.rss_sources)
                )
                
                all_news = []
                successful_sources = 0
                failed_sources = []
                
                # 逐个处理RSS源
                raw_news_count = 0
                for i, url in enumerate(ds_config.rss_sources):
                    progress.update(main_task, description=f"处理RSS源 {i+1}/{len(ds_config.rss_sources)}: {url[:50]}...")
                    
                    try:
                        news_items = rss_source._fetch_from_url(url, keywords_list)
                        all_news.extend(news_items)
                        raw_news_count += len(news_items)
                        successful_sources += 1
                        progress.update(main_task, advance=1)
                    except Exception as e:
                        failed_sources.append((url, str(e)))
                        progress.update(main_task, advance=1)
                        continue
                
                # 进行去重处理
                progress.update(main_task, description="正在去重和排序...")
                unique_news = list(set(all_news))
                
                # 内容哈希去重
                if len(unique_news) != len(all_news):
                    content_hashes = set()
                    final_news = []
                    for item in unique_news:
                        content_hash = item.get_content_hash()
                        if content_hash not in content_hashes:
                            content_hashes.add(content_hash)
                            final_news.append(item)
                    unique_news = final_news
                
                # 按时间排序
                unique_news.sort(key=lambda x: x.published_date, reverse=True)
                all_news = unique_news
                
                progress.update(main_task, description="数据处理完成")
            
            # 显示结果统计
            result_table = Table(title="获取结果统计")
            result_table.add_column("项目", style="cyan")
            result_table.add_column("数量/状态", style="green")
            
            result_table.add_row("成功RSS源", str(successful_sources))
            result_table.add_row("失败RSS源", str(len(failed_sources)))
            result_table.add_row("原始新闻数", str(raw_news_count))
            result_table.add_row("去重后新闻数", str(len(all_news)))
            if raw_news_count > len(all_news):
                result_table.add_row("去重数量", str(raw_news_count - len(all_news)))
            
            console.print(result_table)
            
            # 显示失败的RSS源
            if failed_sources:
                console.print("\n[yellow]警告: 以下RSS源获取失败:[/yellow]")
                for url, error in failed_sources:
                    console.print(f"  [red]×[/red] {url}: {error}")
            
            if not all_news:
                console.print("[yellow]未找到匹配的新闻[/yellow]")
                return
            
            # 保存数据
            with console.status("[bold green]正在保存数据..."):
                filename = output or None
                saved_path = storage_manager.save_news(
                    all_news, keywords_list, format_name, filename
                )
            
            console.print(f"\n[bold green]✓ 新闻已保存至: {saved_path}[/bold green]")
            
        except Exception as e:
            console.print(f"[red]获取新闻时出错: {e}[/red]")
    
    elif source == 'google':
        # 检查Google搜索配置
        ds_config = config.data_sources
        if not ds_config.google_search_enabled:
            console.print("[yellow]提示: Google搜索功能未启用，正在启用...[/yellow]")
            config.set_user_config('data_sources.google_search.enabled', True)
            ds_config = config.data_sources
        
        try:
            # 构建搜索选项
            search_options = {}
            
            if sites:
                search_options['site'] = list(sites)
            elif ds_config.google_search_default_sites:
                search_options['site'] = ds_config.google_search_default_sites
            
            if recent_days:
                search_options.update(GoogleSearchOptions.recent_days(recent_days))
            elif after or before:
                search_options.update(GoogleSearchOptions.date_range(after, before))
            
            if exclude:
                search_options.update(GoogleSearchOptions.exclude_terms(list(exclude)))
            
            # 准备代理配置
            proxy_config = {}
            if ds_config.google_search_proxy_enabled and ds_config.google_search_proxy_server:
                proxy_config = {
                    'enabled': True,
                    'server': ds_config.google_search_proxy_server,
                    'username': ds_config.google_search_proxy_username,
                    'password': ds_config.google_search_proxy_password
                }
            
            # 创建Google搜索数据源
            google_source = GoogleSearchSource(
                delay=ds_config.google_search_delay,
                max_results=ds_config.google_search_max_results,
                headless=ds_config.google_search_headless,
                proxy_config=proxy_config
            )
            
            # 显示搜索选项
            if search_options:
                options_text = []
                if 'site' in search_options:
                    options_text.append(f"网站限制: {', '.join(search_options['site'])}")
                if 'after' in search_options:
                    options_text.append(f"日期范围: {search_options.get('after', '')} 之后")
                if 'before' in search_options:
                    options_text.append(f"日期范围: {search_options.get('before', '')} 之前")
                if 'exclude' in search_options:
                    options_text.append(f"排除词: {', '.join(search_options['exclude'])}")
                
                console.print(f"[cyan]搜索选项: {' | '.join(options_text)}[/cyan]")
            
            console.print("[yellow]注意: Google搜索可能需要较长时间，请耐心等待...[/yellow]")
            
            # 获取新闻
            with console.status("[bold blue]正在进行Google搜索..."):
                all_news = google_source.fetch_news(keywords_list, search_options=search_options)
            
            if not all_news:
                console.print("[yellow]未找到匹配的新闻[/yellow]")
                return
            
            # 显示结果统计
            result_table = Table(title="Google搜索结果")
            result_table.add_column("项目", style="cyan")
            result_table.add_column("数量", style="green")
            
            result_table.add_row("找到新闻数", str(len(all_news)))
            result_table.add_row("搜索关键词", ", ".join(keywords_list))
            
            console.print(result_table)
            
            # 保存数据
            with console.status("[bold green]正在保存数据..."):
                filename = output or None
                saved_path = storage_manager.save_news(
                    all_news, keywords_list, format_name, filename
                )
            
            console.print(f"\n[bold green]✓ 新闻已保存至: {saved_path}[/bold green]")
            
        except Exception as e:
            console.print(f"[red]Google搜索时出错: {e}[/red]")
            console.print("[yellow]提示: 确保已安装Playwright浏览器: playwright install chromium[/yellow]")
    
    elif source == 'bing':
        # 检查Bing搜索配置
        ds_config = config.data_sources
        if not hasattr(ds_config, 'bing_search_enabled') or not ds_config.bing_search_enabled:
            console.print("[yellow]提示: Bing搜索功能未启用，正在启用...[/yellow]")
            config.set_user_config('data_sources.bing_search.enabled', True)
            ds_config = config.data_sources
        
        try:
            # 构建搜索选项
            search_options = {}
            
            if sites:
                search_options['site'] = list(sites)
            elif hasattr(ds_config, 'bing_search_default_sites') and ds_config.bing_search_default_sites:
                search_options['site'] = ds_config.bing_search_default_sites
            
            if exclude:
                search_options.update(BingSearchOptions.exclude_terms(list(exclude)))
            
            # 获取API Key（如果配置了的话）
            api_key = getattr(ds_config, 'bing_search_api_key', None)
            
            # 准备代理配置
            proxy_config = {}
            if (hasattr(ds_config, 'bing_search_proxy_enabled') and 
                ds_config.bing_search_proxy_enabled and 
                hasattr(ds_config, 'bing_search_proxy_server') and
                ds_config.bing_search_proxy_server):
                proxy_config = {
                    'enabled': True,
                    'server': ds_config.bing_search_proxy_server,
                    'username': getattr(ds_config, 'bing_search_proxy_username', None),
                    'password': getattr(ds_config, 'bing_search_proxy_password', None)
                }
            
            # 创建Bing搜索数据源
            bing_source = BingSearchSource(
                api_key=api_key,
                delay=getattr(ds_config, 'bing_search_delay', 1),
                max_results=getattr(ds_config, 'bing_search_max_results', 50),
                market=getattr(ds_config, 'bing_search_market', 'zh-CN'),
                safe_search=getattr(ds_config, 'bing_search_safe_search', 'Moderate'),
                proxy_config=proxy_config
            )
            
            # 显示搜索选项
            if search_options:
                options_text = []
                if 'site' in search_options:
                    options_text.append(f"网站限制: {', '.join(search_options['site'])}")
                if 'exclude' in search_options:
                    options_text.append(f"排除词: {', '.join(search_options['exclude'])}")
                
                console.print(f"[cyan]搜索选项: {' | '.join(options_text)}[/cyan]")
            
            # 显示使用的API状态
            if api_key:
                console.print("[cyan]使用Bing官方API进行搜索...[/cyan]")
            else:
                console.print("[cyan]使用HTTP方式进行搜索（如需更好效果请配置API key）...[/cyan]")
            
            # 获取新闻
            with console.status("[bold blue]正在进行Bing搜索..."):
                all_news = bing_source.fetch_news(keywords_list, search_options=search_options)
            
            if not all_news:
                console.print("[yellow]未找到匹配的新闻[/yellow]")
                return
            
            # 显示结果统计
            result_table = Table(title="Bing搜索结果")
            result_table.add_column("项目", style="cyan")
            result_table.add_column("数量", style="green")
            
            result_table.add_row("找到新闻数", str(len(all_news)))
            result_table.add_row("搜索关键词", ", ".join(keywords_list))
            result_table.add_row("使用API", "是" if api_key else "否")
            
            console.print(result_table)
            
            # 保存数据
            with console.status("[bold green]正在保存数据..."):
                filename = output or None
                saved_path = storage_manager.save_news(
                    all_news, keywords_list, format_name, filename
                )
            
            console.print(f"\n[bold green]✓ 新闻已保存至: {saved_path}[/bold green]")
            
        except Exception as e:
            console.print(f"[red]Bing搜索时出错: {e}[/red]")
    
    else:
        console.print(f"[red]不支持的数据源: {source}[/red]")
        console.print("[cyan]支持的数据源: rss, google, bing[/cyan]")


@cli.group()
def config_cmd():
    """配置管理"""
    pass


@config_cmd.command('add-rss')
@click.argument('url')
def add_rss(url):
    """添加RSS源"""
    current_sources = config.get('data_sources.rss.sources', [])
    
    if url in current_sources:
        click.echo(f"RSS源已存在: {url}")
        return
    
    current_sources.append(url)
    config.set_user_config('data_sources.rss.sources', current_sources)
    
    click.echo(f"已添加RSS源: {url}")


@config_cmd.command('remove-rss')
@click.argument('url')
def remove_rss(url):
    """移除RSS源"""
    current_sources = config.get('data_sources.rss.sources', [])
    
    if url not in current_sources:
        click.echo(f"RSS源不存在: {url}")
        return
    
    current_sources.remove(url)
    config.set_user_config('data_sources.rss.sources', current_sources)
    
    click.echo(f"已移除RSS源: {url}")


@config_cmd.command('list-rss')
def list_rss():
    """列出所有RSS源"""
    sources = config.get('data_sources.rss.sources', [])
    
    if not sources:
        click.echo("未配置RSS源")
        return
    
    click.echo("已配置的RSS源:")
    for i, source in enumerate(sources, 1):
        click.echo(f"  {i}. {source}")


@config_cmd.command('set-format')
@click.argument('format_name', type=click.Choice(['json', 'csv', 'parquet']))
def set_format(format_name):
    """设置默认存储格式"""
    config.set_user_config('storage.format', format_name)
    click.echo(f"默认存储格式已设置为: {format_name}")


@config_cmd.command('enable-google')
def enable_google():
    """启用Google搜索功能"""
    config.set_user_config('data_sources.google_search.enabled', True)
    console.print("[green]✓ Google搜索功能已启用[/green]")
    console.print("[yellow]提示: 请确保已安装Playwright浏览器: playwright install chromium[/yellow]")


@config_cmd.command('disable-google')
def disable_google():
    """禁用Google搜索功能"""
    config.set_user_config('data_sources.google_search.enabled', False)
    console.print("[yellow]Google搜索功能已禁用[/yellow]")


@config_cmd.command('set-google-sites')
@click.argument('sites', nargs=-1, required=True)
def set_google_sites(sites):
    """设置Google搜索默认网站列表"""
    sites_list = list(sites)
    config.set_user_config('data_sources.google_search.default_sites', sites_list)
    console.print(f"[green]✓ 已设置默认搜索网站: {', '.join(sites_list)}[/green]")


@config_cmd.command('set-google-delay')
@click.argument('delay', type=int)
def set_google_delay(delay):
    """设置Google搜索请求间隔（秒）"""
    if delay < 1:
        console.print("[red]错误: 延时必须大于等于1秒[/red]")
        return
    
    config.set_user_config('data_sources.google_search.delay', delay)
    console.print(f"[green]✓ 已设置Google搜索延时为 {delay} 秒[/green]")


@config_cmd.command('set-google-proxy')
@click.argument('proxy_server')
@click.option('--username', help='代理用户名（可选）')
@click.option('--password', help='代理密码（可选）')
def set_google_proxy(proxy_server, username, password):
    """设置Google搜索代理
    
    示例: news-agent config set-google-proxy http://127.0.0.1:7890
    """
    # 启用代理
    config.set_user_config('data_sources.google_search.proxy.enabled', True)
    config.set_user_config('data_sources.google_search.proxy.server', proxy_server)
    
    if username:
        config.set_user_config('data_sources.google_search.proxy.username', username)
    if password:
        config.set_user_config('data_sources.google_search.proxy.password', password)
    
    console.print(f"[green]✓ 已设置Google搜索代理: {proxy_server}[/green]")
    if username:
        console.print(f"[green]  - 用户名: {username}[/green]")


@config_cmd.command('disable-google-proxy')
def disable_google_proxy():
    """禁用Google搜索代理"""
    config.set_user_config('data_sources.google_search.proxy.enabled', False)
    console.print("[yellow]Google搜索代理已禁用[/yellow]")


@config_cmd.command('enable-bing')
def enable_bing():
    """启用Bing搜索功能"""
    config.set_user_config('data_sources.bing_search.enabled', True)
    console.print("[green]✓ Bing搜索功能已启用[/green]")
    console.print("[cyan]提示: 可配置API key以获得更好的搜索效果[/cyan]")


@config_cmd.command('disable-bing')
def disable_bing():
    """禁用Bing搜索功能"""
    config.set_user_config('data_sources.bing_search.enabled', False)
    console.print("[yellow]Bing搜索功能已禁用[/yellow]")


@config_cmd.command('set-bing-api-key')
@click.argument('api_key')
def set_bing_api_key(api_key):
    """设置Bing搜索API密钥
    
    获取方式: https://www.microsoft.com/en-us/bing/apis/bing-web-search-api
    """
    config.set_user_config('data_sources.bing_search.api_key', api_key)
    console.print("[green]✓ Bing搜索API密钥已设置[/green]")
    console.print("[cyan]提示: 使用API可获得更好的搜索结果和稳定性[/cyan]")


@config_cmd.command('remove-bing-api-key')
def remove_bing_api_key():
    """移除Bing搜索API密钥"""
    config.set_user_config('data_sources.bing_search.api_key', None)
    console.print("[yellow]Bing搜索API密钥已移除，将使用HTTP备用方案[/yellow]")


@config_cmd.command('set-bing-sites')
@click.argument('sites', nargs=-1, required=True)
def set_bing_sites(sites):
    """设置Bing搜索默认网站列表"""
    sites_list = list(sites)
    config.set_user_config('data_sources.bing_search.default_sites', sites_list)
    console.print(f"[green]✓ 已设置Bing默认搜索网站: {', '.join(sites_list)}[/green]")


@config_cmd.command('set-bing-delay')
@click.argument('delay', type=int)
def set_bing_delay(delay):
    """设置Bing搜索请求间隔（秒）"""
    if delay < 1:
        console.print("[red]错误: 延时必须大于等于1秒[/red]")
        return
    
    config.set_user_config('data_sources.bing_search.delay', delay)
    console.print(f"[green]✓ 已设置Bing搜索延时为 {delay} 秒[/green]")


@config_cmd.command('set-bing-market')
@click.argument('market', type=click.Choice(['zh-CN', 'en-US', 'en-GB', 'ja-JP', 'ko-KR', 'fr-FR', 'de-DE']))
def set_bing_market(market):
    """设置Bing搜索市场/语言设置"""
    config.set_user_config('data_sources.bing_search.market', market)
    console.print(f"[green]✓ 已设置Bing搜索市场为 {market}[/green]")


@config_cmd.command('set-bing-safe-search')
@click.argument('level', type=click.Choice(['Off', 'Moderate', 'Strict']))
def set_bing_safe_search(level):
    """设置Bing搜索安全级别"""
    config.set_user_config('data_sources.bing_search.safe_search', level)
    console.print(f"[green]✓ 已设置Bing安全搜索级别为 {level}[/green]")


@config_cmd.command('set-bing-proxy')
@click.argument('proxy_server')
@click.option('--username', help='代理用户名（可选）')
@click.option('--password', help='代理密码（可选）')
def set_bing_proxy(proxy_server, username, password):
    """设置Bing搜索代理
    
    示例: news-agent config set-bing-proxy http://127.0.0.1:7890
    """
    # 启用代理
    config.set_user_config('data_sources.bing_search.proxy.enabled', True)
    config.set_user_config('data_sources.bing_search.proxy.server', proxy_server)
    
    if username:
        config.set_user_config('data_sources.bing_search.proxy.username', username)
    if password:
        config.set_user_config('data_sources.bing_search.proxy.password', password)
    
    console.print(f"[green]✓ 已设置Bing搜索代理: {proxy_server}[/green]")
    if username:
        console.print(f"[green]  - 用户名: {username}[/green]")


@config_cmd.command('disable-bing-proxy')
def disable_bing_proxy():
    """禁用Bing搜索代理"""
    config.set_user_config('data_sources.bing_search.proxy.enabled', False)
    console.print("[yellow]Bing搜索代理已禁用[/yellow]")


@config_cmd.command('show')
def show_config():
    """显示当前配置"""
    console.print("[bold cyan]=== 数据源配置 ===[/bold cyan]")
    ds_config = config.data_sources
    
    # RSS配置
    console.print(f"[green]RSS启用:[/green] {ds_config.rss_enabled}")
    console.print(f"[green]RSS源数量:[/green] {len(ds_config.rss_sources)}")
    
    # Google搜索配置
    console.print(f"[green]Google搜索启用:[/green] {ds_config.google_search_enabled}")
    if ds_config.google_search_enabled:
        console.print(f"[green]  - 请求延时:[/green] {ds_config.google_search_delay}秒")
        console.print(f"[green]  - 最大结果数:[/green] {ds_config.google_search_max_results}")
        console.print(f"[green]  - 无头模式:[/green] {ds_config.google_search_headless}")
        
        # 代理配置
        if ds_config.google_search_proxy_enabled and ds_config.google_search_proxy_server:
            console.print(f"[green]  - 代理服务器:[/green] {ds_config.google_search_proxy_server}")
            if ds_config.google_search_proxy_username:
                console.print(f"[green]  - 代理用户:[/green] {ds_config.google_search_proxy_username}")
        else:
            console.print(f"[yellow]  - 代理:[/yellow] 未配置")
        
        if ds_config.google_search_default_sites:
            console.print(f"[green]  - 默认网站:[/green] {', '.join(ds_config.google_search_default_sites)}")
    
    # Bing搜索配置
    bing_enabled = getattr(ds_config, 'bing_search_enabled', False)
    console.print(f"[green]Bing搜索启用:[/green] {bing_enabled}")
    if bing_enabled:
        console.print(f"[green]  - 请求延时:[/green] {getattr(ds_config, 'bing_search_delay', 1)}秒")
        console.print(f"[green]  - 最大结果数:[/green] {getattr(ds_config, 'bing_search_max_results', 50)}")
        console.print(f"[green]  - 市场设置:[/green] {getattr(ds_config, 'bing_search_market', 'zh-CN')}")
        console.print(f"[green]  - 安全搜索:[/green] {getattr(ds_config, 'bing_search_safe_search', 'Moderate')}")
        
        # API Key状态
        api_key = getattr(ds_config, 'bing_search_api_key', None)
        if api_key:
            console.print(f"[green]  - API密钥:[/green] 已配置 (***{api_key[-4:]})")
        else:
            console.print(f"[yellow]  - API密钥:[/yellow] 未配置 (使用HTTP备用方案)")
        
        # 代理配置
        proxy_enabled = getattr(ds_config, 'bing_search_proxy_enabled', False)
        proxy_server = getattr(ds_config, 'bing_search_proxy_server', None)
        if proxy_enabled and proxy_server:
            console.print(f"[green]  - 代理服务器:[/green] {proxy_server}")
            proxy_username = getattr(ds_config, 'bing_search_proxy_username', None)
            if proxy_username:
                console.print(f"[green]  - 代理用户:[/green] {proxy_username}")
        else:
            console.print(f"[yellow]  - 代理:[/yellow] 未配置")
        
        # 默认网站
        default_sites = getattr(ds_config, 'bing_search_default_sites', None)
        if default_sites:
            console.print(f"[green]  - 默认网站:[/green] {', '.join(default_sites)}")
    
    console.print(f"\n[bold cyan]=== 存储配置 ===[/bold cyan]")
    storage_config = config.storage
    console.print(f"[green]默认格式:[/green] {storage_config.format}")
    console.print(f"[green]存储目录:[/green] {storage_config.directory}")
    
    console.print(f"\n[bold cyan]=== 调度配置 ===[/bold cyan]")
    scheduler_config = config.scheduler
    console.print(f"[green]调度启用:[/green] {scheduler_config.enabled}")
    console.print(f"[green]默认间隔:[/green] {scheduler_config.default_interval}")


@cli.command()
@click.option('--format', '-f', help='文件格式过滤')
def list_files(format):
    """列出已保存的文件"""
    storage_config = config.storage
    storage_manager = StorageManager(storage_config.directory)
    
    files = storage_manager.list_files(format)
    
    if not any(files.values()):
        click.echo("未找到任何文件")
        return
    
    for fmt, file_list in files.items():
        if file_list:
            click.echo(f"\n{fmt.upper()} 文件:")
            for file in file_list:
                click.echo(f"  - {file}")


@cli.group()
def schedule_cmd():
    """调度任务管理"""
    pass


@schedule_cmd.command('add')
@click.option('--keywords', '-k', multiple=True, required=True, help='搜索关键词（可指定多个）')
@click.option('--interval', '-i', help='执行间隔（如: 1h, 6h, 1d）')
@click.option('--time', '-t', help='执行时间（如: 08:00）')
def add_schedule(keywords, interval, time):
    """添加定时任务"""
    keywords_list = list(keywords)
    
    try:
        job_id = scheduler.add_rss_job(keywords_list, interval, time)
        click.echo(f"已添加定时任务 #{job_id}")
        click.echo(f"关键词: {', '.join(keywords_list)}")
        if interval:
            click.echo(f"间隔: {interval}")
        if time:
            click.echo(f"时间: {time}")
    except Exception as e:
        click.echo(f"添加任务失败: {e}")


@schedule_cmd.command('list')
def list_schedules():
    """列出所有定时任务"""
    jobs = scheduler.list_jobs()
    
    if not jobs:
        click.echo("无定时任务")
        return
    
    click.echo("定时任务列表:")
    for i, job in enumerate(jobs):
        click.echo(f"  #{i}: {job['keywords']} (间隔: {job['interval']})")


@schedule_cmd.command('start')
def start_scheduler():
    """启动调度器"""
    try:
        scheduler.start()
        click.echo("调度器已启动")
        click.echo(f"下次运行时间: {scheduler.get_next_run_time()}")
    except Exception as e:
        click.echo(f"启动调度器失败: {e}")


@schedule_cmd.command('stop')
def stop_scheduler():
    """停止调度器"""
    scheduler.stop()
    click.echo("调度器已停止")


@schedule_cmd.command('clear')
def clear_schedules():
    """清除所有任务"""
    scheduler.clear_jobs()
    click.echo("已清除所有任务")


# 注册命令组
cli.add_command(config_cmd, name='config')
cli.add_command(schedule_cmd, name='schedule')


@cli.command()
def demo():
    """演示功能和使用示例"""
    demo_panel = Panel(
        """[bold green]新闻收集器使用示例[/bold green]

[cyan]1. RSS数据源基本使用：[/cyan]
news-agent config add-rss https://feeds.bbci.co.uk/news/rss.xml
news-agent fetch -k "python" -k "AI" -s rss

[cyan]2. Google搜索数据源：[/cyan]
news-agent config enable-google
news-agent fetch -k "人工智能" -s google --recent-days 7
news-agent fetch -k "ChatGPT" -s google --sites openai.com --sites techcrunch.com

[cyan]3. Bing搜索数据源：[/cyan]
news-agent config enable-bing
news-agent fetch -k "trump" -s bing
news-agent fetch -k "人工智能" -s bing --sites techcrunch.com --sites theverge.com
news-agent config set-bing-api-key YOUR_API_KEY  # 可选，获得更好效果

[cyan]4. 高级搜索选项：[/cyan]
news-agent fetch -k "机器学习" -s google --after 2024-01-01 --exclude "广告"
news-agent fetch -k "AI" -s bing --exclude "游戏" --exclude "娱乐"

[cyan]5. 输出格式和文件：[/cyan]
news-agent fetch -k "科技" -f csv -o "tech_news.csv" -s bing

[cyan]6. 配置管理：[/cyan]
news-agent config set-google-sites cnn.com bbc.com reuters.com
news-agent config set-bing-sites techcrunch.com theverge.com
news-agent config set-bing-api-key YOUR_BING_API_KEY
news-agent config set-bing-market zh-CN
news-agent config show

[cyan]7. 定时任务：[/cyan]
news-agent schedule add -k "新闻" -i "6h"
news-agent schedule start

[yellow]搜索选项说明：[/yellow]
• --sites: 限制搜索特定网站 (Google/Bing通用)
• --after/--before: 日期范围限制 (仅Google支持)
• --recent-days: 最近N天的内容 (仅Google支持)
• --exclude: 排除特定关键词 (Google/Bing通用)

[red]注意事项：[/red]
• Google搜索需要安装浏览器: playwright install chromium
• 在中国大陆需要配置代理才能访问Google
• Bing搜索无需代理，在国内可直接使用
• 建议为Bing配置API key以获得更好的搜索效果
• 请合理使用搜索频率，避免被封禁

[yellow]Bing搜索配置：[/yellow]
• 启用Bing: news-agent config enable-bing
• 设置API key: news-agent config set-bing-api-key YOUR_KEY
• 获取API key: https://www.microsoft.com/en-us/bing/apis/bing-web-search-api
• 设置市场: news-agent config set-bing-market zh-CN
• 设置代理: news-agent config set-bing-proxy http://127.0.0.1:7890

[yellow]Google代理配置：[/yellow]
• 设置HTTP代理: news-agent config set-google-proxy http://127.0.0.1:7890
• 设置SOCKS代理: news-agent config set-google-proxy socks5://127.0.0.1:1080
• 禁用代理: news-agent config disable-google-proxy
        """,
        title="[bold blue]使用指南[/bold blue]",
        border_style="green"
    )
    console.print(demo_panel)