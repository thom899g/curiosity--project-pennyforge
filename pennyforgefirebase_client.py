"""
Firebase Firestore client for state management and transparency
"""
import json
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
from google.cloud import firestore
from google.oauth2 import service_account
import asyncio
from concurrent.futures import ThreadPoolExecutor

from pennyforge.config import config
from pennyforge.logger import logger

class FirebaseClient:
    """Thread-safe Firebase Firestore client with connection pooling"""
    
    def __init__(self):
        self._client = None
        self._executor = ThreadPoolExecutor(max_workers=5)
        self._connected = False
        self._initialize_client()
    
    def _initialize_client(self) -> None:
        """Initialize Firebase client with credentials"""
        try:
            credentials = service_account.Credentials.from_service_account_file(
                config.firebase.CREDENTIALS_PATH
            )
            
            self._client = firestore.Client(
                project=config.firebase.PROJECT_ID,
                credentials=credentials,
                database=config.firebase.DATABASE_URL
            )
            
            self._connected = True
            logger.log_system_event("Firebase client initialized successfully")
            
        except Exception as e:
            logger.log_error_with_context(e, "Firebase initialization")
            self._connected = False
            raise
    
    @property
    def client(self) -> firestore.Client:
        """Get thread-safe client instance"""
        if not self._connected or not self._client:
            self._initialize_client()
        return self._client
    
    def update_system_state(self, state_data: Dict[str, Any]) -> bool:
        """Update system state with atomic transaction"""
        try:
            doc_ref = self.client.collection(
                config.firebase.SYSTEM_STATE_COLLECTION
            ).document("current")
            
            # Add timestamp and ensure data integrity
            state_data.update({
                "last_updated": datetime.now(timezone.utc),
                "agent_version": "v2.0.0"
            })
            
            # Use transaction for atomic update
            transaction = self.client.transaction()
            
            @firestore.transactional
            def update_in_transaction(transaction, doc_ref, new_data):
                snapshot = doc_ref.get(transaction=transaction)
                if snapshot.exists:
                    # Merge with existing data
                    existing = snapshot.to_dict()
                    new_data = {**existing, **new_data}
                transaction.set(doc_ref, new_data)
            
            update_in_transaction(transaction, doc_ref, state_data)
            return True
            
        except Exception as e:
            logger.log_error_with_context(e, "System state update")
            return False
    
    def log_trade(self, trade_data: Dict[str, Any]) -> str:
        """
        Log trade to Firestore with unique ID
        Returns document ID for reference
        """
        try:
            # Generate unique trade ID
            trade_id = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{trade_data.get('token', '')[:8]}"
            
            # Prepare trade document
            trade_doc = {
                "trade_id": trade_id,
                "timestamp": datetime.now(timezone.utc),
                "status": "pending",
                **trade_data
            }
            
            # Write to Firestore
            doc_ref = self.client.collection(
                config.firebase.TRADES_COLLECTION
            ).document(trade_id)
            
            doc_ref.set(trade_doc)
            
            logger.log_trade(
                trade_data.get("token", "unknown"),
                trade_data.get("action", "unknown"),
                {"trade_id": trade_id, "status": "pending"}
            )
            
            return trade_id
            
        except Exception as e:
            logger.log_error_with_context(e, "Trade logging")
            raise
    
    def update_trade_status(self, trade_id: str, updates: Dict[str, Any]) -> bool:
        """Update trade status and details"""
        try:
            doc_ref = self.client.collection(
                config.firebase.TRADES_COLLECTION
            ).document(trade_id)
            
            updates["last_updated"] = datetime.now(timezone.utc)
            
            # Use merge to preserve existing fields
            doc_ref.set(updates, merge=True)
            return True
            
        except Exception as e:
            logger.log_error_with_context(e, "Trade status update")
            return False
    
    def get_market_conditions(self) -> Optional[Dict[str, Any]]:
        """Retrieve current market conditions"""
        try:
            doc_ref = self.client.collection(
                config.firebase.MARKET_CONDITIONS_COLLECTION
            ).document("latest")
            
            doc = doc_ref.get()
            return doc.to_dict() if doc.exists else None
            
        except Exception as e:
            logger.log_error_with_context(e, "Market conditions fetch")
            return None
    
    def set_circuit_breaker(self, breaker_type: str, active: bool, reason: str) -> bool:
        """Activate or deactivate circuit breaker"""
        try:
            state_update = {
                "circuit_breakers": {
                    breaker_type: {
                        "active": active,
                        "triggered_at": datetime.now(timezone.utc) if active else None,
                        "reason": reason
                    }
                }
            }
            
            return self.update_system_state(state_update)
            
        except Exception as e:
            logger.log_error_with_context(e, "Circuit breaker update")
            return False
    
    def get_active_circuit_breakers(self) -> Dict[str, bool]:
        """Retrieve all active circuit breakers"""
        try:
            doc_ref = self.client.collection(
                config.firebase.SYSTEM_STATE_COLLECTION
            ).document("current")
            
            doc = doc_ref.get()
            if doc.exists:
                data = doc.to_dict()
                breakers = data.get("circuit_breakers", {})
                return {k: v.get("active", False) for k, v in breakers.items()}
            return {}
            
        except Exception as e:
            logger.log_error_with_context(e, "Circuit breakers fetch")
            return {}

# Global Firebase client instance
firebase_client = FirebaseClient()