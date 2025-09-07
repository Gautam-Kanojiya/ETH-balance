"""
报警管理模块
负责管理和协调各种报警方式
"""

import logging
from datetime import datetime
from typing import Dict, Any, Callable, Optional

from .sound_player import SoundPlayer
from ..config.config_manager import AlertSettings


class AlertManager:
    """报警管理器"""
    
    def __init__(self, alert_settings: AlertSettings):
        """
        初始化报警管理器
        
        Args:
            alert_settings: 报警设置
        """
        self.alert_settings = alert_settings
        self.logger = logging.getLogger(__name__)
        
        # 初始化声音播放器
        self.sound_player = SoundPlayer()
        
        # 报警统计（内存存储）
        self._alert_stats = {
            'total_alerts': 0,
            'alerts_by_type': {},
            'last_alert_time': None
        }
        
        # 自定义通知回调函数
        self.custom_notification_handlers: list = []
        
        self.logger.info("🚨 报警管理器初始化完成")
    
    def handle_alert(self, alert_info: Dict[str, Any]) -> None:
        """
        处理报警事件
        
        Args:
            alert_info: 报警信息字典，包含：
                - address_name: 地址名称
                - address: 地址
                - token_name: 代币名称
                - token_address: 代币地址
                - threshold_result: 阈值检查结果
                - timestamp: 时间戳
        """
        try:
            # 更新统计信息
            self._update_alert_stats(alert_info)
            
            # 构建报警消息
            alert_message = self._build_alert_message(alert_info)
            
            # 输出到控制台
            self._console_alert(alert_message)
            
            # 播放声音提醒
            if self.alert_settings.sound_enabled:
                self._play_sound_alert()
            
            # 执行自定义通知处理器
            self._execute_custom_handlers(alert_info, alert_message)
            
            self.logger.info(f"📢 报警处理完成 - {alert_info['token_name']} @ {alert_info['address_name']}")
            
        except Exception as e:
            self.logger.error(f"❌ 报警处理失败: {str(e)}")
    
    def _update_alert_stats(self, alert_info: Dict[str, Any]) -> None:
        """更新报警统计信息"""
        self._alert_stats['total_alerts'] += 1
        self._alert_stats['last_alert_time'] = alert_info['timestamp']
        
        threshold_type = alert_info['threshold_result'].threshold_type
        if threshold_type not in self._alert_stats['alerts_by_type']:
            self._alert_stats['alerts_by_type'][threshold_type] = 0
        self._alert_stats['alerts_by_type'][threshold_type] += 1
    
    def _build_alert_message(self, alert_info: Dict[str, Any]) -> str:
        """构建报警消息"""
        threshold_result = alert_info['threshold_result']
        timestamp = alert_info['timestamp'].strftime("%Y-%m-%d %H:%M:%S")
        
        message_lines = [
            "=" * 60,
            "🚨 ETH余额监控报警 🚨",
            "=" * 60,
            f"时间: {timestamp}",
            f"地址名称: {alert_info['address_name']}",
            f"地址: {alert_info['address'][:20]}...{alert_info['address'][-10:]}",
            f"代币: {alert_info['token_name']}",
            f"报警类型: {self._get_alert_type_description(threshold_result.threshold_type)}",
            "",
            threshold_result.message,
            "",
            "=" * 60
        ]
        
        return "\\n".join(message_lines)
    
    def _get_alert_type_description(self, threshold_type: str) -> str:
        """获取报警类型描述"""
        type_descriptions = {
            'min_balance': '余额低于最小阈值',
            'max_balance': '余额超过最大阈值',
            'percentage_up': '余额上涨百分比触发',
            'percentage_down': '余额下跌百分比触发',
            'percentage_up_time_window': '时间窗口内余额大幅上涨',
            'percentage_down_time_window': '时间窗口内余额大幅下跌'
        }
        return type_descriptions.get(threshold_type, threshold_type)
    
    def _console_alert(self, message: str) -> None:
        """输出控制台报警"""
        print(f"\\n{message}\\n")
        
        # 如果启用了报警日志记录
        if self.alert_settings.log_alerts:
            self.logger.warning(f"报警触发:\\n{message}")
    
    def _play_sound_alert(self) -> None:
        """播放声音报警"""
        try:
            self.sound_player.play_sound(
                sound_file=self.alert_settings.sound_file_path,
                repeat_count=self.alert_settings.sound_repeat_count,
                interval=self.alert_settings.sound_interval_seconds,
                duration=self.alert_settings.sound_duration_seconds
            )
        except Exception as e:
            self.logger.error(f"❌ 声音报警播放失败: {str(e)}")
    
    def _execute_custom_handlers(self, alert_info: Dict[str, Any], alert_message: str) -> None:
        """执行自定义通知处理器"""
        for handler in self.custom_notification_handlers:
            try:
                handler(alert_info, alert_message)
            except Exception as e:
                self.logger.error(f"❌ 自定义通知处理器执行失败: {str(e)}")
    
    def add_notification_handler(self, handler: Callable[[Dict[str, Any], str], None]) -> None:
        """
        添加自定义通知处理器
        
        Args:
            handler: 通知处理函数，接收 (alert_info, alert_message) 参数
        """
        self.custom_notification_handlers.append(handler)
        self.logger.info(f"✅ 添加自定义通知处理器: {handler.__name__}")
    
    def remove_notification_handler(self, handler: Callable) -> bool:
        """
        移除自定义通知处理器
        
        Args:
            handler: 要移除的处理器函数
            
        Returns:
            是否成功移除
        """
        try:
            self.custom_notification_handlers.remove(handler)
            self.logger.info(f"✅ 移除自定义通知处理器: {handler.__name__}")
            return True
        except ValueError:
            self.logger.warning(f"⚠️ 未找到要移除的通知处理器: {handler.__name__}")
            return False
    
    def test_alert_system(self) -> bool:
        """
        测试报警系统
        
        Returns:
            测试是否成功
        """
        self.logger.info("🧪 开始测试报警系统...")
        
        try:
            # 测试声音播放
            if self.alert_settings.sound_enabled:
                sound_test_result = self.sound_player.test_sound(self.alert_settings.sound_file_path)
                if not sound_test_result:
                    self.logger.warning("⚠️ 声音测试失败")
            
            # 创建测试报警信息
            test_alert_info = {
                'address_name': '测试地址',
                'address': '0x0000000000000000000000000000000000000000',
                'token_name': '测试代币',
                'token_address': '0x0000000000000000000000000000000000000000',
                'threshold_result': type('ThresholdResult', (), {
                    'triggered': True,
                    'message': '这是一个测试报警消息',
                    'threshold_type': 'test',
                    'current_value': 100.0,
                    'threshold_value': 50.0
                })(),
                'timestamp': datetime.now()
            }
            
            # 处理测试报警（不播放声音）
            original_sound_enabled = self.alert_settings.sound_enabled
            self.alert_settings.sound_enabled = False
            
            self.handle_alert(test_alert_info)
            
            # 恢复声音设置
            self.alert_settings.sound_enabled = original_sound_enabled
            
            self.logger.info("✅ 报警系统测试完成")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 报警系统测试失败: {str(e)}")
            return False
    
    def get_alert_statistics(self) -> Dict[str, Any]:
        """获取报警统计信息"""
        return {
            'total_alerts': self._alert_stats['total_alerts'],
            'alerts_by_type': self._alert_stats['alerts_by_type'].copy(),
            'last_alert_time': self._alert_stats['last_alert_time'],
            'sound_enabled': self.alert_settings.sound_enabled,
            'sound_player_status': self.sound_player.get_system_info(),
            'custom_handlers_count': len(self.custom_notification_handlers)
        }
    
    def reset_statistics(self) -> None:
        """重置报警统计信息"""
        self._alert_stats = {
            'total_alerts': 0,
            'alerts_by_type': {},
            'last_alert_time': None
        }
        self.logger.info("🗑️ 报警统计信息已重置")
    
    def update_settings(self, new_alert_settings: AlertSettings) -> None:
        """
        更新报警设置
        
        Args:
            new_alert_settings: 新的报警设置
        """
        self.alert_settings = new_alert_settings
        self.logger.info("🔄 报警设置已更新")
    
    def stop_all_sounds(self) -> None:
        """停止所有声音播放"""
        self.sound_player.stop_playing()
        self.logger.info("🛑 已停止所有声音播放")
