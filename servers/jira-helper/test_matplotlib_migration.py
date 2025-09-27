#!/usr/bin/env python3
"""
Test the matplotlib migration implementation directly.
"""

import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from domain.models import WorkflowGraph, WorkflowNode, WorkflowEdge
from infrastructure.graph_generator import MatplotlibGenerator
import asyncio

async def test_matplotlib_migration():
    """Test the matplotlib implementation with sample workflow data."""
    print("🧪 Testing Matplotlib Migration Implementation...")
    
    # Create sample workflow
    workflow = WorkflowGraph(project_key="TEST", issue_type="Task")
    
    # Add nodes
    nodes = [
        WorkflowNode(id="To Do", name="To Do", category="To Do", color="#FF9800"),
        WorkflowNode(id="In Progress", name="In Progress", category="In Progress", color="#2196F3"),
        WorkflowNode(id="Code Review", name="Code Review", category="In Progress", color="#87CEEB"),
        WorkflowNode(id="Done", name="Done", category="Done", color="#4CAF50")
    ]
    
    for node in nodes:
        workflow.add_node(node)
    
    # Add edges
    edges = [
        WorkflowEdge(from_node="To Do", to_node="In Progress", label="Start Work"),
        WorkflowEdge(from_node="In Progress", to_node="Code Review", label="Submit Review"),
        WorkflowEdge(from_node="Code Review", to_node="In Progress", label="Request Changes"),
        WorkflowEdge(from_node="Code Review", to_node="Done", label="Approve")
    ]
    
    for edge in edges:
        workflow.add_edge(edge)
    
    # Test the new implementation
    generator = MatplotlibGenerator()
    
    print(f"✅ Generator available: {generator.is_available()}")
    
    # Test DOT graph generation
    try:
        dot_graph = await generator.generate_dot_graph(workflow)
        print(f"✅ DOT graph generated: {len(dot_graph)} characters")
        print("📋 First few lines of DOT output:")
        for line in dot_graph.split('\n')[:6]:
            print(f"   {line}")
    except Exception as e:
        print(f"❌ DOT generation failed: {e}")
        return False
    
    # Test visual graph generation (SVG)
    try:
        svg_graph = await generator.generate_visual_graph(workflow, "svg")
        print(f"✅ SVG graph generated: {len(svg_graph)} characters")
        
        # Validate it's proper base64
        import base64
        decoded = base64.b64decode(svg_graph)
        print(f"✅ SVG base64 valid, decoded size: {len(decoded)} bytes")
    except Exception as e:
        print(f"❌ SVG generation failed: {e}")
        return False
    
    # Test visual graph generation (PNG)  
    try:
        png_graph = await generator.generate_visual_graph(workflow, "png")
        print(f"✅ PNG graph generated: {len(png_graph)} characters")
        
        # Validate it's proper base64
        decoded = base64.b64decode(png_graph)
        print(f"✅ PNG base64 valid, decoded size: {len(decoded)} bytes")
    except Exception as e:
        print(f"❌ PNG generation failed: {e}")
        return False
    
    # Test text fallback
    text_output = generator._format_workflow_as_text(workflow)
    print(f"✅ Text fallback: {len(text_output)} characters")
    print("📋 Text output preview:")
    for line in text_output.split('\n')[:8]:
        print(f"   {line}")
    
    print("\n🎉 MATPLOTLIB MIGRATION TEST SUCCESSFUL!")
    print("✅ All graph generation methods working correctly")
    print("✅ GraphViz → Matplotlib migration COMPLETE")
    
    return True

if __name__ == "__main__":
    try:
        success = asyncio.run(test_matplotlib_migration())
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        sys.exit(1)
