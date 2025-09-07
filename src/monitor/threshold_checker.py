"""
阈值检查模块
负责检查余额是否触发设定的阈值条件
"""

from typing import Dict, Tuple, Optional, NamedTuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging


class ThresholdResult(NamedTuple):
    """阈值检查结果"""
    triggered: bool
    message: str
    threshold_type: str
    current_value: float
    threshold_value: float


@dataclass
class BalanceRecord:
    """余额记录"""
    balance: float
    timestamp: datetime
    block_number: Optional[int] = None


class ThresholdChecker:
    """阈值检查器"""
    
    def __init__(self):
        """初始化阈值检查器"""
        self.logger = logging.getLogger(__name__)
        
        # 余额历史记录（内存存储）
        # 格式: {(address, token_address): [BalanceRecord, ...]}
        self._balance_history: Dict[Tuple[str, str], list] = {}
    
    def check_balance_thresholds(
        self,
        address: str,
        token_address: str,
        token_name: str,
        current_balance: float,
        min_threshold: float,
        max_threshold: float,
        change_up_threshold: float,
        change_down_threshold: float,
        time_window_minutes: int = 5
    ) -> list:
        """
        检查余额阈值
        
        Args:
            address: 钱包地址
            token_address: 代币合约地址
            token_name: 代币名称
            current_balance: 当前余额
            min_threshold: 最小余额阈值
            max_threshold: 最大余额阈值
            change_up_threshold: 上涨百分比阈值
            change_down_threshold: 下跌百分比阈值
            time_window_minutes: 变化百分比监控时间窗口(分钟)
            
        Returns:
            触发的阈值检查结果列表
        """
        results = []
        key = (address, token_address)
        
        # 记录当前余额
        self._record_balance(key, current_balance)
        
        # 1. 检查绝对值阈值
        min_result = self._check_min_threshold(
            current_balance, min_threshold, token_name, address
        )
        if min_result.triggered:
            results.append(min_result)
        
        max_result = self._check_max_threshold(
            current_balance, max_threshold, token_name, address
        )
        if max_result.triggered:
            results.append(max_result)
        
        # 2. 检查变化百分比阈值（基于时间窗口）
        change_results = self._check_percentage_change_time_window(
            key, current_balance, change_up_threshold, change_down_threshold,
            time_window_minutes, token_name, address
        )
        results.extend(change_results)
        
        return results
    
    def _record_balance(self, key: Tuple[str, str], balance: float) -> None:
        """记录余额历史"""
        if key not in self._balance_history:
            self._balance_history[key] = []
        
        record = BalanceRecord(
            balance=balance,
            timestamp=datetime.now()
        )
        
        self._balance_history[key].append(record)
        
        # 保持最近100条记录（内存限制）
        if len(self._balance_history[key]) > 100:
            self._balance_history[key] = self._balance_history[key][-100:]
    
    def _check_min_threshold(
        self, current_balance: float, min_threshold: float,
        token_name: str, address: str
    ) -> ThresholdResult:
        """检查最小余额阈值"""
        if current_balance < min_threshold:
            message = (f"🔻 {token_name} 余额低于阈值！\n"
                      f"地址: {address[:10]}...\n"
                      f"当前余额: {current_balance:.6f}\n"
                      f"最小阈值: {min_threshold:.6f}")
            
            return ThresholdResult(
                triggered=True,
                message=message,
                threshold_type="min_balance",
                current_value=current_balance,
                threshold_value=min_threshold
            )
        
        return ThresholdResult(False, "", "min_balance", current_balance, min_threshold)
    
    def _check_max_threshold(
        self, current_balance: float, max_threshold: float,
        token_name: str, address: str
    ) -> ThresholdResult:
        """检查最大余额阈值"""
        if current_balance > max_threshold:
            message = (f"🔺 {token_name} 余额超过阈值！\n"
                      f"地址: {address[:10]}...\n"
                      f"当前余额: {current_balance:.6f}\n"
                      f"最大阈值: {max_threshold:.6f}")
            
            return ThresholdResult(
                triggered=True,
                message=message,
                threshold_type="max_balance",
                current_value=current_balance,
                threshold_value=max_threshold
            )
        
        return ThresholdResult(False, "", "max_balance", current_balance, max_threshold)
    
    def _check_percentage_change_time_window(
        self, key: Tuple[str, str], current_balance: float,
        up_threshold: float, down_threshold: float, time_window_minutes: int,
        token_name: str, address: str
    ) -> list:
        """检查基于时间窗口的变化百分比阈值"""
        results = []
        
        if key not in self._balance_history or len(self._balance_history[key]) < 2:
            return results
        
        # 获取当前时间
        current_time = datetime.now()
        
        # 找到时间窗口开始时间
        window_start_time = current_time - timedelta(minutes=time_window_minutes)
        
        # 在历史记录中找到最接近时间窗口开始的记录
        window_start_balance = None
        window_start_record = None
        
        for record in self._balance_history[key]:
            if record.timestamp >= window_start_time:
                window_start_record = record
                window_start_balance = record.balance
                break
        
        # 如果没有找到窗口开始时的记录，使用最早的记录
        if window_start_balance is None and self._balance_history[key]:
            window_start_record = self._balance_history[key][0]
            window_start_balance = window_start_record.balance
        
        if window_start_balance is None or window_start_balance <= 0:
            return results
        
        # 计算时间窗口内的变化百分比
        change_percent = ((current_balance - window_start_balance) / window_start_balance) * 100
        
        # 计算实际时间窗口
        actual_window_minutes = (current_time - window_start_record.timestamp).total_seconds() / 60
        
        # 检查上涨阈值
        if change_percent >= up_threshold:
            message = (f"📈 {token_name} 在{actual_window_minutes:.1f}分钟内大幅上涨！\n"
                      f"地址: {address[:10]}...\n"
                      f"当前余额: {current_balance:.6f}\n"
                      f"窗口开始余额: {window_start_balance:.6f}\n"
                      f"变化百分比: +{change_percent:.2f}%\n"
                      f"上涨阈值: {up_threshold:.2f}%\n"
                      f"时间窗口: {time_window_minutes}分钟")
            
            results.append(ThresholdResult(
                triggered=True,
                message=message,
                threshold_type="percentage_up_time_window",
                current_value=change_percent,
                threshold_value=up_threshold
            ))
        
        # 检查下跌阈值
        elif change_percent <= -down_threshold:
            message = (f"📉 {token_name} 在{actual_window_minutes:.1f}分钟内大幅下跌！\n"
                      f"地址: {address[:10]}...\n"
                      f"当前余额: {current_balance:.6f}\n"
                      f"窗口开始余额: {window_start_balance:.6f}\n"
                      f"变化百分比: {change_percent:.2f}%\n"
                      f"下跌阈值: -{down_threshold:.2f}%\n"
                      f"时间窗口: {time_window_minutes}分钟")
            
            results.append(ThresholdResult(
                triggered=True,
                message=message,
                threshold_type="percentage_down_time_window",
                current_value=abs(change_percent),
                threshold_value=down_threshold
            ))
        
        return results
    
    def _check_percentage_change(
        self, key: Tuple[str, str], current_balance: float,
        up_threshold: float, down_threshold: float,
        token_name: str, address: str
    ) -> list:
        """检查变化百分比阈值"""
        results = []
        
        if key not in self._balance_history or len(self._balance_history[key]) < 2:
            return results
        
        # 获取上一次余额记录
        previous_record = self._balance_history[key][-2]
        previous_balance = previous_record.balance
        
        if previous_balance <= 0:
            return results
        
        # 计算变化百分比
        change_percent = ((current_balance - previous_balance) / previous_balance) * 100
        
        # 检查上涨阈值
        if change_percent >= up_threshold:
            message = (f"📈 {token_name} 余额大幅上涨！\n"
                      f"地址: {address[:10]}...\n"
                      f"当前余额: {current_balance:.6f}\n"
                      f"上次余额: {previous_balance:.6f}\n"
                      f"变化百分比: +{change_percent:.2f}%\n"
                      f"上涨阈值: {up_threshold:.2f}%")
            
            results.append(ThresholdResult(
                triggered=True,
                message=message,
                threshold_type="percentage_up",
                current_value=change_percent,
                threshold_value=up_threshold
            ))
        
        # 检查下跌阈值
        elif change_percent <= -down_threshold:
            message = (f"📉 {token_name} 余额大幅下跌！\n"
                      f"地址: {address[:10]}...\n"
                      f"当前余额: {current_balance:.6f}\n"
                      f"上次余额: {previous_balance:.6f}\n"
                      f"变化百分比: {change_percent:.2f}%\n"
                      f"下跌阈值: -{down_threshold:.2f}%")
            
            results.append(ThresholdResult(
                triggered=True,
                message=message,
                threshold_type="percentage_down",
                current_value=abs(change_percent),
                threshold_value=down_threshold
            ))
        
        return results
    
    def get_balance_history(self, address: str, token_address: str) -> list:
        """获取余额历史记录"""
        key = (address, token_address)
        return self._balance_history.get(key, [])
    
    def get_latest_balance(self, address: str, token_address: str) -> Optional[float]:
        """获取最新余额记录"""
        history = self.get_balance_history(address, token_address)
        return history[-1].balance if history else None
    
    def get_latest_update_time(self, address: str, token_address: str) -> Optional[datetime]:
        """获取最新更新时间"""
        key = (address, token_address)
        history = self._balance_history.get(key, [])
        return history[-1].timestamp if history else None
    
    def get_time_since_last_update(self, address: str, token_address: str) -> str:
        """获取距离上次更新的时间描述"""
        last_time = self.get_latest_update_time(address, token_address)
        if not last_time:
            return "未查询"
        
        now = datetime.now()
        diff = now - last_time
        
        total_seconds = int(diff.total_seconds())
        
        if total_seconds < 60:
            return f"{total_seconds}秒前"
        elif total_seconds < 3600:
            minutes = total_seconds // 60
            return f"{minutes}分钟前"
        elif total_seconds < 86400:
            hours = total_seconds // 3600
            return f"{hours}小时前"
        else:
            days = total_seconds // 86400
            return f"{days}天前"
    
    def clear_history(self) -> None:
        """清空所有历史记录"""
        self._balance_history.clear()
        self.logger.info("🗑️ 余额历史记录已清空")
    
    def get_statistics(self) -> Dict[str, int]:
        """获取统计信息"""
        total_records = sum(len(records) for records in self._balance_history.values())
        return {
            'monitored_pairs': len(self._balance_history),
            'total_records': total_records,
            'memory_usage_kb': len(str(self._balance_history)) / 1024
        }
