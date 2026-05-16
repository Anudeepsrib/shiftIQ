"""
Interactive dependency graph generator.

Generates D3.js force-directed graphs for migration planning:
- File dependency visualization
- Migration wave calculation
- Interactive exploration
- Export capabilities
"""

import json
import networkx as nx
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional

from ..security import PathSanitizer, SafeCodeAnalyzer


class VisualMigrationPlanner:
    """
    Generate interactive dependency graphs for migration planning.
    
    Features:
    - D3.js force-directed graph
    - Click files to see dependencies
    - Drag to reorder migration sequence
    - Export as JSON/HTML
    
    SECURITY: Graph generation is read-only analysis.
    """
    
    def __init__(self, project_path: Path, allowed_base: Optional[Path] = None):
        """
        Initialize visual migration planner.
        
        Args:
            project_path: Path to project to analyze
            allowed_base: Base directory that paths must stay within (default: current working directory)
        """
        self.project_path = PathSanitizer.sanitize(
            str(project_path),
            allowed_base=allowed_base or Path.cwd()
        )
        self.graph = nx.DiGraph()
        self.code_analyzer = SafeCodeAnalyzer()
    
    def build_dependency_graph(self) -> nx.DiGraph:
        """
        Build dependency graph from codebase.
        
        Security: AST parsing only, no imports executed.
        """
        # Clear existing graph
        self.graph = nx.DiGraph()
        
        # Analyze Python files
        for py_file in self.project_path.rglob('*.py'):
            try:
                analysis = self.code_analyzer.analyze(py_file)
                
                if not analysis.get('parsed'):
                    continue
                
                file_node = str(py_file.relative_to(self.project_path))
                self.graph.add_node(file_node, 
                                 type='file',
                                 size=analysis['line_count'],
                                 complexity=analysis.get('complexity', 0),
                                 functions=len(analysis['functions']),
                                 classes=len(analysis['classes']))
                
                # Add import dependencies
                for imp in analysis['imports']:
                    if isinstance(imp, dict):
                        module = imp.get('module', '')
                        if module and not module.startswith('.'):
                            self.graph.add_edge(file_node, module, 
                                             type='import',
                                             line=imp.get('line', 0))
                            
            except Exception:
                continue
        
        # Analyze JavaScript/TypeScript files
        for js_file in self.project_path.rglob('*'):
            if js_file.suffix in ['.js', '.jsx', '.ts', '.tsx']:
                try:
                    content = js_file.read_text(encoding='utf-8', errors='ignore')
                    file_node = str(js_file.relative_to(self.project_path))
                    
                    # Basic line count
                    line_count = len(content.splitlines())
                    
                    self.graph.add_node(file_node,
                                     type='file',
                                     size=line_count,
                                     complexity=0,
                                     functions=0,
                                     classes=0)
                    
                    # Extract import statements (basic regex)
                    import re
                    import_patterns = [
                        r'import\s+.*?\s+from\s+[\'"]([^\'"]+)[\'"]',
                        r'require\([\'"]([^\'"]+)[\'"]\)',
                        r'import\s+[\'"]([^\'"]+)[\'"]'
                    ]
                    
                    for pattern in import_patterns:
                        matches = re.finditer(pattern, content)
                        for match in matches:
                            module = match.group(1)
                            if module and not module.startswith('.'):
                                self.graph.add_edge(file_node, module,
                                                 type='import',
                                                 line=content[:match.start()].count('\n') + 1)
                
                except Exception:
                    continue
        
        return self.graph
    
    def calculate_migration_waves(self) -> List[List[str]]:
        """
        Determine migration order based on dependencies.
        
        Strategy: Topological sort (migrate dependencies first)
        """
        try:
            # Get only file nodes (exclude external modules)
            file_nodes = [node for node in self.graph.nodes() 
                         if self.graph.nodes[node].get('type') == 'file']
            
            # Create subgraph with only files
            file_subgraph = self.graph.subgraph(file_nodes)
            
            # Topological sort gives dependency-respecting order
            ordered_nodes = list(nx.topological_sort(file_subgraph))
            
            # Group into waves (parallel migration groups)
            waves = []
            current_wave = []
            
            for node in ordered_nodes:
                # Check if all file dependencies are already migrated
                file_deps = [pred for pred in file_subgraph.predecessors(node)
                            if file_subgraph.nodes[pred].get('type') == 'file']
                
                deps_migrated = any(
                    any(node in wave for wave in waves)
                    for dep in file_deps
                )
                
                if not file_deps or deps_migrated:
                    current_wave.append(node)
                else:
                    # Start new wave
                    if current_wave:
                        waves.append(current_wave)
                    current_wave = [node]
            
            if current_wave:
                waves.append(current_wave)
            
            return waves
            
        except nx.NetworkXError:
            # Circular dependency detected - return single file waves
            file_nodes = [node for node in self.graph.nodes()
                         if self.graph.nodes[node].get('type') == 'file']
            return [[node] for node in file_nodes]
    
    def get_graph_statistics(self) -> Dict:
        """
        Get graph statistics for analysis.
        
        Returns:
            Dict with graph metrics
        """
        if not self.graph.nodes():
            return {
                'total_nodes': 0,
                'total_edges': 0,
                'file_nodes': 0,
                'external_nodes': 0,
                'circular_dependencies': False
            }
        
        file_nodes = [node for node in self.graph.nodes()
                      if self.graph.nodes[node].get('type') == 'file']
        external_nodes = [node for node in self.graph.nodes()
                         if self.graph.nodes[node].get('type') != 'file']
        
        # Check for circular dependencies
        try:
            nx.find_cycle(self.graph)
            circular_dependencies = True
        except nx.NetworkXNoCycle:
            circular_dependencies = False
        
        return {
            'total_nodes': self.graph.number_of_nodes(),
            'total_edges': self.graph.number_of_edges(),
            'file_nodes': len(file_nodes),
            'external_nodes': len(external_nodes),
            'circular_dependencies': circular_dependencies,
            'average_degree': sum(dict(self.graph.degree()).values()) / max(self.graph.number_of_nodes(), 1),
            'density': nx.density(self.graph)
        }
    
    def generate_d3_visualization(self, output_path: Path) -> None:
        """
        Generate interactive D3.js visualization.
        
        Args:
            output_path: Path to save HTML visualization
        """
        waves = self.calculate_migration_waves()
        stats = self.get_graph_statistics()
        
        # Convert graph to D3-compatible JSON
        nodes = []
        links = []
        
        for i, node in enumerate(self.graph.nodes()):
            node_data = self.graph.nodes[node]
            
            # Determine which wave this node is in (for files only)
            wave_num = 0
            if node_data.get('type') == 'file':
                for j, wave in enumerate(waves):
                    if node in wave:
                        wave_num = j + 1
                        break
            
            # Determine node type for visualization
            if node_data.get('type') == 'file':
                node_type = 'file'
                group = wave_num
            else:
                node_type = 'external'
                group = 99  # External modules in separate group
            
            nodes.append({
                'id': node,
                'group': group,
                'wave': wave_num,
                'type': node_type,
                'label': Path(node).name if '/' in node or '\\' in node else node,
                'size': node_data.get('size', 0),
                'complexity': node_data.get('complexity', 0),
                'functions': node_data.get('functions', 0),
                'classes': node_data.get('classes', 0)
            })
        
        for source, target in self.graph.edges():
            edge_data = self.graph[source][target]
            
            links.append({
                'source': source,
                'target': target,
                'type': edge_data.get('type', 'dependency'),
                'line': edge_data.get('line', 0)
            })
        
        graph_data = {
            'metadata': {
                'total_nodes': len(nodes),
                'total_links': len(links),
                'waves': len(waves),
                'statistics': stats
            },
            'nodes': nodes,
            'links': links,
            'waves': [
                {
                    'wave': i + 1, 
                    'files': wave,
                    'count': len(wave)
                } for i, wave in enumerate(waves)
            ]
        }
        
        # Generate HTML template with embedded graph data. The page avoids
        # external scripts so local-first usage does not make network calls.
        html_template = self._generate_html_template(graph_data)
        
        # Write to file
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_template)
    
    def _generate_html_template(self, graph_data: Dict) -> str:
        """Generate HTML template for D3.js visualization."""
        return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Migration Dependency Graph</title>
    <meta name="description" content="D3.js-compatible migration graph data rendered without external scripts">
    <style>
        body {{ 
            margin: 0; 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: #f5f5f5;
        }}
        #graph {{ 
            width: 100vw; 
            height: 100vh; 
            position: relative;
        }}
        .node {{ 
            cursor: pointer; 
            stroke: #fff;
            stroke-width: 2px;
        }}
        .node.file {{ fill: #4CAF50; }}
        .node.external {{ fill: #2196F3; }}
        .node:hover {{ stroke-width: 3px; }}
        .link {{ 
            stroke: #999; 
            stroke-opacity: 0.6;
            stroke-width: 2px;
        }}
        .node text {{ 
            font-size: 12px; 
            pointer-events: none; 
            text-anchor: middle;
            fill: #333;
        }}
        #legend {{
            position: absolute;
            top: 20px;
            right: 20px;
            background: white;
            padding: 15px;
            border: 1px solid #ddd;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        #waves {{
            position: absolute;
            top: 20px;
            left: 20px;
            background: white;
            padding: 15px;
            border: 1px solid #ddd;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            max-height: 80vh;
            overflow-y: auto;
            max-width: 300px;
        }}
        .wave-item {{ 
            margin: 10px 0; 
            padding: 8px;
            background: #f9f9f9;
            border-radius: 4px;
        }}
        .wave-header {{
            font-weight: bold;
            color: #333;
            margin-bottom: 5px;
        }}
        .wave-files {{
            font-size: 11px;
            color: #666;
        }}
        .tooltip {{
            position: absolute;
            padding: 10px;
            background: rgba(0, 0, 0, 0.8);
            color: white;
            border-radius: 4px;
            font-size: 12px;
            pointer-events: none;
            opacity: 0;
            transition: opacity 0.3s;
        }}
        h3 {{ margin: 0 0 10px 0; color: #333; }}
        .stats {{ font-size: 12px; color: #666; }}
    </style>
</head>
<body>
    <div id="legend">
        <h3>📊 Graph Statistics</h3>
        <div class="stats">
            Total Nodes: {graph_data['metadata']['total_nodes']}<br>
            Total Links: {graph_data['metadata']['total_links']}<br>
            Migration Waves: {graph_data['metadata']['waves']}<br>
            Circular Dependencies: {graph_data['metadata']['statistics']['circular_dependencies']}
        </div>
        <h3>🎨 Legend</h3>
        <div style="color: #4CAF50;">● Project Files</div>
        <div style="color: #2196F3;">● External Dependencies</div>
    </div>
    
    <div id="waves">
        <h3>🌊 Migration Plan</h3>
        <div id="wave-list"></div>
    </div>
    
    <div id="graph"></div>
    <div class="tooltip"></div>
    
    <script>
        const graphData = {json.dumps(graph_data, indent=2)};

        const graph = document.querySelector("#graph");
        const summary = document.createElement("pre");
        summary.textContent = JSON.stringify(graphData.metadata, null, 2);
        summary.style.padding = "24px";
        summary.style.margin = "0";
        summary.style.whiteSpace = "pre-wrap";
        graph.appendChild(summary);

        const waveList = document.querySelector("#wave-list");
        graphData.waves.forEach((wave) => {{
            const item = document.createElement("div");
            item.className = "wave-item";

            const header = document.createElement("div");
            header.className = "wave-header";
            header.textContent = "Wave " + wave.wave + " (" + wave.count + " files)";
            item.appendChild(header);

            const fileList = document.createElement("div");
            fileList.className = "wave-files";
            wave.files.forEach((file) => {{
                const row = document.createElement("div");
                row.textContent = "- " + file;
                fileList.appendChild(row);
            }});
            item.appendChild(fileList);
            waveList.appendChild(item);
        }});
    </script>
</body>
</html>"""
    
    def export_graph_data(self, output_path: Path) -> None:
        """
        Export graph data as JSON.
        
        Args:
            output_path: Path to save JSON data
        """
        waves = self.calculate_migration_waves()
        stats = self.get_graph_statistics()
        
        # Convert to JSON-serializable format
        graph_data = {
            'metadata': {
                'project_path': str(self.project_path),
                'total_nodes': self.graph.number_of_nodes(),
                'total_edges': self.graph.number_of_edges(),
                'waves': len(waves),
                'statistics': stats
            },
            'nodes': [
                {
                    'id': node,
                    'data': self.graph.nodes[node]
                } for node in self.graph.nodes()
            ],
            'links': [
                {
                    'source': source,
                    'target': target,
                    'data': self.graph[source][target]
                } for source, target in self.graph.edges()
            ],
            'waves': [
                {
                    'wave': i + 1,
                    'files': wave,
                    'count': len(wave)
                } for i, wave in enumerate(waves)
            ]
        }
        
        # Write JSON file
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(graph_data, f, indent=2)
