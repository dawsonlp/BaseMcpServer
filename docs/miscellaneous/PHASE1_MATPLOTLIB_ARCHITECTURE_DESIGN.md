# Phase 1.2: Matplotlib Architecture Design - GraphViz → Matplotlib Migration

## 🎯 **STARTING: 1.2 Matplotlib Architecture Design**

### 📋 **MatplotlibGenerator Class Structure**

**Class Design (maintains exact GraphvizGenerator interface):**
```python
class MatplotlibGenerator(GraphGenerator):
    """Graph generator implementation using Matplotlib + NetworkX."""

    def __init__(self):
        """Initialize matplotlib generator with plotting settings."""
        # Configure matplotlib for headless operation
        self._setup_matplotlib()
        
    def _setup_matplotlib(self) -> None:
        """Configure matplotlib for server environment."""
        import matplotlib
        matplotlib.use('Agg')  # Non-interactive backend
        import matplotlib.pyplot as plt
        plt.ioff()  # Turn off interactive mode
        
    def is_available(self) -> bool:
        """Check if graph generation is available."""
        # Always True for pure Python implementation
        return True

    async def generate_dot_graph(self, workflow: WorkflowGraph) -> str:
        """Generate DOT-like text representation using NetworkX."""
        # Convert to NetworkX, then generate text representation
        
    async def generate_visual_graph(self, workflow: WorkflowGraph, format: str = "svg") -> str:
        """Generate matplotlib visualization, return base64 encoded."""
        # NetworkX graph → matplotlib plot → base64
        
    def _format_workflow_as_text(self, workflow: WorkflowGraph) -> str:
        """Enhanced text representation with ASCII art."""
        # Improve current text formatting with NetworkX analysis
```

### 📋 **NetworkX Layout Algorithm Selection**

**Layout Algorithm Strategy:**
```python
class LayoutStrategy:
    """Strategy for selecting optimal layout algorithm."""
    
    @staticmethod
    def select_layout(graph: nx.DiGraph) -> tuple[callable, dict]:
        """Select best layout algorithm based on graph characteristics."""
        
        node_count = graph.number_of_nodes()
        edge_count = graph.number_of_edges()
        
        # Decision matrix for layout selection:
        if node_count <= 5:
            # Simple workflows - use spring layout
            return nx.spring_layout, {
                'k': 2.0,           # Optimal distance between nodes
                'iterations': 100,   # Convergence iterations
                'seed': 42          # Reproducible layouts
            }
        elif node_count <= 15 and edge_count <= 20:
            # Medium workflows - use hierarchical if linear, spring otherwise
            if cls._is_mostly_linear(graph):
                return cls._hierarchical_layout, {
                    'direction': 'horizontal',  # Left-to-right like GraphViz
                    'layer_separation': 2.0
                }
            else:
                return nx.spring_layout, {'k': 1.5, 'iterations': 150}
        else:
            # Complex workflows - use circular or kamada_kawai
            if edge_count > node_count * 1.5:  # Dense graph
                return nx.kamada_kawai_layout, {'scale': 2.0}
            else:
                return nx.circular_layout, {'scale': 2.0}
    
    @staticmethod
    def _is_mostly_linear(graph: nx.DiGraph) -> bool:
        """Check if workflow is mostly linear (few branches)."""
        # Simple heuristic: linear if most nodes have ≤2 connections
        linear_nodes = sum(1 for node in graph.nodes() 
                          if graph.degree(node) <= 2)
        return linear_nodes / len(graph.nodes()) > 0.7
        
    @staticmethod 
    def _hierarchical_layout(graph: nx.DiGraph, direction: str, layer_separation: float) -> dict:
        """Custom hierarchical layout for workflow visualization."""
        # Implement layer-based positioning similar to GraphViz rankdir=LR
        layers = cls._topological_layers(graph)
        positions = {}
        
        for layer_idx, layer_nodes in enumerate(layers):
            x = layer_idx * layer_separation
            y_positions = np.linspace(0, len(layer_nodes)-1, len(layer_nodes))
            
            for node_idx, node in enumerate(layer_nodes):
                positions[node] = (x, y_positions[node_idx])
                
        return positions
```

**Selected Algorithms by Use Case:**
1. **Spring Layout** (`nx.spring_layout`) - General purpose, good for 3-15 nodes
2. **Hierarchical** (custom) - Linear workflows, mimics GraphViz rankdir=LR  
3. **Circular Layout** (`nx.circular_layout`) - Simple workflows, equal importance
4. **Kamada-Kawai** (`nx.kamada_kawai_layout`) - Complex dense graphs

### 📋 **Color Scheme Mapping**

**Direct Color Mapping (maintain exact compatibility):**
```python
class ColorScheme:
    """Matplotlib color scheme matching GraphViz output."""
    
    # Exact color mapping from current implementation
    STATUS_COLORS = {
        "To Do": "#FF9800",      # Orange  
        "In Progress": "#2196F3", # Blue
        "Done": "#4CAF50",       # Green
        "Current": "#9C27B0",    # Purple
        "Available": "#607D8B",  # Blue Grey
        "Unknown": "#9E9E9E"     # Grey
    }
    
    # Matplotlib style configuration
    NODE_STYLE = {
        'node_size': 2000,           # Size of workflow nodes
        'node_shape': 's',           # Square nodes (like GraphViz boxes)
        'alpha': 0.9,                # Slight transparency
        'linewidths': 2,             # Node border width
        'edgecolors': '#333333'      # Dark border color
    }
    
    EDGE_STYLE = {
        'edge_color': '#666666',     # Dark grey edges
        'arrows': True,              # Directional arrows
        'arrowstyle': '->',          # Arrow style
        'arrowsize': 15,             # Arrow size
        'width': 2.0,                # Edge line width
        'alpha': 0.8                 # Slight transparency
    }
    
    FONT_STYLE = {
        'font_size': 10,             # Node label font size
        'font_weight': 'bold',       # Bold labels
        'font_family': 'sans-serif', # Clean font
        'font_color': '#000000'      # Black text
    }
    
    @classmethod
    def get_node_colors(cls, workflow: WorkflowGraph) -> list[str]:
        """Get list of colors for all nodes in order."""
        return [cls.STATUS_COLORS.get(node.category, cls.STATUS_COLORS["Unknown"]) 
                for node in workflow.nodes]
                
    @classmethod
    def get_matplotlib_style(cls) -> dict:
        """Get complete matplotlib styling dictionary."""
        return {**cls.NODE_STYLE, **cls.EDGE_STYLE, **cls.FONT_STYLE}
```

### 📋 **Base64 Export Pipeline Design**

**Image Generation & Encoding:**
```python
class ImageExporter:
    """Handle matplotlib rendering and base64 conversion."""
    
    # High-quality output settings
    EXPORT_SETTINGS = {
        'dpi': 150,              # High resolution
        'bbox_inches': 'tight',  # Trim whitespace
        'pad_inches': 0.2,       # Small margin
        'facecolor': 'white',    # White background
        'edgecolor': 'none'      # No border
    }
    
    @staticmethod
    def render_to_base64(fig, format_type: str) -> str:
        """Render matplotlib figure to base64 encoded string."""
        import io
        import base64
        
        # Create in-memory buffer
        buffer = io.BytesIO()
        
        try:
            # Render to buffer
            if format_type.lower() == 'png':
                fig.savefig(buffer, format='png', **cls.EXPORT_SETTINGS)
            else:  # Default to SVG
                fig.savefig(buffer, format='svg', **cls.EXPORT_SETTINGS)
            
            # Get bytes and encode
            buffer.seek(0)
            image_bytes = buffer.getvalue()
            base64_string = base64.b64encode(image_bytes).decode('utf-8')
            
            return base64_string
            
        finally:
            buffer.close()
            plt.close(fig)  # Clean up matplotlib figure
```

### 📋 **Error Handling Strategy**

**Multi-layer Error Handling:**
```python
class MatplotlibErrorHandler:
    """Robust error handling for matplotlib graph generation."""
    
    @staticmethod
    def safe_import() -> tuple[bool, str]:
        """Safely import required libraries with clear error messages."""
        try:
            import matplotlib
            matplotlib.use('Agg')
            import matplotlib.pyplot as plt
            import networkx as nx
            return True, "Libraries available"
        except ImportError as e:
            return False, f"Missing required libraries: {str(e)}"
    
    @staticmethod
    def safe_render(workflow: WorkflowGraph, format_type: str) -> str:
        """Safely render workflow with fallback chain."""
        
        # Layer 1: Full matplotlib rendering
        try:
            return cls._render_matplotlib(workflow, format_type)
        except Exception as e:
            logger.warning(f"Matplotlib rendering failed: {e}")
            
        # Layer 2: Simplified NetworkX rendering  
        try:
            return cls._render_simple_networkx(workflow, format_type)
        except Exception as e:
            logger.warning(f"Simple NetworkX rendering failed: {e}")
            
        # Layer 3: Enhanced text representation
        try:
            return cls._render_enhanced_text(workflow)
        except Exception as e:
            logger.error(f"Text rendering failed: {e}")
            
        # Layer 4: Basic text fallback (always works)
        return cls._render_basic_text(workflow)
```

**Exception Mapping:**
```python
# Map matplotlib errors to domain exceptions
MATPLOTLIB_ERROR_MAPPING = {
    ImportError: JiraGraphLibraryNotAvailable,
    MemoryError: JiraGraphGenerationError,
    ValueError: JiraGraphGenerationError,
    RuntimeError: JiraGraphGenerationError
}

def handle_matplotlib_error(error: Exception, workflow: WorkflowGraph) -> str:
    """Convert matplotlib errors to domain exceptions."""
    error_type = type(error)
    domain_exception = MATPLOTLIB_ERROR_MAPPING.get(error_type, JiraGraphGenerationError)
    
    # Log original error for debugging
    logger.error(f"Matplotlib error: {error}")
    
    # Raise appropriate domain exception
    if error_type == ImportError:
        raise domain_exception(["matplotlib", "networkx"])
    else:
        raise domain_exception(f"Graph generation failed: {str(error)}")
```

### 📋 **Performance Optimization**

**Matplotlib Performance Settings:**
```python
class PerformanceConfig:
    """Optimize matplotlib for server-side graph generation."""
    
    @staticmethod
    def configure_matplotlib():
        """Apply performance optimizations."""
        import matplotlib
        
        # Use non-interactive backend
        matplotlib.use('Agg')
        
        # Reduce memory usage
        matplotlib.rcParams['figure.max_open_warning'] = 0
        matplotlib.rcParams['axes.unicode_minus'] = False
        
        # Optimize rendering
        matplotlib.rcParams['path.simplify'] = True
        matplotlib.rcParams['path.simplify_threshold'] = 0.1
        
    @staticmethod
    def cleanup_after_render():
        """Clean up matplotlib resources."""
        import matplotlib.pyplot as plt
        plt.clf()  # Clear current figure
        plt.close('all')  # Close all figures
```

### 📋 **NetworkX Graph Construction**

**Workflow → NetworkX Conversion:**
```python
class NetworkXConverter:
    """Convert WorkflowGraph to NetworkX DiGraph."""
    
    @staticmethod
    def workflow_to_networkx(workflow: WorkflowGraph) -> nx.DiGraph:
        """Convert domain WorkflowGraph to NetworkX DiGraph."""
        G = nx.DiGraph()
        
        # Add nodes with attributes
        for node in workflow.nodes:
            G.add_node(node.id, 
                      name=node.name,
                      category=node.category, 
                      color=node.color,
                      label=node.name)  # For matplotlib
        
        # Add edges with labels
        for edge in workflow.edges:
            G.add_edge(edge.from_node, edge.to_node, 
                      label=edge.label,
                      transition_name=edge.label)
        
        return G
    
    @staticmethod
    def add_layout_positions(G: nx.DiGraph, layout_func, layout_params: dict) -> nx.DiGraph:
        """Add x,y positions to nodes using selected layout."""
        positions = layout_func(G, **layout_params)
        
        for node, (x, y) in positions.items():
            G.nodes[node]['x'] = x
            G.nodes[node]['y'] = y
            
        return G
```

---

## ✅ **ARCHITECTURE DESIGN COMPLETED**

### 🎯 **Key Architecture Decisions**

1. **Pure Python Stack**: matplotlib + NetworkX (zero system dependencies)
2. **Layout Intelligence**: Algorithm selection based on graph characteristics  
3. **Visual Compatibility**: Exact color matching and similar styling to GraphViz
4. **Robust Error Handling**: 4-layer fallback chain ensuring operation never fails
5. **Performance Optimized**: Headless matplotlib with memory management
6. **Interface Preservation**: 100% compatible with existing GraphvizGenerator

### 🎯 **Implementation Strategy**

1. **Drop-in Replacement**: New `MatplotlibGenerator` class with identical interface
2. **Gradual Rollout**: Can be tested alongside GraphvizGenerator  
3. **Fallback Safety**: Multiple rendering fallbacks ensure reliability
4. **Visual Quality**: Professional appearance matching current GraphViz output

**PHASE 1.2 ARCHITECTURE DESIGN COMPLETE ✅**
**Ready to proceed to Phase 2: Dependencies & Setup**
