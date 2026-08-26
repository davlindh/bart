"""Graph query utilities, graph centrality algorithms, and dependency path finders."""

from typing import Dict, List, Optional
from src.core.types import DomainType
from src.graph.graph_store import GraphEdge, GraphNode, KnowledgeGraphStore


class GraphQueryEngine:
    """Specialized graph queries for organizational analysis."""

    def __init__(self, store: KnowledgeGraphStore):
        self.store = store

    def find_dependencies(self, node_id: str, max_depth: int = 2) -> List[GraphNode]:
        """Finds all upstream dependency nodes for a given entity."""
        nodes, _, _ = self.store.traverse_subgraph(node_id, depth=max_depth)
        return [n for n in nodes if n.id != node_id]

    def calculate_bottleneck_scores(self) -> Dict[str, float]:
        """Computes in-degree dependency bottleneck scores across nodes."""
        in_counts: Dict[str, int] = {}
        for edge in self.store.get_all_edges():
            if edge.rel_type in ["DEPENDS_ON", "BLOCKED_BY", "MEASURED_BY", "REQUIRES"]:
                in_counts[edge.target] = in_counts.get(edge.target, 0) + 1

        max_count = max(in_counts.values()) if in_counts else 1
        return {nid: count / max_count for nid, count in in_counts.items()}

    def get_domain_clusters(self) -> Dict[DomainType, List[GraphNode]]:
        """Groups all nodes by functional domain."""
        clusters: Dict[DomainType, List[GraphNode]] = {}
        for node in self.store.get_all_nodes():
            if node.domain not in clusters:
                clusters[node.domain] = []
            clusters[node.domain].append(node)
        return clusters
