"""Tests for Phase 3 Platform Layer: StateManager, UIController, StreamBridge, and OmnipodPresenter."""

import asyncio
import pytest
from src.context_engine.resolver import ContextResolutionEngine
from src.core.contracts import ScopeContract, UserEntityState
from src.core.types import PerspectiveWindow, ScopeDepth
from src.platform.omnipod_presenter import OmnipodPresenter, WindowPresentationPayload
from src.platform.state_manager import (
    EntityCacheEntry,
    LocalStateManager,
    StateManagerOptions,
)
from src.platform.stream_bridge import EventType, StreamBridge, StreamFrame
from src.platform.ui_controller import (
    OmnipodUIController,
    UIControllerConfig,
    WindowViewUpdate,
)
from src.seeds.seed_loader import SeedDataLoader


# ── LocalStateManager Tests ─────────────────────────────────────────────


def test_state_manager_cache_and_get():
    """Verify storing and retrieving entities from cache."""
    sm = LocalStateManager()
    entity = UserEntityState(entity_id="u1", display_name="Alice")
    sm.set_entity(entity)

    assert sm.size == 1
    retrieved = sm.get_entity("u1")
    assert retrieved is not None
    assert retrieved.display_name == "Alice"


def test_state_manager_optimistic_update_and_commit():
    """Verify optimistic update can be applied and confirmed."""
    sm = LocalStateManager()
    entity = UserEntityState(entity_id="u2", display_name="Bob")
    sm.set_entity(entity)

    def mutate_fn(e: UserEntityState):
        e.display_name = "Robert"
        e.trust.score = 90.0

    updated = sm.apply_optimistic_update("u2", mutate_fn)
    assert updated is not None
    assert updated.display_name == "Robert"
    assert sm.get_entity("u2").trust.score == 90.0

    # Commit optimistic
    success = sm.commit_optimistic("u2")
    assert success is True


def test_state_manager_optimistic_rollback():
    """Verify optimistic update can be rolled back to pre-mutation snapshot."""
    sm = LocalStateManager()
    entity = UserEntityState(entity_id="u3", display_name="Charlie")
    sm.set_entity(entity)

    def mutate_fn(e: UserEntityState):
        e.display_name = "Chuck"

    sm.apply_optimistic_update("u3", mutate_fn)
    assert sm.get_entity("u3").display_name == "Chuck"

    rolled_back = sm.rollback_optimistic("u3")
    assert rolled_back is not None
    assert rolled_back.display_name == "Charlie"
    assert sm.get_entity("u3").display_name == "Charlie"


def test_state_manager_subscriptions():
    """Verify reactive subscriber notifications on entity changes."""
    sm = LocalStateManager()
    received = []

    def on_change(e: UserEntityState):
        received.append(e.entity_id)

    unsub = sm.subscribe("u4", on_change)
    sm.set_entity(UserEntityState(entity_id="u4", display_name="Dana"))
    assert len(received) == 1

    # Unsubscribe
    unsub()
    sm.set_entity(UserEntityState(entity_id="u4", display_name="Dana 2"))
    assert len(received) == 1  # No additional callback


def test_state_manager_lru_eviction():
    """Verify LRU item is evicted when capacity is reached."""
    opts = StateManagerOptions(max_cache_size=2)
    sm = LocalStateManager(opts)

    sm.set_entity(UserEntityState(entity_id="e1"))
    sm.set_entity(UserEntityState(entity_id="e2"))
    # Touch e1 so e2 becomes least recently accessed
    sm.get_entity("e1")

    # Add e3, triggering eviction of e2
    sm.set_entity(UserEntityState(entity_id="e3"))
    assert sm.size == 2
    assert sm.get_entity("e1") is not None
    assert sm.get_entity("e3") is not None
    assert sm.get_entity("e2") is None


# ── OmnipodUIController Tests ───────────────────────────────────────────


def test_ui_controller_registration_and_dispatch():
    """Verify component callbacks receive targeted updates."""
    ctrl = OmnipodUIController()
    dispatched = []

    def on_trend_update(up: WindowViewUpdate):
        dispatched.append(up.data.get("trend_name"))

    ctrl.register_window_component(
        PerspectiveWindow.CONTEXTUALIZATION,
        "ctx_trend",
        on_trend_update,
    )

    update = WindowViewUpdate(
        window=PerspectiveWindow.CONTEXTUALIZATION,
        component_id="ctx_trend",
        data={"trend_name": "Decentralized Delegation"},
    )
    ctrl.queue_update(update)
    assert ctrl.pending_count == 1

    processed = ctrl.flush_updates()
    assert processed == 1
    assert "Decentralized Delegation" in dispatched


def test_ui_controller_visibility_filtering():
    """Hidden windows should not process updates during flush."""
    ctrl = OmnipodUIController()
    calls = []

    def on_eval(up: WindowViewUpdate):
        calls.append(up)

    ctrl.register_window_component(PerspectiveWindow.EVALUATION, "eval_comp", on_eval)
    ctrl.set_window_visibility(PerspectiveWindow.EVALUATION, False)

    ctrl.queue_update(WindowViewUpdate(
        window=PerspectiveWindow.EVALUATION,
        component_id="eval_comp",
        data={"score": 98},
    ))
    processed = ctrl.flush_updates()
    assert processed == 0
    assert len(calls) == 0


# ── StreamBridge Tests ──────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_stream_bridge_broadcast_and_consume():
    """Verify event broadcasting and consumption via async generator."""
    bridge = StreamBridge()
    received_frames = []

    async def consumer():
        async for frame in bridge.client_stream(replay_history=False):
            received_frames.append(frame)
            if len(received_frames) == 2:
                break

    task = asyncio.create_task(consumer())
    await asyncio.sleep(0.01)  # Allow subscriber to connect

    await bridge.broadcast(EventType.CYCLE_STARTED, {"cycle_id": "c1"})
    await bridge.broadcast(EventType.AGENT_PROGRESS, {"agent": "Observer", "status": "done"})

    await asyncio.wait_for(task, timeout=2.0)
    assert len(received_frames) == 2
    assert received_frames[0].event_type == EventType.CYCLE_STARTED
    assert received_frames[1].event_type == EventType.AGENT_PROGRESS


def test_stream_frame_formatting():
    """Verify SSE and WS message formats."""
    frame = StreamFrame(
        event_type=EventType.ACTION_DISPATCHED,
        payload={"action": "DELEGATE_ROLE"},
    )
    sse_msg = frame.to_sse_message()
    assert sse_msg.startswith("event: action_dispatched\n")
    assert '"action": "DELEGATE_ROLE"' in sse_msg

    ws_msg = frame.to_ws_message()
    assert "action_dispatched" in ws_msg


# ── OmnipodPresenter Tests ──────────────────────────────────────────────


def test_omnipod_presenter_all_windows():
    """Verify 9-window presentation dictionary creation."""
    store = SeedDataLoader.load_seed_graph()
    engine = ContextResolutionEngine(store)
    scope = ScopeContract(depth=ScopeDepth.D1, breadth_limit=5)
    packet = engine.resolve_context(
        role="Data Manager",
        purpose="Improve reporting SLA",
        task="Diagnose bottlenecks",
        current_point="node:role:decision_owner_042",
        scope=scope,
    )

    all_windows = OmnipodPresenter.present_all_windows(packet)
    assert len(all_windows) == 9

    for window in PerspectiveWindow:
        payload = all_windows.get(window)
        assert payload is not None
        assert isinstance(payload, WindowPresentationPayload)
        assert payload.window == window
        assert len(payload.l1_summary) > 0
        assert "nodes" in payload.l2_details
        assert len(payload.active_particles) > 0
