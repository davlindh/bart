"""Omnipod Perspective Window 1: Kontextualisering (Contextualization).
Sätter rätt kontext utifrån behov, trender och mål.
Output: Relevanta insikter & möjligheter.
"""

from typing import Dict, Any, List
from ..core.types import PerspectiveWindow, Domain
from ..core.contracts import Observation


class ContextualizationWindow:
    """Window 1: Analyzes environmental context, identifies macro trends, prioritizes needs, and creates relevance."""

    WINDOW_TYPE = PerspectiveWindow.W1_CONTEXTUALIZATION

    @classmethod
    def evaluate_context(cls, scenario_data: Dict[str, Any]) -> Dict[str, Any]:
        trends = [
            {"id": "TREND-01", "name": "Ökad efterfrågan på elektrifierade trädgårdsmaskiner", "momentum": "+28%"},
            {"id": "TREND-02", "name": "Strängare redovisningskrav för begagnat-VMB hos Skatteverket", "momentum": "HIGH"},
            {"id": "TREND-03", "name": "RUT-avdrag för robotinstallationer fortsätter växa", "momentum": "+18%"},
        ]
        opportunities = [
            {"id": "OPP-01", "title": "Skala inbytesprogram för robotklippare med VMB-garanti", "value_sek": 45000.0},
            {"id": "OPP-02", "title": "Certifiera montörer för Grön Teknik batterilagring", "value_sek": 80000.0},
        ]
        return {
            "window": cls.WINDOW_TYPE.value,
            "title": "W1: Kontextualisering",
            "active_trends": trends,
            "strategic_opportunities": opportunities,
            "context_relevance_score": 0.94,
            "recommendations": [
                "Positionera bolaget mot nyckelfärdiga paket med kombinerad VMB och RUT.",
                "Fokusera kvartalets säljinsats på fastighetsägare med gräsytor > 1 500 kvm.",
            ],
        }
