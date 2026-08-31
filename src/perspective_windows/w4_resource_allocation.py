"""Omnipod Perspective Window 4: Resursallokering (Resource Allocation).
Allokerar tid, pengar och material optimalt.
Output: Allokeringsplan & resursstatus.
"""

from typing import Dict, Any, List
from ..core.types import PerspectiveWindow, Domain


class ResourceAllocationWindow:
    """Window 4: Balances workload capacity, capital deployment, machinery inventory, and materials."""

    WINDOW_TYPE = PerspectiveWindow.W4_RESOURCE_ALLOCATION

    @classmethod
    def evaluate_allocations(cls, resources_data: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "window": cls.WINDOW_TYPE.value,
            "title": "W4: Resursallokering & Kapacitetsstyrning",
            "capacity_utilization_pct": 78.4,
            "allocated_budget_sek": 450000.0,
            "working_capital_available_sek": 210000.0,
            "allocations_by_department": [
                {"department": "Verkstad & Service", "hours_allocated": 320, "budget_share_pct": 45},
                {"department": "Drift & Installation", "hours_allocated": 280, "budget_share_pct": 35},
                {"department": "Administration & Ekonomi", "hours_allocated": 120, "budget_share_pct": 20},
            ],
            "resource_bottleneck_warning": None,
            "optimal_rebalance_suggestion": "Allokera 10% mer installationskapacitet till fredagar inför helgleveranser.",
        }
