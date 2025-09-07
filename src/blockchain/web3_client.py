"""
Web3客户端模块
负责与以太坊网络的基础连接和交互
"""

from web3 import Web3
from web3.providers import HTTPProvider
from typing import Optional
import time
import logging


class Web3Client:
    """Web3客户端类"""
    
    def __init__(self, provider_url: str, request_timeout: int = 30, retry_attempts: int = 3):
        """
        初始化Web3客户端
        
        Args:
            provider_url: 以太坊节点RPC URL
            request_timeout: 请求超时时间(秒)
            retry_attempts: 重试次数
        """
        self.provider_url = provider_url
        self.request_timeout = request_timeout
        self.retry_attempts = retry_attempts
        self.logger = logging.getLogger(__name__)
        
        # 初始化Web3连接
        self._web3 = None
        self._connect()
    
    def _connect(self) -> None:
        """建立Web3连接"""
        try:
            provider = HTTPProvider(
                self.provider_url,
                request_kwargs={'timeout': self.request_timeout}
            )
            self._web3 = Web3(provider)
            
            # 测试连接
            if self._web3.is_connected():
                self.logger.info(f"✅ Web3连接成功: {self.provider_url}")
                # 获取最新区块信息
                latest_block = self._web3.eth.block_number
                self.logger.info(f"📊 当前区块高度: {latest_block}")
            else:
                raise ConnectionError("Web3连接失败")
                
        except Exception as e:
            self.logger.error(f"❌ Web3连接失败: {str(e)}")
            raise
    
    def is_connected(self) -> bool:
        """检查连接状态"""
        try:
            return self._web3.is_connected() if self._web3 else False
        except Exception:
            return False
    
    def get_web3(self) -> Web3:
        """获取Web3实例"""
        if not self.is_connected():
            self.logger.warning("🔄 Web3连接已断开，尝试重新连接...")
            self._connect()
        return self._web3
    
    def execute_with_retry(self, func, *args, **kwargs):
        """
        带重试机制的函数执行
        
        Args:
            func: 要执行的函数
            *args: 函数参数
            **kwargs: 函数关键字参数
            
        Returns:
            函数执行结果
        """
        last_exception = None
        
        for attempt in range(self.retry_attempts):
            try:
                if not self.is_connected():
                    self._connect()
                
                return func(*args, **kwargs)
                
            except Exception as e:
                last_exception = e
                self.logger.warning(f"⚠️ 执行失败，第 {attempt + 1} 次尝试: {str(e)}")
                
                if attempt < self.retry_attempts - 1:
                    time.sleep(2 ** attempt)  # 指数退避
                    continue
                else:
                    break
        
        self.logger.error(f"❌ 执行失败，已达到最大重试次数: {str(last_exception)}")
        raise last_exception
    
    def get_balance(self, address: str) -> int:
        """
        获取地址的ETH余额
        
        Args:
            address: 以太坊地址
            
        Returns:
            余额（wei单位）
        """
        def _get_balance():
            checksum_address = Web3.to_checksum_address(address)
            return self._web3.eth.get_balance(checksum_address)
        
        return self.execute_with_retry(_get_balance)
    
    def call_contract_function(self, contract_address: str, abi: list, function_name: str, *args):
        """
        调用合约函数
        
        Args:
            contract_address: 合约地址
            abi: 合约ABI
            function_name: 函数名
            *args: 函数参数
            
        Returns:
            函数调用结果
        """
        def _call_function():
            checksum_address = Web3.to_checksum_address(contract_address)
            contract = self._web3.eth.contract(address=checksum_address, abi=abi)
            return getattr(contract.functions, function_name)(*args).call()
        
        return self.execute_with_retry(_call_function)
    
    def get_latest_block_number(self) -> int:
        """获取最新区块号"""
        def _get_block_number():
            return self._web3.eth.block_number
        
        return self.execute_with_retry(_get_block_number)
