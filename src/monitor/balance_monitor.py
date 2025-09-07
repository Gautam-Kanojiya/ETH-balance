"""
余额监控模块
负责定期监控地址余额并触发阈值检查
"""

import time
import threading
from typing import List, Dict, Any
from datetime import datetime, timedelta
import logging

from ..config.config_manager import ConfigManager, AddressConfig
from ..blockchain.token_service import TokenService
from .threshold_checker import ThresholdChecker


class BalanceMonitor:
    """余额监控器"""
    
    def __init__(self, config_manager: ConfigManager, token_service: TokenService):
        """
        初始化余额监控器
        
        Args:
            config_manager: 配置管理器
            token_service: 代币服务
        """
        self.config_manager = config_manager
        self.token_service = token_service
        self.threshold_checker = ThresholdChecker()
        self.logger = logging.getLogger(__name__)
        
        # 监控状态
        self._is_running = False
        self._monitor_thread = None
        
        # 报警冷却期管理（内存存储）
        self._last_alert_time: Dict[str, datetime] = {}
        
        # 获取配置
        self.monitoring_settings = config_manager.get_monitoring_settings()
        self.alert_settings = config_manager.get_alert_settings()
        self.addresses = config_manager.get_addresses()
        
        # 事件回调
        self.on_threshold_triggered = None  # 阈值触发回调函数
    
    def start_monitoring(self) -> None:
        """开始监控"""
        if self._is_running:
            self.logger.warning("⚠️ 监控已在运行中")
            return
        
        self._is_running = True
        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()
        
        self.logger.info("🚀 余额监控已启动")
        self._log_monitoring_summary()
    
    def stop_monitoring(self) -> None:
        """停止监控"""
        if not self._is_running:
            self.logger.warning("⚠️ 监控未在运行")
            return
        
        self._is_running = False
        
        if self._monitor_thread and self._monitor_thread.is_alive():
            self._monitor_thread.join(timeout=5)
        
        self.logger.info("🛑 余额监控已停止")
    
    def _monitor_loop(self) -> None:
        """监控主循环"""
        self.logger.info(f"🔄 监控循环启动，检查间隔: {self.monitoring_settings.check_interval_seconds}秒")
        
        while self._is_running:
            try:
                self._check_all_balances()
                
                # 等待下一次检查
                for i in range(self.monitoring_settings.check_interval_seconds):
                    if not self._is_running:
                        break
                    time.sleep(1)
                    
            except Exception as e:
                self.logger.error(f"❌ 监控循环出错: {str(e)}")
                time.sleep(10)  # 出错后等待10秒再继续
    
    def _check_all_balances(self) -> None:
        """检查所有配置的地址余额"""
        self.logger.debug("🔍 开始检查所有地址余额...")
        
        for address_config in self.addresses:
            try:
                self._check_address_balances(address_config)
            except Exception as e:
                self.logger.error(f"❌ 检查地址 {address_config.address} 失败: {str(e)}")
        
        self.logger.debug("✅ 完成所有地址余额检查")
    
    def _check_address_balances(self, address_config: AddressConfig) -> None:
        """检查单个地址的所有代币余额"""
        address = address_config.address
        
        for token_config in address_config.tokens:
            try:
                # 获取当前余额
                current_balance = self.token_service.get_token_balance(
                    token_config.contract_address,
                    address,
                    token_config.decimals
                )
                
                # 检查阈值
                threshold_results = self.threshold_checker.check_balance_thresholds(
                    address=address,
                    token_address=token_config.contract_address,
                    token_name=token_config.name,
                    current_balance=current_balance,
                    min_threshold=token_config.thresholds.min_balance,
                    max_threshold=token_config.thresholds.max_balance,
                    change_up_threshold=token_config.thresholds.change_percentage_up,
                    change_down_threshold=token_config.thresholds.change_percentage_down,
                    time_window_minutes=token_config.thresholds.change_time_window_minutes
                )
                
                # 处理触发的阈值
                for result in threshold_results:
                    if result.triggered:
                        self._handle_threshold_triggered(address_config, token_config, result)
                
                self.logger.debug(f"📊 {address_config.name} - {token_config.name}: {current_balance:.6f}")
                
            except Exception as e:
                self.logger.error(f"❌ 检查 {address_config.name} 的 {token_config.name} 余额失败: {str(e)}")
    
    def _handle_threshold_triggered(self, address_config, token_config, threshold_result) -> None:
        """处理阈值触发事件"""
        # 检查报警冷却期
        alert_key = f"{address_config.address}_{token_config.contract_address}_{threshold_result.threshold_type}"
        
        if self._is_in_cooldown(alert_key):
            self.logger.debug(f"⏰ 报警在冷却期内，跳过: {alert_key}")
            return
        
        # 记录报警时间
        self._last_alert_time[alert_key] = datetime.now()
        
        # 构建报警信息
        alert_info = {
            'address_name': address_config.name,
            'address': address_config.address,
            'token_name': token_config.name,
            'token_address': token_config.contract_address,
            'threshold_result': threshold_result,
            'timestamp': datetime.now()
        }
        
        # 记录报警日志
        if self.alert_settings.log_alerts:
            self.logger.warning(f"🚨 阈值触发报警:\n{threshold_result.message}")
        
        # 调用回调函数
        if self.on_threshold_triggered:
            try:
                self.on_threshold_triggered(alert_info)
            except Exception as e:
                self.logger.error(f"❌ 报警回调函数执行失败: {str(e)}")
    
    def _is_in_cooldown(self, alert_key: str) -> bool:
        """检查是否在报警冷却期内"""
        if alert_key not in self._last_alert_time:
            return False
        
        last_alert = self._last_alert_time[alert_key]
        cooldown_period = timedelta(minutes=self.alert_settings.alert_cooldown_minutes)
        
        return datetime.now() - last_alert < cooldown_period
    
    def _log_monitoring_summary(self) -> None:
        """记录监控摘要信息"""
        total_addresses = len(self.addresses)
        total_tokens = sum(len(addr.tokens) for addr in self.addresses)
        
        self.logger.info(f"📋 监控摘要:")
        self.logger.info(f"   - 监控地址数: {total_addresses}")
        self.logger.info(f"   - 监控代币对数: {total_tokens}")
        self.logger.info(f"   - 检查间隔: {self.monitoring_settings.check_interval_seconds}秒")
        self.logger.info(f"   - 报警冷却期: {self.alert_settings.alert_cooldown_minutes}分钟")
        
        for i, addr in enumerate(self.addresses, 1):
            self.logger.info(f"   {i}. {addr.name} ({addr.address[:10]}...)")
            for token in addr.tokens:
                self.logger.info(f"      - {token.name} (阈值: {token.thresholds.min_balance}-{token.thresholds.max_balance}, "
                               f"变化: ±{token.thresholds.change_percentage_up}%/{token.thresholds.change_percentage_down}%, "
                               f"时间窗口: {token.thresholds.change_time_window_minutes}分钟)")
    
    def get_current_balances(self) -> Dict[str, Any]:
        """获取当前所有监控地址的余额快照"""
        balances = {}
        
        for address_config in self.addresses:
            address_data = {
                'name': address_config.name,
                'address': address_config.address,
                'tokens': {}
            }
            
            for token_config in address_config.tokens:
                try:
                    current_balance = self.token_service.get_token_balance(
                        token_config.contract_address,
                        address_config.address,
                        token_config.decimals
                    )
                    
                    # 获取历史信息
                    latest_balance = self.threshold_checker.get_latest_balance(
                        address_config.address,
                        token_config.contract_address
                    )
                    
                    # 获取上次更新时间
                    time_since_update = self.threshold_checker.get_time_since_last_update(
                        address_config.address,
                        token_config.contract_address
                    )
                    
                    address_data['tokens'][token_config.name] = {
                        'current_balance': current_balance,
                        'previous_balance': latest_balance,
                        'last_update_time': time_since_update,
                        'contract_address': token_config.contract_address,
                        'thresholds': {
                            'min': token_config.thresholds.min_balance,
                            'max': token_config.thresholds.max_balance,
                            'change_up': token_config.thresholds.change_percentage_up,
                            'change_down': token_config.thresholds.change_percentage_down,
                            'time_window': token_config.thresholds.change_time_window_minutes
                        }
                    }
                    
                except Exception as e:
                    address_data['tokens'][token_config.name] = {
                        'error': str(e)
                    }
            
            balances[address_config.address] = address_data
        
        return balances
    
    def reload_config(self) -> None:
        """重新加载配置"""
        self.logger.info("🔄 重新加载监控配置...")
        
        try:
            self.config_manager.reload_config()
            
            # 更新配置
            self.monitoring_settings = self.config_manager.get_monitoring_settings()
            self.alert_settings = self.config_manager.get_alert_settings()
            self.addresses = self.config_manager.get_addresses()
            
            self.logger.info("✅ 配置重新加载成功")
            self._log_monitoring_summary()
            
        except Exception as e:
            self.logger.error(f"❌ 配置重新加载失败: {str(e)}")
    
    def get_status(self) -> Dict[str, Any]:
        """获取监控状态信息"""
        threshold_stats = self.threshold_checker.get_statistics()
        
        return {
            'is_running': self._is_running,
            'check_interval': self.monitoring_settings.check_interval_seconds,
            'addresses_count': len(self.addresses),
            'total_token_pairs': sum(len(addr.tokens) for addr in self.addresses),
            'active_cooldowns': len(self._last_alert_time),
            'threshold_statistics': threshold_stats,
            'uptime': datetime.now() if self._is_running else None
        }
