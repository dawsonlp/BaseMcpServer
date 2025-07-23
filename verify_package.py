import sys
sys.path.insert(0, './utils/mcp_manager/src')

try:
    from mcp_manager.commands import install
    print("Successfully imported mcp_manager.commands.install")
except ImportError as e:
    print(f"Failed to import mcp_manager.commands.install: {e}")
