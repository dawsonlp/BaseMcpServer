"""
Tool Configuration for WorldContext MCP Server

This module contains the metadata configuration for all WorldContext MCP tools.
This enables bulk registration and reduces boilerplate code.
"""

from typing import Dict, Any, Callable
import datetime
import httpx
import json
import logging
import threading
from datetime import timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from config import config

logger = logging.getLogger(__name__)


# Thread-safe cache for version data
class VersionCache:
    """Thread-safe cache for version data with TTL support."""
    
    def __init__(self, ttl_hours: int = 1):
        self._cache = {}
        self._ttl = timedelta(hours=ttl_hours)
        self._lock = threading.Lock()
    
    def get_or_fetch(self, key: str, fetch_func):
        """Get cached data or fetch new data if cache is stale."""
        with self._lock:
            if self._is_valid(key):
                return self._cache[key]["data"]
            
            # Cache miss - fetch new data
            try:
                data = fetch_func()
                self._cache[key] = {
                    "data": data,
                    "timestamp": datetime.datetime.now()
                }
                return data
            except Exception as e:
                # Return stale data if available, otherwise raise
                if key in self._cache:
                    logger.warning(f"Using stale cache for {key} due to error: {e}")
                    return self._cache[key]["data"]
                raise
    
    def _is_valid(self, key: str) -> bool:
        """Check if cached data is still valid."""
        if key not in self._cache:
            return False
        
        age = datetime.datetime.now() - self._cache[key]["timestamp"]
        return age < self._ttl


# Global cache instance
_version_cache = VersionCache(ttl_hours=1)

# Tool configuration
PYTHON_PACKAGES = [
    "mcp",
    "httpx", 
    "pandas",
    "pyarrow",
    "langchain",
    "langgraph",
    "torch",
    "psycopg",
    "atlassian-python-api"
]

INFRASTRUCTURE_TOOLS = {
    "postgresql": {
        "source": "github",
        "repo": "postgresql/postgresql",
        "name": "PostgreSQL"
    },
    "quarkus": {
        "source": "github", 
        "repo": "quarkusio/quarkus",
        "name": "Quarkus"
    },
    "kafka": {
        "source": "github",
        "repo": "apache/kafka", 
        "name": "Apache Kafka"
    },
    "redpanda": {
        "source": "github",
        "repo": "redpanda-data/redpanda",
        "name": "Redpanda"
    }
}


def fetch_pypi_version(package: str) -> Dict[str, Any]:
    """Fetch version info for a Python package from PyPI."""
    try:
        url = f"https://pypi.org/pypi/{package}/json"
        with httpx.Client(timeout=10) as client:
            response = client.get(url)
        
        if response.status_code == 200:
            data = response.json()
            info = data.get("info", {})
            
            # Get latest release info
            releases = data.get("releases", {})
            latest_version = info.get("version", "unknown")
            
            # Find release date for latest version
            release_date = "unknown"
            if latest_version in releases and releases[latest_version]:
                # Get the first release file's upload time
                first_file = releases[latest_version][0]
                release_date = first_file.get("upload_time", "unknown")
                if release_date != "unknown":
                    # Parse and format the date
                    try:
                        dt = datetime.datetime.fromisoformat(release_date.replace("Z", "+00:00"))
                        release_date = dt.strftime("%Y-%m-%d")
                    except:
                        release_date = "unknown"
            
            return {
                "name": package,
                "latest_version": latest_version,
                "release_date": release_date,
                "source": "PyPI",
                "homepage": info.get("home_page", ""),
                "summary": info.get("summary", "")[:100] + "..." if info.get("summary", "") else ""
            }
        else:
            return {
                "name": package,
                "error": f"HTTP {response.status_code}",
                "source": "PyPI"
            }
            
    except httpx.TimeoutException:
        return {"name": package, "error": "timeout", "source": "PyPI"}
    except Exception as e:
        return {"name": package, "error": f"unexpected: {str(e)}", "source": "PyPI"}


def fetch_github_version(tool_name: str, tool_config: Dict[str, Any]) -> Dict[str, Any]:
    """Fetch version info for a tool from GitHub releases."""
    try:
        repo = tool_config["repo"]
        url = f"https://api.github.com/repos/{repo}/releases/latest"
        
        with httpx.Client(timeout=10) as client:
            response = client.get(url)
        
        if response.status_code == 200:
            data = response.json()
            
            # Parse release date
            release_date = "unknown"
            published_at = data.get("published_at", "")
            if published_at:
                try:
                    dt = datetime.datetime.fromisoformat(published_at.replace("Z", "+00:00"))
                    release_date = dt.strftime("%Y-%m-%d")
                except:
                    release_date = "unknown"
            
            return {
                "name": tool_config["name"],
                "latest_version": data.get("tag_name", "unknown").lstrip("v"),
                "release_date": release_date,
                "source": "GitHub",
                "url": data.get("html_url", ""),
                "description": data.get("body", "")[:100] + "..." if data.get("body", "") else ""
            }
        else:
            return {
                "name": tool_config["name"],
                "error": f"HTTP {response.status_code}",
                "source": "GitHub"
            }
            
    except httpx.TimeoutException:
        return {"name": tool_config["name"], "error": "timeout", "source": "GitHub"}
    except Exception as e:
        return {"name": tool_config["name"], "error": f"unexpected: {str(e)}", "source": "GitHub"}


def fetch_python_versions() -> Dict[str, Any]:
    """Fetch versions for all Python packages concurrently using threads."""
    python_data = {}
    
    with ThreadPoolExecutor(max_workers=5) as executor:
        # Submit all tasks
        future_to_package = {
            executor.submit(fetch_pypi_version, package): package 
            for package in PYTHON_PACKAGES
        }
        
        # Collect results
        for future in as_completed(future_to_package):
            try:
                result = future.result()
                package_name = result.get("name", "unknown")
                python_data[package_name] = result
            except Exception as e:
                package = future_to_package[future]
                logger.error(f"Error fetching Python package version for {package}: {e}")
                python_data[package] = {
                    "name": package,
                    "error": f"execution_error: {str(e)}",
                    "source": "PyPI"
                }
    
    return python_data


def fetch_infrastructure_versions() -> Dict[str, Any]:
    """Fetch versions for all infrastructure tools concurrently using threads."""
    infra_data = {}
    
    with ThreadPoolExecutor(max_workers=4) as executor:
        # Submit all tasks
        future_to_tool = {
            executor.submit(fetch_github_version, tool_name, tool_config): tool_name
            for tool_name, tool_config in INFRASTRUCTURE_TOOLS.items()
        }
        
        # Collect results
        for future in as_completed(future_to_tool):
            try:
                result = future.result()
                tool_name = result.get("name", "unknown").lower().replace(" ", "_")
                infra_data[tool_name] = result
            except Exception as e:
                tool_name = future_to_tool[future]
                logger.error(f"Error fetching infrastructure tool version for {tool_name}: {e}")
                infra_data[tool_name] = {
                    "name": INFRASTRUCTURE_TOOLS[tool_name]["name"],
                    "error": f"execution_error: {str(e)}",
                    "source": "GitHub"
                }
    
    return infra_data


def get_python_package_version(package_name: str) -> Dict[str, Any]:
    """Get the latest version of any Python package from PyPI.
    
    Args:
        package_name: Name of the Python package to look up
        
    Returns:
        Dictionary containing package version information including:
        - Latest version number
        - Release date
        - Homepage URL
        - Package summary
        - PyPI URL
    """
    try:
        # Validate package name
        if not package_name or not isinstance(package_name, str):
            return {
                "error": "Package name must be a non-empty string",
                "package_name": str(package_name) if package_name else "None"
            }
        
        # Clean package name
        package_name = package_name.strip().lower()
        if not package_name:
            return {
                "error": "Package name cannot be empty after cleaning",
                "package_name": package_name
            }
        
        # Fetch from PyPI
        result = fetch_pypi_version(package_name)
        
        # Add PyPI URL
        if "error" not in result:
            result["pypi_url"] = f"https://pypi.org/project/{package_name}/"
            result["install_command"] = f"pip install {package_name}"
        
        return result
        
    except Exception as e:
        return {
            "error": f"Failed to fetch package version: {str(e)}",
            "package_name": package_name,
            "note": "Check package name spelling and PyPI availability"
        }


def get_latest_tool_versions() -> Dict[str, Any]:
    """Get latest versions of development tools using concurrent fetching."""
    
    def fetch_all_versions():
        """Fetch all version data concurrently using threads."""
        with ThreadPoolExecutor(max_workers=2) as executor:
            # Submit both tasks
            python_future = executor.submit(fetch_python_versions)
            infra_future = executor.submit(fetch_infrastructure_versions)
            
            # Get results
            python_data = python_future.result()
            infra_data = infra_future.result()
            
            return python_data, infra_data
    
    # Use cache to avoid repeated API calls (include minute to force refresh after torch fix)
    cache_key = f"tool_versions_{datetime.datetime.now().hour}_{datetime.datetime.now().minute}"
    
    try:
        python_data, infra_data = _version_cache.get_or_fetch(
            cache_key, fetch_all_versions
        )
        
        # Count successful vs failed fetches
        python_success = sum(1 for v in python_data.values() if "error" not in v)
        python_total = len(python_data)
        infra_success = sum(1 for v in infra_data.values() if "error" not in v)
        infra_total = len(infra_data)
        
        return {
            "last_updated": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "python_packages": python_data,
            "infrastructure": infra_data,
            "summary": {
                "total_tools_tracked": python_total + infra_total,
                "successful_fetches": python_success + infra_success,
                "failed_fetches": (python_total - python_success) + (infra_total - infra_success),
                "python_packages_count": python_total,
                "infrastructure_tools_count": infra_total,
                "cache_status": "hit" if cache_key in _version_cache._cache else "miss"
            },
            "note": "Version data fetched concurrently from PyPI and GitHub APIs with 1-hour caching"
        }
        
    except Exception as e:
        logger.error(f"Error in get_latest_tool_versions: {e}")
        return {
            "error": f"Failed to fetch tool versions: {str(e)}",
            "last_updated": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "note": "Tool version data unavailable"
        }


def get_current_datetime() -> Dict[str, Any]:
    """Get current date and time information.
    
    Returns comprehensive date/time information including:
    - Current date and time
    - Day of week
    - Week number
    - Time zone information
    - Unix timestamp
    """
    now = datetime.datetime.now()
    utc_now = datetime.datetime.utcnow()
    
    return {
        "current_datetime": now.strftime("%Y-%m-%d %H:%M:%S"),
        "current_date": now.strftime("%Y-%m-%d"),
        "current_time": now.strftime("%H:%M:%S"),
        "day_of_week": now.strftime("%A"),
        "month": now.strftime("%B"),
        "year": now.year,
        "week_number": now.isocalendar()[1],
        "timezone": str(now.astimezone().tzinfo),
        "utc_datetime": utc_now.strftime("%Y-%m-%d %H:%M:%S UTC"),
        "unix_timestamp": int(now.timestamp()),
        "formatted_display": now.strftime("%A, %B %d, %Y at %I:%M %p")
    }


def get_stock_market_overview() -> Dict[str, Any]:
    """Get current stock market overview and major indices.
    
    Provides information about major stock market indices including:
    - S&P 500, Dow Jones, NASDAQ
    - Current values and daily changes
    - Market status (open/closed)
    
    Note: Uses Alpha Vantage API - configure your API key in config.yaml
    """
    try:
        api_key = config.get("api_keys", "alphavantage", default="demo")
        base_url = "https://www.alphavantage.co/query"
        
        # Default market symbols
        indices = {
            "SPY": "S&P 500 ETF",
            "DIA": "Dow Jones ETF", 
            "QQQ": "NASDAQ ETF"
        }
        
        market_data = {}
        
        # Fetch data for each symbol
        for symbol, name in indices.items():
            try:
                url = f"{base_url}?function=GLOBAL_QUOTE&symbol={symbol}&apikey={api_key}"
                with httpx.Client() as client:
                    response = client.get(url, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    if "Global Quote" in data:
                        quote = data["Global Quote"]
                        market_data[symbol] = {
                            "name": name,
                            "price": quote.get("05. price", "N/A"),
                            "change": quote.get("09. change", "N/A"),
                            "change_percent": quote.get("10. change percent", "N/A"),
                            "last_updated": quote.get("07. latest trading day", "N/A")
                        }
                    elif "Note" in data:
                        # API rate limit or other issue
                        market_data[symbol] = {
                            "name": name,
                            "error": "API rate limit or quota exceeded",
                            "note": data.get("Note", "Unknown API issue")
                        }
                    else:
                        market_data[symbol] = {
                            "name": name,
                            "error": "Unexpected API response format"
                        }
                else:
                    market_data[symbol] = {
                        "name": name,
                        "error": f"HTTP {response.status_code}: {response.text[:100]}"
                    }
            except Exception as e:
                market_data[symbol] = {
                    "name": name,
                    "error": f"Unable to fetch data: {str(e)}"
                }
        
        # Market status calculation (simplified)
        now = datetime.datetime.now()
        is_weekend = now.weekday() >= 5
        is_market_hours = 9 <= now.hour < 16  # Simplified market hours
        
        status_note = "Using demo API key - limited functionality" if api_key == "demo" else "Live market data"
        
        return {
            "market_status": "Closed" if is_weekend or not is_market_hours else "Open",
            "last_updated": now.strftime("%Y-%m-%d %H:%M:%S"),
            "indices": market_data,
            "api_key_status": "demo" if api_key == "demo" else "configured",
            "note": status_note
        }
        
    except Exception as e:
        return {
            "error": f"Failed to fetch market data: {str(e)}",
            "market_status": "Unknown",
            "note": "Market data unavailable - check API configuration"
        }


def get_news_headlines(category: str = "general", count: int = 5) -> Dict[str, Any]:
    """Get current news headlines from NewsAPI.
    
    Args:
        category: News category (general, business, technology, health, etc.)
        count: Number of headlines to return (1-20)
        
    Returns:
        Dictionary containing current news headlines with titles, descriptions, and sources.
        
    Note: Uses NewsAPI - configure your API key in config.yaml
    """
    try:
        api_key = config.get("api_keys", "newsapi", default="demo")
        
        # Validate inputs
        count = max(1, min(count, 20))
        valid_categories = ["general", "business", "technology", "health", "science", "sports", "entertainment"]
        if category not in valid_categories:
            category = "general"
        
        # Get multiple news sources for comprehensive coverage
        all_headlines = []
        
        # 1. Major international/geopolitical news - focus on consequential events
        international_url = "https://newsapi.org/v2/everything"
        international_params = {
            "q": "(war OR conflict OR military OR invasion OR ceasefire OR peace OR treaty OR sanctions OR tariff OR trade OR embargo OR humanitarian OR crisis OR famine OR starvation OR refugee OR genocide OR coup OR election OR democracy OR authoritarian OR nuclear OR missile OR terrorism OR climate OR disaster OR pandemic OR epidemic) AND NOT (sports OR entertainment OR celebrity OR local)",
            "domains": "reuters.com,bbc.com,apnews.com,cnn.com,theguardian.com,wsj.com,ft.com,economist.com",
            "language": "en",
            "sortBy": "publishedAt",
            "pageSize": max(2, count // 2),
            "apiKey": api_key
        }
        
        # 2. US political and economic policy - focus on consequential domestic issues
        politics_url = "https://newsapi.org/v2/everything"
        politics_params = {
            "q": "(congress OR senate OR \"white house\" OR federal OR legislation OR policy OR tariff OR trade OR economy OR inflation OR recession OR unemployment OR healthcare OR immigration OR climate OR energy OR defense OR military OR budget OR debt OR tax) AND NOT (sports OR entertainment OR celebrity OR local)",
            "domains": "reuters.com,apnews.com,npr.org,politico.com,washingtonpost.com,nytimes.com,wsj.com,ft.com",
            "language": "en",
            "sortBy": "publishedAt",
            "pageSize": max(1, count // 4),
            "apiKey": api_key
        }
        
        # 3. Tennessee news - focus on significant local developments
        tennessee_url = "https://newsapi.org/v2/everything"
        tennessee_params = {
            "q": "(Tennessee OR Nashville OR Memphis OR Knoxville) AND (government OR politics OR economy OR education OR health OR infrastructure OR environment OR disaster OR policy) AND NOT (sports OR entertainment OR celebrity)",
            "language": "en",
            "sortBy": "publishedAt",
            "pageSize": max(1, count // 4),
            "apiKey": api_key
        }
        
        # Fetch from all sources
        sources = [
            ("International", international_url, international_params),
            ("US Politics", politics_url, politics_params),
            ("Tennessee", tennessee_url, tennessee_params)
        ]
        
        for source_name, url, params in sources:
            try:
                with httpx.Client() as client:
                    response = client.get(url, params=params, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if "articles" in data and data["articles"]:
                        for article in data["articles"]:
                            if len(all_headlines) >= count:
                                break
                            
                            all_headlines.append({
                                "title": article.get("title", "No title"),
                                "description": article.get("description", "No description"),
                                "source": f"{article.get('source', {}).get('name', 'Unknown')} ({source_name})",
                                "published_at": article.get("publishedAt", "Unknown"),
                                "url": article.get("url", ""),
                                "category": source_name.lower()
                            })
                            
            except Exception as e:
                logger.warning(f"Failed to fetch {source_name} news: {str(e)}")
                continue
        
        # If we got news, return it
        if all_headlines:
            status_note = "Using demo API key - limited functionality" if api_key == "demo" else "Live news data from multiple sources"
            
            return {
                "category": f"{category} + international + politics + Tennessee",
                "count": len(all_headlines),
                "headlines": all_headlines[:count],
                "last_updated": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "api_key_status": "demo" if api_key == "demo" else "configured",
                "sources": "International, US Politics, Tennessee",
                "note": status_note
            }
        
        # Fallback if no news retrieved
        return {
            "category": category,
            "count": 0,
            "headlines": [],
            "error": "No news articles retrieved from any source",
            "api_key_status": "demo" if api_key == "demo" else "configured",
            "note": "Check NewsAPI configuration and network connectivity"
        }
        
    except Exception as e:
        return {
            "error": f"Failed to fetch news: {str(e)}",
            "category": category,
            "note": "News data unavailable - check API configuration"
        }


def get_context_summary() -> Dict[str, Any]:
    """Get a comprehensive context summary including date/time, market, and news.
    
    Returns a combined summary of current context information including:
    - Current date and time
    - Stock market overview
    - Top news headlines
    
    This is a convenience tool that combines all context information in one call.
    """
    try:
        # Get all context information
        datetime_info = get_current_datetime()
        market_info = get_stock_market_overview()
        news_info = get_news_headlines("general", 3)
        
        return {
            "summary_generated_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "current_context": {
                "date_time": {
                    "current_datetime": datetime_info.get("current_datetime"),
                    "formatted_display": datetime_info.get("formatted_display"),
                    "day_of_week": datetime_info.get("day_of_week")
                },
                "market_status": {
                    "status": market_info.get("market_status", "Unknown"),
                    "indices_count": len(market_info.get("indices", {})),
                    "last_updated": market_info.get("last_updated")
                },
                "news_summary": {
                    "headlines_count": news_info.get("count", 0),
                    "category": news_info.get("category", "general"),
                    "top_headline": news_info.get("headlines", [{}])[0].get("title", "No headlines available") if news_info.get("headlines") else "No headlines available"
                }
            },
            "detailed_data": {
                "datetime": datetime_info,
                "market": market_info,
                "news": news_info
            },
            "note": "This is a comprehensive context summary. Use individual tools for more detailed information."
        }
        
    except Exception as e:
        return {
            "error": f"Failed to generate context summary: {str(e)}",
            "summary_generated_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }


# Tool configuration - single source of truth for all WorldContext MCP tools
WORLDCONTEXT_TOOLS: Dict[str, Dict[str, Any]] = {
    # Primary intuitive names
    'current_time': {
        'function': get_current_datetime,
        'description': 'Get current date and time - essential for timestamping files, reports, logs, and making time-aware decisions. Use this whenever you need to know the current date for file naming, scheduling, or documentation.'
    },
    
    'market_status': {
        'function': get_stock_market_overview,
        'description': 'Check if markets are open and how major indices are performing - know market status and trends before making business decisions or timing deployments.'
    },
    
    'breaking_news': {
        'function': get_news_headlines,
        'description': 'Get breaking news and current events - stay informed on what\'s happening globally to understand external factors that might affect your work or decisions.'
    },
    
    'world_context': {
        'function': get_context_summary,
        'description': 'Get complete situational awareness in one call - current time, market status, and breaking news combined. Perfect for understanding the full context before important decisions or actions.'
    },
    
    'check_versions': {
        'function': get_latest_tool_versions,
        'description': 'Check latest versions of development tools and libraries - keep your development stack current, secure, and up-to-date with recent improvements and security patches.'
    },
    
    'lookup_package': {
        'function': get_python_package_version,
        'description': 'Look up any Python package version instantly - verify dependencies, check for updates, and ensure you\'re using the latest stable version of any PyPI package.'
    },
    
    # Keep original names for backwards compatibility
    'get_current_datetime': {
        'function': get_current_datetime,
        'description': 'Get current date and time - essential for timestamping files, reports, logs, and making time-aware decisions. Use this whenever you need to know the current date for file naming, scheduling, or documentation.'
    },
    
    'get_stock_market_overview': {
        'function': get_stock_market_overview,
        'description': 'Check if markets are open and how major indices are performing - know market status and trends before making business decisions or timing deployments.'
    },
    
    'get_news_headlines': {
        'function': get_news_headlines,
        'description': 'Get breaking news and current events - stay informed on what\'s happening globally to understand external factors that might affect your work or decisions.'
    },
    
    'get_context_summary': {
        'function': get_context_summary,
        'description': 'Get complete situational awareness in one call - current time, market status, and breaking news combined. Perfect for understanding the full context before important decisions or actions.'
    },
    
    'get_latest_tool_versions': {
        'function': get_latest_tool_versions,
        'description': 'Check latest versions of development tools and libraries - keep your development stack current, secure, and up-to-date with recent improvements and security patches.'
    },
    
    'get_python_package_version': {
        'function': get_python_package_version,
        'description': 'Look up any Python package version instantly - verify dependencies, check for updates, and ensure you\'re using the latest stable version of any PyPI package.'
    }
}


def get_tool_count() -> int:
    """Get the total number of configured tools."""
    return len(WORLDCONTEXT_TOOLS)


def get_tool_names() -> list[str]:
    """Get list of all tool names."""
    return list(WORLDCONTEXT_TOOLS.keys())


def get_tool_config(tool_name: str) -> Dict[str, Any]:
    """
    Get configuration for a specific tool.

    Args:
        tool_name: Name of the tool

    Returns:
        Tool configuration dictionary

    Raises:
        KeyError: If tool name not found
    """
    if tool_name not in WORLDCONTEXT_TOOLS:
        raise KeyError(f"Tool '{tool_name}' not found in configuration")
    
    return WORLDCONTEXT_TOOLS[tool_name].copy()


def validate_tool_config() -> Dict[str, Any]:
    """
    Validate the tool configuration for completeness and correctness.

    Returns:
        Validation results with any issues found
    """
    issues = []
    warnings = []
    
    required_keys = ['function', 'description', 'parameters']
    
    for tool_name, config in WORLDCONTEXT_TOOLS.items():
        # Check required keys
        for key in required_keys:
            if key not in config:
                issues.append(f"Tool '{tool_name}' missing required key: {key}")
        
        # Check function is callable
        if 'function' in config:
            if not callable(config['function']):
                issues.append(f"Tool '{tool_name}' function must be callable")
        
        # Check description is non-empty string
        if 'description' in config:
            if not isinstance(config['description'], str) or not config['description'].strip():
                issues.append(f"Tool '{tool_name}' description must be non-empty string")
        
        # Check parameters is dict
        if 'parameters' in config:
            if not isinstance(config['parameters'], dict):
                issues.append(f"Tool '{tool_name}' parameters must be a dictionary")
    
    return {
        'valid': len(issues) == 0,
        'tool_count': len(WORLDCONTEXT_TOOLS),
        'issues': issues,
        'warnings': warnings
    }


def get_tools_config() -> Dict[str, Dict[str, Any]]:
    """
    Get the tools configuration for registration.
    
    Returns:
        Dictionary mapping tool names to their configuration
    """
    return WORLDCONTEXT_TOOLS


def get_config_stats() -> Dict[str, Any]:
    """
    Get statistics about the tool configuration.

    Returns:
        Configuration statistics
    """
    validation = validate_tool_config()
    
    return {
        'total_tools': len(WORLDCONTEXT_TOOLS),
        'validation': validation,
        'description': 'Metadata-driven tool configuration for WorldContext MCP server'
    }
