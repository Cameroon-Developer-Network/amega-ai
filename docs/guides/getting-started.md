# Getting Started with Amega AI

This guide will help you get up and running with Amega AI quickly.

## Prerequisites

- Python 3.8 or higher
- pip package manager
- Git (for version control)
- Virtual environment (recommended)

## Installation

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

## Quick Start Example

Here's a simple example to get you started with model training:

```python
from amega_ai import Model, Dataset

# Load example dataset
dataset = Dataset.load_example("sentiment")

# Create a model
model = Model.create("sentiment-classifier")

# Train the model
model.train(dataset, epochs=5)

# Make predictions
text = "This product exceeded my expectations!"
prediction = model.predict(text)
print(f"Sentiment: {prediction}")
```

## Next Steps

1. Check out our [Installation Guide](installation.md) for detailed setup instructions
2. Learn about [Configuration](configuration.md) options
3. Explore the [API Documentation](../api.md)
4. Join our [Community](https://discord.gg/amega-ai) for support 