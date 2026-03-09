"""
Web3 client for Base L2 with enhanced error handling and connection management
"""
from web3 import Web3, HTTPProvider
from web3.middleware import geth_poa_middleware
from web3.exceptions import TransactionNotFound, ContractLogicError
from typing import Optional, Dict, Any, Tuple
import time
from decimal import Decimal

from pennyforge.config import config
from pennyforge.logger import logger

class BlockchainClient:
    """Robust Web3 client with connection pooling and retry logic"""
    
    def __init__(self):
        self.w3 = None
        self._last_block = 0
        self._gas_price_cache = {"price": 0, "timestamp": 0}
        self._initialize_web3()
    
    def _initialize_web3(self) -> None:
        """Initialize Web3 connection with middleware"""
        try:
            # Main RPC connection
            self.w3 = Web3(HTTPProvider(
                config.blockchain.RPC_URL,
                request_kwargs={'timeout': 30}
            ))
            
            # Flashbots RPC for protected transactions
            self