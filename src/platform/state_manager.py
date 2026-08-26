"""Local State Manager — Client-side caching, optimistic updates, and reactive subscriptions.

Migrated and adapted from 3.7fmossmorph/meta-framework/layered_runner/local_state_manager.ts.
Provides:
  - In-memory entity caching with TTL staleness expiration
  - LRU/capacity-bounded eviction
  - Optimistic local state updates with rollback capability
  - Multi-subscriber change notification bus
"""

import time
from typing import Any, Callable, Dict, List, Optional, Set
from pydantic import BaseModel, Field

from src.core.contracts import UserEntityState


class StateManagerOptions(BaseModel):
    """Configuration options for LocalStateManager."""
    max_cache_size: int = Field(default=1000, description="Max entities to hold in cache")
    stale_duration_seconds: float = Field(default=300.0, description="Staleness threshold (5 mins)")
    enable_auto_cleanup: bool = Field(default=True)


class EntityCacheEntry(BaseModel):
    """Metadata wrapper around cached entity state."""
    entity: UserEntityState
    last_updated: float = Field(default_factory=time.time)
    last_accessed: float = Field(default_factory=time.time)
    is_optimistic: bool = False
    original_snapshot: Optional[Dict[str, Any]] = None


class LocalStateManager:
    """Manages client-side cached entity state, optimistic modifications, and subscribers."""

    def __init__(self, options: Optional[StateManagerOptions] = None):
        self.options = options or StateManagerOptions()
        self._cache: Dict[str, EntityCacheEntry] = {}
        self._subscribers: Dict[str, Set[Callable[[UserEntityState], Any]]] = {}  # entity_id -> callbacks
        self._global_subscribers: Set[Callable[[str, UserEntityState], Any]] = set()

    # ── Cache Operations ────────────────────────────────────────────────

    def get_entity(self, entity_id: str) -> Optional[UserEntityState]:
        """Retrieve an entity from the local cache and update its access time."""
        entry = self._cache.get(entity_id)
        if not entry:
            return None
        entry.last_accessed = time.time()
        return entry.entity

    def set_entity(
        self,
        entity: UserEntityState,
        is_optimistic: bool = False,
        original_snapshot: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Store or update an entity in the cache and notify listeners."""
        if len(self._cache) >= self.options.max_cache_size and entity.entity_id not in self._cache:
            self._evict_lru()

        entry = EntityCacheEntry(
            entity=entity,
            last_updated=time.time(),
            last_accessed=time.time(),
            is_optimistic=is_optimistic,
            original_snapshot=original_snapshot,
        )
        self._cache[entity.entity_id] = entry
        self._notify_subscribers(entity.entity_id, entity)

    def is_stale(self, entity_id: str) -> bool:
        """Check if an entity's cached data has exceeded its staleness duration."""
        entry = self._cache.get(entity_id)
        if not entry:
            return True
        return (time.time() - entry.last_updated) > self.options.stale_duration_seconds

    def apply_optimistic_update(
        self,
        entity_id: str,
        mutation_fn: Callable[[UserEntityState], None],
    ) -> Optional[UserEntityState]:
        """Apply an immediate in-memory update with an original snapshot saved for rollback."""
        current = self.get_entity(entity_id)
        if not current:
            return None

        # Take shallow snapshot of model dict for rollback
        snapshot = current.model_dump()
        mutation_fn(current)
        self.set_entity(current, is_optimistic=True, original_snapshot=snapshot)
        return current

    def rollback_optimistic(self, entity_id: str) -> Optional[UserEntityState]:
        """Revert an entity to its pre-optimistic state snapshot."""
        entry = self._cache.get(entity_id)
        if not entry or not entry.is_optimistic or not entry.original_snapshot:
            return None

        restored_entity = UserEntityState.model_validate(entry.original_snapshot)
        self.set_entity(restored_entity, is_optimistic=False, original_snapshot=None)
        return restored_entity

    def commit_optimistic(self, entity_id: str) -> bool:
        """Mark an optimistic update as confirmed by server."""
        entry = self._cache.get(entity_id)
        if not entry:
            return False
        entry.is_optimistic = False
        entry.original_snapshot = None
        return True

    def remove_entity(self, entity_id: str) -> bool:
        """Delete an entity from the cache."""
        if entity_id in self._cache:
            del self._cache[entity_id]
            return True
        return False

    def clear(self) -> None:
        """Clear all cached entities."""
        self._cache.clear()

    @property
    def size(self) -> int:
        return len(self._cache)

    # ── Subscriptions ───────────────────────────────────────────────────

    def subscribe(self, entity_id: str, callback: Callable[[UserEntityState], Any]) -> Callable[[], None]:
        """Subscribe to updates for a specific entity ID. Returns an unsubscribe function."""
        if entity_id not in self._subscribers:
            self._subscribers[entity_id] = set()
        self._subscribers[entity_id].add(callback)

        def unsubscribe():
            if entity_id in self._subscribers and callback in self._subscribers[entity_id]:
                self._subscribers[entity_id].remove(callback)

        return unsubscribe

    def subscribe_all(self, callback: Callable[[str, UserEntityState], Any]) -> Callable[[], None]:
        """Subscribe to all entity updates. Returns an unsubscribe function."""
        self._global_subscribers.add(callback)

        def unsubscribe():
            self._global_subscribers.discard(callback)

        return unsubscribe

    def _notify_subscribers(self, entity_id: str, entity: UserEntityState) -> None:
        """Dispatch notifications to all relevant callbacks."""
        if entity_id in self._subscribers:
            for cb in list(self._subscribers[entity_id]):
                try:
                    cb(entity)
                except Exception:
                    pass

        for g_cb in list(self._global_subscribers):
            try:
                g_cb(entity_id, entity)
            except Exception:
                pass

    # ── Internal Cleanup & Eviction ─────────────────────────────────────

    def _evict_lru(self) -> None:
        """Evict the least-recently accessed entity from cache."""
        if not self._cache:
            return
        lru_id = min(self._cache.keys(), key=lambda k: self._cache[k].last_accessed)
        del self._cache[lru_id]

    def cleanup_stale_entries(self) -> int:
        """Remove all stale non-optimistic entities. Returns count of removed items."""
        now = time.time()
        to_remove = [
            k for k, v in self._cache.items()
            if not v.is_optimistic and (now - v.last_updated) > self.options.stale_duration_seconds
        ]
        for k in to_remove:
            del self._cache[k]
        return len(to_remove)
