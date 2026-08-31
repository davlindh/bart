"""Unit tests for Tier 1: SQLiteEngine, DiskStateStore, VariableSerializer, and PersistenceManager."""

import os
import sqlite3
import tempfile
import time
from pathlib import Path
import pytest

from antigravity.storage.models import (
    CodecType,
    DeserializationError,
    PersistedModelConfig,
    PersistedSandboxRecord,
    PersistedSnapshotRecord,
    SerializationError,
    StateVectorManifest,
    StorageConfig,
    StorageError,
    StorageNotFoundError,
    VariableDescriptor,
)
from antigravity.storage.sqlite_engine import SQLiteEngine
from antigravity.storage.disk_store import DiskStateStore
from antigravity.storage.serializer import RestrictedUnpickler, VariableSerializer
from antigravity.storage.persistence_manager import PersistenceManager


@pytest.fixture
def temp_storage_dir():
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def storage_config(temp_storage_dir):
    return StorageConfig(
        base_dir=str(temp_storage_dir),
        db_name="test_state.db",
        max_inline_bytes=256,
        wal_mode=True,
    )


class TestSQLiteEngine:
    def test_initialize_schema_and_wal_mode(self, storage_config):
        engine = SQLiteEngine(storage_config)
        assert engine.db_path.exists()

        # Verify PRAGMA journal_mode
        with engine.connection() as conn:
            cur = conn.cursor()
            cur.execute("PRAGMA journal_mode;")
            journal_mode = cur.fetchone()[0]
            assert journal_mode.lower() == "wal"

            cur.execute("PRAGMA foreign_keys;")
            fk = cur.fetchone()[0]
            assert fk == 1

        # Verify 8 tables exist
        expected_tables = {
            "schema_meta",
            "sandboxes",
            "sandbox_variables",
            "snapshots",
            "scheduled_tasks",
            "task_execution_records",
            "model_configurations",
            "blob_registry",
        }
        rows = engine.execute_query(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        )
        found_tables = {r["name"] for r in rows}
        assert expected_tables.issubset(found_tables)

        engine.close()

    def test_transactions_commit_and_rollback(self, storage_config):
        engine = SQLiteEngine(storage_config)

        # Successful transaction
        with engine.transaction() as cur:
            cur.execute(
                "INSERT INTO schema_meta (key, value, updated_at) VALUES ('test_key', 'val1', ?)",
                (time.time(),),
            )

        row = engine.execute_single("SELECT value FROM schema_meta WHERE key = 'test_key'")
        assert row is not None
        assert row["value"] == "val1"

        # Failed transaction with rollback
        with pytest.raises(ValueError):
            with engine.transaction() as cur:
                cur.execute(
                    "INSERT INTO schema_meta (key, value, updated_at) VALUES ('rollback_key', 'val2', ?)",
                    (time.time(),),
                )
                raise ValueError("Force rollback")

        row = engine.execute_single("SELECT value FROM schema_meta WHERE key = 'rollback_key'")
        assert row is None

        engine.close()


class TestDiskStateStore:
    def test_write_and_read_blob(self, storage_config):
        store = DiskStateStore(storage_config)
        data = b"Hello, disk persistence store!"
        blob_hash = store.write_blob(data, ext="txt", mime_type="text/plain")
        assert len(blob_hash) == 64
        assert store.has_blob(blob_hash)

        read_data = store.read_blob(blob_hash)
        assert read_data == data

    def test_blob_deduplication(self, storage_config):
        store = DiskStateStore(storage_config)
        data = b"Identical binary data for deduplication test."
        hash1 = store.write_blob(data, ext="bin")
        hash2 = store.write_blob(data, ext="bin")
        assert hash1 == hash2

    def test_read_nonexistent_blob_raises_not_found(self, storage_config):
        store = DiskStateStore(storage_config)
        with pytest.raises(StorageNotFoundError):
            store.read_blob("0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef")

    def test_save_and_read_artifact(self, storage_config):
        store = DiskStateStore(storage_config)
        exec_id = "exec_12345"
        art_name = "figure.png"
        art_data = b"\x89PNG\r\n\x1a\nfakeimagebytes"

        rel_path = store.save_artifact(exec_id, art_name, art_data)
        assert exec_id in rel_path

        loaded = store.read_artifact(exec_id, art_name)
        assert loaded == art_data

    def test_purge_orphaned_blobs(self, storage_config):
        store = DiskStateStore(storage_config)
        h1 = store.write_blob(b"active data 1")
        h2 = store.write_blob(b"active data 2")
        h_orphan = store.write_blob(b"orphaned data")

        purged = store.purge_orphaned_blobs(active_hashes={h1, h2})
        assert purged == 1
        assert store.has_blob(h1)
        assert store.has_blob(h2)
        assert not store.has_blob(h_orphan)


class TestVariableSerializer:
    def test_primitive_json_tier(self, storage_config):
        store = DiskStateStore(storage_config)
        serializer = VariableSerializer(store, max_inline_bytes=100)

        # Small primitive (inline)
        desc_small = serializer.serialize_variable("int_var", 12345)
        assert desc_small.codec == CodecType.JSON
        assert desc_small.inline_data == "12345"
        assert desc_small.blob_hash is None

        val_restored = serializer.deserialize_variable(desc_small)
        assert val_restored == 12345

        # Large primitive (blob)
        large_str = "x" * 200
        desc_large = serializer.serialize_variable("str_var", large_str)
        assert desc_large.codec == CodecType.JSON
        assert desc_large.inline_data is None
        assert desc_large.blob_hash is not None

        val_large_restored = serializer.deserialize_variable(desc_large)
        assert val_large_restored == large_str

    def test_complex_types_pickle_tier(self, storage_config):
        store = DiskStateStore(storage_config)
        serializer = VariableSerializer(store)

        # Set
        my_set = {1, 2, 3, "apple", "banana"}
        desc_set = serializer.serialize_variable("set_var", my_set)
        assert desc_set.codec == CodecType.PICKLE
        assert desc_set.blob_hash is not None

        restored_set = serializer.deserialize_variable(desc_set)
        assert restored_set == my_set

        # Tuple with nested types
        my_tuple = (10, "test", (1, 2))
        desc_tuple = serializer.serialize_variable("tuple_var", my_tuple)
        restored_tuple = serializer.deserialize_variable(desc_tuple)
        assert restored_tuple == my_tuple

    def test_unrestorable_fallback(self, storage_config):
        store = DiskStateStore(storage_config)
        serializer = VariableSerializer(store)

        # Open StringIO buffer
        import io
        buf = io.StringIO("test stream")
        desc = serializer.serialize_variable("open_stream", buf)
        assert desc.codec == CodecType.UNRESTORABLE
        assert desc.is_restorable is False

        restored = serializer.deserialize_variable(desc)
        assert restored is None

    def test_namespace_round_trip(self, storage_config):
        store = DiskStateStore(storage_config)
        serializer = VariableSerializer(store)

        ns = {
            "a": 100,
            "b": 3.14159,
            "c": "antigravity persistence",
            "d": [1, 2, 3],
            "e": {"key": "value", "nested": [10, 20]},
            "f": {1, 2, 3},
        }

        manifest = serializer.serialize_namespace(ns, sandbox_id="sb_test")
        assert len(manifest.variables) == 6

        restored_ns = serializer.deserialize_namespace(manifest)
        assert restored_ns["a"] == 100
        assert restored_ns["b"] == 3.14159
        assert restored_ns["c"] == "antigravity persistence"
        assert restored_ns["d"] == [1, 2, 3]
        assert restored_ns["e"] == {"key": "value", "nested": [10, 20]}
        assert restored_ns["f"] == {1, 2, 3}


class TestPersistenceManager:
    def test_save_and_load_sandbox(self, storage_config):
        pm = PersistenceManager(storage_config)

        variables = {
            "x": 42,
            "name": "Alpha",
            "data": [1, 2, 3, 4],
        }

        rec = pm.save_sandbox(
            sandbox_or_id="sb_001",
            mode="local",
            env={"FOO": "BAR"},
            variables=variables,
            metadata={"tag": "unit_test"},
        )
        assert rec.sandbox_id == "sb_001"
        assert rec.variable_count == 3

        loaded = pm.load_sandbox("sb_001")
        assert loaded is not None
        rec_loaded, vars_loaded = loaded
        assert rec_loaded.sandbox_id == "sb_001"
        assert vars_loaded["x"] == 42
        assert vars_loaded["name"] == "Alpha"
        assert vars_loaded["data"] == [1, 2, 3, 4]

        # List sandboxes
        sbs = pm.list_persisted_sandboxes()
        assert len(sbs) == 1
        assert sbs[0].sandbox_id == "sb_001"

        # Delete sandbox
        deleted = pm.delete_persisted_sandbox("sb_001")
        assert deleted is True
        assert pm.load_sandbox("sb_001") is None
        pm.close()

    def test_save_and_load_snapshot(self, storage_config):
        pm = PersistenceManager(storage_config)

        vars_v1 = {"step": 1, "score": 10.5}
        snap1 = pm.save_snapshot(
            sandbox_id="sb_002",
            name="v1",
            variables=vars_v1,
            branch_name="main",
            description="Initial version",
        )
        assert snap1.variable_count == 2

        vars_v2 = {"step": 2, "score": 25.0, "notes": "improved"}
        snap2 = pm.save_snapshot(
            sandbox_id="sb_002",
            name="v2",
            variables=vars_v2,
            parent_snapshot_id=snap1.snapshot_id,
            branch_name="main",
            description="Second version",
        )

        # List snapshots
        snaps = pm.list_snapshots("sb_002")
        assert len(snaps) == 2
        assert snaps[0].name == "v1"
        assert snaps[1].name == "v2"

        # Check tree
        tree = pm.get_snapshot_tree("sb_002")
        assert tree["total_snapshots"] == 2
        assert snap1.snapshot_id in tree["roots"]
        assert snap2.snapshot_id in tree["nodes"][snap1.snapshot_id]["children"]
        pm.close()

    def test_model_config_persistence(self, storage_config):
        pm = PersistenceManager(storage_config)

        model_cfg = PersistedModelConfig(
            model_id="nemotron-mini-4b",
            name="NVIDIA Nemotron-Mini-4B-Instruct",
            architecture="nemotron",
            model_path="/weights/nemotron-mini-4b",
            tokenizer_path="/weights/nemotron-mini-4b/tokenizer.model",
            device="cuda:0",
            dtype="float16",
            quantization="4bit",
            context_window=4096,
            generation_params={"temperature": 0.7, "top_p": 0.95},
        )

        pm.save_model_config(model_cfg)

        loaded = pm.get_model_config("nemotron-mini-4b")
        assert loaded is not None
        assert loaded.model_id == "nemotron-mini-4b"
        assert loaded.architecture == "nemotron"
        assert loaded.generation_params["temperature"] == 0.7

        models = pm.list_model_configs(architecture="nemotron")
        assert len(models) == 1

        pm.delete_model_config("nemotron-mini-4b")
        assert pm.get_model_config("nemotron-mini-4b") is None
        pm.close()
