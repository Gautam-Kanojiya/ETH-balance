"""
代币服务模块
负责ERC20代币相关的操作
"""

from typing import Dict, Any
import logging
from .web3_client import Web3Client


class TokenService:
    """代币服务类"""
    
    # ERC20标准ABI（仅包含必需的方法）
    ERC20_ABI = [
        {
            "constant": True,
            "inputs": [{"name": "_owner", "type": "address"}],
            "name": "balanceOf",
            "outputs": [{"name": "balance", "type": "uint256"}],
            "payable": False,
            "stateMutability": "view",
            "type": "function"
        },
        {
            "constant": True,
            "inputs": [],
            "name": "decimals",
            "outputs": [{"name": "", "type": "uint8"}],
            "payable": False,
            "stateMutability": "view",
            "type": "function"
        },
        {
            "constant": True,
            "inputs": [],
            "name": "symbol",
            "outputs": [{"name": "", "type": "string"}],
            "payable": False,
            "stateMutability": "view",
            "type": "function"
        },
        {
            "constant": True,
            "inputs": [],
            "name": "name",
            "outputs": [{"name": "", "type": "string"}],
            "payable": False,
            "stateMutability": "view",
            "type": "function"
        }
    ]
    
    def __init__(self, web3_client: Web3Client):
        """
        初始化代币服务
        
        Args:
            web3_client: Web3客户端实例
        """
        self.web3_client = web3_client
        self.logger = logging.getLogger(__name__)
        
        # 代币信息缓存（内存存储）
        self._token_cache: Dict[str, Dict[str, Any]] = {}
    
    def get_token_balance(self, token_address: str, wallet_address: str, decimals: int = None) -> float:
        """
        获取指定地址的代币余额
        
        Args:
            token_address: 代币合约地址
            wallet_address: 钱包地址
            decimals: 代币精度（如果提供则使用，否则从合约获取）
            
        Returns:
            代币余额（已根据精度转换）
        """
        try:
            # 确保地址格式正确
            from web3 import Web3
            token_address = Web3.to_checksum_address(token_address)
            wallet_address = Web3.to_checksum_address(wallet_address)
            
            # 获取原始余额
            raw_balance = self.web3_client.call_contract_function(
                token_address,
                self.ERC20_ABI,
                'balanceOf',
                wallet_address
            )
            
            # 获取或使用代币精度
            if decimals is None:
                decimals = self.get_token_decimals(token_address)
            
            # 转换为人类可读的余额
            balance = raw_balance / (10 ** decimals)
            
            self.logger.debug(f"📈 获取余额 - 地址: {wallet_address[:10]}..., "
                            f"代币: {token_address[:10]}..., "
                            f"余额: {balance:.6f}")
            
            return balance
            
        except Exception as e:
            self.logger.error(f"❌ 获取代币余额失败: {str(e)}")
            raise
    
    def get_token_info(self, token_address: str) -> Dict[str, Any]:
        """
        获取代币基本信息
        
        Args:
            token_address: 代币合约地址
            
        Returns:
            代币信息字典，包含name, symbol, decimals
        """
        # 确保地址格式正确
        from web3 import Web3
        token_address = Web3.to_checksum_address(token_address)
        
        # 检查缓存
        if token_address in self._token_cache:
            return self._token_cache[token_address]
        
        try:
            # 获取代币信息
            name = self.web3_client.call_contract_function(
                token_address, self.ERC20_ABI, 'name'
            )
            symbol = self.web3_client.call_contract_function(
                token_address, self.ERC20_ABI, 'symbol'
            )
            decimals = self.web3_client.call_contract_function(
                token_address, self.ERC20_ABI, 'decimals'
            )
            
            token_info = {
                'name': name,
                'symbol': symbol,
                'decimals': decimals,
                'address': token_address
            }
            
            # 缓存信息
            self._token_cache[token_address] = token_info
            
            self.logger.info(f"ℹ️ 代币信息 - {symbol} ({name}), 精度: {decimals}")
            
            return token_info
            
        except Exception as e:
            self.logger.error(f"❌ 获取代币信息失败: {str(e)}")
            raise
    
    def get_token_decimals(self, token_address: str) -> int:
        """
        获取代币精度
        
        Args:
            token_address: 代币合约地址
            
        Returns:
            代币精度
        """
        token_info = self.get_token_info(token_address)
        return token_info['decimals']
    
    def get_token_symbol(self, token_address: str) -> str:
        """
        获取代币符号
        
        Args:
            token_address: 代币合约地址
            
        Returns:
            代币符号
        """
        token_info = self.get_token_info(token_address)
        return token_info['symbol']
    
    def verify_token_contract(self, token_address: str) -> bool:
        """
        验证代币合约是否有效
        
        Args:
            token_address: 代币合约地址
            
        Returns:
            是否为有效的ERC20代币合约
        """
        try:
            # 尝试调用ERC20标准方法
            self.get_token_info(token_address)
            return True
            
        except Exception as e:
            self.logger.warning(f"⚠️ 代币合约验证失败: {token_address} - {str(e)}")
            return False
    
    def clear_cache(self) -> None:
        """清空代币信息缓存"""
        self._token_cache.clear()
        self.logger.info("🗑️ 代币缓存已清空")
    
    def get_cache_info(self) -> Dict[str, int]:
        """获取缓存统计信息"""
        return {
            'cached_tokens': len(self._token_cache),
            'cache_size_kb': len(str(self._token_cache)) / 1024
        }
