# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial project setup
- Backend security implementation with role-based access control (RBAC)
- Role hierarchy system with admin, moderator, and user roles
- Security test suite for RBAC functionality
- DeepSource integration for code quality
- Intelligent code chunking system in embedder.py with:
  - Language-specific parsing for Python (AST-based) and JavaScript
  - Smart chunk size management with configurable overlap
  - Support for functions, classes, and code blocks
  - Fallback mechanisms for robust parsing
  - Extensible language detection system
- Vector embedding generation system with:
  - Support for multiple providers (OpenAI, Nomic, Ollama)
  - Async batch processing with configurable batch sizes
  - Automatic retry logic with exponential backoff
  - Comprehensive error handling and logging
  - Environment-based configuration
  - Context-aware text preparation for improved embeddings
- New dependencies for embedding functionality:
  - aiohttp>=3.9.0 for async HTTP requests
  - tenacity>=8.2.0 for retry logic
  - numpy>=1.24.0 for vector operations
- Vector store management system with ChromaDB:
  - Efficient storage and retrieval of code embeddings
  - Similarity search with customizable metrics
  - Metadata filtering and querying
  - Batch processing for large datasets
  - Persistent storage support
  - Collection management and statistics
  - Added chromadb>=0.4.22 dependency
  - Environment-based configuration with auto-directory creation
  - Pydantic settings integration for type-safe config

### Changed
- Updated DeepSource configuration for Python and Shell analysis
- Simplified .deepsource.toml configuration
- Fixed role hierarchy implementation in security middleware
- Enhanced CodeChunk dataclass with embedding support
- Updated requirements.txt with new dependencies
- Improved vector store initialization with automatic directory creation
- Enhanced environment variable template with vector store settings

### Deprecated
- N/A

### Removed
- N/A

### Fixed
- N/A

### Security
- Implemented role-based access control (RBAC) middleware
- Added security headers middleware
- Created role hierarchy with proper permission inheritance
- Secure API key handling for embedding providers 