# API Reference

## REST API Endpoints

### Model Management

#### List Models

```http
GET /api/v1/models
```

Returns a list of all available models.

**Response**
```json
{
    "models": [
        {
            "id": "model-123",
            "name": "sentiment-analysis",
            "version": "1.0.0",
            "status": "active"
        }
    ]
}
```

#### Create Model

```http
POST /api/v1/models
```

Create a new model.

**Request Body**
```json
{
    "name": "sentiment-analysis",
    "description": "BERT-based sentiment analysis model",
    "framework": "pytorch",
    "version": "1.0.0"
}
```

### Inference

#### Predict

```http
POST /api/v1/models/{model_id}/predict
```

Make predictions using a specific model.

**Request Body**
```json
{
    "inputs": [
        {
            "text": "This is a great product!"
        }
    ]
}
```

## Python SDK

### Installation

```bash
pip install amega-ai
```

### Quick Start

```python
from amega_ai import Client

# Initialize client
client = Client(api_key="your-api-key")

# Load a model
model = client.load_model("sentiment-analysis")

# Make predictions
result = model.predict("This is a great product!")
print(result)
```

### Advanced Usage

```python
# Custom model training
from amega_ai import Model, Dataset

# Load dataset
dataset = Dataset.from_csv("data.csv")

# Initialize model
model = Model(
    name="custom-classifier",
    architecture="transformer",
    config={
        "num_layers": 12,
        "hidden_size": 768
    }
)

# Train model
model.train(
    dataset=dataset,
    epochs=10,
    batch_size=32
)

# Save model
model.save("custom-classifier-v1")
``` 