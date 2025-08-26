# Context Provider MCP Server - API Setup Guide

## Overview

The context-provider MCP server provides current date/time, stock market data, and news headlines. While the date/time functionality works immediately, the stock market and news features require API keys for full functionality.

## API Configuration

### 1. Stock Market Data (Alpha Vantage)

**Free Tier Available**: Yes (500 requests/day)

1. Visit: https://www.alphavantage.co/support/#api-key
2. Sign up for a free API key
3. Replace `apikey=demo` in the server code with your actual key

**Alternative APIs:**
- Yahoo Finance API (free, unofficial)
- IEX Cloud (free tier available)
- Polygon.io (free tier available)

### 2. News Headlines (NewsAPI)

**Free Tier Available**: Yes (1000 requests/month)

1. Visit: https://newsapi.org/register
2. Sign up for a free API key
3. Replace `apiKey: "demo"` in the server code with your actual key

**Alternative APIs:**
- RSS feeds (free)
- Guardian API (free)
- New York Times API (free tier)

## Configuration Steps

### Option 1: Edit Server Code Directly

1. Navigate to: `~/.mcp_servers/servers/context-provider/code/src/server.py`
2. Find the API key placeholders:
   - Line ~65: `"apikey=demo"` → `"apikey=YOUR_ALPHA_VANTAGE_KEY"`
   - Line ~120: `"apiKey": "demo"` → `"apiKey": "YOUR_NEWSAPI_KEY"`
3. Save the file
4. Restart VS Code

### Option 2: Environment Variables (Recommended)

1. Create a `.env` file in: `~/.mcp_servers/servers/context-provider/`
2. Add your API keys:
   ```
   ALPHA_VANTAGE_API_KEY=your_alpha_vantage_key_here
   NEWSAPI_KEY=your_newsapi_key_here
   ```
3. Modify the server code to use environment variables (requires code update)

## Testing the Server

After setup, you can test the tools:

1. **Date/Time** (works immediately):
   ```
   get_current_datetime()
   ```

2. **Stock Market** (requires Alpha Vantage key):
   ```
   get_stock_market_overview()
   ```

3. **News Headlines** (requires NewsAPI key):
   ```
   get_news_headlines(category="business", count=5)
   ```

4. **Complete Context** (combines all):
   ```
   get_context_summary()
   ```

## Fallback Behavior

- **Without API keys**: The server will return sample/demo data with appropriate warnings
- **API failures**: Graceful fallback to cached or sample data
- **Rate limits**: Error messages with retry suggestions

## Production Considerations

1. **API Key Security**: Store keys in environment variables, not in code
2. **Rate Limiting**: Implement caching to avoid hitting API limits
3. **Error Handling**: Add retry logic for failed API calls
4. **Data Freshness**: Consider caching strategies for different data types

## Troubleshooting

### Common Issues:

1. **"Demo API" messages**: API keys not configured properly
2. **Network errors**: Check internet connection and API endpoints
3. **Rate limit errors**: Wait or upgrade to paid API tiers
4. **Invalid API keys**: Verify keys are correct and active

### Debug Steps:

1. Check server logs in VS Code terminal
2. Test API endpoints directly in browser
3. Verify API key permissions and quotas
4. Check firewall/proxy settings

## Support

For issues with:
- **Alpha Vantage**: https://www.alphavantage.co/support/
- **NewsAPI**: https://newsapi.org/docs
- **MCP Server**: Check the generated server code and logs
