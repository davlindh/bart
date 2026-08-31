"""Boundary and security tests for persistence layer (Tier 2)."""

import io
import pickle
import tempfile
import threading
import time
from pathlib import Path
import pytest

from antigravity.storage.models import (
    CodecType,
    DeserializationError,
    StorageConfig,
    StorageError,
    StorageNotFoundError,
    VariableDescriptor,
)
from antigravity.storage.disk_store import DiskStateStore
from antigravity.storage.serializer import RestrictedUnpickler, VariableSerializer
from antigravity.storage.sqlite_engine import SQLiteEngine
from antigravity.storage.persistence_manager import PersistenceManager


@pytest.fixture
def temp_storage_dir():
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def storage_config(temp_storage_dir):
    return StorageConfig(
        base_dir=str(temp_storage_dir),
        db_name="boundary_state.db",
        max_inline_bytes=512,
        wal_mode=True,
    )


class MaliciousExploit:
    def __reduce__(self):
        import os
        return (os.system, ("echo pwned",))


class MaliciousSubprocess:
    def __reduce__(self):
        import subprocess
        return (subprocess.Popen, (["echo", "pwned"],))


class MaliciousEval:
    def __reduce__(self):
        return (eval, ("1 + 1",))


class TestRestrictedUnpicklerSecurity:
    def test_blocks_os_system_exploit(self):
        bad_payload = pickle.dumps(MaliciousExploit())
        buf = io.BytesIO(bad_payload)
        unpickler = RestrictedUnpickler(buf)

        with pytest.raises(DeserializationError) as exc_info:
            unpickler.load()
        assert "RestrictedUnpickler blocked" in str(exc_info.value) or "Security violation" in str(exc_info.value)

    def test_blocks_subprocess_exploit(self):
        bad_payload = pickle.dumps(MaliciousSubprocess())
        buf = io.BytesIO(bad_payload)
        unpickler = RestrictedUnpickler(buf)

        with pytest.raises(DeserializationError) as exc_info:
            unpickler.load()
        assert "RestrictedUnpickler blocked" in str(exc_info.value) or "Security violation" in str(exc_info.value)

    def test_blocks_eval_exploit(self):
        bad_payload = pickle.dumps(MaliciousEval())
        buf = io.BytesIO(bad_payload)
        unpickler = RestrictedUnpickler(buf)

        with pytest.raises(DeserializationError) as exc_info:
            unpickler.load()
        assert "RestrictedUnpickler blocked" in str(exc_info.value) or "Security violation" in str(exc_info.value)


class TestPersistenceBoundaries:
    def test_concurrent_multithreaded_writes(self, storage_config):
        pm = PersistenceManager(storage_config)
        errors = []

        def worker(idx: int):
            try:
                # Save unique sandbox
                sb_id = f"sb_thread_{idx}"
                pm.save_sandbox(
                    sandbox_or_id=sb_id,
                    mode="local",
                    variables={"worker_id": idx, "array": list(range(idx * 10))},
                )
                # Read it back
                loaded = pm.load_sandbox(sb_id)
                assert loaded is not None
                assert loaded[1]["worker_id"] == idx
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0, f"Thread errors: {errors}"
        sbs = pm.list_persisted_sandboxes()
        assert len(sbs) == 10
        pm.close()

    def test_large_variable_payload_boundary(self, storage_config):
        pm = PersistenceManager(storage_config)

        # 500 KB string
        large_text = "antigravity_persistent_data_" * 20000
        # Large dictionary
        large_dict = {f"k_{i}": f"val_{i}" for i in range(5000)}

        pm.save_sandbox(
            sandbox_or_id="sb_large",
            mode="local",
            variables={"text": large_text, "dict": large_dict},
        )

        loaded = pm.load_sandbox("sb_large")
        assert loaded is not None
        _, vars_dict = loaded
        assert vars_dict["text"] == large_text
        assert len(vars_dict["dict"]) == 5000
        assert vars_dict["dict"]["k_4999"] == "val_4999"
        pm.close()

    def test_missing_blob_handling(self, storage_config):
        store = DiskStateStore(storage_config)
        serializer = VariableSerializer(store)

        # Create descriptor with nonexistent blob
        fake_desc = VariableDescriptor(
            name="missing_var",
            type_name="dict",
            codec=CodecType.JSON,
            blob_hash="nonexistent_blob_hash_1234567890",
        )

        with pytest.raises(StorageNotFoundError):
            serializer.deserialize_variable(fake_desc)
