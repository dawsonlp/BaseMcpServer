# MCP Manager 2.0 - Architectural Planning Document

## Executive Summary

This document outlines a comprehensive redesign of mcp-manager to address current limitations and create a production-ready tool suitable for PyPI distribution. The new architecture emphasizes modularity, cross-platform compatibility, and enterprise-grade features.

## Current Architecture Limitations

### Critical Issues
- **Platform Lock-in**: Hardcoded VS Code/Cline integration
- **Bash Dependencies**: Non-portable shell script execution
- **Local-Only Design**: No support for remote/containerized deployments
- **Manual Configuration**: Opaque .env/.yaml setup process
- **Limited Observability**: Poor logging and debugging capabilities
- **No Health Monitoring**: No validation or diagnostics

## Proposed Architecture: MCP Manager 2.0

### Core Design Principles

1. **Plugin Architecture**: Extensible platform support
2. **Python-Native**: No external shell dependencies
3. **Configuration-Driven**: Declarative server definitions
4. **Cloud-Ready**: Support for local, remote, and containerized deployments
5. **Observable**: Comprehensive logging and monitoring
6. **Secure**: Built-in secrets management and sandboxing

## Detailed Architecture

### 1. Multi-Platform AI Support System

```
mcp_manager/
├── platforms/
│   ├── __init__.py
│   ├── base.py              # Abstract platform interface
│   ├── vscode_cline.py      # VS Code Cline integration
│   ├── claude_desktop.py    # Claude Desktop integration
│   ├── cursor.py            # Cursor editor integration
│   └── registry.py          # Platform discovery and registration
```

**Key Components:**

**Platform Interface (base.py)**
```python
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Any, List
from ..models import Server

class PlatformAdapter(ABC):
    """Abstract base class for AI platform integrations."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Platform name (e.g., 'vscode-cline', 'claude-desktop')."""
        pass
    
    @property
    @abstractmethod
    def display_name(self) -> str:
        """Human-readable platform name."""
        pass
    
    @abstractmethod
    def is_installed(self) -> bool:
        """Check if the platform is installed on the system."""
        pass
    
    @abstractmethod
    def get_config_path(self) -> Path:
        """Get the path to the platform's configuration file."""
        pass
    
    @abstractmethod
    def generate_config(self, servers: List[Server]) -> Dict[str, Any]:
        """Generate platform-specific configuration from servers."""
        pass
    
    @abstractmethod
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate platform configuration format."""
        pass
    
    @abstractmethod
    def backup_config(self) -> Path:
        """Create a backup of the current configuration."""
        pass
    
    @abstractmethod
    def apply_config(self, config: Dict[str, Any]) -> bool:
        """Apply configuration to the platform."""
        pass
```

**Claude Desktop Adapter**
```python
class ClaudeDesktopAdapter(PlatformAdapter):
    """Adapter for Claude Desktop application."""
    
    @property
    def name(self) -> str:
        return "claude-desktop"
    
    @property
    def display_name(self) -> str:
        return "Claude Desktop"
    
    def get_config_path(self) -> Path:
        """Claude Desktop config location varies by platform."""
        import sys
        if sys.platform == "darwin":  # macOS
            return Path.home() / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json"
        elif sys.platform == "win32":  # Windows
            return Path.home() / "AppData" / "Roaming" / "Claude" / "claude_desktop_config.json"
        else:  # Linux
            return Path.home() / ".config" / "Claude" / "claude_desktop_config.json"
    
    def generate_config(self, servers: List[Server]) -> Dict[str, Any]:
        """Generate Claude Desktop configuration format."""
        config = {"mcpServers": {}}
        
        for server in servers:
            if server.enabled:
                if server.execution_mode == "local":
                    config["mcpServers"][server.name] = {
                        "command": "python",
                        "args": [str(server.get_main_script_path())],
                        "env": server.get_environment_variables()
                    }
                elif server.execution_mode == "remote":
                    config["mcpServers"][server.name] = {
                        "url": server.remote_config.url,
                        "apiKey": server.remote_config.api_key
                    }
        
        return config
```

### 2. Python-Native Execution Model

```
mcp_manager/
├── execution/
│   ├── __init__.py
│   ├── manager.py           # Process management
│   ├── local.py             # Local execution
│   ├── docker.py            # Docker container execution
│   ├── remote.py            # Remote server execution
│   └── monitoring.py        # Process monitoring and health checks
```

**Execution Manager**
```python
from enum import Enum
from typing import Dict, Optional, List
import asyncio
import subprocess
from pathlib import Path

class ExecutionMode(str, Enum):
    LOCAL = "local"
    DOCKER = "docker"
    REMOTE = "remote"
    DEVELOPMENT = "development"

class ServerStatus(str, Enum):
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    ERROR = "error"
    UNKNOWN = "unknown"

class ServerProcess:
    """Represents a running MCP server process."""
    
    def __init__(self, server_id: str, process: subprocess.Popen, mode: ExecutionMode):
        self.server_id = server_id
        self.process = process
        self.mode = mode
        self.start_time = datetime.now()
        self.status = ServerStatus.STARTING
    
    def is_alive(self) -> bool:
        return self.process.poll() is None
    
    def get_pid(self) -> Optional[int]:
        return self.process.pid if self.is_alive() else None
    
    def terminate(self) -> bool:
        if self.is_alive():
            self.process.terminate()
            return True
        return False
    
    def kill(self) -> bool:
        if self.is_alive():
            self.process.kill()
            return True
        return False

class ExecutionManager:
    """Manages execution of MCP servers across different modes."""
    
    def __init__(self):
        self.running_servers: Dict[str, ServerProcess] = {}
        self.executors = {
            ExecutionMode.LOCAL: LocalExecutor(),
            ExecutionMode.DOCKER: DockerExecutor(),
            ExecutionMode.REMOTE: RemoteExecutor(),
            ExecutionMode.DEVELOPMENT: DevelopmentExecutor()
        }
    
    async def start_server(self, server: Server, mode: ExecutionMode) -> ServerProcess:
        """Start a server in the specified execution mode."""
        if server.name in self.running_servers:
            raise ValueError(f"Server {server.name} is already running")
        
        executor = self.executors[mode]
        process = await executor.start(server)
        
        self.running_servers[server.name] = process
        return process
    
    async def stop_server(self, server_id: str) -> bool:
        """Stop a running server."""
        if server_id not in self.running_servers:
            return False
        
        process = self.running_servers[server_id]
        success = process.terminate()
        
        if success:
            del self.running_servers[server_id]
        
        return success
    
    async def restart_server(self, server_id: str) -> bool:
        """Restart a running server."""
        if server_id not in self.running_servers:
            return False
        
        # Get server config and stop current process
        process = self.running_servers[server_id]
        server = await self.get_server_config(server_id)
        
        await self.stop_server(server_id)
        new_process = await self.start_server(server, process.mode)
        
        return new_process is not None
    
    def get_status(self, server_id: str) -> ServerStatus:
        """Get the status of a server."""
        if server_id not in self.running_servers:
            return ServerStatus.STOPPED
        
        process = self.running_servers[server_id]
        if process.is_alive():
            return ServerStatus.RUNNING
        else:
            return ServerStatus.ERROR
    
    async def get_logs(self, server_id: str, lines: int = 100) -> List[str]:
        """Get recent logs for a server."""
        if server_id not in self.running_servers:
            return []
        
        # Implementation depends on logging strategy
        log_file = self.get_log_file_path(server_id)
        if log_file.exists():
            return self.tail_file(log_file, lines)
        
        return []
```

**Local Executor**
```python
class LocalExecutor:
    """Executes MCP servers as local Python processes."""
    
    async def start(self, server: Server) -> ServerProcess:
        """Start a server locally using Python subprocess."""
        # Prepare environment
        env = os.environ.copy()
        env.update(server.get_environment_variables())
        
        # Add secrets to environment
        secrets = await self.secrets_manager.get_secrets(server.name)
        env.update(secrets)
        
        # Prepare command
        python_path = server.get_python_executable()
        main_script = server.get_main_script_path()
        args = [str(python_path), str(main_script), "stdio"]
        
        # Start process
        process = subprocess.Popen(
            args,
            cwd=server.source_dir,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            stdin=subprocess.PIPE
        )
        
        return ServerProcess(server.name, process, ExecutionMode.LOCAL)
```

### 3. Enhanced Configuration System

```
mcp_manager/
├── config/
│   ├── __init__.py
│   ├── schema.py            # Configuration schemas
│   ├── loader.py            # Configuration loading and validation
│   ├── secrets.py           # Secrets management
│   ├── templates.py         # Server templates
│   └── migration.py         # Configuration migration tools
```

**Server Configuration Schema**
```yaml
# ~/.mcp_servers/servers/jira-helper.yaml
name: jira-helper
version: "1.0.0"
description: "Jira integration MCP server"
author: "Your Name <your.email@example.com>"
license: "MIT"
homepage: "https://github.com/user/jira-helper"

# Execution configuration
execution:
  mode: local  # local, docker, remote, development
  python_version: "3.11+"
  
  # Local execution
  local:
    source_dir: "./code"
    main_script: "main.py"
    requirements: "./requirements.txt"
    environment:
      PYTHONPATH: "${source_dir}"
      LOG_LEVEL: "INFO"
    
  # Docker execution
  docker:
    image: "python:3.11-slim"
    dockerfile: "./Dockerfile"
    build_context: "."
    ports:
      - "7501:7501"
    volumes:
      - "${config_dir}:/app/config:ro"
      - "${logs_dir}:/app/logs"
    environment:
      - "MCP_SERVER_MODE=docker"
    
  # Remote execution
  remote:
    host: "mcp-server.example.com"
    port: 7501
    protocol: "https"
    auth_method: "api_key"
    health_check_path: "/health"

# Secrets configuration
secrets:
  - name: "JIRA_API_TOKEN"
    description: "Jira API token for authentication"
    required: true
    type: "password"
    validation:
      min_length: 10
      pattern: "^[A-Za-z0-9+/=]+$"
  - name: "JIRA_BASE_URL"
    description: "Base URL for Jira instance"
    required: true
    type: "url"
    validation:
      schemes: ["https"]
      example: "https://company.atlassian.net"
  - name: "JIRA_USER_EMAIL"
    description: "Email address for Jira authentication"
    required: false
    type: "email"

# Platform integration
platforms:
  vscode_cline:
    enabled: true
    auto_approve: []
    disabled: false
  claude_desktop:
    enabled: true
    disabled: false
  cursor:
    enabled: false
    disabled: true

# Monitoring and logging
monitoring:
  health_check:
    enabled: true
    interval: 30  # seconds
    timeout: 10   # seconds
    endpoint: "/health"
    retries: 3
  
  logging:
    level: "INFO"
    format: "json"  # json, text
    file: "${server_dir}/logs/server.log"
    max_size: "10MB"
    backup_count: 5
    console: true
  
  metrics:
    enabled: true
    port: 9090
    path: "/metrics"
    
# Development settings
development:
  hot_reload: true
  debug_mode: true
  test_mode: false
  mock_external_apis: false

# Dependencies and requirements
dependencies:
  python_packages:
    - "fastapi>=0.104.0"
    - "uvicorn>=0.24.0"
    - "pydantic>=2.5.0"
  
  system_packages:
    - "git"
  
  optional_packages:
    - "redis"  # for caching

# Metadata
metadata:
  tags:
    - "jira"
    - "project-management"
    - "atlassian"
  category: "productivity"
  maturity: "stable"  # alpha, beta, stable
  support_url: "https://github.com/user/jira-helper/issues"
  documentation_url: "https://github.com/user/jira-helper/wiki"
```

### 4. Secrets Management System

```python
from abc import ABC, abstractmethod
from typing import Dict, Optional, Any
import keyring
import getpass
from pathlib import Path

class SecretsBackend(ABC):
    """Abstract base class for secrets storage backends."""
    
    @abstractmethod
    def store_secret(self, service: str, key: str, value: str) -> bool:
        pass
    
    @abstractmethod
    def get_secret(self, service: str, key: str) -> Optional[str]:
        pass
    
    @abstractmethod
    def delete_secret(self, service: str, key: str) -> bool:
        pass
    
    @abstractmethod
    def list_secrets(self, service: str) -> List[str]:
        pass

class KeyringBackend(SecretsBackend):
    """System keyring backend using the keyring library."""
    
    def store_secret(self, service: str, key: str, value: str) -> bool:
        try:
            keyring.set_password(service, key, value)
            return True
        except Exception:
            return False
    
    def get_secret(self, service: str, key: str) -> Optional[str]:
        try:
            return keyring.get_password(service, key)
        except Exception:
            return None

class SecretsManager:
    """Manages secrets for MCP servers with multiple backend support."""
    
    def __init__(self, backend: Optional[SecretsBackend] = None):
        self.backend = backend or KeyringBackend()
        self.service_prefix = "mcp-manager"
    
    def _get_service_name(self, server_name: str) -> str:
        return f"{self.service_prefix}.{server_name}"
    
    async def prompt_for_secrets(self, server_config: ServerConfig) -> Dict[str, str]:
        """Interactively prompt user for required secrets."""
        secrets = {}
        
        for secret_def in server_config.secrets:
            if secret_def.required or self._should_prompt_optional(secret_def):
                value = await self._prompt_for_secret(secret_def)
                if value:
                    secrets[secret_def.name] = value
        
        return secrets
    
    async def _prompt_for_secret(self, secret_def: SecretDefinition) -> Optional[str]:
        """Prompt user for a single secret with validation."""
        while True:
            prompt = f"{secret_def.description}"
            if secret_def.example:
                prompt += f" (e.g., {secret_def.example})"
            prompt += ": "
            
            if secret_def.type == "password":
                value = getpass.getpass(prompt)
            else:
                value = input(prompt).strip()
            
            if not value and secret_def.required:
                print("This field is required. Please enter a value.")
                continue
            
            if value and not self._validate_secret(value, secret_def):
                print(f"Invalid value. {secret_def.validation_message}")
                continue
            
            return value
    
    def store_secrets(self, server_name: str, secrets: Dict[str, str]) -> None:
        """Store secrets for a server."""
        service_name = self._get_service_name(server_name)
        
        for key, value in secrets.items():
            success = self.backend.store_secret(service_name, key, value)
            if not success:
                raise RuntimeError(f"Failed to store secret {key} for server {server_name}")
    
    def get_secrets(self, server_name: str) -> Dict[str, str]:
        """Retrieve all secrets for a server."""
        service_name = self._get_service_name(server_name)
        secrets = {}
        
        # Get list of secret keys from server config
        server_config = self._load_server_config(server_name)
        
        for secret_def in server_config.secrets:
            value = self.backend.get_secret(service_name, secret_def.name)
            if value:
                secrets[secret_def.name] = value
        
        return secrets
    
    def update_secret(self, server_name: str, key: str, value: str) -> None:
        """Update a specific secret for a server."""
        service_name = self._get_service_name(server_name)
        success = self.backend.store_secret(service_name, key, value)
        
        if not success:
            raise RuntimeError(f"Failed to update secret {key} for server {server_name}")
    
    def delete_secrets(self, server_name: str) -> None:
        """Delete all secrets for a server."""
        service_name = self._get_service_name(server_name)
        
        # Get list of secret keys and delete each one
        server_config = self._load_server_config(server_name)
        
        for secret_def in server_config.secrets:
            self.backend.delete_secret(service_name, secret_def.name)
```

### 5. Docker & Remote Deployment Support

**Docker Integration**
```python
import docker
from typing import Dict, List, Optional

class DockerExecutor:
    """Executes MCP servers in Docker containers."""
    
    def __init__(self):
        self.client = docker.from_env()
    
    async def build_image(self, server: Server) -> str:
        """Build Docker image for the server."""
        build_context = server.docker_config.build_context
        dockerfile = server.docker_config.dockerfile
        
        # Build image
        image, logs = self.client.images.build(
            path=str(build_context),
            dockerfile=str(dockerfile),
            tag=f"mcp-{server.name}:latest",
            rm=True
        )
        
        return image.id
    
    async def run_container(self, server: Server, config: DockerConfig) -> ContainerProcess:
        """Run server in a Docker container."""
        # Prepare environment variables
        env_vars = server.get_environment_variables()
        secrets = await self.secrets_manager.get_secrets(server.name)
        env_vars.update(secrets)
        
        # Prepare port mappings
        port_mappings = {}
        for port_mapping in config.ports:
            host_port, container_port = port_mapping.split(":")
            port_mappings[container_port] = host_port
        
        # Prepare volume mounts
        volumes = {}
        for volume in config.volumes:
            host_path, container_path = volume.split(":")
            volumes[host_path] = {"bind": container_path, "mode": "rw"}
        
        # Run container
        container = self.client.containers.run(
            image=f"mcp-{server.name}:latest",
            environment=env_vars,
            ports=port_mappings,
            volumes=volumes,
            detach=True,
            name=f"mcp-{server.name}",
            restart_policy={"Name": "unless-stopped"}
        )
        
        return ContainerProcess(server.name, container, ExecutionMode.DOCKER)
    
    def get_container_logs(self, container_id: str, lines: int = 100) -> List[str]:
        """Get logs from a Docker container."""
        try:
            container = self.client.containers.get(container_id)
            logs = container.logs(tail=lines, timestamps=True)
            return logs.decode('utf-8').split('\n')
        except docker.errors.NotFound:
            return []
    
    def health_check(self, container_id: str) -> HealthStatus:
        """Check health of a Docker container."""
        try:
            container = self.client.containers.get(container_id)
            
            if container.status == "running":
                # Check if container has health check
                health = container.attrs.get("State", {}).get("Health", {})
                if health:
                    status = health.get("Status", "unknown")
                    return HealthStatus.from_docker_status(status)
                else:
                    return HealthStatus.HEALTHY
            else:
                return HealthStatus.UNHEALTHY
                
        except docker.errors.NotFound:
            return HealthStatus.NOT_FOUND
```

**Remote Server Management**
```python
import httpx
import asyncio
from typing import Dict, Any

class RemoteExecutor:
    """Manages remote MCP servers via HTTP API."""
    
    def __init__(self):
        self.client = httpx.AsyncClient()
    
    async def deploy_server(self, server: Server, remote_config: RemoteConfig) -> DeploymentResult:
        """Deploy server to remote host."""
        deployment_data = {
            "name": server.name,
            "source": server.get_source_archive(),
            "config": server.to_dict(),
            "secrets": await self.secrets_manager.get_secrets(server.name)
        }
        
        response = await self.client.post(
            f"{remote_config.base_url}/api/v1/servers",
            json=deployment_data,
            headers={"Authorization": f"Bearer {remote_config.api_key}"}
        )
        
        if response.status_code == 201:
            return DeploymentResult.success(response.json())
        else:
            return DeploymentResult.error(response.text)
    
    async def start_remote_server(self, server_id: str, remote_config: RemoteConfig) -> bool:
        """Start a server on remote host."""
        response = await self.client.post(
            f"{remote_config.base_url}/api/v1/servers/{server_id}/start",
            headers={"Authorization": f"Bearer {remote_config.api_key}"}
        )
        
        return response.status_code == 200
    
    async def get_remote_status(self, server_id: str, remote_config: RemoteConfig) -> RemoteStatus:
        """Get status of remote server."""
        response = await self.client.get(
            f"{remote_config.base_url}/api/v1/servers/{server_id}/status",
            headers={"Authorization": f"Bearer {remote_config.api_key}"}
        )
        
        if response.status_code == 200:
            data = response.json()
            return RemoteStatus.from_dict(data)
        else:
            return RemoteStatus.unknown()
    
    async def sync_configuration(self, server_id: str, remote_config: RemoteConfig) -> bool:
        """Sync local configuration with remote server."""
        local_config = self._load_local_config(server_id)
        
        response = await self.client.put(
            f"{remote_config.base_url}/api/v1/servers/{server_id}/config",
            json=local_config.to_dict(),
            headers={"Authorization": f"Bearer {remote_config.api_key}"}
        )
        
        return response.status_code == 200
```

### 6. Comprehensive Logging & Monitoring

```
mcp_manager/
├── monitoring/
│   ├── __init__.py
│   ├── logger.py            # Centralized logging
│   ├── metrics.py           # Performance metrics
│   ├── health.py            # Health checking
│   └── alerts.py            # Alert system
```

**Logging Architecture**
```python
import logging
import json
from typing import Dict, Any, Optional
from pathlib import Path
import structlog

class StructuredLogger:
    """Structured logging with correlation IDs and context."""
    
    def __init__(self, server_name: str, log_dir: Path):
        self.server_name = server_name
        self.log_dir = log_dir
        self.log_file = log_dir / f"{server_name}.log"
        
        # Configure structlog
        structlog.configure(
            processors=[
                structlog.stdlib.filter_by_level,
                structlog.stdlib.add_logger_name,
                structlog.stdlib.add_log_level,
                structlog.stdlib.PositionalArgumentsFormatter(),
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.StackInfoRenderer(),
                structlog.processors.format_exc_info,
                structlog.processors.UnicodeDecoder(),
                structlog.processors.JSONRenderer()
            ],
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
            wrapper_class=structlog.stdlib.BoundLogger,
            cache_logger_on_first_use=True,
        )
        
        # Set up file handler
        self._setup_file_handler()
    
    def _setup_file_handler(self):
        """Set up rotating file handler."""
        from logging.handlers import RotatingFileHandler
        
        handler = RotatingFileHandler(
            self.log_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        
        logger = logging.getLogger(self.server_name)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    
    def get_logger(self, context: Optional[Dict[str, Any]] = None) -> structlog.BoundLogger:
        """Get a logger with optional context."""
        logger = structlog.get_logger(self.server_name)
        
        if context:
            logger = logger.bind(**context)
        
        return logger

class LogAggregator:
    """Aggregates logs from multiple servers."""
    
    def __init__(self, log_dir: Path):
        self.log_dir = log_dir
        self.servers: Dict[str, StructuredLogger] = {}
    
    def add_server(self, server_name: str) -> StructuredLogger:
        """Add a server to log aggregation."""
        if server_name not in self.servers:
            self.servers[server_name] = StructuredLogger(server_name, self.log_dir)
        
        return self.servers[server_name]
    
    def get_recent_logs(self, server_name: str, lines: int = 100) -> List[Dict[str, Any]]:
        """Get recent logs for a server."""
        if server_name not in self.servers:
            return []
        
        log_file = self.servers[server_name].log_file
        if not log_file.exists():
            return []
        
        logs = []
        with open(log_file, 'r') as f:
            for line in f.readlines()[-lines:]:
                try:
                    logs.append(json.loads(line.strip()))
                except json.JSONDecodeError:
                    # Handle non-JSON log lines
                    logs.append({"message": line.strip(), "level": "info"})
        
        return logs
    
    def search_logs(self, query: str, server_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """Search logs across servers."""
        results = []
        
        servers_to_search = [server_name] if server_name else self.servers.keys()
        
        for srv_name in servers_to_search:
            logs = self.get_recent_logs(srv_name, 1000)  # Search last 1000 lines
            
            for log_entry in logs:
                if query.lower() in str(log_entry).lower():
                    log_entry["server"] = srv_name
                    results.append(log_entry)
        
        return results
```

**Health Monitoring**
```python
import asyncio
import httpx
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from enum import Enum

class HealthStatus(str, Enum):
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    DEGRADED = "degraded"
    UNKNOWN = "unknown"
    NOT_FOUND = "not_found"

class HealthReport:
    """Health report for a server."""
    
    def __init__(self, server_id: str, status: HealthStatus, 
                 response_time: Optional[float] = None,
                 error_message: Optional[str] = None,
                 details: Optional[Dict[str, Any]] = None):
        self.server_id = server_id
        self.status = status
        self.response_time = response_time
        self.error_message = error_message
        self.details = details or {}
        self.timestamp = datetime.now()

class HealthMonitor:
    """Monitors health of MCP servers."""
    
    def __init__(self, check_interval: int = 30):
        self.check_interval = check_interval
        self.health_history: Dict[str, List[HealthReport]] = {}
        self.running = False
    
    async def start_monitoring(self, servers: List[Server]):
        """Start continuous health monitoring."""
        self.running = True
        
        while self.running:
            for server in servers:
                if server.monitoring.health_check.enabled:
                    report = await self.check_server_health(server.name)
                    self._record_health_report(report)
            
            await asyncio.sleep(self.check_interval)
    
    async def check_server_health(self, server_id: str) -> HealthReport:
        """Check health of a specific server."""
        server = await self._get_server_config(server_id)
        
        try:
            start_time = datetime.now()
            
            if server.execution_mode == "local":
                # Check if process is running
                process = self.execution_manager.get_process(server_id)
                if not process or not process.is_alive():
                    return HealthReport(server_id, HealthStatus.UNHEALTHY, 
                                      error_message="Process not running")
                
                # Check health endpoint if available
                if server.monitoring.health_check.endpoint:
                    health_url = f"http://localhost:{server.port}{server.monitoring.health_check.endpoint}"
                    async with httpx.AsyncClient() as client:
                        response = await client.get(health_url, timeout=server.monitoring.health_check.timeout)
                        response_time = (datetime.now() - start_time).total_seconds()
                        
                        if response.status_code == 200:
                            return HealthReport(server_id, HealthStatus.HEALTHY, response_time)
                        else:
                            return HealthReport(server_id, HealthStatus.UNHEALTHY, response_time,
                                              f"Health check failed: {response.status_code}")
                else:
                    return HealthReport(server_id, HealthStatus.HEALTHY)
            
            elif server.execution_mode == "docker":
                # Check Docker container health
                container_status = await self.docker_executor.health_check(server_id)
                response_time = (datetime.now() - start_time).total_seconds()
                return HealthReport(server_id, container_status, response_time)
            
            elif server.execution_mode == "remote":
                # Check remote server health
                remote_status = await self.remote_executor.get_remote_status(server_id, server.remote_config)
                response_time = (datetime.now() - start_time).total_seconds()
                return HealthReport(server_id, remote_status.health, response_time)
        
        except Exception as e:
            response_time = (datetime.now() - start_time).total_seconds()
            return HealthReport(server_id, HealthStatus.UNKNOWN, response_time, str(e))
    
    def _record_health_report(self, report: HealthReport):
        """Record a health report in history."""
        if report.server_id not in self.health_history:
            self.health_history[report.server_id] = []
        
        self.health_history[report.server_id].append(report)
        
        # Keep only last 100 reports
        if len(self.health_history[report.server_id]) > 100:
            self.health_history[report.server_id] = self.health_history[report.server_id][-100:]
```

### 7. Enhanced CLI Interface

```
mcp-manager/
├── cli/
│   ├── __init__.py
│   ├── main.py              # Main CLI entry point
│   ├── install.py           # Installation commands
│   ├── config.py            # Configuration commands
│   ├── run.py               # Execution commands
│   ├── monitor.py           # Monitoring commands
│   ├── secrets.py           # Secrets management commands
│   └── doctor.py            # Diagnostics commands
```

**New Commands:**
```bash
# Installation and management
mcp-manager install template jira-helper
mcp-manager install git jira-helper --repo https://github.com/user/repo
mcp-manager update jira-helper
mcp-manager uninstall jira-helper

# Configuration
mcp-manager config edit jira-helper
mcp-manager config validate jira-helper
mcp-manager config migrate --from-version 1.0

# Secrets management
mcp-manager secrets setup jira-helper
mcp-manager secrets update jira-helper JIRA_API_TOKEN
mcp-manager secrets rotate jira-helper

# Execution and monitoring
mcp-manager start jira-helper --mode docker
mcp-manager stop jira-helper
mcp-manager restart jira-helper
mcp-manager status --all
mcp-manager logs jira-helper --follow --lines 100

# Platform integration
mcp-manager platform configure claude-desktop
mcp-manager platform list
mcp-manager platform sync

# Diagnostics
mcp-manager doctor
mcp-manager test jira-helper
mcp-manager debug jira-helper --verbose
```

### 8. Server Templates & Registry

```
mcp_manager/
├── templates/
│   ├── __init__.py
│   ├── registry.py          # Template registry
│   ├── generator.py         # Server generation
│   └── builtin/             # Built-in templates
│       ├── basic.yaml
│       ├── fastapi.yaml
│       └── docker.yaml
```

**Template System**
- Pre-built templates for common server types
- Custom template creation and sharing
- Template versioning and updates
- Scaffolding for new server development

## Implementation Phases

### Phase 1: Core Architecture (4-6 weeks)
1. **Plugin System**: Implement platform adapter interface
2. **Python Execution**: Replace bash scripts with Python process management
3. **Configuration Schema**: Design and implement new YAML-based configuration
4. **Basic CLI**: Implement core commands with new architecture

### Phase 2: Platform Integration (3-4 weeks)
1. **Claude Desktop**: Implement Claude Desktop platform adapter
2. **VS Code Migration**: Migrate existing VS Code integration to new system
3. **Platform Discovery**: Auto-detection of installed AI platforms
4. **Configuration Migration**: Tools to migrate from v1 to v2

### Phase 3: Deployment & Monitoring (4-5 weeks)
1. **Docker Support**: Container-based execution
2. **Remote Deployment**: SSH and HTTP-based remote management
3. **Logging System**: Comprehensive logging and monitoring
4. **Health Checks**: Automated health monitoring and alerting

### Phase 4: Advanced Features (3-4 weeks)
1. **Secrets Management**: Secure credential storage and management
2. **Template System**: Server templates and scaffolding
3. **Performance Monitoring**: Metrics collection and analysis
4. **Documentation**: Comprehensive user and developer documentation

### Phase 5: Testing & Release (2-3 weeks)
1. **Integration Testing**: End-to-end testing across platforms
2. **Performance Testing**: Load and stress testing
3. **Security Audit**: Security review and penetration testing
4. **PyPI Preparation**: Package preparation and release

## Migration Strategy

### Backward Compatibility
- **Configuration Migration**: Automatic migration from v1 to v2 format
- **Gradual Deprecation**: Support v1 format with deprecation warnings
- **Migration Tools**: CLI tools to assist with migration

### User Communication
- **Migration Guide**: Step-by-step migration documentation
- **Breaking Changes**: Clear documentation of breaking changes
- **Support Timeline**: Clear timeline for v1 support deprecation

## Risk Assessment

### Technical Risks
- **Complexity**: New architecture is significantly more complex
- **Dependencies**: Additional dependencies (Docker, keyring, etc.)
- **Platform Compatibility**: Cross-platform testing requirements
- **Performance**: Overhead from additional abstraction layers

### Mitigation Strategies
- **Phased Implementation**: Gradual rollout with fallback options
- **Comprehensive Testing**: Automated testing across platforms
- **Documentation**: Extensive documentation and examples
- **Community Feedback**: Early beta testing with community

## Success Metrics

### User Experience
- **Installation Time**: < 2 minutes from install to first working server
- **Configuration Complexity**: < 5 steps to configure a new server
- **Error Recovery**: Clear error messages with suggested fixes
- **Documentation Quality**: 90%+ user satisfaction with documentation

### Technical Performance
- **Startup Time**: < 5 seconds for local server startup
- **Memory Usage**: < 50MB baseline memory usage
- **CPU Usage**: < 5% CPU usage when idle
- **Reliability**: 99.9% uptime for managed servers

### Adoption Metrics
- **PyPI Downloads**: Target 1000+ downloads per month
- **GitHub Stars**: Target 100+ stars within 6 months
- **Community Contributions**: 5+ external contributors
- **Platform Support**: Support for 3+ AI platforms

This architecture provides a solid foundation for a production-ready MCP manager that addresses all the identified limitations while providing room for future growth and extensibility.
