# Quick Start Guide: `mcp-manager` and `jira-helper`

This guide provides a streamlined set of instructions for developers to get up and running with the `mcp-manager` and the `jira-helper` MCP server.

## 1. Prerequisites

-   Python 3.11+
-   `pipx` (for installing `mcp-manager`)

If you don't have `pipx`, you can install it with:
```bash
pip install pipx
pipx ensurepath
```

## 2. Install `mcp-manager`

Install the `mcp-manager` CLI tool from its source directory using `pipx`. This will make it available globally in your shell.

```bash
pipx install ./utils/mcp_manager
```

Verify the installation:
```bash
mcp-manager --version
```

## 3. Install the `jira-helper` Server

Now, use `mcp-manager` to install the `jira-helper` server as a standalone application. The `--pipx` flag tells the manager to use the `pipx`-style installation, which creates an isolated environment for the server.

```bash
mcp-manager install local jira-helper --source servers/jira-helper --pipx --force
```
*   `--source`: Points to the directory containing the server's source code.
*   `--pipx`: Specifies the installation method.
*   `--force`: Overwrites any existing server with the same name.

## 4. Configure for Multiple Jira Instances

The `jira-helper` server is configured via a `config.yaml` file. This is where you will add the connection details for each of your Jira instances.

1.  **Navigate to the `jira-helper` configuration directory:**
    ```bash
    cd ~/.mcp_servers/servers/jira-helper
    ```

2.  **Create the configuration file:**
    A sample configuration file is provided as `config.yaml.example`. Copy it to create your own configuration:
    ```bash
    cp config.yaml.example config.yaml
    ```

3.  **Edit the configuration file:**
    Open `config.yaml` in your favorite editor. The file contains a list of `instances`, where you can add the details for each of your Jira accounts.

    **Example `config.yaml`:**
    ```yaml
    # ~/.mcp_servers/servers/jira-helper/config.yaml
    
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
    *   Replace the placeholder values with your actual Jira URLs, usernames, and API tokens.
    *   You can add as many instances as you need.

## 5. Configure Cline Integration

Finally, run the `configure` command to make the newly installed `jira-helper` server available to Cline in your editor.

```bash
mcp-manager configure vscode
```

This command will automatically detect the `jira-helper` server and update your VS Code settings to use it. You may need to restart your editor for the changes to take effect.

You are now ready to use the `jira-helper` with all your configured Jira instances directly from your editor!
