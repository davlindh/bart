"""In-Memory Knowledge Graph Store with Entity & Relationship Indexing."""

from typing import Any, Dict, List, Optional, Set, Tuple
from pydantic import BaseModel, Field
from src.core.types import DomainType, PermissionLevel, SensitivityLevel


class GraphNode(BaseModel):
    """Semantic graph node containing structured metadata."""
    id: str
    type: str
    domain: DomainType
    label: str
    nav_id: Optional[str] = Field(
        default=None,
        description="NavID-style hierarchical identifier (e.g. 'OPS-Pipeline.DataETL.PipelineZ')",
    )
    properties: Dict[str, Any] = Field(default_factory=dict)
    permission_level: PermissionLevel = Field(default=PermissionLevel.TEAM)
    sensitivity_level: SensitivityLevel = Field(default=SensitivityLevel.STANDARD)
    verification_level: float = Field(default=1.0, ge=0.0, le=1.0)
    last_updated: float = Field(default=0.0)


class GraphEdge(BaseModel):
    """Directed relationship between two graph nodes."""
    source: str
    target: str
    rel_type: str
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    properties: Dict[str, Any] = Field(default_factory=dict)


# ── NavID Utilities ─────────────────────────────────────────────────────
# Migrated from 3.7fmossmorph NavID system (e.g. "EXE-Core.Processors.DualPath")

# Standard NavID prefixes by domain
NAVID_DOMAIN_PREFIX: Dict[DomainType, str] = {
    DomainType.TRUST: "TRS",
    DomainType.KNOWLEDGE: "KNW",
    DomainType.TOOLS: "TLS",
    DomainType.EXCHANGE: "EXC",
    DomainType.INTERACTIONAL_INTERFACE: "INT",
    DomainType.OPERATIONAL: "OPS",
    DomainType.DATA: "DAT",
}


def generate_nav_id(domain: DomainType, node_type: str, label: str) -> str:
    """Generate a NavID-style hierarchical identifier.

    Format: {DOMAIN_PREFIX}-{NodeType}.{Sanitized Label}
    Example: OPS-Process.DataPipelineZ
    """
    prefix = NAVID_DOMAIN_PREFIX.get(domain, "GEN")
    sanitized_type = node_type.strip().replace(" ", "")
    sanitized_label = label.strip().replace(" ", "").replace("_", "")
    # Truncate to keep NavIDs concise
    sanitized_label = sanitized_label[:32]
    return f"{prefix}-{sanitized_type}.{sanitized_label}"


class KnowledgeGraphStore:
    """Core knowledge graph store supporting indexed lookups, multi-hop traversals, and sub-graph extraction."""

    def __init__(self):
        self._nodes: Dict[str, GraphNode] = {}
        self._out_edges: Dict[str, List[GraphEdge]] = {}
        self._in_edges: Dict[str, List[GraphEdge]] = {}
        self._navid_index: Dict[str, str] = {}  # nav_id → node_id

    def add_node(
        self,
        node_id: str,
        node_type: str,
        domain: DomainType,
        label: str,
        properties: Optional[Dict[str, Any]] = None,
        permission_level: PermissionLevel = PermissionLevel.TEAM,
        sensitivity_level: SensitivityLevel = SensitivityLevel.STANDARD,
        verification_level: float = 1.0,
        nav_id: Optional[str] = None,
    ) -> GraphNode:
        """Registers a node into the graph store."""
        # Auto-generate NavID if not provided
        resolved_nav_id = nav_id or generate_nav_id(domain, node_type, label)

        node = GraphNode(
            id=node_id,
            type=node_type,
            domain=domain,
            label=label,
            nav_id=resolved_nav_id,
            properties=properties or {},
            permission_level=permission_level,
            sensitivity_level=sensitivity_level,
            verification_level=verification_level,
        )
        self._nodes[node_id] = node
        if node_id not in self._out_edges:
            self._out_edges[node_id] = []
        if node_id not in self._in_edges:
            self._in_edges[node_id] = []
        # Index by NavID for O(1) lookups
        if resolved_nav_id:
            self._navid_index[resolved_nav_id] = node_id
        return node

    def add_edge(
        self,
        source: str,
        target: str,
        rel_type: str,
        confidence: float = 1.0,
        properties: Optional[Dict[str, Any]] = None,
    ) -> GraphEdge:
        """Registers a directed relationship edge between source and target."""
        if source not in self._nodes or target not in self._nodes:
            # Auto-stub placeholder nodes if missing
            if source not in self._nodes:
                self.add_node(source, "Entity", DomainType.OPERATIONAL, source)
            if target not in self._nodes:
                self.add_node(target, "Entity", DomainType.OPERATIONAL, target)

        edge = GraphEdge(
            source=source,
            target=target,
            rel_type=rel_type,
            confidence=confidence,
            properties=properties or {},
        )
        self._out_edges[source].append(edge)
        self._in_edges[target].append(edge)
        return edge

    def get_node(self, node_id: str) -> Optional[GraphNode]:
        """Retrieves a single node by ID."""
        return self._nodes.get(node_id)

    def get_node_by_navid(self, nav_id: str) -> Optional[GraphNode]:
        """Retrieves a node by its NavID hierarchical identifier."""
        node_id = self._navid_index.get(nav_id)
        if node_id:
            return self._nodes.get(node_id)
        return None

    def search_by_navid_prefix(self, prefix: str) -> List[GraphNode]:
        """Find all nodes whose NavID starts with the given prefix.

        Example: search_by_navid_prefix("OPS-") returns all Operational domain nodes.
        """
        results: List[GraphNode] = []
        for nav_id, node_id in self._navid_index.items():
            if nav_id.startswith(prefix):
                node = self._nodes.get(node_id)
                if node:
                    results.append(node)
        return results

    def get_all_nodes(self) -> List[GraphNode]:
        """Returns all registered nodes."""
        return list(self._nodes.values())

    def get_all_edges(self) -> List[GraphEdge]:
        """Returns all registered edges."""
        edges = []
        for edge_list in self._out_edges.values():
            edges.extend(edge_list)
        return edges

    def search_nodes(
        self,
        query: str,
        domain: Optional[DomainType] = None,
        limit: int = 10,
    ) -> List[GraphNode]:
        """Performs lexical search across labels, types, NavIDs, and properties."""
        q = query.lower()
        results: List[Tuple[float, GraphNode]] = []
        for node in self._nodes.values():
            if domain and node.domain != domain:
                continue
            score = 0.0
            if q in node.label.lower():
                score += 1.0
            if q in node.id.lower():
                score += 0.8
            if q in node.type.lower():
                score += 0.5
            if node.nav_id and q in node.nav_id.lower():
                score += 0.9
            for val in node.properties.values():
                if q in str(val).lower():
                    score += 0.3
            if score > 0.0:
                results.append((score, node))

        results.sort(key=lambda x: x[0], reverse=True)
        return [node for _, node in results[:limit]]

    def traverse_subgraph(
        self,
        focal_node_id: str,
        depth: int = 1,
        allowed_domains: Optional[List[DomainType]] = None,
    ) -> Tuple[List[GraphNode], List[GraphEdge], Dict[str, int]]:
        """
        Traverses the graph outwards from focal_node_id up to depth hops.
        Returns (nodes, edges, node_distance_map).
        """
        if focal_node_id not in self._nodes:
            return [], [], {}

        visited_nodes: Set[str] = {focal_node_id}
        node_distances: Dict[str, int] = {focal_node_id: 0}
        collected_edges: List[GraphEdge] = []
        current_layer: Set[str] = {focal_node_id}

        for current_depth in range(1, depth + 1):
            next_layer: Set[str] = set()
            for u in current_layer:
                # Traverse outgoing edges
                for edge in self._out_edges.get(u, []):
                    v = edge.target
                    target_node = self._nodes.get(v)
                    if not target_node:
                        continue
                    if allowed_domains and target_node.domain not in allowed_domains:
                        continue
                    collected_edges.append(edge)
                    if v not in visited_nodes:
                        visited_nodes.add(v)
                        node_distances[v] = current_depth
                        next_layer.add(v)

                # Traverse incoming edges (bidirectional traversal for context relevance)
                for edge in self._in_edges.get(u, []):
                    v = edge.source
                    source_node = self._nodes.get(v)
                    if not source_node:
                        continue
                    if allowed_domains and source_node.domain not in allowed_domains:
                        continue
                    collected_edges.append(edge)
                    if v not in visited_nodes:
                        visited_nodes.add(v)
                        node_distances[v] = current_depth
                        next_layer.add(v)

            current_layer = next_layer
            if not current_layer:
                break

        nodes = [self._nodes[nid] for nid in visited_nodes if nid in self._nodes]
        # Deduplicate edges
        deduped_edges = []
        seen_edges = set()
        for edge in collected_edges:
            key = (edge.source, edge.target, edge.rel_type)
            if key not in seen_edges:
                seen_edges.add(key)
                deduped_edges.append(edge)

        return nodes, deduped_edges, node_distances

