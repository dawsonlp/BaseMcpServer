#!/usr/bin/env bash
#
# Install a BaseMcpServer MCP server via mcp-manager, from anywhere.
#
# Usage:
#   install_mcp_server.sh <server-name> [--source DIR] [--transport stdio|sse]
#                         [--force] [--no-sync]
#
# Behaviour:
#   1. Ensures `uv` and `mcp-manager` are available (installs mcp-manager if not).
#   2. Locates the server source: --source, else ./servers/<name> if run inside
#      the repo, else a shallow clone of the public BaseMcpServer repo in a cache.
#   3. Runs `mcp-manager install local <name> --source <dir>`.
#   4. Unless --no-sync, runs `mcp-manager config sync` to wire it into Cline /
#      Claude Desktop.
#
# Idempotent: pass --force to reinstall an already-installed server.
set -euo pipefail

REPO_URL="https://github.com/dawsonlp/BaseMcpServer.git"
CACHE_DIR="${XDG_CACHE_HOME:-$HOME/.cache}/basemcpserver"

SERVER=""
SOURCE=""
TRANSPORT="stdio"
FORCE=""
SYNC="yes"

die() { echo "error: $*" >&2; exit 1; }
info() { echo ">> $*" >&2; }

# --- args ------------------------------------------------------------------
while [ $# -gt 0 ]; do
  case "$1" in
    --source) SOURCE="${2:-}"; shift 2 ;;
    --transport) TRANSPORT="${2:-}"; shift 2 ;;
    --force) FORCE="--force"; shift ;;
    --no-sync) SYNC="no"; shift ;;
    -h|--help) grep '^#' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    -*) die "unknown option: $1" ;;
    *) [ -z "$SERVER" ] && SERVER="$1" || die "unexpected arg: $1"; shift ;;
  esac
done
[ -n "$SERVER" ] || die "server name is required (e.g. loadbearing-youtube)"

# --- prerequisites ---------------------------------------------------------
command -v uv >/dev/null 2>&1 || die \
  "uv not found. Install it: curl -LsSf https://astral.sh/uv/install.sh | sh"

if ! command -v mcp-manager >/dev/null 2>&1; then
  info "mcp-manager not found; installing it as a uv tool..."
  uv tool install "git+${REPO_URL}#subdirectory=utils/mcp_manager"
  uv tool update-shell || true
  command -v mcp-manager >/dev/null 2>&1 || die \
    "mcp-manager still not on PATH. Open a new shell (uv tool update-shell) and retry."
fi

# --- locate the server source ----------------------------------------------
if [ -z "$SOURCE" ]; then
  if [ -f "./servers/$SERVER/pyproject.toml" ]; then
    SOURCE="./servers/$SERVER"
  else
    info "Not inside the repo; using a shallow clone at $CACHE_DIR"
    if [ -d "$CACHE_DIR/.git" ]; then
      git -C "$CACHE_DIR" pull --ff-only --quiet || info "clone pull skipped"
    else
      mkdir -p "$(dirname "$CACHE_DIR")"
      git clone --depth 1 "$REPO_URL" "$CACHE_DIR"
    fi
    SOURCE="$CACHE_DIR/servers/$SERVER"
  fi
fi
[ -f "$SOURCE/pyproject.toml" ] || die "no server source at: $SOURCE"

# --- install ---------------------------------------------------------------
info "Installing '$SERVER' from $SOURCE (transport: $TRANSPORT)"
mcp-manager install local "$SERVER" --source "$SOURCE" --transport "$TRANSPORT" $FORCE

# --- wire into editors -----------------------------------------------------
if [ "$SYNC" = "yes" ]; then
  info "Syncing into detected AI platforms (Cline / Claude Desktop)..."
  mcp-manager config sync
else
  info "Skipping editor sync (--no-sync). Run 'mcp-manager config sync' when ready."
fi

CONFIG="$HOME/.config/mcp-manager/servers/$SERVER/config.yaml"
info "Done. Server '$SERVER' registered."
[ -f "$CONFIG" ] && info "Config (edit for credentials if the server needs them): $CONFIG"
info "Inspect with: mcp-manager info show $SERVER"
