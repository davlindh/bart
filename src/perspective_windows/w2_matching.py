"""Omnipod Perspective Window 2: Matchning (Matching).
Matchar användare, resurser, kompetens och behov.
Output: Matchningar & förslag.
"""

from typing import Dict, Any, List
from ..core.types import PerspectiveWindow, Domain


class MatchingWindow:
    """Window 2: Intelligent quote configuration, customer demand to resource capability matching."""

    WINDOW_TYPE = PerspectiveWindow.W2_MATCHING

    @classmethod
    def match_quote_configuration(
        cls,
        customer_need: str,
        budget_sek: float,
        has_trade_in: bool = True,
        is_private_individual: bool = True,
    ) -> Dict[str, Any]:
        matched_packages = []
        if has_trade_in:
            matched_packages.append({
                "package_id": "PKG-VMB-HYBRID",
                "name": "Husqvarna Automower 430X Inbytespaket",
                "sales_price_gross": 16000.0,
                "customer_net_cost": 16000.0,
                "vat_treatment": "ML 9a kap. VMB (sparar 2 000 SEK moms)",
                "match_score": 0.96,
            })

        if is_private_individual:
            matched_packages.append({
                "package_id": "PKG-RUT-INSTALL",
                "name": "Komplett Fältinstallation & Kabeldragning",
                "standard_price": 8000.0,
                "rut_customer_price": 4000.0,
                "vat_treatment": "IL 67 kap. 50% RUT-avdrag",
                "match_score": 0.98,
            })

        return {
            "window": cls.WINDOW_TYPE.value,
            "title": "W2: Matchning & Offertkonfigurator",
            "matched_packages": matched_packages,
            "resource_availability": "3 fältmontörer lediga vecka 36",
            "optimal_matching_score": 0.97,
        }
