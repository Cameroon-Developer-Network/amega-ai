# API Endpoints

This document provides details about all available API endpoints.

## Base URL

All endpoints are relative to: `https://api.amega-ai.com/v1`

## Available Endpoints

### Models

#### List Models

```http
GET /models
```

Lists all available AI models.

#### Get Model Details

```http
GET /models/{model_id}
```

Get detailed information about a specific model.

### Predictions

#### Create Prediction

```http
POST /predictions
```

Create a new prediction using a specified model.

#### Get Prediction Results

```http
GET /predictions/{prediction_id}
```

Retrieve the results of a specific prediction. 