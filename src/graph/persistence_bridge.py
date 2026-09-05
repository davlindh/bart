"""Graph Persistence Bridge: Self-preservation engine for Universal ERD, Projects & Agent States.

Backed by SQLite with Write-Ahead Logging (WAL) mode for crash resilience and zero data loss.
"""

import os
import json
import sqlite3
import hashlib
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from contextlib import contextmanager

from ..core.precognition import ProjectCheckpoint, ProjectIntent, PreCognitionTrajectory
from .universal_erd import UniversalERDGraph


class GraphPersistenceBridge:
    """Provides atomic disk persistence and restoration for Universal ERD and Project states."""

    DEFAULT_STORAGE_DIR = Path(".antigravity/storage/projects")

    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            storage_dir = Path(os.getcwd()) / self.DEFAULT_STORAGE_DIR
            storage_dir.mkdir(parents=True, exist_ok=True)
            self.db_path = str(storage_dir / "project_persistence.db")
        else:
            self.db_path = db_path
            Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

        self._init_db()

    @contextmanager
    def _connection(self):
        """Context manager that yields an open SQLite connection and closes it cleanly."""
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        conn.execute("PRAGMA journal_mode = WAL;")
        conn.execute("PRAGMA synchronous = NORMAL;")
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def _init_db(self) -> None:
        """Initializes database tables for checkpoints, graph entities, and agent memories."""
        with self._connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS project_checkpoints (
                    checkpoint_id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    intent_json TEXT,
                    node_count INTEGER NOT NULL DEFAULT 0,
                    edge_count INTEGER NOT NULL DEFAULT 0,
                    variable_count INTEGER NOT NULL DEFAULT 0,
                    agent_states_json TEXT,
                    erd_snapshot_json TEXT NOT NULL,
                    trajectory_snapshot_json TEXT,
                    checksum_sha256 TEXT NOT NULL,
                    trigger_source TEXT DEFAULT 'manual'
                );
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_checkpoints_project 
                ON project_checkpoints (project_id, timestamp DESC);
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS persistent_agent_memory (
                    agent_name TEXT NOT NULL,
                    project_id TEXT NOT NULL,
                    memory_key TEXT NOT NULL,
                    memory_value_json TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    PRIMARY KEY (agent_name, project_id, memory_key)
                );
            """)
            conn.commit()

            # Migration-safe: add trigger_source column if missing
            try:
                conn.execute("SELECT trigger_source FROM project_checkpoints LIMIT 1;")
            except sqlite3.OperationalError:
                conn.execute("ALTER TABLE project_checkpoints ADD COLUMN trigger_source TEXT DEFAULT 'manual';")
                conn.commit()

    def save_checkpoint(
        self,
        project_id: str,
        erd_graph: UniversalERDGraph,
        intent: Optional[ProjectIntent] = None,
        agent_states: Optional[Dict[str, Any]] = None,
        trajectory: Optional[PreCognitionTrajectory] = None,
        checkpoint_id: Optional[str] = None,
        trigger_source: str = "manual",
    ) -> ProjectCheckpoint:
        """Atomically serializes graph, intent, agent states, and trajectory to SQLite."""
        ts = datetime.utcnow().isoformat()
        cid = checkpoint_id or f"chk_{project_id}_{int(datetime.utcnow().timestamp() * 1000)}_{uuid.uuid4().hex[:4]}"

        erd_dict = erd_graph.to_dict() if hasattr(erd_graph, "to_dict") else {}
        node_count = len(erd_dict.get("nodes", []))
        edge_count = len(erd_dict.get("edges", []))
        agent_states = agent_states or {}

        intent_json = intent.model_dump_json() if intent else None
        agent_states_json = json.dumps(agent_states, ensure_ascii=False)
        erd_snapshot_json = json.dumps(erd_dict, ensure_ascii=False)
        trajectory_json = trajectory.model_dump_json() if trajectory else None

        # Compute SHA256 checksum for data integrity verification
        hasher = hashlib.sha256()
        hasher.update(cid.encode("utf-8"))
        hasher.update(erd_snapshot_json.encode("utf-8"))
        if intent_json:
            hasher.update(intent_json.encode("utf-8"))
        checksum = hasher.hexdigest()

        with self._connection() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO project_checkpoints (
                    checkpoint_id, project_id, timestamp, intent_json,
                    node_count, edge_count, variable_count, agent_states_json,
                    erd_snapshot_json, trajectory_snapshot_json, checksum_sha256,
                    trigger_source
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """, (
                cid, project_id, ts, intent_json,
                node_count, edge_count, len(agent_states), agent_states_json,
                erd_snapshot_json, trajectory_json, checksum, trigger_source
            ))
            conn.commit()

        return ProjectCheckpoint(
            checkpoint_id=cid,
            project_id=project_id,
            timestamp=ts,
            intent=intent,
            node_count=node_count,
            edge_count=edge_count,
            variable_count=len(agent_states),
            agent_states=agent_states,
            erd_snapshot=erd_dict,
            trajectory_snapshot=trajectory,
            checksum_sha256=checksum,
            has_trajectory=trajectory is not None,
            trigger_source=trigger_source
        )

    def restore_checkpoint(
        self,
        checkpoint_id: Optional[str] = None,
        project_id: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """Restores full project state, rehydrating the Universal ERD Graph and intent."""
        with self._connection() as conn:
            if checkpoint_id:
                cursor = conn.execute(
                    "SELECT * FROM project_checkpoints WHERE checkpoint_id = ?;",
                    (checkpoint_id,)
                )
            elif project_id:
                cursor = conn.execute(
                    "SELECT * FROM project_checkpoints WHERE project_id = ? ORDER BY timestamp DESC LIMIT 1;",
                    (project_id,)
                )
            else:
                return None

            row = cursor.fetchone()
            if not row:
                return None

        erd_dict = json.loads(row["erd_snapshot_json"])
        erd_graph = UniversalERDGraph.from_dict(erd_dict) if hasattr(UniversalERDGraph, "from_dict") else UniversalERDGraph()

        if not hasattr(UniversalERDGraph, "from_dict"):
            for n in erd_dict.get("nodes", []):
                erd_graph.add_node(
                    node_id=n.get("id"),
                    label=n.get("label", ""),
                    node_type=n.get("type", "Generic"),
                    domain=n.get("domain", "Operational"),
                    metadata=n.get("metadata", {})
                )
            for e in erd_dict.get("edges", []):
                erd_graph.add_edge(
                    source_id=e.get("source"),
                    target_id=e.get("target"),
                    relation=e.get("relation", "CONNECTS_TO"),
                    weight=e.get("weight", 1.0)
                )

        intent = ProjectIntent.model_validate_json(row["intent_json"]) if row["intent_json"] else None
        agent_states = json.loads(row["agent_states_json"]) if row["agent_states_json"] else {}
        trajectory = PreCognitionTrajectory.model_validate_json(row["trajectory_snapshot_json"]) if row["trajectory_snapshot_json"] else None

        return {
            "checkpoint_id": row["checkpoint_id"],
            "project_id": row["project_id"],
            "timestamp": row["timestamp"],
            "erd_graph": erd_graph,
            "intent": intent,
            "agent_states": agent_states,
            "trajectory": trajectory,
            "checksum_sha256": row["checksum_sha256"],
            "trigger_source": row["trigger_source"] if "trigger_source" in row.keys() else "manual",
        }

    def list_checkpoints(self, project_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Returns catalog of all saved checkpoints."""
        query = "SELECT checkpoint_id, project_id, timestamp, node_count, edge_count, checksum_sha256, trajectory_snapshot_json, trigger_source FROM project_checkpoints"
        params: List[Any] = []
        if project_id:
            query += " WHERE project_id = ? ORDER BY timestamp DESC;"
            params.append(project_id)
        else:
            query += " ORDER BY timestamp DESC;"

        with self._connection() as conn:
            rows = conn.execute(query, params).fetchall()
            results = []
            for r in rows:
                d = dict(r)
                raw_traj = d.pop("trajectory_snapshot_json", None)
                d["has_trajectory"] = bool(raw_traj)
                if raw_traj:
                    try:
                        d["trajectory_snapshot"] = json.loads(raw_traj)
                    except Exception:
                        d["trajectory_snapshot"] = None
                else:
                    d["trajectory_snapshot"] = None
                results.append(d)
            return results

    def prune_checkpoints(self, project_id: str, keep_last: int = 20) -> int:
        """Removes old checkpoints, keeping only the most recent `keep_last` per project."""
        with self._connection() as conn:
            # Count total
            total = conn.execute(
                "SELECT COUNT(*) FROM project_checkpoints WHERE project_id = ?;",
                (project_id,)
            ).fetchone()[0]

            if total <= keep_last:
                return 0

            # Get IDs to keep
            keep_ids = [
                row[0] for row in conn.execute(
                    "SELECT checkpoint_id FROM project_checkpoints WHERE project_id = ? ORDER BY timestamp DESC LIMIT ?;",
                    (project_id, keep_last)
                ).fetchall()
            ]

            if not keep_ids:
                return 0

            placeholders = ",".join("?" * len(keep_ids))
            cursor = conn.execute(
                f"DELETE FROM project_checkpoints WHERE project_id = ? AND checkpoint_id NOT IN ({placeholders});",
                [project_id] + keep_ids
            )
            deleted = cursor.rowcount
            conn.commit()
            return deleted

    def diff_checkpoints(self, checkpoint_id_a: str, checkpoint_id_b: str) -> Dict[str, Any]:
        """Computes structural and semantic diff between two checkpoint snapshots."""
        state_a = self.restore_checkpoint(checkpoint_id=checkpoint_id_a)
        state_b = self.restore_checkpoint(checkpoint_id=checkpoint_id_b)

        if not state_a or not state_b:
            return {"error": "One or both checkpoints not found"}

        erd_a = state_a["erd_graph"].to_dict() if hasattr(state_a["erd_graph"], "to_dict") else {}
        erd_b = state_b["erd_graph"].to_dict() if hasattr(state_b["erd_graph"], "to_dict") else {}

        nodes_a = {n["id"] for n in erd_a.get("nodes", [])}
        nodes_b = {n["id"] for n in erd_b.get("nodes", [])}

        edges_a = {(e["source"], e["target"]) for e in erd_a.get("edges", [])}
        edges_b = {(e["source"], e["target"]) for e in erd_b.get("edges", [])}

        # Intent drift
        intent_a = state_a.get("intent")
        intent_b = state_b.get("intent")
        intent_drift = None
        if intent_a and intent_b and intent_a.mandate != intent_b.mandate:
            intent_drift = f"'{intent_a.mandate}' → '{intent_b.mandate}'"
        elif intent_a and not intent_b:
            intent_drift = f"Intent removed (was: '{intent_a.mandate}')"
        elif not intent_a and intent_b:
            intent_drift = f"Intent added: '{intent_b.mandate}'"

        # Agent state deltas
        agent_a = state_a.get("agent_states", {})
        agent_b = state_b.get("agent_states", {})
        agent_deltas = {}
        all_keys = set(list(agent_a.keys()) + list(agent_b.keys()))
        for k in all_keys:
            val_a = agent_a.get(k)
            val_b = agent_b.get(k)
            if val_a != val_b:
                agent_deltas[k] = {"from": val_a, "to": val_b}

        return {
            "checkpoint_a": checkpoint_id_a,
            "checkpoint_b": checkpoint_id_b,
            "timestamp_a": state_a.get("timestamp"),
            "timestamp_b": state_b.get("timestamp"),
            "nodes_added": sorted(list(nodes_b - nodes_a)),
            "nodes_removed": sorted(list(nodes_a - nodes_b)),
            "nodes_unchanged": len(nodes_a & nodes_b),
            "edges_added": len(edges_b - edges_a),
            "edges_removed": len(edges_a - edges_b),
            "intent_drift": intent_drift,
            "agent_state_deltas": agent_deltas,
        }

    def save_agent_memory(self, agent_name: str, project_id: str, key: str, value: Any) -> None:
        """Persists granular agent memory key-value pair."""
        ts = datetime.utcnow().isoformat()
        val_json = json.dumps(value, ensure_ascii=False)
        with self._connection() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO persistent_agent_memory (
                    agent_name, project_id, memory_key, memory_value_json, updated_at
                ) VALUES (?, ?, ?, ?, ?);
            """, (agent_name, project_id, key, val_json, ts))
            conn.commit()

    def get_agent_memory(self, agent_name: str, project_id: str, key: str) -> Optional[Any]:
        """Retrieves persisted agent memory value."""
        with self._connection() as conn:
            row = conn.execute("""
                SELECT memory_value_json FROM persistent_agent_memory
                WHERE agent_name = ? AND project_id = ? AND memory_key = ?;
            """, (agent_name, project_id, key)).fetchone()
            if row:
                return json.loads(row["memory_value_json"])
            return None

