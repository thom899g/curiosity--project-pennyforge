"""
Unified logging system for Project Pennyforge
"""
import logging
import sys
from datetime import datetime
from typing import Optional
from pennyforge.config import config

class PennyforgeLogger:
    """Custom logger with structured formatting"""
    
    def __init__(self, name: str = "pennyforge"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, config.agent.LOG_LEVEL))
        
        # Prevent duplicate handlers
        if not self.logger.handlers:
            self._setup_handlers()
    
    def _setup_handlers(self) -> None:
        """Configure console and file handlers"""
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_format = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(console_format)
        self.logger.addHandler(console_handler)
        
        # File handler for persistent logs
        try:
            file_handler = logging.FileHandler(f'pennyforge_{datetime.now().strftime("%Y%m%d")}.log')
            file_format = logging.Formatter(
                '%(asctime)s | %(levelname)s | %(name)s | %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            file_handler.setFormatter(file_format)
            self.logger.addHandler(file_handler)
        except Exception as e:
            self.logger.warning(f"Could not set up file logging: {e}")
    
    def log_trade(self, token: str, action: str, details: dict) -> None:
        """Structured trade logging"""
        self.logger.info(
            f"TRADE | {action.upper()} | Token: {token[:10]}... | "
            f"Details: {details}"
        )
    
    def log_system_event(self, event: str, data: Optional[dict] = None) -> None:
        """System-level event logging"""
        log_message = f"SYSTEM | {event}"
        if data:
            log_message += f" | Data: {data}"
        self.logger.info(log_message)
    
    def log_error_with_context(self, error: Exception, context: str) -> None:
        """Error logging with context for debugging"""
        self.logger.error(
            f"ERROR | Context: {context} | "
            f"Type: {type(error).__name__} | Message: {str(error)}"
        )
    
    def debug_mempool(self, event_type: str, data: dict) -> None:
        """Mempool event debugging"""
        self.logger.debug(
            f"MEMPOOL | {event_type} | {data.get('hash', '')[:10]}... | "
            f"Block: {data.get('blockNumber', 'pending')}"
        )

# Global logger instance
logger = PennyforgeLogger()