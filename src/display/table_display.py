"""
表格显示模块
负责实时更新的表格界面显示
"""

import os
import sys
import time
from datetime import datetime
from typing import Dict, Any, List
import threading
import logging

try:
    from prettytable import PrettyTable
    PRETTYTABLE_AVAILABLE = True
except ImportError:
    PRETTYTABLE_AVAILABLE = False

try:
    from colorama import init, Fore, Back, Style
    init()  # 初始化colorama
    COLORAMA_AVAILABLE = True
except ImportError:
    COLORAMA_AVAILABLE = False


class TableDisplay:
    """表格显示管理器"""
    
    def __init__(self):
        """初始化表格显示器"""
        self.logger = logging.getLogger(__name__)
        self._is_displaying = False
        self._display_thread = None
        self._current_data = {}
        self._alert_data = []
        self._stats_data = {}
        self._start_time = None
        
        # 检查依赖
        if not PRETTYTABLE_AVAILABLE:
            self.logger.warning("⚠️ prettytable未安装，将使用简单表格显示")
        
        # 颜色配置
        self.colors = self._init_colors()
        
        # 清屏函数
        self._clear_screen = self._get_clear_function()
    
    def _init_colors(self) -> Dict[str, str]:
        """初始化颜色配置"""
        if COLORAMA_AVAILABLE:
            return {
                'header': Fore.CYAN + Style.BRIGHT,
                'success': Fore.GREEN + Style.BRIGHT,
                'warning': Fore.YELLOW + Style.BRIGHT,
                'error': Fore.RED + Style.BRIGHT,
                'info': Fore.BLUE + Style.BRIGHT,
                'reset': Style.RESET_ALL,
                'bold': Style.BRIGHT,
                'dim': Style.DIM
            }
        else:
            return {key: '' for key in ['header', 'success', 'warning', 'error', 'info', 'reset', 'bold', 'dim']}
    
    def _get_clear_function(self):
        """获取清屏函数"""
        if os.name == 'nt':  # Windows
            return lambda: os.system('cls')
        else:  # Unix/Linux/macOS
            return lambda: os.system('clear')
    
    def start_display(self) -> None:
        """启动实时显示"""
        if self._is_displaying:
            self.logger.warning("⚠️ 显示已在运行中")
            return
        
        self._is_displaying = True
        self._start_time = datetime.now()
        self._display_thread = threading.Thread(target=self._display_loop, daemon=True)
        self._display_thread.start()
        
        self.logger.info("📺 表格显示已启动")
    
    def stop_display(self) -> None:
        """停止实时显示"""
        if not self._is_displaying:
            return
        
        self._is_displaying = False
        
        if self._display_thread and self._display_thread.is_alive():
            self._display_thread.join(timeout=2)
        
        self.logger.info("📺 表格显示已停止")
    
    def _update_time_displays(self) -> None:
        """更新时间显示"""
        # 这个方法会在渲染时被调用，实时计算时间差
        # 由于我们使用的是实时计算，所以这里不需要修改数据
        # 时间计算在threshold_checker中进行
        pass
    
    def update_balance_data(self, data: Dict[str, Any]) -> None:
        """更新余额数据"""
        self._current_data = data
        # 在显示时实时计算时间差，确保显示是最新的
        self._update_time_displays()
    
    def add_alert(self, alert_info: Dict[str, Any]) -> None:
        """添加报警信息"""
        alert_record = {
            'time': alert_info['timestamp'].strftime('%H:%M:%S'),
            'address': alert_info['address_name'],
            'token': alert_info['token_name'],
            'type': alert_info['threshold_result'].threshold_type,
            'message': alert_info['threshold_result'].message.split('\\n')[0]  # 只取第一行
        }
        
        self._alert_data.append(alert_record)
        
        # 保持最近10条报警记录
        if len(self._alert_data) > 10:
            self._alert_data = self._alert_data[-10:]
    
    def update_stats(self, stats: Dict[str, Any]) -> None:
        """更新统计信息"""
        self._stats_data = stats
    
    def _display_loop(self) -> None:
        """显示主循环"""
        while self._is_displaying:
            try:
                self._render_display()
                time.sleep(2)  # 每2秒更新一次
            except Exception as e:
                self.logger.error(f"❌ 显示更新出错: {str(e)}")
                time.sleep(5)
    
    def _render_display(self) -> None:
        """渲染完整显示界面"""
        # 清屏
        self._clear_screen()
        
        # 显示标题
        self._print_header()
        
        # 显示余额表格
        self._print_balance_table()
        
        # 显示报警历史
        self._print_alert_history()
        
        # 显示统计信息
        self._print_statistics()
        
        # 显示底部信息
        self._print_footer()
    
    def _print_header(self) -> None:
        """打印标题区域"""
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        uptime = ""
        if self._start_time:
            elapsed = datetime.now() - self._start_time
            hours, remainder = divmod(int(elapsed.total_seconds()), 3600)
            minutes, seconds = divmod(remainder, 60)
            uptime = f"运行时间: {hours:02d}:{minutes:02d}:{seconds:02d}"
        
        header = f"""
{self.colors['header']}╔════════════════════════════════════════════════════════════════════════════════╗
║                              🚀 ETH余额监控工具                                 ║
║                              实时监控 | 智能报警                               ║
╚════════════════════════════════════════════════════════════════════════════════╝{self.colors['reset']}

{self.colors['info']}📅 当前时间: {current_time}    {uptime}{self.colors['reset']}
"""
        print(header)
    
    def _print_balance_table(self) -> None:
        """打印余额表格"""
        print(f"{self.colors['header']}📊 实时余额监控{self.colors['reset']}")
        print("─" * 100)
        
        if not self._current_data:
            print(f"{self.colors['warning']}⏳ 等待数据加载...{self.colors['reset']}")
            return
        
        if PRETTYTABLE_AVAILABLE:
            self._print_pretty_table()
        else:
            self._print_simple_table()
    
    def _print_pretty_table(self) -> None:
        """使用PrettyTable打印表格"""
        table = PrettyTable()
        table.field_names = ["地址名称", "代币", "当前余额", "状态", "阈值范围", "变化阈值", "时间窗口", "更新时间"]
        table.align = "l"
        table.padding_width = 1
        
        for address, data in self._current_data.items():
            address_name = data['name']
            
            for token_name, token_data in data['tokens'].items():
                if 'error' in token_data:
                    table.add_row([
                        address_name,
                        token_name,
                        "获取失败",
                        "❌ 错误",
                        "-",
                        "-",
                        "-",
                        "-"
                    ])
                else:
                    balance = token_data['current_balance']
                    thresholds = token_data['thresholds']
                    
                    # 判断状态
                    status = self._get_balance_status(balance, thresholds)
                    
                    # 格式化余额
                    balance_str = f"{balance:,.6f}"
                    
                    # 阈值范围
                    range_str = f"{thresholds['min']}-{thresholds['max']}"
                    
                    # 变化阈值
                    change_str = f"±{thresholds['change_up']}%/{thresholds['change_down']}%"
                    
                    # 时间窗口
                    time_window_str = f"{thresholds['time_window']}分钟"
                    
                    # 更新时间
                    last_update = token_data.get('last_update_time', '未知')
                    
                    table.add_row([
                        address_name,
                        token_name,
                        balance_str,
                        status,
                        range_str,
                        change_str,
                        time_window_str,
                        last_update
                    ])
                
                # 只在第一行显示地址名称
                address_name = ""
        
        print(table)
    
    def _print_simple_table(self) -> None:
        """打印简单表格"""
        # 表头
        header = f"{'地址名称':<15} {'代币':<8} {'当前余额':<20} {'状态':<10} {'阈值范围':<15} {'更新时间':<12}"
        print(header)
        print("─" * len(header))
        
        for address, data in self._current_data.items():
            address_name = data['name']
            
            for token_name, token_data in data['tokens'].items():
                if 'error' in token_data:
                    print(f"{address_name:<15} {token_name:<8} {'获取失败':<20} {'❌ 错误':<10} {'-':<15} {'-':<12}")
                else:
                    balance = token_data['current_balance']
                    thresholds = token_data['thresholds']
                    last_update = token_data.get('last_update_time', '未知')
                    
                    status = self._get_balance_status(balance, thresholds)
                    balance_str = f"{balance:,.6f}"
                    range_str = f"{thresholds['min']}-{thresholds['max']}"
                    
                    print(f"{address_name:<15} {token_name:<8} {balance_str:<20} {status:<10} {range_str:<15} {last_update:<12}")
                
                address_name = ""  # 只在第一行显示地址名称
    
    def _get_balance_status(self, balance: float, thresholds: Dict) -> str:
        """获取余额状态"""
        if balance < thresholds['min']:
            return f"{self.colors['error']}🔻 过低{self.colors['reset']}"
        elif balance > thresholds['max']:
            return f"{self.colors['error']}🔺 过高{self.colors['reset']}"
        else:
            return f"{self.colors['success']}✅ 正常{self.colors['reset']}"
    
    def _print_alert_history(self) -> None:
        """打印报警历史"""
        print(f"\\n{self.colors['header']}🚨 最近报警记录{self.colors['reset']}")
        print("─" * 100)
        
        if not self._alert_data:
            print(f"{self.colors['success']}✅ 暂无报警记录{self.colors['reset']}")
            return
        
        if PRETTYTABLE_AVAILABLE:
            alert_table = PrettyTable()
            alert_table.field_names = ["时间", "地址", "代币", "类型", "描述"]
            alert_table.align = "l"
            
            for alert in self._alert_data[-5:]:  # 显示最近5条
                alert_table.add_row([
                    alert['time'],
                    alert['address'],
                    alert['token'],
                    self._get_alert_type_display(alert['type']),
                    alert['message'][:50] + "..." if len(alert['message']) > 50 else alert['message']
                ])
            
            print(alert_table)
        else:
            for alert in self._alert_data[-5:]:
                print(f"{alert['time']} | {alert['address']} | {alert['token']} | {alert['type']}")
    
    def _get_alert_type_display(self, alert_type: str) -> str:
        """获取报警类型显示"""
        type_map = {
            'min_balance': f"{self.colors['warning']}余额过低{self.colors['reset']}",
            'max_balance': f"{self.colors['error']}余额过高{self.colors['reset']}",
            'percentage_up': f"{self.colors['info']}大幅上涨{self.colors['reset']}",
            'percentage_down': f"{self.colors['warning']}大幅下跌{self.colors['reset']}",
            'percentage_up_time_window': f"{self.colors['info']}时段上涨{self.colors['reset']}",
            'percentage_down_time_window': f"{self.colors['warning']}时段下跌{self.colors['reset']}"
        }
        return type_map.get(alert_type, alert_type)
    
    def _print_statistics(self) -> None:
        """打印统计信息"""
        print(f"\\n{self.colors['header']}📈 监控统计{self.colors['reset']}")
        print("─" * 50)
        
        if self._stats_data:
            stats_text = f"""
监控状态: {'🟢 运行中' if self._stats_data.get('is_running', False) else '🔴 已停止'}
监控地址: {self._stats_data.get('addresses_count', 0)} 个
代币对数: {self._stats_data.get('total_token_pairs', 0)} 个
总报警数: {len(self._alert_data)} 次
检查间隔: {self._stats_data.get('check_interval', 60)} 秒
"""
            print(stats_text)
        else:
            print("📊 统计信息加载中...")
    
    def _print_footer(self) -> None:
        """打印底部信息"""
        footer = f"""
{self.colors['dim']}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💡 提示: 按 Ctrl+C 停止监控   |   ⚡ 自动刷新: 每2秒   |   🔊 声音报警: 已启用
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{self.colors['reset']}
"""
        print(footer)
    
    def show_startup_message(self) -> None:
        """显示启动消息"""
        self._clear_screen()
        startup_msg = f"""
{self.colors['header']}╔════════════════════════════════════════════════════════════════════════════════╗
║                              🚀 ETH余额监控工具                                 ║
║                                  启动中...                                     ║
╚════════════════════════════════════════════════════════════════════════════════╝{self.colors['reset']}

{self.colors['info']}📋 正在初始化系统组件...{self.colors['reset']}
"""
        print(startup_msg)
    
    def show_error_message(self, error: str) -> None:
        """显示错误消息"""
        error_msg = f"""
{self.colors['error']}❌ 启动失败: {error}{self.colors['reset']}
"""
        print(error_msg)
