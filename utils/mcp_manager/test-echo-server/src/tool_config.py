"""
Tool Configuration for Test Echo MCP Server

Simple test server with a single echo tool for testing removal functionality.
"""

from typing import Dict, Any


def test_echo(message: str = "🧪 TEST-ECHO-SERVER IS WORKING! 🎉") -> Dict[str, Any]:
    """Test echo tool - returns a unique test message to verify server is working.
    
    Args:
        message: Optional message to echo (default: test message)
        
    Returns:
        Dictionary containing the echo response
    """
    return {
        "status": "success",
        "message": message,
        "confirmation": "✅ Test Echo Response",
        "note": "This confirms the test-echo-server MCP server is installed and functioning correctly."
    }


# Tool configuration - single source of truth
TEST_ECHO_TOOLS: Dict[str, Dict[str, Any]] = {
    'test_echo': {
        'function': test_echo,
        'description': 'Test echo tool - returns a unique test message to verify server is working. Use this to confirm the test-echo-server is properly installed and functional.'
    }
}


def get_tools_config() -> Dict[str, Dict[str, Any]]:
    """Get the tools configuration for registration."""
    return TEST_ECHO_TOOLS
