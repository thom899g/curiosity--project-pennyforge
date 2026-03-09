"""
Project Pennyforge v2.0 Configuration
Centralized configuration management with environment validation
"""
import os
from dataclasses import dataclass
from typing import Optional
from dotenv import load_dotenv
import logging

# Load environment variables first
load_dotenv()

@dataclass
class BlockchainConfig:
    """Blockchain network configuration"""
    RPC_URL: str
    WS_URL: str
    CHAIN_ID: int = 8453  # Base mainnet
    CONTRACT_ADDRESS: Optional[str] = None
    FLASHBOTS_PROTECT_RPC: str = "https://rpc.flashbots.net"

@dataclass
class TradingConfig:
    """Trading parameters with safety constraints"""
    MAX_TRADE_SIZE_ETH: float = 0.001  # $5 initial, 0.1% trade size
    MAX_SLIPPAGE_PERCENT: float = 2.0
    MIN_PROFIT_THRESHOLD_MULTIPLIER: float = 3.0
    GAS_BUFFER_PERCENT: float = 20.0
    COOLDOWN_BLOCKS: int = 10
    
    # Circuit breakers
    MAX_DAILY_DRAWDOWN_PERCENT: float = 2.0
    MAX_CONSECUTIVE_FAILS: int = 5
    GAS_PRICE_THRESHOLD_ETH: float = 0.01
    
    # Profit distribution
    PROFIT_SWEEP_PERCENT: float = 0.9  # 90% to hardware fund

@dataclass
class FirebaseConfig:
    """Firebase configuration for state management"""
    CREDENTIALS_PATH: str
    PROJECT_ID: str
    DATABASE_URL: str
    
    # Collection names
    TRADES_COLLECTION: str = "trades"
    SYSTEM_STATE_COLLECTION: str = "system_state"
    MARKET_CONDITIONS_COLLECTION: str = "market_conditions"

@dataclass
class APIConfig:
    """External API configurations"""
    DEXSCREENER_API: str = "https://api.dexscreener.com/latest/dex"
    BASESCAN_API: str = "https://api.basescan.org/api"
    TWITTER_API_KEY: Optional[str] = None
    TELEGRAM_API_KEY: Optional[str] = None

@dataclass
class AgentConfig:
    """Agent runtime configuration"""
    LOG_LEVEL: str = "INFO"
    HEALTH_CHECK_INTERVAL: int = 60  # seconds
    MAX_RETRIES: int = 3
    RETRY_DELAY: int = 5  # seconds
    
    # AWS configuration for KMS
    AWS_REGION: str = "us-east-1"
    AWS_KMS_KEY_ID: Optional[str] = None

class Config:
    """Master configuration class with validation"""
    
    def __init__(self):
        self.validate_environment()
        
        self.blockchain = BlockchainConfig(
            RPC_URL=os.getenv("RPC_URL", ""),
            WS_URL=os.getenv("WS_URL", ""),
            CONTRACT_ADDRESS=os.getenv("CONTRACT_ADDRESS")
        )
        
        self.trading = TradingConfig()
        
        self.firebase = FirebaseConfig(
            CREDENTIALS_PATH=os.getenv("FIREBASE_CREDENTIALS_PATH", ""),
            PROJECT_ID=os.getenv("FIREBASE_PROJECT_ID", ""),
            DATABASE_URL=os.getenv("FIREBASE_DATABASE_URL", "")
        )
        
        self.api = APIConfig(
            DEXSCREENER_API=os.getenv("DEXSCREENER_API", "https://api.dexscreener.com/latest/dex"),
            TWITTER_API_KEY=os.getenv("TWITTER_API_KEY"),
            TELEGRAM_API_KEY=os.getenv("TELEGRAM_API_KEY")
        )
        
        self.agent = AgentConfig(
            LOG_LEVEL=os.getenv("LOG_LEVEL", "INFO"),
            AWS_KMS_KEY_ID=os.getenv("AWS_KMS_KEY_ID")
        )
        
        # Validate critical configurations
        self.validate_configs()
    
    def validate_environment(self) -> None:
        """Validate required environment variables"""
        required_vars = [
            "RPC_URL",
            "WS_URL", 
            "FIREBASE_CREDENTIALS_PATH",
            "FIREBASE_PROJECT_ID",
            "FIREBASE_DATABASE_URL"
        ]
        
        missing = [var for var in required_vars if not os.getenv(var)]
        if missing:
            raise ValueError(f"Missing required environment variables: {missing}")
    
    def validate_configs(self) -> None:
        """Validate configuration values"""
        # Trading parameter validation
        if self.trading.MAX_TRADE_SIZE_ETH <= 0:
            raise ValueError("MAX_TRADE_SIZE_ETH must be positive")
        
        if not (0 < self.trading.MAX_SLIPPAGE_PERCENT <= 100):
            raise ValueError("MAX_SLIPPAGE_PERCENT must be between 0 and 100")
        
        if not os.path.exists(self.firebase.CREDENTIALS_PATH):
            raise FileNotFoundError(f"Firebase credentials not found at: {self.firebase.CREDENTIALS_PATH}")

# Global configuration instance
config = Config()