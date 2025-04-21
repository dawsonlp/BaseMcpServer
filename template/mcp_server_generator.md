# MCP Server Generator

This document outlines how to create a script that takes a Python file containing MCP annotations and generates a complete, containerized MCP server using the HTTP+SSE transport.

## Concept

The idea is to take a simple, annotated Python file like this:

```python
# example_annotated.py

"""Example file with MCP annotations."""

from typing import Dict, Any, Optional

# Tool definition with MCP annotation
@mcp.tool()
def calculate_area(shape: str, width: float, height: Optional[float] = None) -> Dict[str, Any]:
    """
    Calculate the area of a geometric shape.
    
    Args:
        shape: The shape type (rectangle, square, circle)
        width: The width or radius of the shape
        height: The height of the shape (only needed for rectangle)
        
    Returns:
        A dictionary containing the calculated area
    """
    if shape.lower() == "rectangle":
        if height is None:
            raise ValueError("Height is required for rectangle")
        area = width * height
    elif shape.lower() == "square":
        area = width * width
    elif shape.lower() == "circle":
        import math
        area = math.pi * (width ** 2)
    else:
        raise ValueError(f"Unsupported shape: {shape}")
        
    return {"area": area, "shape": shape}

# Resource definition with MCP annotation
@mcp.resource("resource://shapes")
def available_shapes() -> Dict[str, Any]:
    """
    Get a list of available shapes for the area calculator.
    
    Returns:
        A dictionary containing the available shapes
    """
    return {
        "shapes": ["rectangle", "square", "circle"],
        "description": "Shapes available for area calculation"
    }
```

And automatically generate a complete MCP server with Docker configuration, ready to be built and deployed.

## Script Requirements

The server generator script would:

1. Parse a Python file with MCP annotations
2. Extract tool and resource definitions
3. Generate a complete MCP server based on the template
4. Configure Docker settings
5. Create necessary configuration files

## Implementation Overview

### 1. Parser Component

The script needs to parse the Python file to identify MCP annotations:

```python
def parse_mcp_annotations(file_path):
    """Parse a Python file to extract MCP annotations."""
    # Use ast (Abstract Syntax Tree) module to parse Python code
    import ast
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Parse the Python code
    tree = ast.parse(content)
    
    tools = []
    resources = []
    
    # Traverse the AST to find decorated functions
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            # Check for decorators
            for decorator in node.decorator_list:
                # Check if it's an MCP tool decorator
                if isinstance(decorator, ast.Call) and hasattr(decorator.func, 'attr') and decorator.func.attr == 'tool':
                    # Extract function details
                    tool = extract_function_details(node)
                    tools.append(tool)
                
                # Check if it's an MCP resource decorator
                if isinstance(decorator, ast.Call) and hasattr(decorator.func, 'attr') and decorator.func.attr == 'resource':
                    # Extract resource details
                    resource = extract_function_details(node)
                    # Extract resource path from decorator arguments
                    if decorator.args:
                        resource['uri'] = decorator.args[0].value
                    resources.append(resource)
    
    return {
        'tools': tools,
        'resources': resources
    }
```

### 2. Generator Component

The script would then use the extracted information to generate the server code:

```python
def generate_mcp_server(output_dir, server_name, annotations, base_port=7501):
    """Generate an MCP server from the parsed annotations."""
    # Create directory structure
    os.makedirs(os.path.join(output_dir, 'src'), exist_ok=True)
    os.makedirs(os.path.join(output_dir, 'docker'), exist_ok=True)
    
    # Generate server.py with the tool and resource implementations
    generate_server_file(output_dir, server_name, annotations)
    
    # Generate other necessary files by copying from the template
    copy_template_files(output_dir, server_name, base_port)
    
    # Customize the configuration files
    customize_config_files(output_dir, server_name, annotations, base_port)
    
    # Make build script executable
    os.chmod(os.path.join(output_dir, 'docker', 'build.sh'), 0o755)
    
    print(f"MCP server '{server_name}' generated successfully in '{output_dir}'")
```

### 3. Docker Configuration

The script would set up the Docker configuration files:

```python
def configure_docker(output_dir, server_name):
    """Configure Docker files for the MCP server."""
    # Copy Dockerfile template
    docker_file = os.path.join(output_dir, 'docker', 'Dockerfile')
    with open(docker_file, 'w') as f:
        f.write(f"""# Use the base MCP server image
ARG DOCKER_USERNAME

FROM docker.io/${{DOCKER_USERNAME}}/base-mcp-server:latest

# Set working directory
WORKDIR /app

# Copy the application code
COPY ./src ./src

# Add metadata
LABEL maintainer="{server_name} Maintainer" \\
      version="0.1.0" \\
      description="{server_name} MCP Server"

# The command to run the MCP server
CMD ["python", "-m", "src.main"]
""")
    
    # Copy build script template
    build_script = os.path.join(output_dir, 'docker', 'build.sh')
    # (content similar to the template/docker/build.sh with customizations)
```

### 4. Configuration Files

The script would generate the necessary configuration files:

```python
def generate_config_files(output_dir, server_name, annotations, base_port):
    """Generate configuration files for the MCP server."""
    # Generate .env.example
    env_example = os.path.join(output_dir, '.env.example')
    with open(env_example, 'w') as f:
        f.write(f"""# Server configuration
HOST=0.0.0.0
PORT={base_port}

# Security settings
API_KEY=your_api_key_here
""")
    
    # Generate .mcp.json
    mcp_json = os.path.join(output_dir, '.mcp.json')
    with open(mcp_json, 'w') as f:
        f.write(json.dumps({
            "servers": [
                {
                    "name": server_name,
                    "url": f"http://localhost:{base_port}",
                    "apiKey": "your_api_key_here",
                    "description": f"{server_name} MCP Server",
                    "tools": [
                        {
                            "name": tool["name"],
                            "description": tool["docstring"],
                            "parameters": tool["parameters"]
                        } for tool in annotations["tools"]
                    ],
                    "resources": [
                        {
                            "uri": resource["uri"],
                            "description": resource["docstring"],
                            "parameters": resource.get("parameters", {})
                        } for resource in annotations["resources"]
                    ]
                }
            ]
        }, indent=2))
```

## Full Script Structure

The complete script would have the following structure:

```
mcp_generator.py
├── parse_mcp_annotations()       # Parse Python file for MCP annotations
├── extract_function_details()    # Extract details from function definitions
├── generate_mcp_server()         # Generate the full server
├── generate_server_file()        # Generate server.py
├── generate_main_file()          # Generate main.py
├── generate_config_file()        # Generate config.py
├── generate_config_files()       # Generate env and MCP config files
├── configure_docker()            # Set up Docker files
└── main()                        # Main script entry point
```

## Usage Example

The script would be used like this:

```bash
python mcp_generator.py \
  --input example_annotated.py \
  --output my-mcp-server \
  --name "My MCP Server" \
  --port 7501
```

This would:
1. Parse `example_annotated.py` for MCP annotations
2. Generate a complete MCP server in the `my-mcp-server` directory
3. Configure it with the name "My MCP Server" listening on port 7501

## Implementation Considerations

### Parsing Challenges

- Python's `ast` module can parse Python code but has limitations
- Consider using tools like `libcst` for better handling of comments and formatting
- Need to handle docstrings correctly to extract function documentation

### Code Generation

- Use templates with placeholders instead of string concatenation
- Consider using a templating engine like Jinja2
- Ensure generated code is properly formatted and follows PEP 8

### Error Handling

- Validate input Python files before parsing
- Handle missing or incomplete annotations gracefully
- Provide clear error messages for invalid input

## Next Steps

This document outlines the concept and architecture of the MCP server generator script. To implement this script:

1. Create the parser component to extract MCP annotations
2. Develop the generator component to create server files
3. Implement Docker configuration generation
4. Add validation and error handling
5. Test with various input files
6. Document the final script

## Security Considerations

- Validate user input to prevent injection attacks
- Ensure generated code doesn't contain security vulnerabilities
- Use secure defaults for configuration files
- Warn users to change default API keys and credentials

## Future Enhancements

- Support for additional MCP features and annotations
- Interactive mode for guided server generation
- Integration with existing codebases
- Support for custom templates and configurations
- Option to generate tests for the generated server
