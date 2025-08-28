"""
Process management system for MCP Manager 3.0.

Handles starting, stopping, monitoring, and managing MCP server processes
with proper lifecycle management and resource cleanup.
"""

import asyncio
import os
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
from datetime import datetime, timedelta
import psutil

from mcp_manager.core.models import (
    Server, ProcessInfo, ProcessStatus, TransportType, ServerType
)
from mcp_manager.core.state import get_state_manager
from mcp_manager.core.logging import get_logger, log_server_event, log_error_with_context


logger = get_logger("process_manager")


class ProcessManager:
    """Manages MCP server processes with proper lifecycle tracking."""
    
    def __init__(self):
        self.running_processes: Dict[str, ProcessInfo] = {}
        self.state_manager = get_state_manager()
        self._cleanup_on_exit = True
        self._setup_signal_handlers()
    
    def _setup_signal_handlers(self):
        """Set up signal handlers for graceful shutdown."""
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, cleaning up processes...")
            self.cleanup_all_processes()
            sys.exit(0)
        
        try:
            signal.signal(signal.SIGINT, signal_handler)
            signal.signal(signal.SIGTERM, signal_handler)
            if hasattr(signal, 'SIGHUP'):
                signal.signal(signal.SIGHUP, signal_handler)
        except Exception as e:
            logger.warning(f"Could not set up signal handlers: {e}")
    
    def start_server(self, server_name: str, transport: Optional[str] = None, 
                    port: Optional[int] = None, background: bool = False) -> ProcessInfo:
        """Start an MCP server process."""
        logger.info(f"Starting server: {server_name}")
        
        # Get server configuration
        server = self.state_manager.get_server(server_name)
        if not server:
            raise ValueError(f"Server '{server_name}' not found")
        
        if not server.enabled:
            raise ValueError(f"Server '{server_name}' is disabled")
        
        # Check if already running
        if self.is_server_running(server_name):
            raise ValueError(f"Server '{server_name}' is already running")
        
        # Use provided transport or server default
        transport = transport or server.transport.value
        port = port or server.port
        
        # Validate transport and port combination
        if transport == TransportType.SSE.value and not port:
            raise ValueError("Port is required for SSE transport")
        
        try:
            if server.is_local():
                process_info = self._start_local_server(server, transport, port, background)
            else:
                raise ValueError("Remote server starting not implemented yet")
            
            # Track the process
            self.running_processes[server_name] = process_info
            self.state_manager.add_process(process_info)
            
            log_server_event(server_name, "started", {
                "transport": transport,
                "port": port,
                "background": background,
                "pid": process_info.pid
            })
            
            logger.info(f"Server '{server_name}' started successfully (PID: {process_info.pid})")
            return process_info
            
        except Exception as e:
            log_error_with_context(e, {
                "server_name": server_name,
                "transport": transport,
                "port": port,
                "background": background
            })
            raise
    
    def _start_local_server(self, server: Server, transport: str, 
                           port: Optional[int], background: bool) -> ProcessInfo:
        """Start a local MCP server process."""
        
        # Get paths and validate
        python_path = server.get_python_executable()
        main_script = server.get_main_script_path()
        
        if not python_path or not python_path.exists():
            raise ValueError(f"Python executable not found: {python_path}")
        
        if not main_script or not main_script.exists():
            raise ValueError(f"Main script not found: {main_script}")
        
        # Prepare command
        cmd = [str(python_path), str(main_script)]
        
        # Add transport argument
        if transport == TransportType.SSE.value:
            cmd.extend(["--transport", "sse", "--port", str(port)])
        else:
            cmd.extend(["--transport", "stdio"])
        
        # Prepare environment
        env = os.environ.copy()
        env.update(server.environment)
        
        # Set working directory
        working_dir = main_script.parent
        
        # Prepare process arguments
        process_kwargs = {
            "cwd": str(working_dir),
            "env": env,
        }
        
        if background:
            # Background process - detach from terminal
            process_kwargs.update({
                "stdout": subprocess.PIPE,
                "stderr": subprocess.PIPE,
                "stdin": subprocess.DEVNULL,
            })
            if sys.platform != "win32":
                process_kwargs["preexec_fn"] = os.setsid
        else:
            # Foreground process - inherit terminal
            process_kwargs.update({
                "stdout": None,
                "stderr": None,
                "stdin": None,
            })
        
        logger.debug(f"Starting process with command: {cmd}")
        logger.debug(f"Working directory: {working_dir}")
        
        # Start the process
        try:
            process = subprocess.Popen(cmd, **process_kwargs)
        except Exception as e:
            raise RuntimeError(f"Failed to start server process: {e}")
        
        # Give process a moment to start and check if it's still running
        time.sleep(0.5)
        
        if process.poll() is not None:
            # Process already exited
            stdout, stderr = "", ""
            if background:
                try:
                    stdout, stderr = process.communicate(timeout=1)
                    if stdout:
                        stdout = stdout.decode('utf-8', errors='ignore')
                    if stderr:
                        stderr = stderr.decode('utf-8', errors='ignore')
                except subprocess.TimeoutExpired:
                    pass
            
            error_msg = f"Server process exited immediately (exit code: {process.returncode})"
            if stderr:
                error_msg += f"\nError output: {stderr}"
            raise RuntimeError(error_msg)
        
        # Create process info
        process_info = ProcessInfo(
            pid=process.pid,
            server_name=server.name,
            transport=TransportType(transport),
            port=port,
            started_at=datetime.now(),
            command=cmd,
            working_dir=working_dir,
            environment=server.environment
        )
        
        return process_info
    
    def stop_server(self, server_name: str, force: bool = False, 
                   timeout: int = 10) -> bool:
        """Stop a running MCP server process."""
        logger.info(f"Stopping server: {server_name} (force: {force})")
        
        process_info = self.running_processes.get(server_name)
        if not process_info:
            # Check if process exists in state manager
            process_info = self.state_manager.get_process(server_name)
            if not process_info:
                logger.warning(f"Server '{server_name}' is not running")
                return False
        
        try:
            success = self._stop_process(process_info, force, timeout)
            
            if success:
                # Remove from tracking
                if server_name in self.running_processes:
                    del self.running_processes[server_name]
                self.state_manager.remove_process(server_name)
                
                log_server_event(server_name, "stopped", {
                    "force": force,
                    "pid": process_info.pid
                })
                logger.info(f"Server '{server_name}' stopped successfully")
            else:
                logger.error(f"Failed to stop server '{server_name}'")
            
            return success
            
        except Exception as e:
            log_error_with_context(e, {
                "server_name": server_name,
                "force": force,
                "timeout": timeout,
                "pid": process_info.pid
            })
            return False
    
    def _stop_process(self, process_info: ProcessInfo, force: bool, timeout: int) -> bool:
        """Stop a specific process with optional force and timeout."""
        try:
            if not process_info.is_running():
                logger.debug(f"Process {process_info.pid} is already stopped")
                return True
            
            psutil_process = psutil.Process(process_info.pid)
            
            if force:
                # Force kill immediately
                logger.debug(f"Force killing process {process_info.pid}")
                if sys.platform == "win32":
                    psutil_process.kill()
                else:
                    psutil_process.send_signal(signal.SIGKILL)
            else:
                # Graceful shutdown with timeout
                logger.debug(f"Sending SIGTERM to process {process_info.pid}")
                
                if sys.platform == "win32":
                    psutil_process.terminate()
                else:
                    psutil_process.send_signal(signal.SIGTERM)
                
                # Wait for process to exit
                try:
                    psutil_process.wait(timeout=timeout)
                except psutil.TimeoutExpired:
                    logger.warning(f"Process {process_info.pid} didn't exit gracefully, force killing")
                    psutil_process.kill()
                    try:
                        psutil_process.wait(timeout=5)
                    except psutil.TimeoutExpired:
                        logger.error(f"Could not kill process {process_info.pid}")
                        return False
            
            return not process_info.is_running()
            
        except psutil.NoSuchProcess:
            logger.debug(f"Process {process_info.pid} no longer exists")
            return True
        except Exception as e:
            logger.error(f"Error stopping process {process_info.pid}: {e}")
            return False
    
    def restart_server(self, server_name: str, transport: Optional[str] = None,
                      port: Optional[int] = None, background: bool = False) -> ProcessInfo:
        """Restart an MCP server process."""
        logger.info(f"Restarting server: {server_name}")
        
        # Stop the server first
        if self.is_server_running(server_name):
            success = self.stop_server(server_name)
            if not success:
                raise RuntimeError(f"Failed to stop server '{server_name}' before restart")
        
        # Wait a moment for cleanup
        time.sleep(1)
        
        # Start the server again
        return self.start_server(server_name, transport, port, background)
    
    def is_server_running(self, server_name: str) -> bool:
        """Check if a server is currently running."""
        process_info = self.running_processes.get(server_name)
        if not process_info:
            # Check persistent state
            process_info = self.state_manager.get_process(server_name)
            if not process_info:
                return False
        
        is_running = process_info.is_running()
        
        # Clean up if process is no longer running
        if not is_running and server_name in self.running_processes:
            del self.running_processes[server_name]
            self.state_manager.remove_process(server_name)
        
        return is_running
    
    def get_server_status(self, server_name: str) -> ProcessStatus:
        """Get the status of a server process."""
        if not self.is_server_running(server_name):
            return ProcessStatus.STOPPED
        
        process_info = (self.running_processes.get(server_name) or 
                       self.state_manager.get_process(server_name))
        
        if not process_info:
            return ProcessStatus.UNKNOWN
        
        try:
            psutil_process = psutil.Process(process_info.pid)
            status = psutil_process.status()
            
            if status == psutil.STATUS_RUNNING:
                return ProcessStatus.RUNNING
            elif status in [psutil.STATUS_ZOMBIE, psutil.STATUS_DEAD]:
                return ProcessStatus.CRASHED
            else:
                return ProcessStatus.UNKNOWN
                
        except psutil.NoSuchProcess:
            return ProcessStatus.STOPPED
        except Exception:
            return ProcessStatus.UNKNOWN
    
    def get_process_info(self, server_name: str) -> Optional[ProcessInfo]:
        """Get detailed process information for a server."""
        return (self.running_processes.get(server_name) or 
                self.state_manager.get_process(server_name))
    
    def get_all_running_servers(self) -> Dict[str, ProcessInfo]:
        """Get information about all running servers."""
        # Refresh from state manager and validate
        all_processes = self.state_manager.get_processes()
        running = {}
        
        for name, process_info in all_processes.items():
            if process_info.is_running():
                running[name] = process_info
                # Cache in memory for faster access
                self.running_processes[name] = process_info
            else:
                # Clean up stale entries
                if name in self.running_processes:
                    del self.running_processes[name]
                self.state_manager.remove_process(name)
        
        return running
    
    def cleanup_stale_processes(self) -> List[str]:
        """Clean up stale process entries and return list of cleaned up servers."""
        logger.debug("Cleaning up stale process entries")
        
        cleaned = []
        for name in list(self.running_processes.keys()):
            if not self.is_server_running(name):
                cleaned.append(name)
        
        # Also clean up state manager
        state_cleaned = self.state_manager.cleanup_stale_processes()
        cleaned.extend([name for name in state_cleaned if name not in cleaned])
        
        if cleaned:
            logger.info(f"Cleaned up {len(cleaned)} stale process entries: {', '.join(cleaned)}")
        
        return cleaned
    
    def cleanup_all_processes(self, timeout: int = 10):
        """Stop all running processes (used during shutdown)."""
        if not self._cleanup_on_exit:
            return
        
        logger.info("Stopping all running MCP server processes...")
        
        running_servers = list(self.running_processes.keys())
        if not running_servers:
            return
        
        # Stop all processes
        for server_name in running_servers:
            try:
                self.stop_server(server_name, force=False, timeout=timeout)
            except Exception as e:
                logger.error(f"Error stopping server '{server_name}': {e}")
        
        # Force kill any remaining processes
        remaining = [name for name in running_servers if self.is_server_running(name)]
        if remaining:
            logger.warning(f"Force killing remaining processes: {', '.join(remaining)}")
            for server_name in remaining:
                try:
                    self.stop_server(server_name, force=True, timeout=5)
                except Exception as e:
                    logger.error(f"Error force killing server '{server_name}': {e}")
    
    def get_server_logs(self, server_name: str, lines: int = 100) -> List[str]:
        """Get recent log lines for a server."""
        # This is a placeholder - actual implementation would read from log files
        # or capture process output depending on how the server was started
        try:
            from mcp_manager.core.state import get_logs_dir
            log_file = get_logs_dir() / f"server-{server_name}.log"
            
            if not log_file.exists():
                return []
            
            # Read last N lines from file
            with open(log_file, 'r') as f:
                all_lines = f.readlines()
                return [line.strip() for line in all_lines[-lines:]]
        
        except Exception as e:
            logger.error(f"Error reading logs for server '{server_name}': {e}")
            return []
    
    def set_cleanup_on_exit(self, enabled: bool):
        """Enable or disable automatic cleanup on exit."""
        self._cleanup_on_exit = enabled


# Global process manager instance
_process_manager: Optional[ProcessManager] = None


def get_process_manager() -> ProcessManager:
    """Get the global process manager instance."""
    global _process_manager
    if _process_manager is None:
        _process_manager = ProcessManager()
    return _process_manager


# Convenience functions
def start_server(server_name: str, transport: Optional[str] = None, 
                port: Optional[int] = None, background: bool = False) -> ProcessInfo:
    """Start a server (convenience function)."""
    return get_process_manager().start_server(server_name, transport, port, background)


def stop_server(server_name: str, force: bool = False, timeout: int = 10) -> bool:
    """Stop a server (convenience function)."""
    return get_process_manager().stop_server(server_name, force, timeout)


def restart_server(server_name: str, transport: Optional[str] = None,
                  port: Optional[int] = None, background: bool = False) -> ProcessInfo:
    """Restart a server (convenience function)."""
    return get_process_manager().restart_server(server_name, transport, port, background)


def is_server_running(server_name: str) -> bool:
    """Check if server is running (convenience function)."""
    return get_process_manager().is_server_running(server_name)


def get_server_status(server_name: str) -> ProcessStatus:
    """Get server status (convenience function)."""
    return get_process_manager().get_server_status(server_name)


def cleanup_stale_processes() -> List[str]:
    """Clean up stale processes (convenience function)."""
    return get_process_manager().cleanup_stale_processes()
