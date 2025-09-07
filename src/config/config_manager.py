"""
配置管理模块
负责加载和验证YAML配置文件
"""

import yaml
import os
from typing import Dict, Any, List
from dataclasses import dataclass


@dataclass
class TokenThreshold:
    """代币阈值配置"""
    min_balance: float
    max_balance: float
    change_percentage_up: float
    change_percentage_down: float
    change_time_window_minutes: int = 5  # 默认5分钟时间窗口


@dataclass
class TokenConfig:
    """代币配置"""
    name: str
    contract_address: str
    decimals: int
    thresholds: TokenThreshold


@dataclass
class AddressConfig:
    """地址配置"""
    name: str
    address: str
    tokens: List[TokenConfig]


@dataclass
class RPCSettings:
    """RPC连接设置"""
    provider_url: str
    request_timeout: int
    retry_attempts: int


@dataclass
class MonitoringSettings:
    """监控设置"""
    check_interval_seconds: int
    memory_only: bool


@dataclass
class AlertSettings:
    """报警设置"""
    sound_enabled: bool
    sound_file_path: str
    sound_repeat_count: int
    sound_interval_seconds: int
    alert_cooldown_minutes: int
    log_alerts: bool
    sound_duration_seconds: int = 2


@dataclass
class LoggingSettings:
    """日志设置"""
    level: str
    console_only: bool


class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_path: str = "config.yaml"):
        """
        初始化配置管理器
        
        Args:
            config_path: 配置文件路径
        """
        self.config_path = config_path
        self._config_data = None
        self.load_config()
    
    def load_config(self) -> None:
        """加载配置文件"""
        try:
            if not os.path.exists(self.config_path):
                raise FileNotFoundError(f"配置文件不存在: {self.config_path}")
            
            with open(self.config_path, 'r', encoding='utf-8') as file:
                self._config_data = yaml.safe_load(file)
            
            self._validate_config()
            print(f"✅ 配置文件加载成功: {self.config_path}")
            
        except Exception as e:
            raise Exception(f"配置文件加载失败: {str(e)}")
    
    def _validate_config(self) -> None:
        """验证配置文件格式"""
        required_sections = ['rpc_settings', 'monitoring', 'addresses', 'alert_settings', 'logging']
        
        for section in required_sections:
            if section not in self._config_data:
                raise ValueError(f"配置文件缺少必需的节: {section}")
        
        # 验证地址配置
        if not self._config_data['addresses']:
            raise ValueError("至少需要配置一个监控地址")
        
        for addr in self._config_data['addresses']:
            if 'address' not in addr or 'tokens' not in addr:
                raise ValueError("地址配置必须包含 address 和 tokens 字段")
            
            if not addr['tokens']:
                raise ValueError(f"地址 {addr['address']} 必须至少配置一个代币")
    
    def get_rpc_settings(self) -> RPCSettings:
        """获取RPC设置"""
        rpc_data = self._config_data['rpc_settings']
        return RPCSettings(
            provider_url=rpc_data['provider_url'],
            request_timeout=rpc_data['request_timeout'],
            retry_attempts=rpc_data['retry_attempts']
        )
    
    def get_monitoring_settings(self) -> MonitoringSettings:
        """获取监控设置"""
        monitoring_data = self._config_data['monitoring']
        return MonitoringSettings(
            check_interval_seconds=monitoring_data['check_interval_seconds'],
            memory_only=monitoring_data['memory_only']
        )
    
    def get_alert_settings(self) -> AlertSettings:
        """获取报警设置"""
        alert_data = self._config_data['alert_settings']
        return AlertSettings(
            sound_enabled=alert_data['sound_enabled'],
            sound_file_path=alert_data['sound_file_path'],
            sound_repeat_count=alert_data['sound_repeat_count'],
            sound_interval_seconds=alert_data['sound_interval_seconds'],
            sound_duration_seconds=alert_data.get('sound_duration_seconds', 2),
            alert_cooldown_minutes=alert_data['alert_cooldown_minutes'],
            log_alerts=alert_data['log_alerts']
        )
    
    def get_logging_settings(self) -> LoggingSettings:
        """获取日志设置"""
        logging_data = self._config_data['logging']
        return LoggingSettings(
            level=logging_data['level'],
            console_only=logging_data['console_only']
        )
    
    def get_addresses(self) -> List[AddressConfig]:
        """获取所有地址配置"""
        addresses = []
        
        for addr_data in self._config_data['addresses']:
            tokens = []
            for token_data in addr_data['tokens']:
                threshold = TokenThreshold(
                    min_balance=token_data['thresholds']['min_balance'],
                    max_balance=token_data['thresholds']['max_balance'],
                    change_percentage_up=token_data['thresholds']['change_percentage_up'],
                    change_percentage_down=token_data['thresholds']['change_percentage_down'],
                    change_time_window_minutes=token_data['thresholds'].get('change_time_window_minutes', 5)
                )
                
                token = TokenConfig(
                    name=token_data['name'],
                    contract_address=token_data['contract_address'],
                    decimals=token_data['decimals'],
                    thresholds=threshold
                )
                tokens.append(token)
            
            address_config = AddressConfig(
                name=addr_data['name'],
                address=addr_data['address'],
                tokens=tokens
            )
            addresses.append(address_config)
        
        return addresses
    
    def reload_config(self) -> None:
        """重新加载配置文件"""
        print("🔄 重新加载配置文件...")
        self.load_config()
