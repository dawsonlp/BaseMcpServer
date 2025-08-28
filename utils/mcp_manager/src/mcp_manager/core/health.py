"""
Health checking framework for MCP servers.

This module provides comprehensive health checking capabilities for MCP servers,
including connectivity tests, response validation, and performance monitoring.
"""

import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable, Awaitable
from pathlib import Path
import json
import subprocess
import psutil
from pydantic import BaseModel, Field

from mcp_manager.core.models import Server, HealthStatus, HealthReport, ProcessInfo
from mcp_manager.core.logging import MCPManagerLogger


class HealthCheck(BaseModel):
    """Individual health check definition."""
    name: str
    description: str
    check_function: str  # Function name to call
    timeout: float = 5.0
    critical: bool = True
    enabled: bool = True
    metadata: Dict[str, Any] = Field(default_factory=dict)


class HealthCheckResult(BaseModel):
    """Result of a single health check."""
    check_name: str
    status: HealthStatus
    message: str
    duration_ms: float
    timestamp: datetime = Field(default_factory=datetime.now)
    details: Dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None


class HealthChecker:
    """Comprehensive health checker for MCP servers."""
    
    def __init__(self, logger: Optional[MCPManagerLogger] = None):
        self.logger = logger or MCPManagerLogger()
        self._checks: Dict[str, HealthCheck] = {}
        self._results_cache: Dict[str, List[HealthCheckResult]] = {}
        self._max_cache_size = 100
        
        # Register default health checks
        self._register_default_checks()
    
    def _register_default_checks(self) -> None:
        """Register default health checks."""
        default_checks = [
            HealthCheck(
                name="process_running",
                description="Check if server process is running",
                check_function="check_process_running",
                critical=True
            ),
            HealthCheck(
                name="port_responsive",
                description="Check if server port is responsive",
                check_function="check_port_responsive",
                critical=True
            ),
            HealthCheck(
                name="memory_usage",
                description="Check server memory usage",
                check_function="check_memory_usage",
                critical=False
            ),
            HealthCheck(
                name="cpu_usage",
                description="Check server CPU usage",
                check_function="check_cpu_usage",
                critical=False
            ),
            HealthCheck(
                name="log_errors",
                description="Check for recent errors in logs",
                check_function="check_log_errors",
                critical=False
            ),
            HealthCheck(
                name="mcp_connectivity",
                description="Test MCP protocol connectivity",
                check_function="check_mcp_connectivity",
                critical=True
            )
        ]
        
        for check in default_checks:
            self._checks[check.name] = check
    
    def register_check(self, check: HealthCheck) -> None:
        """Register a custom health check."""
        self._checks[check.name] = check
        self.logger.debug(f"Registered health check: {check.name}")
    
    def unregister_check(self, check_name: str) -> None:
        """Unregister a health check."""
        if check_name in self._checks:
            del self._checks[check_name]
            self.logger.debug(f"Unregistered health check: {check_name}")
    
    async def check_server_health(
        self,
        server: Server,
        process_info: Optional[ProcessInfo] = None,
        checks: Optional[List[str]] = None
    ) -> HealthReport:
        """
        Run comprehensive health checks on a server.
        
        Args:
            server: Server configuration
            process_info: Current process information
            checks: Specific checks to run (None = all enabled checks)
        
        Returns:
            Complete health report
        """
        start_time = time.time()
        
        # Determine which checks to run
        checks_to_run = checks or [name for name, check in self._checks.items() if check.enabled]
        
        results = []
        overall_status = HealthStatus.HEALTHY
        
        for check_name in checks_to_run:
            if check_name not in self._checks:
                self.logger.warning(f"Unknown health check: {check_name}")
                continue
            
            check = self._checks[check_name]
            result = await self._run_single_check(check, server, process_info)
            results.append(result)
            
            # Update overall status
            if result.status == HealthStatus.UNHEALTHY and check.critical:
                overall_status = HealthStatus.UNHEALTHY
            elif result.status == HealthStatus.DEGRADED and overall_status == HealthStatus.HEALTHY:
                overall_status = HealthStatus.DEGRADED
        
        # Cache results
        if server.name not in self._results_cache:
            self._results_cache[server.name] = []
        
        self._results_cache[server.name].extend(results)
        # Keep only recent results
        if len(self._results_cache[server.name]) > self._max_cache_size:
            self._results_cache[server.name] = self._results_cache[server.name][-self._max_cache_size:]
        
        duration = time.time() - start_time
        
        return HealthReport(
            server_name=server.name,
            overall_status=overall_status,
            checks=results,
            duration_ms=duration * 1000,
            process_info=process_info
        )
    
    async def _run_single_check(
        self,
        check: HealthCheck,
        server: Server,
        process_info: Optional[ProcessInfo]
    ) -> HealthCheckResult:
        """Run a single health check with timeout."""
        start_time = time.time()
        
        try:
            # Get the check function
            check_func = getattr(self, check.check_function, None)
            if not check_func:
                raise ValueError(f"Unknown check function: {check.check_function}")
            
            # Run with timeout
            result = await asyncio.wait_for(
                check_func(server, process_info, check.metadata),
                timeout=check.timeout
            )
            
            duration = (time.time() - start_time) * 1000
            
            return HealthCheckResult(
                check_name=check.name,
                status=result.get("status", HealthStatus.UNKNOWN),
                message=result.get("message", "No message"),
                duration_ms=duration,
                details=result.get("details", {}),
                error=result.get("error")
            )
            
        except asyncio.TimeoutError:
            duration = (time.time() - start_time) * 1000
            return HealthCheckResult(
                check_name=check.name,
                status=HealthStatus.UNHEALTHY,
                message=f"Check timed out after {check.timeout}s",
                duration_ms=duration,
                error="timeout"
            )
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            return HealthCheckResult(
                check_name=check.name,
                status=HealthStatus.UNHEALTHY,
                message=f"Check failed: {str(e)}",
                duration_ms=duration,
                error=str(e)
            )
    
    async def check_process_running(
        self,
        server: Server,
        process_info: Optional[ProcessInfo],
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Check if server process is running."""
        if not process_info or not process_info.pid:
            return {
                "status": HealthStatus.UNHEALTHY,
                "message": "No process information available"
            }
        
        try:
            process = psutil.Process(process_info.pid)
            if process.is_running():
                return {
                    "status": HealthStatus.HEALTHY,
                    "message": f"Process running (PID: {process_info.pid})",
                    "details": {
                        "pid": process_info.pid,
                        "status": process.status(),
                        "create_time": process.create_time()
                    }
                }
            else:
                return {
                    "status": HealthStatus.UNHEALTHY,
                    "message": f"Process not running (PID: {process_info.pid})"
                }
        except psutil.NoSuchProcess:
            return {
                "status": HealthStatus.UNHEALTHY,
                "message": f"Process not found (PID: {process_info.pid})"
            }
        except Exception as e:
            return {
                "status": HealthStatus.UNHEALTHY,
                "message": f"Error checking process: {str(e)}",
                "error": str(e)
            }
    
    async def check_port_responsive(
        self,
        server: Server,
        process_info: Optional[ProcessInfo],
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Check if server port is responsive."""
        if server.transport != "sse" or not server.port:
            return {
                "status": HealthStatus.HEALTHY,
                "message": "Not applicable for stdio transport"
            }
        
        try:
            # Simple TCP connection test
            reader, writer = await asyncio.open_connection(
                server.host or "localhost",
                server.port
            )
            writer.close()
            await writer.wait_closed()
            
            return {
                "status": HealthStatus.HEALTHY,
                "message": f"Port {server.port} is responsive",
                "details": {"port": server.port, "host": server.host or "localhost"}
            }
        except Exception as e:
            return {
                "status": HealthStatus.UNHEALTHY,
                "message": f"Port {server.port} not responsive: {str(e)}",
                "error": str(e)
            }
    
    async def check_memory_usage(
        self,
        server: Server,
        process_info: Optional[ProcessInfo],
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Check server memory usage."""
        if not process_info or not process_info.pid:
            return {
                "status": HealthStatus.UNKNOWN,
                "message": "No process information available"
            }
        
        try:
            process = psutil.Process(process_info.pid)
            memory_info = process.memory_info()
            memory_percent = process.memory_percent()
            
            # Define thresholds
            warning_threshold = metadata.get("memory_warning_mb", 500)
            critical_threshold = metadata.get("memory_critical_mb", 1000)
            
            memory_mb = memory_info.rss / 1024 / 1024
            
            if memory_mb > critical_threshold:
                status = HealthStatus.UNHEALTHY
                message = f"High memory usage: {memory_mb:.1f}MB ({memory_percent:.1f}%)"
            elif memory_mb > warning_threshold:
                status = HealthStatus.DEGRADED
                message = f"Elevated memory usage: {memory_mb:.1f}MB ({memory_percent:.1f}%)"
            else:
                status = HealthStatus.HEALTHY
                message = f"Normal memory usage: {memory_mb:.1f}MB ({memory_percent:.1f}%)"
            
            return {
                "status": status,
                "message": message,
                "details": {
                    "memory_mb": memory_mb,
                    "memory_percent": memory_percent,
                    "rss": memory_info.rss,
                    "vms": memory_info.vms
                }
            }
        except Exception as e:
            return {
                "status": HealthStatus.UNKNOWN,
                "message": f"Error checking memory: {str(e)}",
                "error": str(e)
            }
    
    async def check_cpu_usage(
        self,
        server: Server,
        process_info: Optional[ProcessInfo],
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Check server CPU usage."""
        if not process_info or not process_info.pid:
            return {
                "status": HealthStatus.UNKNOWN,
                "message": "No process information available"
            }
        
        try:
            process = psutil.Process(process_info.pid)
            
            # Get CPU usage over a short interval
            cpu_percent = process.cpu_percent(interval=1.0)
            
            # Define thresholds
            warning_threshold = metadata.get("cpu_warning_percent", 80)
            critical_threshold = metadata.get("cpu_critical_percent", 95)
            
            if cpu_percent > critical_threshold:
                status = HealthStatus.UNHEALTHY
                message = f"High CPU usage: {cpu_percent:.1f}%"
            elif cpu_percent > warning_threshold:
                status = HealthStatus.DEGRADED
                message = f"Elevated CPU usage: {cpu_percent:.1f}%"
            else:
                status = HealthStatus.HEALTHY
                message = f"Normal CPU usage: {cpu_percent:.1f}%"
            
            return {
                "status": status,
                "message": message,
                "details": {
                    "cpu_percent": cpu_percent,
                    "num_threads": process.num_threads()
                }
            }
        except Exception as e:
            return {
                "status": HealthStatus.UNKNOWN,
                "message": f"Error checking CPU: {str(e)}",
                "error": str(e)
            }
    
    async def check_log_errors(
        self,
        server: Server,
        process_info: Optional[ProcessInfo],
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Check for recent errors in server logs."""
        try:
            log_dir = Path.home() / ".mcp_manager" / "logs"
            log_file = log_dir / f"{server.name}.log"
            
            if not log_file.exists():
                return {
                    "status": HealthStatus.HEALTHY,
                    "message": "No log file found"
                }
            
            # Check last N lines for errors
            lines_to_check = metadata.get("log_lines_check", 50)
            error_patterns = metadata.get("error_patterns", ["ERROR", "CRITICAL", "Exception", "Traceback"])
            
            # Read last N lines
            with open(log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            recent_lines = lines[-lines_to_check:] if len(lines) > lines_to_check else lines
            
            # Count errors
            error_count = 0
            recent_errors = []
            
            for line in recent_lines:
                if any(pattern in line for pattern in error_patterns):
                    error_count += 1
                    if len(recent_errors) < 5:  # Keep last 5 errors
                        recent_errors.append(line.strip())
            
            if error_count > 0:
                critical_threshold = metadata.get("error_critical_count", 10)
                warning_threshold = metadata.get("error_warning_count", 3)
                
                if error_count > critical_threshold:
                    status = HealthStatus.UNHEALTHY
                elif error_count > warning_threshold:
                    status = HealthStatus.DEGRADED
                else:
                    status = HealthStatus.HEALTHY
                
                message = f"Found {error_count} errors in recent logs"
            else:
                status = HealthStatus.HEALTHY
                message = "No errors found in recent logs"
            
            return {
                "status": status,
                "message": message,
                "details": {
                    "error_count": error_count,
                    "lines_checked": len(recent_lines),
                    "recent_errors": recent_errors
                }
            }
        except Exception as e:
            return {
                "status": HealthStatus.UNKNOWN,
                "message": f"Error checking logs: {str(e)}",
                "error": str(e)
            }
    
    async def check_mcp_connectivity(
        self,
        server: Server,
        process_info: Optional[ProcessInfo],
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Test MCP protocol connectivity."""
        try:
            # This is a placeholder for actual MCP connectivity test
            # In a real implementation, this would attempt to communicate
            # with the MCP server using the protocol
            
            if server.transport == "stdio":
                # For stdio, we can't easily test connectivity without
                # interfering with the main process
                return {
                    "status": HealthStatus.HEALTHY,
                    "message": "Stdio transport - assuming healthy if process running"
                }
            
            elif server.transport == "sse":
                # For SSE, we could attempt an HTTP connection
                if not server.port:
                    return {
                        "status": HealthStatus.UNHEALTHY,
                        "message": "SSE transport configured but no port specified"
                    }
                
                # Simple connectivity test
                import aiohttp
                timeout = aiohttp.ClientTimeout(total=5.0)
                
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    url = f"http://{server.host or 'localhost'}:{server.port}/health"
                    try:
                        async with session.get(url) as response:
                            if response.status == 200:
                                return {
                                    "status": HealthStatus.HEALTHY,
                                    "message": f"MCP server responding on port {server.port}",
                                    "details": {"response_code": response.status}
                                }
                            else:
                                return {
                                    "status": HealthStatus.DEGRADED,
                                    "message": f"MCP server returned status {response.status}",
                                    "details": {"response_code": response.status}
                                }
                    except aiohttp.ClientError as e:
                        return {
                            "status": HealthStatus.UNHEALTHY,
                            "message": f"Cannot connect to MCP server: {str(e)}",
                            "error": str(e)
                        }
            
            return {
                "status": HealthStatus.UNKNOWN,
                "message": f"Unknown transport type: {server.transport}"
            }
            
        except Exception as e:
            return {
                "status": HealthStatus.UNKNOWN,
                "message": f"Error testing MCP connectivity: {str(e)}",
                "error": str(e)
            }
    
    def get_cached_results(self, server_name: str, limit: Optional[int] = None) -> List[HealthCheckResult]:
        """Get cached health check results for a server."""
        results = self._results_cache.get(server_name, [])
        if limit:
            return results[-limit:]
        return results
    
    def clear_cache(self, server_name: Optional[str] = None) -> None:
        """Clear health check results cache."""
        if server_name:
            self._results_cache.pop(server_name, None)
        else:
            self._results_cache.clear()
    
    def get_health_summary(self, server_name: str) -> Dict[str, Any]:
        """Get a summary of recent health check results."""
        results = self._results_cache.get(server_name, [])
        if not results:
            return {"status": "no_data", "message": "No health check data available"}
        
        # Analyze recent results
        recent_results = results[-10:]  # Last 10 checks
        
        status_counts = {}
        total_checks = len(recent_results)
        
        for result in recent_results:
            status = result.status.value
            status_counts[status] = status_counts.get(status, 0) + 1
        
        # Determine overall health trend
        healthy_ratio = status_counts.get("healthy", 0) / total_checks
        
        if healthy_ratio >= 0.8:
            trend = "stable"
        elif healthy_ratio >= 0.5:
            trend = "degraded"
        else:
            trend = "unstable"
        
        return {
            "server_name": server_name,
            "trend": trend,
            "healthy_ratio": healthy_ratio,
            "total_checks": total_checks,
            "status_distribution": status_counts,
            "latest_check": recent_results[-1].timestamp if recent_results else None
        }
