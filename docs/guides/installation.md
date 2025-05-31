# Installation Guide

This guide provides detailed instructions for installing Amega AI and its dependencies.

## System Requirements

- **Operating System**: Linux, macOS, or Windows
- **Python Version**: 3.8 or higher
- **RAM**: Minimum 8GB (16GB recommended)
- **Storage**: At least 2GB free space
- **GPU**: Optional but recommended for training large models

## Installation Methods

### 1. Using pip (Recommended)

```bash
pip install amega-ai
```

### 2. From Source

1. **Clone the Repository**
   ```bash
   git clone https://github.com/yourusername/amega-ai.git
   cd amega-ai
   ```

2. **Create Virtual Environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: .\venv\Scripts\activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Install in Development Mode**
   ```bash
   pip install -e .
   ```

## GPU Support

For GPU support, install the CUDA version compatible with your GPU:

```bash
pip install amega-ai[gpu]
```

This will install additional dependencies including:
- CUDA Toolkit
- cuDNN
- GPU-enabled TensorFlow and PyTorch

## Verification

Verify the installation:

```python
import amega_ai

# Check version
print(amega_ai.__version__)

# Verify GPU support
print(amega_ai.gpu_available())
```

## Common Issues

### 1. CUDA Installation Problems

If you encounter CUDA-related issues:
1. Verify CUDA toolkit installation
2. Check GPU compatibility
3. Update graphics drivers

### 2. Dependencies Conflicts

If you encounter dependency conflicts:
1. Create a fresh virtual environment
2. Install dependencies one by one
3. Check for version compatibility

## Next Steps

1. Follow our [Getting Started Guide](getting-started.md)
2. Configure your [Environment](configuration.md)
3. Run the [Example Projects](../examples/) 