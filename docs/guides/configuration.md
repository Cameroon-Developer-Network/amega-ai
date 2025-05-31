# Configuration Guide

Learn how to configure Amega AI for your specific needs.

## Configuration File

Amega AI uses a YAML configuration file (`config.yml`) for managing settings. Create this file in your project root:

```yaml
# config.yml

# API Configuration
api:
  host: localhost
  port: 8000
  debug: false
  api_key: your-api-key

# Model Settings
model:
  default_framework: pytorch
  cache_dir: ~/.amega/models
  max_batch_size: 32
  device: cuda  # or cpu

# Training
training:
  default_epochs: 10
  learning_rate: 0.001
  optimizer: adam
  early_stopping:
    enabled: true
    patience: 3
    min_delta: 0.001

# Logging
logging:
  level: INFO
  file: logs/amega.log
  format: '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

# Security
security:
  enable_ssl: true
  ssl_cert: path/to/cert.pem
  ssl_key: path/to/key.pem
```

## Environment Variables

You can also configure Amega AI using environment variables:

```bash
# API Settings
export AMEGA_API_KEY=your-api-key
export AMEGA_HOST=localhost
export AMEGA_PORT=8000

# Model Settings
export AMEGA_MODEL_FRAMEWORK=pytorch
export AMEGA_DEVICE=cuda

# Security
export AMEGA_SSL_ENABLED=true
```

## Configuration Priority

Settings are loaded in the following order (highest priority first):

1. Environment variables
2. Command line arguments
3. Configuration file
4. Default values

## Example Usage

```python
from amega_ai import Config

# Load configuration
config = Config.load("config.yml")

# Access configuration values
api_key = config.api.key
model_framework = config.model.framework

# Override settings
config.model.device = "cpu"
config.save()
```

## Advanced Configuration

### Custom Model Configuration

```yaml
# config.yml

models:
  sentiment_analysis:
    architecture: transformer
    hidden_size: 768
    num_layers: 12
    dropout: 0.1
  
  image_classification:
    architecture: resnet
    num_classes: 1000
    pretrained: true
```

### Distributed Training

```yaml
# config.yml

distributed:
  enabled: true
  backend: nccl
  world_size: 4
  master_addr: localhost
  master_port: 29500
```

### Monitoring Configuration

```yaml
# config.yml

monitoring:
  prometheus:
    enabled: true
    port: 9090
  
  grafana:
    enabled: true
    dashboard_dir: dashboards/
```

## Security Best Practices

1. Never commit API keys or sensitive data
2. Use environment variables for secrets
3. Enable SSL in production
4. Regularly rotate API keys
5. Set appropriate file permissions 