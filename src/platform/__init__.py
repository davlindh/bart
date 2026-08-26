"""Platform Layer — Client State Management, 9-Window UI Controller & Streaming Sync."""

from src.platform.state_manager import (
    EntityCacheEntry,
    LocalStateManager,
    StateManagerOptions,
)
from src.platform.ui_controller import (
    OmnipodUIController,
    UIControllerConfig,
    WindowViewUpdate,
)
from src.platform.stream_bridge import (
    EventType,
    StreamBridge,
    StreamFrame,
)
from src.platform.omnipod_presenter import (
    OmnipodPresenter,
    WindowPresentationPayload,
)

__all__ = [
    "EntityCacheEntry",
    "LocalStateManager",
    "StateManagerOptions",
    "OmnipodUIController",
    "UIControllerConfig",
    "WindowViewUpdate",
    "EventType",
    "StreamBridge",
    "StreamFrame",
    "OmnipodPresenter",
    "WindowPresentationPayload",
]
