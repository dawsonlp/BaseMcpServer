#!/usr/bin/env python3
"""
CLI Test Program for WorldContext MCP Server

This program exercises the WorldContext context summary tool directly without going through
the MCP protocol, allowing us to test the functionality and see the output.
"""

import json
from typing import Dict, Any

# Import the context summary function directly
from src.tool_config import get_context_summary


def print_json(data: Dict[str, Any], title: str) -> None:
    """Pretty print JSON data with a title."""
    print(f"\n{'='*60}")
    print(f" {title}")
    print('='*60)
    print(json.dumps(data, indent=2, default=str))


def main():
    """Main CLI test program."""
    print("WorldContext MCP Server - CLI Test Program")
    print("Testing context summary with live data...")
    
    try:
        result = get_context_summary()
        print_json(result, "WORLDCONTEXT SUMMARY")
        
        print(f"\n{'='*60}")
        print(" Test Complete - Check output above for:")
        print(" - Current date/time information")
        print(" - Stock market data (Alpha Vantage API)")
        print(" - Live news headlines (NewsAPI)")
        print(" - International, Political, and Tennessee news")
        print('='*60)
        
    except Exception as e:
        print(f"ERROR: {e}")
        print("\nThis might indicate:")
        print("- Missing API keys in ~/.config/worldcontext/config.yaml")
        print("- Network connectivity issues")
        print("- API rate limits or quota exceeded")


if __name__ == "__main__":
    main()
