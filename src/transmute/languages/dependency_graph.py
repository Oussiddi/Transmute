"""
Dependency graph for tracking code dependencies and relationships.

Provides dependency analysis, circular dependency detection, and impact analysis.
"""

from typing import Dict, Any, List, Optional, Set, Tuple
from collections import defaultdict, deque
from dataclasses import dataclass, field
from enum import Enum

from transmute.utils.logger import get_logger

logger = get_logger(__name__)


class DependencyType(Enum):
    """Types of dependencies."""
    IMPORT = "import"           # Module/file import
    INHERITANCE = "inheritance" # Class inheritance
    CALLS = "calls"            # Function calls
    USES = "uses"              # Variable/constant usage
    COMPOSITION = "composition" # Class composition
    AGGREGATION = "aggregation" # Class aggregation


@dataclass
class DependencyEdge:
    """
    Represents a dependency edge between two nodes.
    """
    source: str
    target: str
    dep_type: DependencyType
    weight: int = 1
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __hash__(self):
        """Make edge hashable."""
        return hash((self.source, self.target, self.dep_type))
    
    def __eq__(self, other):
        """Check edge equality."""
        if not isinstance(other, DependencyEdge):
            return False
        return (
            self.source == other.source and
            self.target == other.target and
            self.dep_type == other.dep_type
        )


class DependencyGraph:
    """
    Dependency graph for tracking relationships between code elements.
    
    Features:
    - Multiple dependency types
    - Circular dependency detection
    - Topological sorting
    - Impact analysis
    - Dependency metrics
    """
    
    def __init__(self):
        """Initialize dependency graph."""
        self.nodes: Set[str] = set()
        self.edges: Set[DependencyEdge] = set()
        
        # Adjacency lists for fast lookups
        self._outgoing: Dict[str, List[DependencyEdge]] = defaultdict(list)
        self._incoming: Dict[str, List[DependencyEdge]] = defaultdict(list)
        
        logger.debug("DependencyGraph initialized")
    
    def add_node(self, node: str) -> None:
        """
        Add a node to the graph.
        
        Args:
            node: Node identifier (e.g., module name, class name)
            
        Example:
            >>> graph.add_node("my_module")
        """
        self.nodes.add(node)
        logger.debug(f"Added node: {node}")
    
    def add_dependency(
        self,
        source: str,
        target: str,
        dep_type: DependencyType,
        weight: int = 1,
        **metadata
    ) -> None:
        """
        Add a dependency edge.
        
        Args:
            source: Source node
            target: Target node
            dep_type: Type of dependency
            weight: Edge weight (default 1)
            **metadata: Additional edge metadata
            
        Example:
            >>> graph.add_dependency("module_a", "module_b", DependencyType.IMPORT)
        """
        # Add nodes if not exist
        self.add_node(source)
        self.add_node(target)
        
        # Create edge
        edge = DependencyEdge(
            source=source,
            target=target,
            dep_type=dep_type,
            weight=weight,
            metadata=metadata
        )
        
        # Add to sets
        self.edges.add(edge)
        self._outgoing[source].append(edge)
        self._incoming[target].append(edge)
        
        logger.debug(f"Added dependency: {source} -> {target} ({dep_type.value})")
    
    def get_dependencies(
        self,
        node: str,
        dep_type: Optional[DependencyType] = None
    ) -> List[str]:
        """
        Get all dependencies (outgoing edges) of a node.
        
        Args:
            node: Node identifier
            dep_type: Optional filter by dependency type
            
        Returns:
            List of dependent nodes
            
        Example:
            >>> deps = graph.get_dependencies("my_module")
            >>> imports = graph.get_dependencies("my_module", DependencyType.IMPORT)
        """
        edges = self._outgoing.get(node, [])
        
        if dep_type:
            edges = [e for e in edges if e.dep_type == dep_type]
        
        return [edge.target for edge in edges]
    
    def get_dependents(
        self,
        node: str,
        dep_type: Optional[DependencyType] = None
    ) -> List[str]:
        """
        Get all dependents (incoming edges) of a node.
        
        Args:
            node: Node identifier
            dep_type: Optional filter by dependency type
            
        Returns:
            List of nodes that depend on this node
            
        Example:
            >>> dependents = graph.get_dependents("my_module")
        """
        edges = self._incoming.get(node, [])
        
        if dep_type:
            edges = [e for e in edges if e.dep_type == dep_type]
        
        return [edge.source for edge in edges]
    
    def find_circular_dependencies(self) -> List[List[str]]:
        """
        Find all circular dependencies (cycles) in the graph.
        
        Returns:
            List of cycles, each cycle is a list of nodes
            
        Example:
            >>> cycles = graph.find_circular_dependencies()
            >>> for cycle in cycles:
            ...     print(f"Circular: {' -> '.join(cycle)}")
        """
        cycles = []
        visited = set()
        path = []
        path_set = set()
        
        def dfs(node: str):
            if node in path_set:
                # Found a cycle
                cycle_start = path.index(node)
                cycle = path[cycle_start:] + [node]
                cycles.append(cycle)
                return
            
            if node in visited:
                return
            
            visited.add(node)
            path.append(node)
            path_set.add(node)
            
            # Visit dependencies
            for dep in self.get_dependencies(node):
                dfs(dep)
            
            path.pop()
            path_set.remove(node)
        
        # Start DFS from each node
        for node in self.nodes:
            if node not in visited:
                dfs(node)
        
        logger.info(f"Found {len(cycles)} circular dependencies")
        
        return cycles
    
    def topological_sort(self) -> Optional[List[str]]:
        """
        Get topological sort of nodes (dependency order).
        
        Returns:
            Ordered list of nodes, or None if cycles exist
            
        Example:
            >>> order = graph.topological_sort()
            >>> if order:
            ...     print(f"Build order: {order}")
        """
        # Calculate in-degrees
        in_degree = {node: 0 for node in self.nodes}
        
        for edge in self.edges:
            in_degree[edge.target] += 1
        
        # Queue with nodes that have no dependencies
        queue = deque([node for node, degree in in_degree.items() if degree == 0])
        result = []
        
        while queue:
            node = queue.popleft()
            result.append(node)
            
            # Reduce in-degree for dependents
            for dep in self.get_dependencies(node):
                in_degree[dep] -= 1
                if in_degree[dep] == 0:
                    queue.append(dep)
        
        # Check if all nodes processed (no cycles)
        if len(result) == len(self.nodes):
            logger.info("Topological sort successful")
            return result
        else:
            logger.warning("Topological sort failed - circular dependencies exist")
            return None
    
    def get_impact_analysis(self, node: str, max_depth: int = -1) -> Dict[str, Any]:
        """
        Analyze impact of changing a node.
        
        Args:
            node: Node to analyze
            max_depth: Maximum depth to traverse (-1 for unlimited)
            
        Returns:
            Impact analysis results
            
        Example:
            >>> impact = graph.get_impact_analysis("core_module")
            >>> print(f"Would affect {impact['affected_count']} modules")
        """
        affected = set()
        visited = set()
        
        def bfs(start: str, depth: int = 0):
            if max_depth >= 0 and depth > max_depth:
                return
            
            if start in visited:
                return
            
            visited.add(start)
            affected.add(start)
            
            # Visit all dependents
            for dependent in self.get_dependents(start):
                bfs(dependent, depth + 1)
        
        bfs(node)
        affected.remove(node)  # Don't count the node itself
        
        return {
            'node': node,
            'directly_affected': len(self.get_dependents(node)),
            'total_affected': len(affected),
            'affected_nodes': list(affected),
            'impact_depth': self._calculate_max_depth(node)
        }
    
    def _calculate_max_depth(self, node: str) -> int:
        """Calculate maximum depth of dependency tree."""
        max_depth = 0
        visited = set()
        
        def dfs(n: str, depth: int):
            nonlocal max_depth
            
            if n in visited:
                return
            
            visited.add(n)
            max_depth = max(max_depth, depth)
            
            for dep in self.get_dependents(n):
                dfs(dep, depth + 1)
        
        dfs(node, 0)
        
        return max_depth
    
    def get_leaf_nodes(self) -> List[str]:
        """
        Get leaf nodes (nodes with no dependencies).
        
        Returns:
            List of leaf nodes
            
        Example:
            >>> leaves = graph.get_leaf_nodes()
        """
        return [
            node for node in self.nodes
            if len(self.get_dependencies(node)) == 0
        ]
    
    def get_root_nodes(self) -> List[str]:
        """
        Get root nodes (nodes with no dependents).
        
        Returns:
            List of root nodes
            
        Example:
            >>> roots = graph.get_root_nodes()
        """
        return [
            node for node in self.nodes
            if len(self.get_dependents(node)) == 0
        ]
    
    def get_strongly_connected_components(self) -> List[Set[str]]:
        """
        Find strongly connected components (groups of mutually dependent nodes).
        
        Returns:
            List of strongly connected components
            
        Example:
            >>> components = graph.get_strongly_connected_components()
            >>> for comp in components:
            ...     if len(comp) > 1:
            ...         print(f"Tightly coupled: {comp}")
        """
        # Tarjan's algorithm
        index_counter = [0]
        stack = []
        lowlink = {}
        index = {}
        on_stack = set()
        components = []
        
        def strongconnect(node: str):
            index[node] = index_counter[0]
            lowlink[node] = index_counter[0]
            index_counter[0] += 1
            stack.append(node)
            on_stack.add(node)
            
            # Visit dependencies
            for dep in self.get_dependencies(node):
                if dep not in index:
                    strongconnect(dep)
                    lowlink[node] = min(lowlink[node], lowlink[dep])
                elif dep in on_stack:
                    lowlink[node] = min(lowlink[node], index[dep])
            
            # If node is a root, pop the stack to create component
            if lowlink[node] == index[node]:
                component = set()
                while True:
                    w = stack.pop()
                    on_stack.remove(w)
                    component.add(w)
                    if w == node:
                        break
                components.append(component)
        
        for node in self.nodes:
            if node not in index:
                strongconnect(node)
        
        return components
    
    def calculate_metrics(self) -> Dict[str, Any]:
        """
        Calculate graph metrics.
        
        Returns:
            Dictionary of metrics
            
        Example:
            >>> metrics = graph.calculate_metrics()
            >>> print(f"Coupling: {metrics['average_dependencies']:.2f}")
        """
        if not self.nodes:
            return {
                'node_count': 0,
                'edge_count': 0,
                'average_dependencies': 0,
                'max_dependencies': 0,
                'has_cycles': False
            }
        
        dep_counts = [len(self.get_dependencies(node)) for node in self.nodes]
        
        return {
            'node_count': len(self.nodes),
            'edge_count': len(self.edges),
            'average_dependencies': sum(dep_counts) / len(self.nodes),
            'max_dependencies': max(dep_counts) if dep_counts else 0,
            'leaf_count': len(self.get_leaf_nodes()),
            'root_count': len(self.get_root_nodes()),
            'has_cycles': len(self.find_circular_dependencies()) > 0,
            'strongly_connected_components': len(self.get_strongly_connected_components())
        }
    
    def export_to_dot(self, output_file: Optional[str] = None) -> str:
        """
        Export graph to DOT format (Graphviz).
        
        Args:
            output_file: Optional file to write to
            
        Returns:
            DOT format string
            
        Example:
            >>> dot = graph.export_to_dot("dependencies.dot")
        """
        lines = ['digraph Dependencies {']
        lines.append('    rankdir=LR;')
        lines.append('    node [shape=box];')
        lines.append('')
        
        # Add nodes
        for node in self.nodes:
            lines.append(f'    "{node}";')
        
        lines.append('')
        
        # Add edges
        for edge in self.edges:
            label = edge.dep_type.value
            lines.append(f'    "{edge.source}" -> "{edge.target}" [label="{label}"];')
        
        lines.append('}')
        
        dot_string = '\n'.join(lines)
        
        if output_file:
            with open(output_file, 'w') as f:
                f.write(dot_string)
            logger.info(f"Exported graph to {output_file}")
        
        return dot_string
    
    def get_critical_nodes(self, top_n: int = 10) -> List[Tuple[str, int]]:
        """
        Get most critical nodes (highest impact if removed).
        
        Args:
            top_n: Number of nodes to return
            
        Returns:
            List of (node, impact_score) tuples
            
        Example:
            >>> critical = graph.get_critical_nodes(5)
            >>> for node, score in critical:
            ...     print(f"{node}: impact {score}")
        """
        node_scores = []
        
        for node in self.nodes:
            # Impact = number of transitive dependents
            impact = self.get_impact_analysis(node)
            score = impact['total_affected']
            node_scores.append((node, score))
        
        # Sort by score descending
        node_scores.sort(key=lambda x: x[1], reverse=True)
        
        return node_scores[:top_n]