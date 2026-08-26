"""Graph MCP Server exposing tools for Knowledge Graph queries, entity inspection and mutations."""

from typing import Any, Dict, List, Optional
from src.core.types import DomainType, PermissionLevel, SensitivityLevel
from src.graph.graph_store import KnowledgeGraphStore


class GraphMcpServer:
    """MCP Server providing tool handlers for graph operations."""

    def __init__(self, store: KnowledgeGraphStore):
        self.store = store

    def get_entity(self, entity_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves a single entity node and its properties from the graph."""
        node = self.store.get_node(entity_id)
        return node.model_dump() if node else None

    def search_nodes(self, query: str, domain: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """Searches the knowledge graph by keyword, entity label, or property value."""
        dom = DomainType(domain) if domain else None
        nodes = self.store.search_nodes(query=query, domain=dom, limit=limit)
        return [n.model_dump() for n in nodes]

    def get_relationships(self, entity_id: str, direction: str = "both") -> List[Dict[str, Any]]:
        """Returns all directed incoming, outgoing, or bidirectional edges for an entity."""
        all_edges = self.store.get_all_edges()
        results = []
        for e in all_edges:
            if direction in ["outgoing", "both"] and e.source == entity_id:
                results.append(e.model_dump())
            elif direction in ["incoming", "both"] and e.target == entity_id:
                results.append(e.model_dump())
        return results

    def add_entity(
        self,
        node_id: str,
        node_type: str,
        domain: str,
        label: str,
        properties: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Registers a new entity node into the knowledge graph."""
        dom = DomainType(domain)
        node = self.store.add_node(
            node_id=node_id,
            node_type=node_type,
            domain=dom,
            label=label,
            properties=properties or {},
        )
        return node.model_dump()

    def add_relationship(
        self,
        source: str,
        target: str,
        rel_type: str,
        confidence: float = 1.0,
        properties: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Registers a directed relationship edge between two entities."""
        edge = self.store.add_edge(
            source=source,
            target=target,
            rel_type=rel_type,
            confidence=confidence,
            properties=properties or {},
        )
        return edge.model_dump()
