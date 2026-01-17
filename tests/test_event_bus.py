
import os
import sys
import shutil
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.chatbot.core.event_bus import (
    EventBus, Event, DocumentUploadEvent, ProcessingStartEvent, 
    ProcessingCompleteEvent, VectorStoreUpdateEvent
)
from src.chatbot.core.document_processor import DocumentProcessor
from src.chatbot.core.vector_store_manager import VectorStoreManager

def test_event_flow():
    print("Testing Event Flow...")
    
    # Setup
    events_received = []
    
    def on_event(event: Event):
        print(f"Captured: {type(event).__name__}")
        events_received.append(event)
        
    event_bus = EventBus()
    event_bus.subscribe(Event, on_event)
    
    # Create a dummy file
    test_file = "test_doc.txt"
    with open(test_file, "w") as f:
        f.write("This is a test document.\nIt has multiple lines.\nFor testing purposes.")
        
    try:
        # Test DocumentProcessor
        print("\nTesting DocumentProcessor...")
        processor = DocumentProcessor(chunk_size=50, chunk_overlap=10, event_bus=event_bus)
        chunks = processor.process_document(test_file)
        
        # Verify processor events
        start_events = [e for e in events_received if isinstance(e, ProcessingStartEvent)]
        complete_events = [e for e in events_received if isinstance(e, ProcessingCompleteEvent)]
        
        assert len(start_events) == 1, "Should have 1 ProcessingStartEvent"
        assert len(complete_events) == 1, "Should have 1 ProcessingCompleteEvent"
        assert complete_events[0].chunk_count == len(chunks)
        print("✓ DocumentProcessor events verified")
        
        # Test VectorStoreManager
        print("\nTesting VectorStoreManager (HuggingFace)...")
        # We need to mock or ensure we have dependencies. 
        # Assuming HuggingFace is available as per requirements.
        
        manager = VectorStoreManager(
            event_bus=event_bus
        )
        
        # Clear previous events
        events_received.clear()
        
        manager.create_vector_store(chunks)
        
        # Verify vector store events
        update_events = [e for e in events_received if isinstance(e, VectorStoreUpdateEvent)]
        assert len(update_events) >= 1, "Should have at least 1 VectorStoreUpdateEvent"
        assert update_events[0].operation == "create", "First event should be create"
        print("✓ VectorStoreManager events verified")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        raise e
    finally:
        # Cleanup
        if os.path.exists(test_file):
            os.remove(test_file)
        if os.path.exists("faiss_index"):
            shutil.rmtree("faiss_index", ignore_errors=True)
            
if __name__ == "__main__":
    test_event_flow()
