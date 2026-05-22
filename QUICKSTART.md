# Quick Start Guide: `mcp-manager` and `jira-helper`

This guide provides a streamlined set of instructions for developers to get up and running with the `mcp-manager` tool and the `jira-helper` MCP server.

## 1. Prerequisites

-   Python 3.11+
-   [`uv`](https://docs.astral.sh/uv/) (for installing `mcp-manager` and managing per-server environments)

If you don't have `uv`, install it with:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
uv tool update-shell   # ensure uv's tool bin dir is on your PATH
```

## 2. Install `mcp-manager`

Install the `mcp-manager` CLI tool globally with `uv`:

```bash
# Install from this checkout
uv tool install ./utils/mcp_manager

# Or install from GitHub
uv tool install "git+https://github.com/dawsonlp/BaseMcpServer.git#subdirectory=utils/mcp_manager"
```

Verify the installation:
```bash
mcp-manager --version
mcp-manager --help
```

**Note:** `mcpmanager` (without the hyphen) is registered as an alias.

## 3. Install the `jira-helper` Server

Use `mcp-manager` to install the `jira-helper` server in an isolated environment:

```bash
mcp-manager install local jira-helper --source servers/jira-helper --force
```
*   `--source`: Points to the directory containing the server's source code.
*   `--force`: Overwrites any existing server with the same name.

The server will be installed under `~/.config/mcp-manager/servers/jira-helper/`.

## 4. Configure for Multiple Jira Instances

The `jira-helper` server is configured via a `config.yaml` file where you add connection details for each Jira instance.

1.  **Navigate to the `jira-helper` configuration directory:**
    ```bash
    cd ~/.config/mcp-manager/servers/jira-helper
    ```

2.  **Create the configuration file:**
    Copy the example configuration to create your own:
    ```bash
    cp config.yaml.example config.yaml
    ```

3.  **Edit the configuration file:**
    Open `config.yaml` and configure your Jira instances:

    **Example `config.yaml`:**
    ```yaml
    # ~/.config/mcp-manager/servers/jira-helper/config.yaml
    
    # Set the default instance to use when one is not specified
    default_instance: "personal"
    
    instances:
      - name: "personal"
        url: "https://your-personal-space.atlassian.net"
        user: "your-email@example.com"
        token: "YOUR_JIRA_API_TOKEN"
        description: "Personal Jira Instance"
    
      - name: "work"
        url: "https://your-company.atlassian.net"
        user: "your-work-email@example.com"
        token: "YOUR_OTHER_JIRA_API_TOKEN"
        description: "Work Jira Instance"
    ```
    
    **Getting Jira API Tokens:**
    - Go to your Atlassian Account Settings
    - Navigate to Security → API Tokens
    - Create a new token for each instance
    - Replace the placeholder values with your actual URLs, emails, and tokens

## 5. Configure Cline Integration

Configure VS Code Cline to use the `jira-helper` server:

```bash
mcp-manager config cline
```

This automatically updates your VS Code settings to include the `jira-helper` server.

## 6. Verify Your Setup

Check your complete MCP system status:

```bash
mcp-manager info tree
```

This command displays:
- System information (Python version, total servers, disk usage)
- Platform integration status (VS Code Cline, Claude Desktop)
- Server counts by platform

You should see `jira-helper` counted in the VS Code Cline servers, and both platforms showing "Available" status.

## 7. Using Multiple Jira Instances

When using Jira tools in your editor, you can specify which instance to use:

- **Default instance**: Commands use your configured `default_instance`
- **Specific instance**: Use the `instance_name` parameter in tool calls

**Example Usage:**
- `list_jira_projects` with instance `personal` 
- `get_issue_details` for issue `PROJ-123` on `work` instance
- `create_jira_ticket` on your default instance

## Troubleshooting

If you encounter issues:

1. **List installed servers**: `mcp-manager list`
2. **Test server directly**: `mcp-manager server start jira-helper`
3. **Verify Jira credentials**: Check your API tokens and URLs
4. **Restart VS Code** after configuration changes

You are now ready to use the `jira-helper` with all your configured Jira instances directly from your editor!
