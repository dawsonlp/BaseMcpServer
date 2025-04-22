# MCP Server Debugging Notes

This document chronicles the troubleshooting process for setting up a Jira-connected MCP server for Claude. The process was particularly challenging and revealed several nuances about MCP server configuration, Docker, and environment variables.

## Initial Goal

Create an MCP server that connects to Jira, allowing Claude to:
1. List Jira projects
2. Get details about specific Jira issues

## Approach 1: Starting from Template

We initially tried to create a custom MCP server by:
1. Copying the template directory from BaseMcpServer
2. Modifying it to add Jira functionality
3. Building and running the Docker container

### Issues Encountered

- **Error: "Received request before initialization was complete"**
  - This error occurred consistently when trying to use any MCP tool
  - The same error appeared across multiple attempts with different server configurations

### Investigation Steps

1. Checked if the example server was working (it was)
2. Created a fresh copy of the template with different names and ports
3. Tried rebuilding the original example server to see if it would break (it did)

### Key Discovery

We discovered that the base image might have changed since the original example was created, causing initialization issues. Even rebuilding the example server led to the same initialization error.

## Approach 2: Restarting VS Code

After encountering consistent connectivity issues, we tried restarting VS Code.

### Results

- The example-mcp-server began working again
- We could successfully use the calculator tool

## Approach 3: Clone the Working Example

Rather than starting from the template, we:
1. Made a direct copy of the working example directory (`example` → `jira-clone`)
2. Made minimal modifications to avoid breaking functionality
3. Added Jira functionality to this working base

### Adding Jira Integration

1. Updated Dockerfile to install the Jira Python library
2. Added Jira connection credentials to the .env file
3. Created a get_issue_details tool to fetch Jira ticket information
4. Added list_jira_projects to retrieve all projects

### New Issues Encountered

- The server could not connect to the correct Jira URL
- It used the default "example.atlassian.net" instead of our specified URL
- The .env file wasn't being properly loaded in the container

## Environment Variable Debugging

We made several improvements to environment variable handling:

1. Updated Dockerfile to copy the .env file into the container
2. Added robust .env file finding logic to src/config.py
3. Added detailed logging to show which configuration was being used
4. Changed port settings to match base container expectations

## Port Configuration Issues

We found multiple port-related issues:

1. Base Dockerfile exposes port 7501
2. Our .env had PORT=7601
3. Docker run command used -p 7888:7501
4. This created a mismatch where Claude was trying to connect to port 7888 but the server was on a different port

## Final Solution

1. Changed .env to use PORT=7501 to match the base image's exposed port
2. Used consistent port mapping: docker run -p 7888:7501
3. Rebuilt the container with the updated configuration
4. Restarted VS Code to ensure clean connection state
5. Successfully connected to the Jira MCP server

## Successful Tools

1. `get_issue_details` - fetches detailed information about a specific Jira issue
   - Example: Successfully fetched details for TRIL-120 "Meet w/ MC for Jira Breakdown"

2. `list_jira_projects` - retrieves all projects from Jira
   - Example: Successfully retrieved 34 projects including TPA, TRIL, etc.

## Key Lessons

1. **Configuration Consistency**: Docker container ports, environment variables, and MCP settings must all align
2. **Proper Environment Variables**: .env files should be properly mounted/copied into containers
3. **VS Code Restart**: Sometimes connectivity issues can be resolved by restarting VS Code
4. **Detailed Logging**: Adding detailed logging about configuration is crucial for debugging
5. **Base Image Awareness**: Be aware of what ports the base image exposes and align with those
6. **Environment Variable Loading**: Implementing robust environment variable loading with fallbacks helps with debugging

## Next Steps

Future enhancements could include:
- Adding functionality to create Jira issues
- Implementing issue updates
- Adding search capabilities with JQL
- Creating webhooks for real-time updates
