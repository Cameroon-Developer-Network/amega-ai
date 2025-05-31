import ast
import re
from dataclasses import dataclass
from typing import List, Optional, Tuple, Union, Dict, Any
from pathlib import Path
import tokenize
import io
import abc
import asyncio
import aiohttp
import numpy as np
from enum import Enum
import logging
import json
import os
from tenacity import retry, stop_after_attempt, wait_exponential

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EmbeddingProvider(Enum):
    OPENAI = "openai"
    NOMIC = "nomic"
    OLLAMA = "ollama"

@dataclass
class CodeChunk:
    content: str
    start_line: int
    end_line: int
    type: str  
    name: Optional[str] = None
    language: Optional[str] = None
    embedding: Optional[List[float]] = None

@dataclass
class EmbeddingConfig:
    provider: EmbeddingProvider
    api_key: Optional[str] = None
    model_name: Optional[str] = None
    api_base: Optional[str] = None
    batch_size: int = 10
    max_retries: int = 3
    timeout: int = 30

class EmbeddingError(Exception):
    """Base class for embedding-related errors."""
    pass

class APIError(EmbeddingError):
    """Error occurred while calling the embedding API."""
    pass

class ModelNotFoundError(EmbeddingError):
    """Specified embedding model was not found."""
    pass

class BaseEmbedder(abc.ABC):
    def __init__(self, config: EmbeddingConfig):
        self.config = config
        self.session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.config.timeout)
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    @abc.abstractmethod
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Embed a batch of texts."""
        pass

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        reraise=True
    )
    async def _make_request(self, url: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Make an HTTP request with retry logic."""
        if not self.session:
            raise RuntimeError("Session not initialized. Use async with context.")
        
        headers = self._get_headers()
        async with self.session.post(url, json=payload, headers=headers) as response:
            if response.status != 200:
                error_text = await response.text()
                raise APIError(f"API request failed: {response.status} - {error_text}")
            return await response.json()

    def _get_headers(self) -> Dict[str, str]:
        """Get headers for API requests."""
        headers = {"Content-Type": "application/json"}
        if self.config.api_key:
            headers["Authorization"] = f"Bearer {self.config.api_key}"
        return headers

class OpenAIEmbedder(BaseEmbedder):
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        url = f"{self.config.api_base or 'https://api.openai.com'}/v1/embeddings"
        model = self.config.model_name or "text-embedding-3-small"
        
        payload = {
            "input": texts,
            "model": model,
            "encoding_format": "float"
        }
        
        response = await self._make_request(url, payload)
        return [item["embedding"] for item in response["data"]]

class NomicEmbedder(BaseEmbedder):
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        url = f"{self.config.api_base or 'https://api.nomic.ai'}/v1/embeddings"
        model = self.config.model_name or "nomic-embed-text-v1"
        
        payload = {
            "texts": texts,
            "model": model
        }
        
        response = await self._make_request(url, payload)
        return response["embeddings"]

class OllamaEmbedder(BaseEmbedder):
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        url = f"{self.config.api_base or 'http://localhost:11434'}/api/embeddings"
        model = self.config.model_name or "llama2"
        
        embeddings = []
        for text in texts:
            payload = {
                "model": model,
                "prompt": text
            }
            response = await self._make_request(url, payload)
            embeddings.append(response["embedding"])
        return embeddings

class EmbeddingManager:
    def __init__(self, config: EmbeddingConfig):
        self.config = config
        self._embedder_map = {
            EmbeddingProvider.OPENAI: OpenAIEmbedder,
            EmbeddingProvider.NOMIC: NomicEmbedder,
            EmbeddingProvider.OLLAMA: OllamaEmbedder
        }

    def _get_embedder_class(self) -> type:
        embedder_class = self._embedder_map.get(self.config.provider)
        if not embedder_class:
            raise ValueError(f"Unsupported embedding provider: {self.config.provider}")
        return embedder_class

    async def embed_chunks(self, chunks: List[CodeChunk]) -> List[CodeChunk]:
        """Generate embeddings for a list of code chunks."""
        texts = [self._prepare_text(chunk) for chunk in chunks]
        embedder_class = self._get_embedder_class()
        
        async with embedder_class(self.config) as embedder:
            for i in range(0, len(texts), self.config.batch_size):
                batch = texts[i:i + self.config.batch_size]
                try:
                    embeddings = await embedder.embed_batch(batch)
                    for chunk, embedding in zip(chunks[i:i + self.config.batch_size], embeddings):
                        chunk.embedding = embedding
                except Exception as e:
                    logger.error(f"Error generating embeddings for batch: {e}")
                    raise EmbeddingError(f"Failed to generate embeddings: {str(e)}")
        
        return chunks

    def _prepare_text(self, chunk: CodeChunk) -> str:
        """Prepare code chunk text for embedding."""
        context = []
        if chunk.language:
            context.append(f"Language: {chunk.language}")
        if chunk.type:
            context.append(f"Type: {chunk.type}")
        if chunk.name:
            context.append(f"Name: {chunk.name}")
        
        header = " | ".join(context)
        return f"{header}\n\n{chunk.content}" if header else chunk.content

class CodeChunker:
    def __init__(self, max_chunk_size: int = 1000, min_chunk_size: int = 50, overlap: int = 20):
        self.max_chunk_size = max_chunk_size
        self.min_chunk_size = min_chunk_size
        self.overlap = overlap
        
        # Language-specific patterns for improved chunking
        self.language_patterns = {
            'python': {
                'function_def': r'def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(',
                'class_def': r'class\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*[:\(]',
                'comment': r'#.*$|"""[\s\S]*?"""|\'\'\'[\s\S]*?\'\'\'',
            },
            'javascript': {
                'function_def': r'function\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(|const\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*(?:async\s*)?\(|([a-zA-Z_][a-zA-Z0-9_]*)\s*:\s*(?:async\s*)?\(',
                'class_def': r'class\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*{',
                'comment': r'\/\/.*$|\/\*[\s\S]*?\*\/',
            }
        }

    def detect_language(self, file_path: Union[str, Path]) -> str:
        """Detect the programming language based on file extension."""
        extensions = {
            '.py': 'python',
            '.js': 'javascript',
            '.jsx': 'javascript',
            '.ts': 'javascript',
            '.tsx': 'javascript',
        }
        return extensions.get(Path(file_path).suffix.lower(), 'unknown')

    def chunk_python_ast(self, code: str) -> List[CodeChunk]:
        """Chunk Python code using AST parsing for more accurate results."""
        chunks = []
        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    chunks.append(CodeChunk(
                        content=ast.get_source_segment(code, node),
                        start_line=node.lineno,
                        end_line=node.end_lineno,
                        type='function',
                        name=node.name,
                        language='python'
                    ))
                elif isinstance(node, ast.ClassDef):
                    chunks.append(CodeChunk(
                        content=ast.get_source_segment(code, node),
                        start_line=node.lineno,
                        end_line=node.end_lineno,
                        type='class',
                        name=node.name,
                        language='python'
                    ))
        except SyntaxError:
            # Fallback to regex-based chunking if AST parsing fails
            return self.chunk_by_regex(code, 'python')
        return chunks

    def chunk_by_regex(self, code: str, language: str) -> List[CodeChunk]:
        """Chunk code using regex patterns when AST parsing is not available."""
        chunks = []
        lines = code.split('\n')
        patterns = self.language_patterns.get(language, {})
        
        current_chunk = []
        current_type = None
        current_name = None
        start_line = 1
        
        for i, line in enumerate(lines, 1):
            for chunk_type, pattern in patterns.items():
                if match := re.search(pattern, line):
                    if current_chunk:
                        chunks.append(CodeChunk(
                            content='\n'.join(current_chunk),
                            start_line=start_line,
                            end_line=i-1,
                            type=current_type or 'block',
                            name=current_name,
                            language=language
                        ))
                        current_chunk = []
                    
                    current_type = chunk_type
                    current_name = match.group(1) if match.groups() else None
                    start_line = i
            
            current_chunk.append(line)
            
        if current_chunk:
            chunks.append(CodeChunk(
                content='\n'.join(current_chunk),
                start_line=start_line,
                end_line=len(lines),
                type=current_type or 'block',
                name=current_name,
                language=language
            ))
            
        return chunks

    def ensure_chunk_size(self, chunks: List[CodeChunk]) -> List[CodeChunk]:
        """Ensure chunks meet size constraints and add overlap where needed."""
        result = []
        for chunk in chunks:
            if len(chunk.content) <= self.max_chunk_size:
                result.append(chunk)
                continue
                
            # Split large chunks while preserving meaningful boundaries
            lines = chunk.content.split('\n')
            current_chunk = []
            current_size = 0
            start_line = chunk.start_line
            
            for i, line in enumerate(lines):
                line_size = len(line)
                if current_size + line_size > self.max_chunk_size and current_chunk:
                    # Add overlap from previous chunk if possible
                    overlap_start = max(0, len(current_chunk) - self.overlap)
                    overlap_lines = current_chunk[overlap_start:]
                    
                    result.append(CodeChunk(
                        content='\n'.join(current_chunk),
                        start_line=start_line,
                        end_line=start_line + len(current_chunk) - 1,
                        type='fragment',
                        language=chunk.language
                    ))
                    
                    current_chunk = overlap_lines + [line]
                    current_size = sum(len(l) for l in current_chunk)
                    start_line = start_line + len(current_chunk) - len(overlap_lines)
                else:
                    current_chunk.append(line)
                    current_size += line_size
            
            if current_chunk:
                result.append(CodeChunk(
                    content='\n'.join(current_chunk),
                    start_line=start_line,
                    end_line=start_line + len(current_chunk) - 1,
                    type='fragment',
                    language=chunk.language
                ))
                
        return result

    def chunk_code(self, code: str, file_path: Union[str, Path]) -> List[CodeChunk]:
        """Main method to chunk code with language-specific handling."""
        language = self.detect_language(file_path)
        
        if language == 'python':
            chunks = self.chunk_python_ast(code)
        else:
            chunks = self.chunk_by_regex(code, language)
            
        return self.ensure_chunk_size(chunks)

async def create_embeddings(chunks: List[CodeChunk], config: Optional[EmbeddingConfig] = None):
    """
    Generate embeddings for code chunks using the configured embedding provider.
    
    Args:
        chunks: List of code chunks to embed
        config: Optional embedding configuration. If not provided, uses environment variables.
    
    Returns:
        List of code chunks with embeddings added
    """
    if not config:
        config = EmbeddingConfig(
            provider=EmbeddingProvider(os.getenv("EMBEDDING_PROVIDER", "openai")),
            api_key=os.getenv("EMBEDDING_API_KEY"),
            model_name=os.getenv("EMBEDDING_MODEL"),
            api_base=os.getenv("EMBEDDING_API_BASE"),
            batch_size=int(os.getenv("EMBEDDING_BATCH_SIZE", "10")),
            max_retries=int(os.getenv("EMBEDDING_MAX_RETRIES", "3")),
            timeout=int(os.getenv("EMBEDDING_TIMEOUT", "30"))
        )
    
    manager = EmbeddingManager(config)
    try:
        return await manager.embed_chunks(chunks)
    except Exception as e:
        logger.error(f"Failed to create embeddings: {e}")
        raise
