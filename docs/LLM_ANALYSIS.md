# LLM Analysis Integration Guide

This document provides comprehensive instructions for setting up and using the OpenAI GPT integration in Ultra Trader for professional-grade market analysis.

## Railway Deployment Setup

### Required Environment Variables

Set these variables in your Railway project's Variables section:

#### **Required:**
- `OPENAI_API_KEY`: Your OpenAI API key (get it from [OpenAI Platform](https://platform.openai.com/api-keys))

#### **Optional (with defaults):**
- `OPENAI_MODEL`: AI model to use (default: `gpt-4o-mini`)
- `OPENAI_TEMPERATURE`: Response creativity 0.0-2.0 (default: `0.7`)
- `OPENAI_MAX_TOKENS`: Maximum response length (default: `2000`)
- `OPENAI_BASE_URL`: Custom OpenAI endpoint (for Azure OpenAI or other providers)
- `OPENAI_TIMEOUT`: Request timeout in seconds (default: `30`)

### Setting Up on Railway

1. **Navigate to your Railway project dashboard**
2. **Go to the Variables tab**
3. **Add the required variables:**
   ```
   OPENAI_API_KEY=sk-your-openai-api-key-here
   OPENAI_MODEL=gpt-4o-mini
   OPENAI_TEMPERATURE=0.7
   OPENAI_MAX_TOKENS=2000
   ```
4. **Deploy your application** - the GPT Analysis tab will become available

### Getting an OpenAI API Key

1. Visit [OpenAI Platform](https://platform.openai.com/)
2. Sign up or log in to your account
3. Navigate to [API Keys](https://platform.openai.com/api-keys)
4. Click "Create new secret key"
5. Copy the key and add it to your Railway environment variables

## Local Development Setup

For local development, create a `.env` file in your project root:

```env
OPENAI_API_KEY=sk-your-openai-api-key-here
OPENAI_MODEL=gpt-4o-mini
OPENAI_TEMPERATURE=0.7
OPENAI_MAX_TOKENS=2000
```

## Using the GPT Analysis Dashboard

### Access the Feature

1. Open your Ultra Trader dashboard
2. Click on the **"🤖 GPT Analysis"** tab
3. If properly configured, you'll see the analysis interface

### Analysis Types

#### **1. Custom Prompt**
- Ask any trading or market-related question
- Get personalized analysis and insights
- Ideal for specific scenarios or questions

#### **2. Market Sentiment Analysis**  
- Analyze news articles or market text
- Get sentiment classification (Bullish/Bearish/Neutral)
- Understand market impact and trading implications

#### **3. Signal Explanation**
- Understand trading signals and technical indicators
- Get educational explanations of market patterns
- Learn risk-reward assessments

#### **4. Strategy Report**
- Generate comprehensive trading strategy analysis
- Receive structured reports with entry/exit points
- Get risk assessment and scenario analysis

### Input Options

- **Symbol**: Specify the asset (BTC, ETH, etc.)
- **Timeframe**: Choose analysis timeframe (1h, 4h, 1d, 1w)
- **Recent Metrics**: Include recent trading data from your database
- **Custom Context**: Provide news, data, or specific scenarios

### Response Features

- **Structured Analysis**: Professional, well-organized insights
- **Caching**: Responses are cached to reduce costs and improve speed
- **Logging**: Request metadata is stored (when MongoDB is available)
- **Export**: Copy/save analysis results

## Cost Management & Best Practices

### Token Usage & Costs

- **Model Costs** (approximate per 1M tokens):
  - `gpt-4o-mini`: $0.15 input, $0.60 output (recommended)
  - `gpt-4o`: $5.00 input, $15.00 output (premium)
  - `gpt-3.5-turbo`: $0.50 input, $1.50 output (budget)

### Budget Control Tips

1. **Use Default Model**: `gpt-4o-mini` provides excellent analysis at low cost
2. **Set Token Limits**: Configure `OPENAI_MAX_TOKENS` to control response length
3. **Leverage Caching**: Identical queries use cached responses (free)
4. **Be Specific**: Focused prompts get better results with fewer tokens
5. **Monitor Usage**: Check your OpenAI dashboard for usage tracking

### Caching Behavior

- **MongoDB Caching**: When `MONGODB_URI` is set, responses are cached in the database
- **Memory Fallback**: If MongoDB unavailable, uses in-memory cache for the session
- **Cache Duration**: 24 hours for MongoDB, 1 hour for memory cache
- **Cache Keys**: Based on prompt + template + parameters (identical requests reuse cache)

## Rate Limits & Error Handling

### OpenAI Rate Limits

- **Free Tier**: 3 requests/minute, 200 requests/day
- **Paid Tier**: Higher limits based on usage tier
- **Error Handling**: Automatic retries with exponential backoff

### Common Issues & Solutions

#### **"API Key Not Configured"**
- Verify `OPENAI_API_KEY` is set in Railway variables
- Check the key is valid and not expired
- Ensure no extra spaces or characters in the key

#### **"Rate Limit Exceeded"**  
- Wait for rate limit reset (shown in error message)
- Consider upgrading your OpenAI account
- Use caching to reduce API calls

#### **"Model Not Available"**
- Check if the specified model exists and you have access
- Fall back to `gpt-4o-mini` or `gpt-3.5-turbo`
- Verify your OpenAI account has the required permissions

#### **"Timeout Errors"**
- Increase `OPENAI_TIMEOUT` value
- Reduce `OPENAI_MAX_TOKENS` for faster responses
- Check your network connection

## Security & Privacy

### Best Practices

- **Never commit API keys** to version control
- **Use environment variables** for all sensitive configuration
- **Rotate keys regularly** for enhanced security
- **Monitor usage** for unexpected activity

### Data Privacy

- **Analysis requests** are sent to OpenAI for processing
- **Cached responses** are stored in your MongoDB (when available)
- **No sensitive trading data** should be included in prompts
- **API keys are never logged** or displayed in the interface

## Advanced Configuration

### Azure OpenAI Integration

To use Azure OpenAI instead of OpenAI directly:

```env
OPENAI_API_KEY=your-azure-openai-key
OPENAI_BASE_URL=https://your-resource.openai.azure.com/
OPENAI_MODEL=your-azure-deployment-name
```

### Custom Models

For organizations with custom fine-tuned models:

```env
OPENAI_MODEL=ft:gpt-3.5-turbo:your-org:your-model:abc123
```

### Temperature Settings

Adjust response creativity:
- `0.0-0.3`: Focused, deterministic responses
- `0.4-0.7`: Balanced creativity and consistency (recommended)  
- `0.8-1.0`: More creative, varied responses
- `1.1-2.0`: Very creative (may be less reliable)

## Troubleshooting

### Check Configuration Status

The dashboard shows configuration status under "🔧 Configuration Status":
- Model and parameters being used
- Cache backend status
- Number of cached responses

### Clear Cache

If responses seem outdated or incorrect:
1. Enable "Show Admin Controls" in the dashboard
2. Click "Clear Cache" to remove all cached responses
3. Subsequent requests will fetch fresh responses

### Logs and Monitoring  

Request metadata is logged to MongoDB collection `gpt_logs` (when available):
- Timestamp and request details
- Template and model used
- Response length and performance metrics
- Error information for debugging

## Support

For issues specific to:
- **OpenAI API**: Check [OpenAI Status](https://status.openai.com/) and [Documentation](https://platform.openai.com/docs)
- **Railway Deployment**: Review [Railway Documentation](https://docs.railway.app/)
- **Ultra Trader Integration**: Check application logs and configuration status

## Future Enhancements

Planned features for future releases:
- **Automated Analysis**: Scheduled GPT summaries and reports
- **Custom Templates**: User-defined analysis templates
- **Multi-Model Support**: Compare responses from different models
- **Advanced Caching**: Configurable cache duration and policies
- **Batch Processing**: Analyze multiple assets simultaneously