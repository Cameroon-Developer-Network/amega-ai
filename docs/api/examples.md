# API Examples

This guide provides practical examples of using the Amega AI API.

## Python Example

```python
import requests

API_KEY = "your_api_key"
BASE_URL = "https://api.amega-ai.com/v1"

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

# Create a prediction
response = requests.post(
    f"{BASE_URL}/predictions",
    headers=headers,
    json={
        "model": "text-analysis-v1",
        "input": "Sample text for analysis"
    }
)

print(response.json())
```

## JavaScript Example

```javascript
const API_KEY = 'your_api_key';
const BASE_URL = 'https://api.amega-ai.com/v1';

async function createPrediction() {
    const response = await fetch(`${BASE_URL}/predictions`, {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${API_KEY}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            model: 'text-analysis-v1',
            input: 'Sample text for analysis'
        })
    });

    const data = await response.json();
    console.log(data);
}

createPrediction(); 