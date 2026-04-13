"""
Tool Configuration for WorldContext MCP Server.

Contains tool implementations and the registration dictionary for bulk registration.
"""

import datetime
import logging
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import timedelta
from typing import Any, Dict

import httpx

from config import config

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Thread-safe cache
# ---------------------------------------------------------------------------

class VersionCache:
    """Thread-safe cache with TTL support."""

    def __init__(self, ttl_hours: int = 1):
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._ttl = timedelta(hours=ttl_hours)
        self._lock = threading.Lock()

    def get_or_fetch(self, key: str, fetch_func):
        with self._lock:
            if self._is_valid(key):
                return self._cache[key]["data"]

        # Fetch outside the lock to avoid blocking other threads
        try:
            data = fetch_func()
            with self._lock:
                self._cache[key] = {"data": data, "timestamp": datetime.datetime.now()}
            return data
        except Exception as e:
            with self._lock:
                if key in self._cache:
                    logger.warning("Using stale cache for %s due to error: %s", key, e)
                    return self._cache[key]["data"]
            raise

    def _is_valid(self, key: str) -> bool:
        if key not in self._cache:
            return False
        age = datetime.datetime.now() - self._cache[key]["timestamp"]
        return age < self._ttl


_version_cache = VersionCache(ttl_hours=1)


# ---------------------------------------------------------------------------
# Package / tool version lists
# ---------------------------------------------------------------------------

PYTHON_PACKAGES = [
    "mcp",
    "httpx",
    "pandas",
    "pyarrow",
    "langchain",
    "langgraph",
    "torch",
    "psycopg",
    "atlassian-python-api",
]

INFRASTRUCTURE_TOOLS: Dict[str, Dict[str, str]] = {
    "postgresql": {"source": "github", "repo": "postgresql/postgresql", "name": "PostgreSQL"},
    "quarkus": {"source": "github", "repo": "quarkusio/quarkus", "name": "Quarkus"},
    "kafka": {"source": "github", "repo": "apache/kafka", "name": "Apache Kafka"},
    "redpanda": {"source": "github", "repo": "redpanda-data/redpanda", "name": "Redpanda"},
}


# ---------------------------------------------------------------------------
# Low-level fetch helpers
# ---------------------------------------------------------------------------

def _parse_date(raw: str) -> str:
    """Best-effort ISO date string → YYYY-MM-DD."""
    try:
        dt = datetime.datetime.fromisoformat(raw.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d")
    except Exception:
        return "unknown"


def fetch_pypi_version(package: str) -> Dict[str, Any]:
    """Fetch version info for a single Python package from PyPI."""
    try:
        with httpx.Client(timeout=10) as client:
            response = client.get(f"https://pypi.org/pypi/{package}/json")

        if response.status_code != 200:
            return {"name": package, "error": f"HTTP {response.status_code}", "source": "PyPI"}

        data = response.json()
        info = data.get("info", {})
        latest = info.get("version", "unknown")
        releases = data.get("releases", {})

        release_date = "unknown"
        if latest in releases and releases[latest]:
            raw = releases[latest][0].get("upload_time", "")
            if raw:
                release_date = _parse_date(raw)

        return {
            "name": package,
            "latest_version": latest,
            "release_date": release_date,
            "source": "PyPI",
            "homepage": info.get("home_page", ""),
            "summary": (info.get("summary", "") or "")[:100],
        }
    except httpx.TimeoutException:
        return {"name": package, "error": "timeout", "source": "PyPI"}
    except Exception as e:
        return {"name": package, "error": str(e), "source": "PyPI"}


def fetch_github_version(tool_name: str, tool_cfg: Dict[str, str]) -> Dict[str, Any]:
    """Fetch latest release info from GitHub."""
    name = tool_cfg["name"]
    try:
        url = f"https://api.github.com/repos/{tool_cfg['repo']}/releases/latest"
        with httpx.Client(timeout=10) as client:
            response = client.get(url)

        if response.status_code != 200:
            return {"name": name, "error": f"HTTP {response.status_code}", "source": "GitHub"}

        data = response.json()
        release_date = _parse_date(data.get("published_at", "")) if data.get("published_at") else "unknown"

        return {
            "name": name,
            "latest_version": data.get("tag_name", "unknown").lstrip("v"),
            "release_date": release_date,
            "source": "GitHub",
            "url": data.get("html_url", ""),
            "description": (data.get("body", "") or "")[:100],
        }
    except httpx.TimeoutException:
        return {"name": name, "error": "timeout", "source": "GitHub"}
    except Exception as e:
        return {"name": name, "error": str(e), "source": "GitHub"}


def _fetch_versions_concurrently() -> tuple:
    """Fetch all Python + infrastructure versions in parallel."""
    python_data: Dict[str, Any] = {}
    infra_data: Dict[str, Any] = {}

    with ThreadPoolExecutor(max_workers=6) as pool:
        py_futures = {pool.submit(fetch_pypi_version, p): p for p in PYTHON_PACKAGES}
        infra_futures = {
            pool.submit(fetch_github_version, name, cfg): name
            for name, cfg in INFRASTRUCTURE_TOOLS.items()
        }

        for f in as_completed(py_futures):
            pkg = py_futures[f]
            try:
                result = f.result()
                python_data[result.get("name", pkg)] = result
            except Exception as e:
                python_data[pkg] = {"name": pkg, "error": str(e), "source": "PyPI"}

        for f in as_completed(infra_futures):
            tool = infra_futures[f]
            try:
                result = f.result()
                key = result.get("name", tool).lower().replace(" ", "_")
                infra_data[key] = result
            except Exception as e:
                infra_data[tool] = {"name": INFRASTRUCTURE_TOOLS[tool]["name"], "error": str(e), "source": "GitHub"}

    return python_data, infra_data


# ---------------------------------------------------------------------------
# MCP tool implementations
# ---------------------------------------------------------------------------

def get_current_datetime() -> Dict[str, Any]:
    """Get current date and time information."""
    now = datetime.datetime.now()
    utc_now = datetime.datetime.now(datetime.timezone.utc)

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
        "formatted_display": now.strftime("%A, %B %d, %Y at %I:%M %p"),
    }


def get_python_package_version(package_name: str) -> Dict[str, Any]:
    """Get the latest version of any Python package from PyPI.

    Args:
        package_name: Name of the Python package to look up.
    """
    if not package_name or not isinstance(package_name, str):
        return {"error": "Package name must be a non-empty string", "package_name": str(package_name)}

    package_name = package_name.strip().lower()
    if not package_name:
        return {"error": "Package name cannot be empty after cleaning"}

    result = fetch_pypi_version(package_name)
    if "error" not in result:
        result["pypi_url"] = f"https://pypi.org/project/{package_name}/"
        result["install_command"] = f"pip install {package_name}"
    return result


def get_latest_tool_versions() -> Dict[str, Any]:
    """Get latest versions of tracked development tools (cached 1 hour)."""

    # Stable cache key — changes once per hour
    cache_key = f"tool_versions_{datetime.datetime.now().strftime('%Y%m%d%H')}"

    try:
        python_data, infra_data = _version_cache.get_or_fetch(cache_key, _fetch_versions_concurrently)

        py_ok = sum(1 for v in python_data.values() if "error" not in v)
        infra_ok = sum(1 for v in infra_data.values() if "error" not in v)

        return {
            "last_updated": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "python_packages": python_data,
            "infrastructure": infra_data,
            "summary": {
                "total_tools_tracked": len(python_data) + len(infra_data),
                "successful_fetches": py_ok + infra_ok,
                "failed_fetches": (len(python_data) - py_ok) + (len(infra_data) - infra_ok),
            },
            "note": "Versions fetched from PyPI and GitHub with 1-hour caching",
        }
    except Exception as e:
        logger.error("Error in get_latest_tool_versions: %s", e)
        return {"error": str(e), "last_updated": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}


def get_stock_market_overview() -> Dict[str, Any]:
    """Get current stock market overview and major indices.

    Note: Uses Alpha Vantage API — configure your API key in config.yaml.
    """
    api_key = config.get("api_keys", "alphavantage", default="demo")
    base_url = "https://www.alphavantage.co/query"

    indices = {"SPY": "S&P 500 ETF", "DIA": "Dow Jones ETF", "QQQ": "NASDAQ ETF"}
    market_data: Dict[str, Any] = {}

    for symbol, name in indices.items():
        try:
            url = f"{base_url}?function=GLOBAL_QUOTE&symbol={symbol}&apikey={api_key}"
            with httpx.Client(timeout=10) as client:
                response = client.get(url)

            if response.status_code != 200:
                market_data[symbol] = {"name": name, "error": f"HTTP {response.status_code}"}
                continue

            data = response.json()
            if "Global Quote" in data:
                q = data["Global Quote"]
                market_data[symbol] = {
                    "name": name,
                    "price": q.get("05. price", "N/A"),
                    "change": q.get("09. change", "N/A"),
                    "change_percent": q.get("10. change percent", "N/A"),
                    "last_updated": q.get("07. latest trading day", "N/A"),
                }
            elif "Note" in data:
                market_data[symbol] = {"name": name, "error": "API rate limit", "note": data["Note"]}
            else:
                market_data[symbol] = {"name": name, "error": "Unexpected response format"}
        except Exception as e:
            market_data[symbol] = {"name": name, "error": str(e)}

    now = datetime.datetime.now()
    is_open = now.weekday() < 5 and 9 <= now.hour < 16

    return {
        "market_status": "Open" if is_open else "Closed",
        "last_updated": now.strftime("%Y-%m-%d %H:%M:%S"),
        "indices": market_data,
        "api_key_status": "demo" if api_key == "demo" else "configured",
        "note": "Using demo API key — limited functionality" if api_key == "demo" else "Live market data",
    }


def get_news_headlines(count: int = 5) -> Dict[str, Any]:
    """Get current news headlines from NewsAPI across multiple categories.

    Args:
        count: Number of headlines to return (1-20).

    Note: Uses NewsAPI — configure your API key in config.yaml.
    """
    api_key = config.get("api_keys", "newsapi", default="demo")
    count = max(1, min(count, 20))
    all_headlines: list[Dict[str, Any]] = []

    # Curated news source queries
    sources = [
        (
            "International",
            "https://newsapi.org/v2/everything",
            {
                "q": "(war OR conflict OR ceasefire OR sanctions OR tariff OR trade OR humanitarian OR crisis OR refugee OR election OR nuclear OR terrorism OR climate OR disaster OR pandemic)",
                "domains": "reuters.com,bbc.com,apnews.com,cnn.com,theguardian.com,wsj.com,ft.com",
                "language": "en",
                "sortBy": "publishedAt",
                "pageSize": max(2, count // 2),
                "apiKey": api_key,
            },
        ),
        (
            "US Politics",
            "https://newsapi.org/v2/everything",
            {
                "q": "(congress OR senate OR \"white house\" OR legislation OR policy OR tariff OR economy OR inflation OR healthcare OR immigration OR defense OR budget)",
                "domains": "reuters.com,apnews.com,npr.org,politico.com,washingtonpost.com,nytimes.com",
                "language": "en",
                "sortBy": "publishedAt",
                "pageSize": max(1, count // 4),
                "apiKey": api_key,
            },
        ),
        (
            "Tennessee",
            "https://newsapi.org/v2/everything",
            {
                "q": "(Tennessee OR Nashville OR Memphis OR Knoxville) AND (government OR economy OR education OR health OR infrastructure OR environment)",
                "language": "en",
                "sortBy": "publishedAt",
                "pageSize": max(1, count // 4),
                "apiKey": api_key,
            },
        ),
    ]

    for source_name, url, params in sources:
        try:
            with httpx.Client(timeout=10) as client:
                response = client.get(url, params=params)

            if response.status_code != 200:
                continue

            articles = response.json().get("articles", [])
            for article in articles:
                if len(all_headlines) >= count:
                    break
                all_headlines.append({
                    "title": article.get("title", "No title"),
                    "description": article.get("description", ""),
                    "source": f"{article.get('source', {}).get('name', 'Unknown')} ({source_name})",
                    "published_at": article.get("publishedAt", ""),
                    "url": article.get("url", ""),
                    "category": source_name.lower(),
                })
        except Exception as e:
            logger.warning("Failed to fetch %s news: %s", source_name, e)

    status_note = "Using demo API key — limited functionality" if api_key == "demo" else "Live news data"

    return {
        "count": len(all_headlines),
        "headlines": all_headlines[:count],
        "last_updated": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "api_key_status": "demo" if api_key == "demo" else "configured",
        "sources": "International, US Politics, Tennessee",
        "note": status_note,
    }


def get_context_summary() -> Dict[str, Any]:
    """Get a comprehensive context summary (date/time + market + news) in one call."""
    dt = get_current_datetime()
    market = get_stock_market_overview()
    news = get_news_headlines(3)

    top_headline = "No headlines available"
    if news.get("headlines"):
        top_headline = news["headlines"][0].get("title", top_headline)

    return {
        "summary_generated_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "current_context": {
            "date_time": {
                "current_datetime": dt.get("current_datetime"),
                "formatted_display": dt.get("formatted_display"),
                "day_of_week": dt.get("day_of_week"),
            },
            "market_status": {
                "status": market.get("market_status", "Unknown"),
                "indices_count": len(market.get("indices", {})),
                "last_updated": market.get("last_updated"),
            },
            "news_summary": {
                "headlines_count": news.get("count", 0),
                "top_headline": top_headline,
            },
        },
        "detailed_data": {"datetime": dt, "market": market, "news": news},
        "note": "Comprehensive context summary. Use individual tools for more detail.",
    }


# ---------------------------------------------------------------------------
# Tool registration dictionary — single source of truth
# ---------------------------------------------------------------------------

WORLDCONTEXT_TOOLS: Dict[str, Dict[str, Any]] = {
    "get_current_datetime": {
        "function": get_current_datetime,
        "description": (
            "Get current date and time — essential for timestamping files, reports, "
            "logs, and making time-aware decisions."
        ),
    },
    "get_stock_market_overview": {
        "function": get_stock_market_overview,
        "description": (
            "Check if markets are open and how major indices are performing."
        ),
    },
    "get_news_headlines": {
        "function": get_news_headlines,
        "description": (
            "Get breaking news and current events across international, US politics, "
            "and Tennessee categories."
        ),
    },
    "get_context_summary": {
        "function": get_context_summary,
        "description": (
            "Get complete situational awareness in one call — current time, market "
            "status, and breaking news combined."
        ),
    },
    "get_latest_tool_versions": {
        "function": get_latest_tool_versions,
        "description": (
            "Check latest versions of tracked development tools and Python libraries "
            "(cached 1 hour)."
        ),
    },
    "get_python_package_version": {
        "function": get_python_package_version,
        "description": (
            "Look up the latest version of any Python package on PyPI."
        ),
    },
}


def get_tools_config() -> Dict[str, Dict[str, Any]]:
    """Return the tools configuration for bulk registration."""
    return WORLDCONTEXT_TOOLS