# Authentication

This guide explains how to authenticate with the Amega AI API.

## API Keys

All requests to the Amega AI API must include an API key. You can obtain an API key by:

1. Creating an account at [Amega AI Dashboard](https://dashboard.amega-ai.com)
2. Navigating to API Settings
3. Generating a new API key

## Using Your API Key

Include your API key in the `Authorization` header of all API requests:

```bash
curl -H "Authorization: Bearer YOUR_API_KEY" https://api.amega-ai.com/v1/endpoint
```

## Security Best Practices

- Keep your API key secure and never share it
- Rotate your keys periodically
- Use environment variables to store keys
- Never commit API keys to version control 