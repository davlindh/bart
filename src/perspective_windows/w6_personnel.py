"""Omnipod Perspective Window 6: Personalhantering (Personnel Management).
Koordinerar team, roller, bemanning och trivsel.
Output: Teamstruktur & rollöversikt.
"""

from typing import Dict, Any, List
from ..core.types import PerspectiveWindow, Domain


class PersonnelManagementWindow:
    """Window 6: Org hierarchy, role mandates, staffing, competence matrix, and team wellbeing."""

    WINDOW_TYPE = PerspectiveWindow.W6_PERSONNEL_MANAGEMENT

    @classmethod
    def evaluate_team_overview(cls, team_data: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "window": cls.WINDOW_TYPE.value,
            "title": "W6: Personalhantering & Teamkarta",
            "active_team_members": 8,
            "roles_configured": [
                {"role": "Ekonomiansvarig (CFO)", "mandate": "Attest & Skatteoptimering", "status": "ACTIVE"},
                {"role": "Verkstadschef", "mandate": "Inbytesvärdering & VMB-kontroll", "status": "ACTIVE"},
                {"role": "Ledande Fältmontör", "mandate": "RUT-installationer & Fältbesiktning", "status": "ACTIVE"},
                {"role": "Tekniker / IT", "mandate": "Systemintegration & FoU-arbete", "status": "ACTIVE"},
            ],
            "team_health_index": 87.5,
            "workload_distribution_score": 86.0,
            "wellness_initiatives_active": ["Friskvårdsbidrag 5 000 kr", "Ergonomisk fältutrustning"],
        }
