#!/usr/bin/env python3
"""
Proof of Concept: NetworkX + Matplotlib Graph Visualization
Tests that matplotlib and networkx work together for workflow visualization.
"""

import io
import base64
import matplotlib.pyplot as plt
import networkx as nx
from typing import Optional

def create_sample_workflow() -> nx.DiGraph:
    """Create a sample Jira workflow for testing"""
    G = nx.DiGraph()
    
    # Add nodes (workflow states)
    nodes = [
        ('To Do', {'color': '#DDD', 'category': 'start'}),
        ('In Progress', {'color': '#FFA500', 'category': 'active'}),
        ('Code Review', {'color': '#87CEEB', 'category': 'review'}),
        ('Testing', {'color': '#FFD700', 'category': 'test'}),
        ('Done', {'color': '#90EE90', 'category': 'end'}),
        ('Blocked', {'color': '#FF6B6B', 'category': 'blocked'})
    ]
    
    for node_id, attrs in nodes:
        G.add_node(node_id, **attrs)
    
    # Add edges (transitions)
    edges = [
        ('To Do', 'In Progress', {'label': 'Start Work'}),
        ('In Progress', 'Code Review', {'label': 'Submit for Review'}),
        ('Code Review', 'Testing', {'label': 'Approve'}),
        ('Code Review', 'In Progress', {'label': 'Request Changes'}),
        ('Testing', 'Done', {'label': 'Pass Tests'}),
        ('Testing', 'In Progress', {'label': 'Fail Tests'}),
        ('In Progress', 'Blocked', {'label': 'Block'}),
        ('Blocked', 'In Progress', {'label': 'Unblock'})
    ]
    
    for source, target, attrs in edges:
        G.add_edge(source, target, **attrs)
    
    return G

def generate_matplotlib_graph(graph: nx.DiGraph, format: str = 'png') -> str:
    """Generate graph visualization using matplotlib and return as base64"""
    
    # Create matplotlib figure
    plt.figure(figsize=(12, 8))
    plt.clf()
    
    # Generate layout
    pos = nx.spring_layout(graph, seed=42, k=3, iterations=50)
    
    # Extract node colors
    node_colors = [graph.nodes[node].get('color', '#DDD') for node in graph.nodes()]
    
    # Draw nodes
    nx.draw_networkx_nodes(
        graph, pos, 
        node_color=node_colors,
        node_size=2000,
        alpha=0.9
    )
    
    # Draw edges with arrows
    nx.draw_networkx_edges(
        graph, pos,
        edge_color='#666',
        arrows=True,
        arrowsize=20,
        arrowstyle='->',
        width=2,
        alpha=0.7
    )
    
    # Draw node labels
    nx.draw_networkx_labels(
        graph, pos,
        font_size=10,
        font_weight='bold',
        font_color='black'
    )
    
    # Draw edge labels
    edge_labels = nx.get_edge_attributes(graph, 'label')
    nx.draw_networkx_edge_labels(
        graph, pos,
        edge_labels,
        font_size=8,
        font_color='#333'
    )
    
    # Styling
    plt.title('Jira Workflow Visualization (Matplotlib + NetworkX)', 
              fontsize=16, fontweight='bold', pad=20)
    plt.axis('off')
    plt.tight_layout()
    
    # Export to base64
    buffer = io.BytesIO()
    if format.lower() == 'svg':
        plt.savefig(buffer, format='svg', bbox_inches='tight', dpi=150)
    else:
        plt.savefig(buffer, format='png', bbox_inches='tight', dpi=150, 
                   facecolor='white', edgecolor='none')
    
    buffer.seek(0)
    image_data = buffer.read()
    buffer.close()
    plt.close()
    
    return base64.b64encode(image_data).decode('utf-8')

def test_proof_of_concept():
    """Test the matplotlib + networkx approach"""
    print("🧪 Testing Matplotlib + NetworkX Proof of Concept...")
    
    try:
        # Test imports
        print("✅ matplotlib imported successfully:", plt.matplotlib.__version__)
        print("✅ networkx imported successfully:", nx.__version__)
        
        # Create sample workflow
        workflow = create_sample_workflow()
        print(f"✅ Created workflow with {len(workflow.nodes())} nodes and {len(workflow.edges())} edges")
        
        # Test PNG generation
        png_base64 = generate_matplotlib_graph(workflow, 'png')
        print(f"✅ PNG generation successful - {len(png_base64)} characters")
        
        # Test SVG generation  
        svg_base64 = generate_matplotlib_graph(workflow, 'svg')
        print(f"✅ SVG generation successful - {len(svg_base64)} characters")
        
        # Validate base64
        try:
            base64.b64decode(png_base64)
            print("✅ PNG base64 encoding valid")
        except Exception as e:
            print(f"❌ PNG base64 invalid: {e}")
            
        try:
            base64.b64decode(svg_base64)
            print("✅ SVG base64 encoding valid")
        except Exception as e:
            print(f"❌ SVG base64 invalid: {e}")
            
        print("\n🎉 Proof of Concept SUCCESS!")
        print("✅ NetworkX + Matplotlib approach works correctly")
        print("✅ Ready to implement MatplotlibGenerator class")
        
        return True
        
    except Exception as e:
        print(f"❌ Proof of concept failed: {e}")
        return False

if __name__ == "__main__":
    success = test_proof_of_concept()
    exit(0 if success else 1)
