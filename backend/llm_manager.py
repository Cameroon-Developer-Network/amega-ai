"""
LLM Manager for AMEGA-AI

This module handles the integration with language models using transformers and langchain.
It provides a unified interface for text generation and chat completion.
"""
from typing import Dict, List, Optional, Literal
from datetime import datetime

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
from langchain_community.llms import HuggingFacePipeline
from langchain.chains import ConversationChain
from langchain.memory import ConversationBufferMemory
from pydantic import BaseModel, Field

class ChatMessage(BaseModel):
    """Model for chat messages."""
    role: Literal["user", "assistant"] = Field(..., description="The role of the message sender")
    content: str = Field(..., min_length=1, description="The content of the message")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Message timestamp")

class LLMManager:
    def __init__(self, model_name: str = "microsoft/DialoGPT-medium"):
        """Initialize the LLM Manager with specified model."""
        self.model_name = model_name
        self.device = "cuda" if torch.cuda.is_available() else "cpu"

        # Initialize tokenizer and model
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self.model = AutoModelForCausalLM.from_pretrained(
            self.model_name,
            device_map="auto" if self.device == "cuda" else None
        )

        # Move model to appropriate device
        if self.device == "cpu":
            self.model = self.model.to(self.device)

        # Initialize conversation memory
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )

        # Setup conversation chain
        self.conversation = ConversationChain(
            llm=self._create_pipeline(),
            memory=self.memory,
            verbose=True
        )

    def _create_pipeline(self) -> HuggingFacePipeline:
        """Create a HuggingFace pipeline for text generation."""
        pipeline = HuggingFacePipeline(
            pipeline=self.model,
            tokenizer=self.tokenizer,
            model_kwargs={
                "temperature": 0.7,
                "max_length": 1000,
                "top_p": 0.9,
                "repetition_penalty": 1.2
            }
        )
        return pipeline

    async def generate_response(self, message: str) -> ChatMessage:
        """Generate a response to the given message."""
        try:
            # Tokenize input
            inputs = self.tokenizer.encode(message + self.tokenizer.eos_token, return_tensors="pt")
            inputs = inputs.to(self.device)

            # Generate response
            outputs = self.model.generate(
                inputs,
                max_length=1000,
                num_return_sequences=1,
                pad_token_id=self.tokenizer.eos_token_id,
                do_sample=True,
                temperature=0.7,
                top_p=0.9,
                repetition_penalty=1.2
            )

            # Decode response
            response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)

            return ChatMessage(
                role="assistant",
                content=response
            )

        except Exception as e:
            # Log the error and return a graceful error message
            print(f"Error generating response: {str(e)}")
            return ChatMessage(
                role="assistant",
                content="I apologize, but I encountered an error processing your request. Please try again."
            )

    async def chat(self, message: ChatMessage) -> ChatMessage:
        """Process a chat message and return a response."""
        try:
            # Add message to conversation history
            self.memory.chat_memory.add_message(message)

            # Generate response
            response = await self.generate_response(message.content)

            # Add response to conversation history
            self.memory.chat_memory.add_message(response)

            return response

        except Exception as e:
            print(f"Error in chat: {str(e)}")
            return ChatMessage(
                role="assistant",
                content="I apologize, but I encountered an error in our conversation. Please try again."
            )

    def get_conversation_history(self) -> List[ChatMessage]:
        """Return the conversation history."""
        return self.memory.chat_memory.messages
