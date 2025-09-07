#!/usr/bin/env python3
"""
ETH余额监控工具主程序
支持多地址、多代币的实时余额监控和智能报警
"""

import os
import sys
import signal
import logging
import argparse
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.config.config_manager import ConfigManager
from src.blockchain.web3_client import Web3Client
from src.blockchain.token_service import TokenService
from src.monitor.balance_monitor import BalanceMonitor
from src.alert.alert_manager import AlertManager
from src.display.table_display import TableDisplay


class ETHBalanceMonitor:
    """ETH余额监控主类"""
    
    def __init__(self, config_path: str = "config.yaml"):
        """
        初始化监控系统
        
        Args:
            config_path: 配置文件路径
        """
        self.config_path = config_path
        self.logger = None
        
        # 核心组件
        self.config_manager = None
        self.web3_client = None
        self.token_service = None
        self.balance_monitor = None
        self.alert_manager = None
        self.table_display = None
        
        # 运行状态
        self.is_running = False
        
        # 初始化系统
        self._initialize_system()
    
    def _initialize_system(self) -> None:
        """初始化系统组件"""
        try:
            # 0. 初始化表格显示器
            self.table_display = TableDisplay()
            self.table_display.show_startup_message()
            
            # 1. 加载配置
            self.config_manager = ConfigManager(self.config_path)
            
            # 2. 设置日志
            self._setup_logging()
            
            # 3. 初始化Web3客户端
            self.logger.info("🌐 初始化Web3连接...")
            rpc_settings = self.config_manager.get_rpc_settings()
            self.web3_client = Web3Client(
                provider_url=rpc_settings.provider_url,
                request_timeout=rpc_settings.request_timeout,
                retry_attempts=rpc_settings.retry_attempts
            )
            
            # 4. 初始化代币服务
            self.logger.info("🪙 初始化代币服务...")
            self.token_service = TokenService(self.web3_client)
            
            # 5. 初始化报警系统
            self.logger.info("🚨 初始化报警系统...")
            alert_settings = self.config_manager.get_alert_settings()
            self.alert_manager = AlertManager(alert_settings)
            
            # 6. 初始化余额监控器
            self.logger.info("📊 初始化余额监控器...")
            self.balance_monitor = BalanceMonitor(
                self.config_manager,
                self.token_service
            )
            
            # 7. 连接监控器和报警系统
            self.balance_monitor.on_threshold_triggered = self._handle_alert_with_display
            
            # 8. 验证代币合约
            self._verify_token_contracts()
            
            self.logger.info("✅ 系统初始化完成")
            
        except Exception as e:
            error_msg = f"❌ 系统初始化失败: {str(e)}"
            if self.logger:
                self.logger.error(error_msg)
            if self.table_display:
                self.table_display.show_error_message(str(e))
            else:
                print(error_msg)
            raise
    
    def _handle_alert_with_display(self, alert_info) -> None:
        """处理报警并更新显示"""
        # 处理报警
        self.alert_manager.handle_alert(alert_info)
        
        # 更新显示
        if self.table_display:
            self.table_display.add_alert(alert_info)
    
    def _setup_logging(self) -> None:
        """设置日志系统"""
        logging_settings = self.config_manager.get_logging_settings()
        
        # 配置根日志记录器
        log_level = getattr(logging, logging_settings.level.upper(), logging.INFO)
        
        # 创建格式化器
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # 配置根日志记录器
        root_logger = logging.getLogger()
        root_logger.setLevel(log_level)
        
        # 清除默认处理器
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        
        # 添加控制台处理器
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
        
        # 如果不是仅控制台模式，则创建日志目录和文件处理器
        if not logging_settings.console_only:
            log_dir = os.path.dirname(logging_settings.file_path) if logging_settings.file_path else "logs"
            if log_dir and not os.path.exists(log_dir):
                os.makedirs(log_dir)
            
            file_handler = logging.FileHandler(logging_settings.file_path or "monitor.log")
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)
        
        self.logger = logging.getLogger(__name__)
        self.logger.info("📝 日志系统初始化完成")
    
    def _verify_token_contracts(self) -> None:
        """验证所有配置的代币合约"""
        self.logger.info("🔍 验证代币合约...")
        
        addresses = self.config_manager.get_addresses()
        
        for address_config in addresses:
            for token_config in address_config.tokens:
                try:
                    is_valid = self.token_service.verify_token_contract(
                        token_config.contract_address
                    )
                    
                    if is_valid:
                        token_info = self.token_service.get_token_info(
                            token_config.contract_address
                        )
                        self.logger.info(
                            f"✅ {token_config.name} 合约验证成功: "
                            f"{token_info['symbol']} ({token_info['name']})"
                        )
                    else:
                        self.logger.warning(
                            f"⚠️ {token_config.name} 合约验证失败: "
                            f"{token_config.contract_address}"
                        )
                        
                except Exception as e:
                    self.logger.error(
                        f"❌ {token_config.name} 合约验证出错: {str(e)}"
                    )
    
    def start(self) -> None:
        """启动监控"""
        if self.is_running:
            self.logger.warning("⚠️ 监控已在运行中")
            return
        
        try:
            self.logger.info("🚀 启动ETH余额监控...")
            
            # 设置信号处理器
            signal.signal(signal.SIGINT, self._signal_handler)
            signal.signal(signal.SIGTERM, self._signal_handler)
            
            # 测试报警系统（静默模式）
            self.logger.info("🧪 测试报警系统...")
            original_sound_enabled = self.alert_manager.alert_settings.sound_enabled
            self.alert_manager.alert_settings.sound_enabled = False
            self.alert_manager.test_alert_system()
            self.alert_manager.alert_settings.sound_enabled = original_sound_enabled
            
            # 启动表格显示
            self.table_display.start_display()
            
            # 启动监控
            self.balance_monitor.start_monitoring()
            self.is_running = True
            
            # 启动数据更新线程
            import threading
            update_thread = threading.Thread(target=self._update_display_data, daemon=True)
            update_thread.start()
            
            # 保持程序运行
            try:
                while self.is_running:
                    import time
                    time.sleep(1)
            except KeyboardInterrupt:
                pass
                
        except Exception as e:
            self.logger.error(f"❌ 启动监控失败: {str(e)}")
            raise
    
    def stop(self) -> None:
        """停止监控"""
        if not self.is_running:
            return
        
        self.logger.info("🛑 停止ETH余额监控...")
        
        try:
            # 停止监控器
            if self.balance_monitor:
                self.balance_monitor.stop_monitoring()
            
            # 停止声音播放
            if self.alert_manager:
                self.alert_manager.stop_all_sounds()
            
            # 停止表格显示
            if self.table_display:
                self.table_display.stop_display()
            
            self.is_running = False
            
            # 显示统计信息
            self._show_final_statistics()
            
            self.logger.info("✅ 监控已停止")
            
        except Exception as e:
            self.logger.error(f"❌ 停止监控时出错: {str(e)}")
    
    def _update_display_data(self) -> None:
        """更新显示数据的线程"""
        while self.is_running:
            try:
                # 获取当前余额数据（实时计算时间差）
                if self.balance_monitor:
                    balance_data = self.balance_monitor.get_current_balances()
                    
                    # 为每个代币重新计算时间显示
                    for address, data in balance_data.items():
                        for token_name, token_data in data['tokens'].items():
                            if 'contract_address' in token_data:
                                # 实时计算时间差
                                time_since_update = self.balance_monitor.threshold_checker.get_time_since_last_update(
                                    data['address'],
                                    token_data['contract_address']
                                )
                                token_data['last_update_time'] = time_since_update
                    
                    self.table_display.update_balance_data(balance_data)
                    
                    # 更新统计信息
                    stats = self.balance_monitor.get_status()
                    if self.alert_manager:
                        alert_stats = self.alert_manager.get_alert_statistics()
                        stats.update(alert_stats)
                    self.table_display.update_stats(stats)
                
                import time
                time.sleep(2)  # 每2秒更新一次数据，让时间显示更及时
                
            except Exception as e:
                self.logger.error(f"❌ 更新显示数据失败: {str(e)}")
                import time
                time.sleep(5)
    
    def _signal_handler(self, signum, frame):
        """信号处理器"""
        self.logger.info(f"📨 接收到信号 {signum}")
        self.stop()
        sys.exit(0)
    
    def _show_initial_balances(self) -> None:
        """显示初始余额快照"""
        self.logger.info("📊 获取初始余额快照...")
        print("\\n📊 当前余额快照:")
        print("-" * 60)
        
        try:
            balances = self.balance_monitor.get_current_balances()
            
            for address, data in balances.items():
                print(f"\\n🏠 {data['name']} ({address[:10]}...{address[-8:]})")
                
                for token_name, token_data in data['tokens'].items():
                    if 'error' in token_data:
                        print(f"   ❌ {token_name}: 获取失败 - {token_data['error']}")
                    else:
                        balance = token_data['current_balance']
                        thresholds = token_data['thresholds']
                        print(f"   💰 {token_name}: {balance:.6f}")
                        print(f"      阈值: {thresholds['min']}-{thresholds['max']}")
                        print(f"      变化触发: ±{thresholds['change_up']}%/{thresholds['change_down']}%")
            
        except Exception as e:
            self.logger.error(f"❌ 获取余额快照失败: {str(e)}")
            print(f"❌ 获取余额快照失败: {str(e)}")
    
    def _show_final_statistics(self) -> None:
        """显示最终统计信息"""
        try:
            # 监控统计
            monitor_stats = self.balance_monitor.get_status()
            alert_stats = self.alert_manager.get_alert_statistics()
            
            print("\\n📈 监控统计:")
            print("-" * 40)
            print(f"监控地址数: {monitor_stats['addresses_count']}")
            print(f"代币对数: {monitor_stats['total_token_pairs']}")
            print(f"总报警次数: {alert_stats['total_alerts']}")
            
            if alert_stats['alerts_by_type']:
                print("\\n报警分类:")
                for alert_type, count in alert_stats['alerts_by_type'].items():
                    print(f"  {alert_type}: {count}次")
            
            if alert_stats['last_alert_time']:
                print(f"\\n最后报警时间: {alert_stats['last_alert_time'].strftime('%Y-%m-%d %H:%M:%S')}")
                
        except Exception as e:
            self.logger.error(f"❌ 显示统计信息失败: {str(e)}")
    
    def get_status(self) -> dict:
        """获取系统状态"""
        return {
            'is_running': self.is_running,
            'config_path': self.config_path,
            'web3_connected': self.web3_client.is_connected() if self.web3_client else False,
            'monitor_status': self.balance_monitor.get_status() if self.balance_monitor else None,
            'alert_stats': self.alert_manager.get_alert_statistics() if self.alert_manager else None
        }


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="ETH余额监控工具")
    parser.add_argument(
        "-c", "--config",
        default="config.yaml",
        help="配置文件路径 (默认: config.yaml)"
    )
    parser.add_argument(
        "-t", "--test",
        action="store_true",
        help="测试模式（仅验证配置和连接）"
    )
    parser.add_argument(
        "-v", "--version",
        action="version",
        version="ETH余额监控工具 v1.0.0"
    )
    
    args = parser.parse_args()
    
    try:
        # 检查配置文件是否存在
        if not os.path.exists(args.config):
            print(f"❌ 配置文件不存在: {args.config}")
            print("请确保配置文件存在并正确配置后再运行。")
            sys.exit(1)
        
        # 创建监控实例
        monitor = ETHBalanceMonitor(args.config)
        
        if args.test:
            print("✅ 测试模式 - 配置和连接验证完成")
            return
        
        # 启动监控
        monitor.start()
        
    except KeyboardInterrupt:
        print("\\n👋 用户中断")
    except Exception as e:
        print(f"❌ 程序运行失败: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
