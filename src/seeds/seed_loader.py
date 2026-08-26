"""Seed Data Loader hydrating the KnowledgeGraphStore from initial knowledge specifications."""

import json
from pathlib import Path
from typing import Optional
from src.core.types import DomainType, PermissionLevel, SensitivityLevel
from src.graph.graph_store import KnowledgeGraphStore


class SeedDataLoader:
    """Loads domain models and seed scenario graph data into memory."""

    DEFAULT_SEED_FILE = Path(__file__).parent / "initial_knowledge.json"

    @classmethod
    def load_seed_graph(
        cls,
        store: Optional[KnowledgeGraphStore] = None,
        seed_file_path: Optional[Path] = None,
    ) -> KnowledgeGraphStore:
        """Parses the JSON seed dataset and registers all nodes and relationship edges."""
        graph = store or KnowledgeGraphStore()
        file_path = seed_file_path or cls.DEFAULT_SEED_FILE

        if not file_path.exists():
            raise FileNotFoundError(f"Seed file not found at: {file_path}")

        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # 1. Register Domains
        for d in data.get("domains", []):
            graph.add_node(
                node_id=d["id"],
                node_type=d.get("type", "Domain"),
                domain=DomainType(d.get("domain", "Operational")),
                label=d.get("label", d["id"]),
                properties=d.get("properties", {}),
                permission_level=PermissionLevel.PUBLIC,
            )

        # 2. Register Nodes
        for n in data.get("nodes", []):
            graph.add_node(
                node_id=n["id"],
                node_type=n.get("type", "Entity"),
                domain=DomainType(n.get("domain", "Operational")),
                label=n.get("label", n["id"]),
                properties=n.get("properties", {}),
                permission_level=PermissionLevel.TEAM,
                sensitivity_level=SensitivityLevel.STANDARD,
                verification_level=1.0,
            )

        # 3. Register Directed Relationship Edges
        for e in data.get("edges", []):
            graph.add_edge(
                source=e["source"],
                target=e["target"],
                rel_type=e["rel_type"],
                confidence=float(e.get("confidence", 1.0)),
                properties=e.get("properties", {}),
            )

        return graph
