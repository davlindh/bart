"""Tests for Phase 1 migrated components: ActionDispatcher, Entity State Model, Window Particles."""

import asyncio
import pytest
import pytest_asyncio
from src.core.action_dispatcher import (
    ActionDispatcher,
    ActionPriority,
    DispatchableAction,
)
from src.core.contracts import (
    ExchangeStatus,
    EntityVisibility,
    LifecycleStage,
    TemporalEvent,
    TrustState,
    UserEntityState,
    ValueState,
    VerificationLevel,
)
from src.core.types import PerspectiveWindow
from src.graph.window_particles import (
    WINDOW_DECOMPOSITIONS,
    get_all_entanglement_nodes,
    get_all_particles,
)


# ── Action Dispatcher Tests ─────────────────────────────────────────────


@pytest.mark.asyncio
async def test_immediate_path_for_high_priority():
    """HIGH priority actions must take the immediate execution path."""
    executed = []

    async def on_execute(action):
        executed.append(action.action_id)
        return True

    dispatcher = ActionDispatcher(on_execute=on_execute)
    action = DispatchableAction(
        source_agent="TestAgent",
        action_type="CRITICAL_FIX",
        priority=ActionPriority.HIGH,
    )
    result = await dispatcher.dispatch(action)

    assert result.path == "immediate"
    assert result.success is True
    assert result.queued_for_sync is True
    assert action.action_id in executed


@pytest.mark.asyncio
async def test_sequential_path_for_low_priority():
    """LOW priority actions must take the sequential queue path."""
    dispatcher = ActionDispatcher()
    action = DispatchableAction(
        source_agent="BackgroundAgent",
        action_type="LOG_UPDATE",
        priority=ActionPriority.LOW,
    )
    result = await dispatcher.dispatch(action)

    assert result.path == "sequential"
    assert dispatcher.queue_size == 1


@pytest.mark.asyncio
async def test_user_initiated_forces_immediate():
    """User-initiated actions always take immediate path regardless of priority."""
    dispatcher = ActionDispatcher()
    action = DispatchableAction(
        source_agent="UIAgent",
        action_type="PREFERENCE_CHANGE",
        priority=ActionPriority.LOW,
        user_initiated=True,
    )
    result = await dispatcher.dispatch(action)
    assert result.path == "immediate"


@pytest.mark.asyncio
async def test_trust_affecting_forces_immediate():
    """Actions affecting trust state always take immediate path."""
    dispatcher = ActionDispatcher()
    action = DispatchableAction(
        source_agent="AIEthics",
        action_type="TRUST_RECALC",
        priority=ActionPriority.NORMAL,
        affects_trust=True,
    )
    result = await dispatcher.dispatch(action)
    assert result.path == "immediate"


@pytest.mark.asyncio
async def test_queue_processing_with_retry():
    """Failed persist operations should be re-queued up to max_retries."""
    call_count = 0

    async def on_persist(action):
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise RuntimeError("Simulated persistence failure")

    dispatcher = ActionDispatcher(on_persist=on_persist)

    # Enqueue a low-priority action
    action = DispatchableAction(
        source_agent="BatchAgent",
        action_type="SYNC",
        priority=ActionPriority.LOW,
    )
    dispatcher._enqueue_sequential(action)
    assert dispatcher.queue_size == 1

    # Process queue — first attempt fails, re-queued
    await dispatcher.process_queue()
    assert dispatcher.queue_size == 1  # Re-queued after failure

    # Second attempt fails, re-queued
    await dispatcher.process_queue()
    assert dispatcher.queue_size == 1

    # Third attempt succeeds
    await dispatcher.process_queue()
    assert dispatcher.queue_size == 0
    assert call_count == 3


# ── Entity State Model Tests ────────────────────────────────────────────


def test_trust_cascade_low_trust():
    """Low trust score (<20) should restrict exchange and limit visibility."""
    entity = UserEntityState(
        entity_id="user_001",
        display_name="Test User",
    )
    entity.trust.score = 15.0
    entity.value.aggregate_weight = 2.0
    entity.apply_trust_cascades()

    assert entity.exchange.status == ExchangeStatus.RESTRICTED
    assert entity.exchange.restriction_reason == "low_trust"
    assert entity.interaction.visibility == EntityVisibility.LIMITED
    assert entity.value.aggregate_weight == pytest.approx(1.0)  # Halved from 2.0


def test_trust_cascade_high_trust():
    """High trust score (>50) should activate exchange and boost weight."""
    entity = UserEntityState(
        entity_id="user_002",
        display_name="Trusted User",
    )
    entity.trust.score = 75.0
    entity.value.aggregate_weight = 2.0
    entity.apply_trust_cascades()

    assert entity.exchange.status == ExchangeStatus.ACTIVE
    assert entity.exchange.promoted is True
    assert entity.interaction.visibility == EntityVisibility.PUBLIC
    assert entity.value.aggregate_weight == pytest.approx(2.4)  # 2.0 * 1.2


def test_value_weight_recalculation():
    """Recalculate aggregate weight and update discovery factor."""
    entity = UserEntityState(entity_id="user_003")
    entity.value.intensity = 10.0
    entity.value.confidence = 80.0
    entity.value.context_weight = 1.5
    entity.recalculate_value_weight()

    # (10.0 * 80.0 / 100) * 1.5 = 12.0
    assert entity.value.aggregate_weight == pytest.approx(12.0)
    assert entity.interaction.discovery_factor == 1.5  # > 5.0 threshold


def test_temporal_event_lifecycle():
    """Temporal events should capture lifecycle stages."""
    entity = UserEntityState(entity_id="user_004")
    event = TemporalEvent(
        event_type="role_change",
        event_data={"from": "analyst", "to": "lead"},
        temporal_weight=0.9,
        lifecycle_stage=LifecycleStage.ACTIVE,
    )
    entity.temporal_events.append(event)

    assert len(entity.temporal_events) == 1
    assert entity.temporal_events[0].lifecycle_stage == LifecycleStage.ACTIVE


# ── Window Particle Tests ───────────────────────────────────────────────


def test_all_nine_windows_decomposed():
    """All 9 perspective windows must have decomposition entries."""
    assert len(WINDOW_DECOMPOSITIONS) == 9
    for window in PerspectiveWindow:
        assert window in WINDOW_DECOMPOSITIONS, f"Missing decomposition for {window}"


def test_each_window_has_components_and_entanglement():
    """Each window must have at least 1 component and 1 entanglement node."""
    for window, decomp in WINDOW_DECOMPOSITIONS.items():
        assert len(decomp.components) >= 1, f"{window} has no components"
        assert len(decomp.entanglement_nodes) >= 1, f"{window} has no entanglement nodes"


def test_each_component_has_particles():
    """Each component must produce at least one contextual particle."""
    for window, decomp in WINDOW_DECOMPOSITIONS.items():
        for comp in decomp.components:
            assert len(comp.particles) >= 1, f"{window}/{comp.label} has no particles"


def test_entanglement_nodes_link_multiple_windows():
    """Every entanglement node must link at least 2 windows."""
    for node in get_all_entanglement_nodes():
        assert len(node.linked_windows) >= 2, f"{node.node_id} links fewer than 2 windows"


def test_total_particle_count():
    """Sanity check: should have 18 particles (2 per window × 9 windows)."""
    particles = get_all_particles()
    assert len(particles) == 18
