"""
Tool Configuration for the loadbearing_youtube MCP Server.

Thin adapter: the real work lives in the `loadbearing_youtube` package
(pipeline, providers, analysis). Each function here returns a plain,
JSON-serialisable dict; mcp-commons handles the MCP protocol details.
"""

import logging
from typing import Any, Dict

from loadbearing_youtube import analyze, get_transcript
from loadbearing_youtube.providers import discover
from loadbearing_youtube.render import render_markdown, render_transcript

from config import config

logger = logging.getLogger(__name__)


def _resolve(provider: str, model: str, languages: str) -> tuple:
    """Precedence for each setting: explicit tool arg > server config.yaml >
    the loadbearing_youtube env defaults (handled downstream)."""
    prov = provider or config.get("analysis", "provider", default="") or None
    mdl = model or config.get("analysis", "model", default="") or None
    langs = languages or config.get("analysis", "languages", default="en") or "en"
    lang_list = [x.strip() for x in langs.split(",") if x.strip()] or ["en"]
    return prov, mdl, lang_list


def get_video_transcript(url: str, languages: str = "", timestamps: bool = True) -> Dict[str, Any]:
    """Fetch the full transcript of a YouTube video (no LLM involved).

    Args:
        url: YouTube video URL or 11-character video id.
        languages: Comma-separated language preference (e.g. "en,es"). Blank = "en".
        timestamps: Include [mm:ss] markers in the transcript text.
    """
    if not url or not isinstance(url, str):
        return {"error": "url must be a non-empty string", "success": False}

    _, _, lang_list = _resolve("", "", languages)
    try:
        t = get_transcript(url, lang_list)
    except Exception as e:
        logger.warning("transcript fetch failed for %s: %s", url, e)
        return {"error": str(e), "success": False}

    return {
        "success": True,
        "video_id": t.video_id,
        "url": t.url,
        "title": t.title,
        "author": t.author,
        "language": t.language,
        "is_generated": t.is_generated,
        "duration_seconds": round(t.duration, 1),
        "char_count": t.char_count,
        "segment_count": len(t.segments),
        "transcript": render_transcript(t, timestamps=timestamps),
    }


def analyze_video(
    url: str,
    provider: str = "",
    model: str = "",
    languages: str = "",
) -> Dict[str, Any]:
    """Extract a video's transcript and expose its LOAD-BEARING components:
    the claims, decisions, tradeoffs, and verdicts the video's conclusion
    actually rests on (not a generic summary).

    Args:
        url: YouTube video URL or 11-character video id.
        provider: LLM provider ("ollama", "openai", "anthropic"). Blank = configured default.
        model: Model name for the provider. Blank = provider default.
        languages: Comma-separated language preference. Blank = "en".
    """
    if not url or not isinstance(url, str):
        return {"error": "url must be a non-empty string", "success": False}

    prov, mdl, lang_list = _resolve(provider, model, languages)
    try:
        report = analyze(url, provider=prov, model=mdl, languages=lang_list)
    except Exception as e:
        logger.warning("analysis failed for %s: %s", url, e)
        return {"error": str(e), "success": False}

    result = report.to_dict()
    result["success"] = True
    result["markdown"] = render_markdown(report)
    return result


def list_analysis_providers() -> Dict[str, Any]:
    """List the LLM providers available for analysis, which are configured
    right now, and the models each one can use."""
    try:
        providers = discover()
    except Exception as e:
        return {"error": str(e), "success": False}
    return {
        "success": True,
        "providers": providers,
        "default": config.get("analysis", "provider", default="ollama"),
    }


# ---------------------------------------------------------------------------
# Tool registration dictionary — single source of truth
# ---------------------------------------------------------------------------

LOADBEARING_YOUTUBE_TOOLS: Dict[str, Dict[str, Any]] = {
    "analyze_video": {
        "function": analyze_video,
        "description": (
            "Extract a YouTube video's transcript and expose its load-bearing "
            "components — the claims, decisions, tradeoffs, comparison verdicts, "
            "and recommendation the conclusion actually rests on, with timestamps. "
            "Returns structured data plus a rendered markdown report."
        ),
    },
    "get_video_transcript": {
        "function": get_video_transcript,
        "description": (
            "Fetch the full transcript of a YouTube video (no LLM), with optional "
            "[mm:ss] timestamps, title, author, and duration."
        ),
    },
    "list_analysis_providers": {
        "function": list_analysis_providers,
        "description": (
            "List LLM providers available for analysis, which are configured, and "
            "the models each can use (Ollama is the local, no-key default)."
        ),
    },
}


def get_tools_config() -> Dict[str, Dict[str, Any]]:
    """Return the tools configuration for bulk registration."""
    return LOADBEARING_YOUTUBE_TOOLS
