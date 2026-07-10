"""
Tool Configuration for the loadbearing_youtube MCP Server.

Thin adapter: the real work lives in the `loadbearing_youtube` package
(pipeline, providers, analysis). Each function here returns a plain,
JSON-serialisable dict; mcp-commons handles the MCP protocol details.
"""

import logging
import os
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict

from loadbearing_youtube import analyze, get_transcript
from loadbearing_youtube.providers import discover
from loadbearing_youtube.render import render_markdown, render_transcript

from config import config

logger = logging.getLogger(__name__)

# --- async job store --------------------------------------------------------
# A full analysis of a long video with a cloud model can take ~60-90s, which
# exceeds a typical MCP client's per-request timeout. So analysis runs on a
# background thread tracked by job id: analyze_video waits briefly and either
# returns the finished report or hands back a job_id for get_analysis_result
# to poll. Jobs live in-process for the server's lifetime.

_JOBS: Dict[str, Dict[str, Any]] = {}
_EVENTS: Dict[str, threading.Event] = {}
_JOBS_LOCK = threading.Lock()
_EXECUTOR = ThreadPoolExecutor(max_workers=2, thread_name_prefix="lb-analysis")

# How long analyze_video blocks before handing back a job_id. Kept under the
# common ~60s MCP request timeout so short videos return inline in one call.
_INLINE_WAIT_S = 45
# Poll wait ceiling for get_analysis_result.
_MAX_POLL_WAIT_S = 45
# Drop finished jobs older than this when a new one starts.
_JOB_TTL_S = 3600


def _prune_jobs() -> None:
    now = time.time()
    with _JOBS_LOCK:
        stale = [
            jid
            for jid, j in _JOBS.items()
            if j["status"] in ("done", "error") and now - j.get("finished", now) > _JOB_TTL_S
        ]
        for jid in stale:
            _JOBS.pop(jid, None)
            _EVENTS.pop(jid, None)


def _public_job(job_id: str, job: Dict[str, Any]) -> Dict[str, Any]:
    """A JSON-serialisable view of a job (never includes threads/events)."""
    out: Dict[str, Any] = {
        "success": job["status"] != "error",
        "job_id": job_id,
        "status": job["status"],
        "url": job["url"],
        "elapsed_seconds": round((job.get("finished") or time.time()) - job["created"], 1),
    }
    if job["status"] == "done":
        out.update(job["result"])
    elif job["status"] == "error":
        out["error"] = job["error"]
    else:
        out["message"] = (
            f"Analysis still running. Call get_analysis_result with job_id "
            f"'{job_id}' to retrieve it."
        )
    return out


def _run_job(job_id: str, url: str, prov, mdl, lang_list) -> None:
    try:
        report = analyze(url, provider=prov, model=mdl, languages=lang_list)
        result = report.to_dict()
        result["markdown"] = render_markdown(report)
        with _JOBS_LOCK:
            _JOBS[job_id].update(status="done", result=result, finished=time.time())
    except Exception as e:  # noqa: BLE001 - surface any failure to the caller
        logger.warning("analysis job %s failed for %s: %s", job_id, url, e)
        with _JOBS_LOCK:
            _JOBS[job_id].update(status="error", error=str(e), finished=time.time())
    finally:
        _EVENTS[job_id].set()


def _apply_secrets() -> None:
    """Bridge cloud API keys from the server config.yaml into the environment
    that loadbearing_youtube's providers read. Keeping keys in config.yaml
    matches the repo convention (see worldcontext). An already-set env var
    always wins, so this never clobbers a real environment key."""
    mapping = {
        "anthropic_api_key": "ANTHROPIC_API_KEY",
        "openai_api_key": "OPENAI_API_KEY",
    }
    for cfg_key, env_key in mapping.items():
        value = config.get("secrets", cfg_key, default="") or ""
        if value and not os.environ.get(env_key):
            os.environ[env_key] = value


_apply_secrets()


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

    Analysis runs on a background job. Short videos finish within a few tens of
    seconds and are returned inline. If the analysis is still running when the
    inline wait elapses, this returns status "running" plus a job_id — call
    get_analysis_result(job_id) to fetch the finished report.

    Args:
        url: YouTube video URL or 11-character video id.
        provider: LLM provider ("ollama", "openai", "anthropic"). Blank = configured default.
        model: Model name for the provider. Blank = provider default.
        languages: Comma-separated language preference. Blank = "en".
    """
    if not url or not isinstance(url, str):
        return {"error": "url must be a non-empty string", "success": False}

    _prune_jobs()
    prov, mdl, lang_list = _resolve(provider, model, languages)

    job_id = uuid.uuid4().hex[:12]
    event = threading.Event()
    with _JOBS_LOCK:
        _EVENTS[job_id] = event
        _JOBS[job_id] = {"status": "running", "url": url, "created": time.time()}
    _EXECUTOR.submit(_run_job, job_id, url, prov, mdl, lang_list)

    event.wait(_INLINE_WAIT_S)
    with _JOBS_LOCK:
        return _public_job(job_id, dict(_JOBS[job_id]))


def get_analysis_result(job_id: str, wait_seconds: int = 30) -> Dict[str, Any]:
    """Retrieve (or wait for) the result of an analyze_video job.

    Args:
        job_id: The id returned by analyze_video when it was still running.
        wait_seconds: How long to block waiting for completion (0-45). Use 0 for
            an immediate status check, or a positive value to wait for a
            still-running job to finish.
    """
    if not job_id or not isinstance(job_id, str):
        return {"error": "job_id must be a non-empty string", "success": False}

    with _JOBS_LOCK:
        event = _EVENTS.get(job_id)
        exists = job_id in _JOBS
    if not exists:
        return {"error": f"unknown job_id: {job_id}", "success": False}

    wait = max(0, min(int(wait_seconds or 0), _MAX_POLL_WAIT_S))
    if wait and event is not None:
        event.wait(wait)

    with _JOBS_LOCK:
        return _public_job(job_id, dict(_JOBS[job_id]))


def list_analysis_jobs() -> Dict[str, Any]:
    """List analysis jobs tracked by this server (most recent first)."""
    with _JOBS_LOCK:
        jobs = [
            {
                "job_id": jid,
                "status": j["status"],
                "url": j["url"],
                "elapsed_seconds": round((j.get("finished") or time.time()) - j["created"], 1),
            }
            for jid, j in _JOBS.items()
        ]
    jobs.sort(key=lambda x: x["elapsed_seconds"])
    return {"success": True, "jobs": jobs, "count": len(jobs)}


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
            "Returns structured data plus a rendered markdown report. Runs as a "
            "background job: short videos return inline; if the response has "
            "status 'running', call get_analysis_result with the returned job_id."
        ),
    },
    "get_analysis_result": {
        "function": get_analysis_result,
        "description": (
            "Fetch the result of an analyze_video job by job_id (optionally "
            "waiting up to 45s for it to finish). Returns status 'running', "
            "'done' (with the full report), or 'error'."
        ),
    },
    "list_analysis_jobs": {
        "function": list_analysis_jobs,
        "description": "List analysis jobs tracked by this server and their status.",
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
