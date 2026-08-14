"""Capture a server's complete public MCP tool/resource inventory as JSON."""

import argparse
import json
import sys
from pathlib import Path

import anyio
from mcp.client import Client


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


async def capture(project: Path) -> dict:
    sys.path.insert(0, str(project.resolve() / "src"))
    from main import create_server

    async with Client(create_server(), raise_exceptions=True) as client:
        tools = await client.list_tools()
        resources = await client.list_resources()
        return {
            "server_info": client.server_info.model_dump(mode="json", by_alias=True),
            "tools": [tool.model_dump(mode="json", by_alias=True) for tool in tools.tools],
            "resources": [
                resource.model_dump(mode="json", by_alias=True)
                for resource in resources.resources
            ],
        }


def main() -> None:
    args = parse_args()
    inventory = anyio.run(capture, args.project)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(inventory, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
