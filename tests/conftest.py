"""
PyTest configuration and fixtures for AMEGA-AI tests.
"""
import pytest
from unittest.mock import MagicMock
from fastapi.testclient import TestClient
from backend.app import app
from backend.auth import fake_users_db
from backend.llm_manager import ChatMessage

# Create a mock LLM manager
class MockLLMManager:
    def __init__(self, *args, **kwargs):
        self.memory = MagicMock()
        self.memory.chat_memory.messages = []

    async def chat(self, message: ChatMessage) -> ChatMessage:
        return ChatMessage(
            role="assistant",
            content="This is a mock response"
        )

    def get_conversation_history(self):
        return []

@pytest.fixture
def client():
    """Create a test client with a mock LLM manager."""
    # Replace the real LLM manager with our mock
    app.state.llm_manager = MockLLMManager()
    return TestClient(app)

@pytest.fixture(autouse=True)
def cleanup_db():
    """Clean up the fake database after each test."""
    yield
    fake_users_db.clear() 
