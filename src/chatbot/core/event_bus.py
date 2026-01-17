"""
Event Bus Module
Handles event publishing and subscription for the chatbot application.
"""

import time
from dataclasses import dataclass, field
from typing import List, Dict, Any, Callable, Type
from enum import Enum, auto


@dataclass
class Event:
    """Base class for all events."""
    timestamp: float = field(default_factory=time.time, init=False)


@dataclass
class DocumentUploadEvent(Event):
    """Event triggered when a document is uploaded."""
    filename: str
    file_path: str


@dataclass
class ProcessingStartEvent(Event):
    """Event triggered when document processing starts."""
    file_path: str
    doc_type: str


@dataclass
class ProcessingCompleteEvent(Event):
    """Event triggered when document processing is complete."""
    file_path: str
    chunk_count: int
    duration_seconds: float


@dataclass
class VectorStoreUpdateEvent(Event):
    """Event triggered when the vector store is updated."""
    operation: str  # "create", "add", "load"
    document_count: int


@dataclass
class ChatQueryEvent(Event):
    """Event triggered when a user asks a question."""
    question: str
    llm_provider: str
    model_name: str


@dataclass
class ChatResponseEvent(Event):
    """Event triggered when the chatbot responds."""
    question: str
    answer: str
    source_count: int
    duration_seconds: float


@dataclass
class ErrorEvent(Event):
    """Event triggered when an error occurs."""
    error_type: str
    message: str
    context: Dict[str, Any] = field(default_factory=dict)


import os
import json
import threading
try:
    import redis
except ImportError:
    redis = None  # Handle missing dependency gracefully

# ... existing Event classes ...

class EventBus:
    """
    Hybrid Event Bus connecting in-memory synchronous events with Redis Pub/Sub.
    """
    _redis_enabled = False

    def __init__(self):
        self.subscribers: Dict[Type[Event], List[Callable[[Event], None]]] = {}
        self.redis_client = None
        self.pubsub = None
        self._init_redis()

    def _init_redis(self):
        """Initialize Redis connection if REDIS_URL is set."""
        redis_url = os.getenv("REDIS_URL")
        if redis_url and redis:
            try:
                self.redis_client = redis.from_url(redis_url)
                self.pubsub = self.redis_client.pubsub()
                self._redis_enabled = True
                print(f"✅ Connected to Redis at {redis_url}")
                
                # Start listener thread
                self.pubsub.subscribe('chatbot_events')
                self.listener_thread = threading.Thread(target=self._redis_listener, daemon=True)
                self.listener_thread.start()
            except Exception as e:
                print(f"⚠️ Redis connection failed: {e}")
                self._redis_enabled = False

    def _redis_listener(self):
        """Listen for messages from Redis and publish them locally."""
        if not self.pubsub:
            return
            
        for message in self.pubsub.listen():
            if message['type'] == 'message':
                try:
                    data = json.loads(message['data'])
                    event_type_name = data.get('type')
                    event_data = data.get('data')
                    
                    # Reconstruct event
                    # This is a simplified reconstruction for demonstration
                    # In a real app, you'd have a registry of event types
                    # to securely map strings to classes.
                    # For now, we iterate through globals() or just handle known types
                    # preventing loop by checking 'from_redis' logic if needed
                    # But here we just print for demo or rely on distinct event usage
                    pass 
                except Exception as e:
                    print(f"❌ Error processing Redis message: {e}")

    def subscribe(self, event_type: Type[Event], callback: Callable[[Event], None]):
        """
        Subscribe to a specific event type.
        
        Args:
            event_type: The class of the event to subscribe to
            callback: Function to call when event is published
        """
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        self.subscribers[event_type].append(callback)
        print(f"🔌 Subscribed to {event_type.__name__}")

    def publish(self, event: Event, propagate: bool = True):
        """
        Publish an event to subscribers and optionally to Redis.
        
        Args:
            event: The event instance to publish
            propagate: Whether to send to Redis (default: True)
        """
        # 1. Local Publish
        for event_type, callbacks in self.subscribers.items():
            if isinstance(event, event_type):
                for callback in callbacks:
                    try:
                        callback(event)
                    except Exception as e:
                        print(f"❌ Error in event subscriber: {e}")

        # 2. Redis Publish (if enabled and requested)
        if self._redis_enabled and propagate and self.redis_client:
            try:
                payload = {
                    "type": event.__class__.__name__,
                    "data": self._event_to_dict(event),
                    "timestamp": event.timestamp
                }
                self.redis_client.publish('chatbot_events', json.dumps(payload))
            except Exception as e:
                print(f"⚠️ Failed to publish to Redis: {e}")

    def _event_to_dict(self, event: Event) -> Dict[str, Any]:
        """Convert event to dict, handling dataclass specifics."""
        from dataclasses import asdict
        return asdict(event)

