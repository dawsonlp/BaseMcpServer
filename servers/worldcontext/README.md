# WorldContext MCP Server

WorldContext provides quick situational context through MCP tools for:

- current date and time
- stock market overview and single-symbol stock quotes
- current news headlines
- Python package and infrastructure version lookups

## Configuration

Copy `config.yaml.example` to the managed configuration location and provide
Alpha Vantage and NewsAPI keys as needed.

## Tools

- `get_current_datetime`
- `get_stock_market_overview`
- `get_stock_quote`
- `get_news_headlines`
- `get_context_summary`
- `get_latest_tool_versions`
- `get_python_package_version`
