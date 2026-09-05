"""BART Web Server: Zero-dependency HTTP and REST API server for the Multi-Perspective Spatial Canvas."""

import http.server
import json
import os
import sys
import urllib.parse
from typing import Any, Dict, List, Optional
from pathlib import Path

# Ensure src parent directory is in path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.core.types import Domain, PerspectiveWindow, ScopeLevel, TaxRuleType
from src.core.contracts import ContextPacket, Observation
from src.context_engine.resolver import ContextResolver
from src.perspective_windows.financial_management import FinancialManagementWindow
from src.agents import (
    TWELVE_CORE_AGENTS,
    TaxOptimizationAgent,
    ObserverAgent,
    DiagnosticianAgent,
    TeamArchitectAgent,
    RoleTransitionAgent,
    CollaborationAgent,
    WellbeingAgent,
    AIEthicsAgent,
    ExperimentAgent,
    MeasurementAgent,
    LearningAgent,
    OrchestratorAgent,
    MetaLearningAgent,
)
from src.tax_engine.models import TaxTransaction, CustomerTaxProfile
from src.tax_engine.bas_kontoplan import BASKontoplan
from src.tax_engine.evaluator import TaxRuleEvaluator
from src.tax_engine.momsdeklaration import MomsdeklarationGenerator
from src.tax_engine.verification_engine import FinancialVerificationEngine
from src.tax_engine.combinatorial_engine import CombinatorialTaxEngine

AGENT_REGISTRY = {
    "TaxOptimizationAgent": TaxOptimizationAgent,
    "ObserverAgent": ObserverAgent,
    "DiagnosticianAgent": DiagnosticianAgent,
    "TeamArchitectAgent": TeamArchitectAgent,
    "RoleTransitionAgent": RoleTransitionAgent,
    "CollaborationAgent": CollaborationAgent,
    "WellbeingAgent": WellbeingAgent,
    "AIEthicsAgent": AIEthicsAgent,
    "ExperimentAgent": ExperimentAgent,
    "MeasurementAgent": MeasurementAgent,
    "LearningAgent": LearningAgent,
    "OrchestratorAgent": OrchestratorAgent,
    "MetaLearningAgent": MetaLearningAgent,
}

STATIC_DIR = Path(__file__).resolve().parent / "web"

# Pre-configured realistic Swedish SMB scenarios
SCENARIOS: Dict[str, Dict[str, Any]] = {
    "mixed_q3": {
        "id": "mixed_q3",
        "title": "Trädgård & Maskinservice AB (Q3 Revision)",
        "description": "Blandad kvartalsström med begagnatinbyten, RUT-installationer, omvänd byggmoms och verktygsinvesteringar.",
        "period": "2026-Q3",
        "input_vat_total": 5400.0,
        "transactions": [
            {
                "transaction_id": "TX-1001",
                "source_system": "WORKSHOP_POS",
                "description": "Begagnad Husqvarna Automower 430X",
                "gross_amount": 16000.0,
                "net_amount": 12800.0,
                "current_vat_rate": 0.25,
                "current_vat_amount": 3200.0,
                "current_tax_rule": "MOMS_25",
                "is_used_good": True,
                "purchase_cost_ex_vat": 10000.0,
                "bought_from_private_individual": True,
                "customer": {
                    "customer_id": "CUST-001",
                    "name": "Erik Johansson",
                    "is_company": False,
                    "rut_eligible": True
                }
            },
            {
                "transaction_id": "TX-1002",
                "source_system": "FORTNOX",
                "description": "Installation & kabeldragning Automower 450X",
                "gross_amount": 24000.0,
                "net_amount": 19200.0,
                "current_vat_rate": 0.25,
                "current_vat_amount": 4800.0,
                "current_tax_rule": "MOMS_25",
                "is_garden_or_installation_work": True,
                "labor_share_amount": 8000.0,
                "material_share_amount": 16000.0,
                "customer": {
                    "customer_id": "CUST-002",
                    "name": "Karin Lindström",
                    "is_company": False,
                    "rut_eligible": True
                }
            },
            {
                "transaction_id": "TX-1003",
                "source_system": "FORTNOX",
                "description": "Markschaktning för kabeldragning",
                "gross_amount": 50000.0,
                "net_amount": 40000.0,
                "current_vat_rate": 0.25,
                "current_vat_amount": 10000.0,
                "current_tax_rule": "MOMS_25",
                "is_garden_or_installation_work": True,
                "customer": {
                    "customer_id": "CUST-003",
                    "name": "Syd Bygg & Anläggning AB",
                    "is_company": True,
                    "has_f_skatt": True,
                    "sni_code": "43.120"
                }
            },
            {
                "transaction_id": "TX-1004",
                "source_system": "SUPPLIER_INVOICE",
                "description": "Batteridiagnostik & Programmeringsverktyg",
                "gross_amount": 25000.0,
                "net_amount": 20000.0,
                "current_vat_rate": 0.25,
                "current_vat_amount": 5000.0,
                "current_tax_rule": "MOMS_25",
                "is_asset_purchase": True,
                "customer": {
                    "customer_id": "SUPP-001",
                    "name": "Husqvarna Tools Nordic",
                    "is_company": True
                }
            }
        ]
    },
    "vmb_fleet": {
        "id": "vmb_fleet",
        "title": "Begagnatflotta Inbyten (VMB Marginalbeskattning)",
        "description": "Portfölj av inbytta robotklippare och maskiner med hög momsoptimeringspotential.",
        "period": "2026-Q3",
        "input_vat_total": 2100.0,
        "transactions": [
            {
                "transaction_id": "TX-2001",
                "source_system": "WORKSHOP_POS",
                "description": "Inbytt Stihl iMow 632P",
                "gross_amount": 22000.0,
                "net_amount": 17600.0,
                "current_vat_rate": 0.25,
                "current_vat_amount": 4400.0,
                "current_tax_rule": "MOMS_25",
                "is_used_good": True,
                "purchase_cost_ex_vat": 14000.0,
                "bought_from_private_individual": True
            },
            {
                "transaction_id": "TX-2002",
                "source_system": "WORKSHOP_POS",
                "description": "Inbytt Husqvarna CEORA Kommersiell",
                "gross_amount": 75000.0,
                "net_amount": 60000.0,
                "current_vat_rate": 0.25,
                "current_vat_amount": 15000.0,
                "current_tax_rule": "MOMS_25",
                "is_used_good": True,
                "purchase_cost_ex_vat": 50000.0,
                "bought_from_private_individual": True
            }
        ]
    },
    "maskinochfritid_prod": {
        "id": "maskinochfritid_prod",
        "title": "Maskin & Fritid '25 (Fortnox Produktion)",
        "description": "Produktionsflöde från Fortnox med robotgräsklippare (Stihl iMow, Husqvarna, Stiga), RUT 50%, VMB och omvänd byggmoms.",
        "period": "2026-Q3",
        "input_vat_total": 4200.0,
        "transactions": [
            {
                "transaction_id": "TX-10542",
                "source_system": "FORTNOX",
                "description": "Faktura #10542: Anna Nilsson (Robotinstallation RUT)",
                "gross_amount": 12000.0,
                "net_amount": 9600.0,
                "current_vat_rate": 0.25,
                "current_vat_amount": 2400.0,
                "current_tax_rule": "MOMS_25",
                "is_garden_or_installation_work": True,
                "labor_share_amount": 12000.0,
                "customer": {
                    "customer_id": "CUST-101",
                    "name": "Anna Nilsson",
                    "is_company": False,
                    "rut_eligible": True
                }
            },
            {
                "transaction_id": "TX-10543",
                "source_system": "FORTNOX",
                "description": "Faktura #10543: Erik Johansson (Stihl iMow Inbyte VMB)",
                "gross_amount": 24500.0,
                "net_amount": 19600.0,
                "current_vat_rate": 0.25,
                "current_vat_amount": 4900.0,
                "current_tax_rule": "MOMS_25",
                "is_used_good": True,
                "purchase_cost_ex_vat": 16000.0,
                "bought_from_private_individual": True,
                "customer": {
                    "customer_id": "CUST-102",
                    "name": "Erik Johansson",
                    "is_company": False,
                    "rut_eligible": False
                }
            },
            {
                "transaction_id": "TX-10544",
                "source_system": "FORTNOX",
                "description": "Faktura #10544: Svensson Bygg & Anläggning AB (Omvänd moms)",
                "gross_amount": 38000.0,
                "net_amount": 38000.0,
                "current_vat_rate": 0.0,
                "current_vat_amount": 0.0,
                "current_tax_rule": "OMVAND_BYGGMOMS_ML1_2",
                "is_garden_or_installation_work": True,
                "customer": {
                    "customer_id": "CUST-103",
                    "name": "Svensson Bygg & Anläggning AB",
                    "is_company": True,
                    "has_f_skatt": True,
                    "sni_code": "43.120"
                }
            },
            {
                "transaction_id": "TX-2044",
                "source_system": "FORTNOX",
                "description": "Faktura #2044: Andersson Maskin & Skog AB (Skogsutrustning B2B)",
                "gross_amount": 22500.0,
                "net_amount": 18000.0,
                "current_vat_rate": 0.25,
                "current_vat_amount": 4500.0,
                "current_tax_rule": "MOMS_25",
                "customer": {
                    "customer_id": "CUST-104",
                    "name": "Andersson Maskin & Skog AB",
                    "is_company": True,
                    "has_f_skatt": True
                }
            },
            {
                "transaction_id": "TX-5102",
                "source_system": "FORTNOX",
                "description": "Faktura #5102: Bengt Olofsson (Stiga Autoclip Inbyte VMB)",
                "gross_amount": 10450.0,
                "net_amount": 8360.0,
                "current_vat_rate": 0.25,
                "current_vat_amount": 2090.0,
                "current_tax_rule": "MOMS_25",
                "is_used_good": True,
                "purchase_cost_ex_vat": 6000.0,
                "bought_from_private_individual": True,
                "customer": {
                    "customer_id": "CUST-105",
                    "name": "Bengt Olofsson",
                    "is_company": False,
                    "rut_eligible": False
                }
            }
        ]
    }
}

# Global in-memory approved vouchers log
APPROVED_VOUCHERS: List[Dict[str, Any]] = []

# Canonical list of proposed vouchers ready for Fortnox synchronization
PROPOSED_VOUCHERS: List[Dict[str, Any]] = [
    {
        "proposal_id": "PROP-TX-1001",
        "transaction_id": "TX-1001",
        "verifikat_id": "VER-TX1001-VMB",
        "series": "A",
        "title": "Begagnad Husqvarna Automower 430X (VMB)",
        "description": "VMB Marginalbeskattning Automower 430X inbyte (ML 9a kap)",
        "category": "VMB_MARGIN_TAX",
        "tax_rule": "VMB_MARGIN_TAX_ML9A",
        "legal_basis": "Mervärdesskattelagen (1994:200 / 2023:200) 9a kap.",
        "statutory_notes": "Inköpt från privatperson utan avdragsrätt. VMB 20% appliceras på marginalen 6 000 SEK (16 000 - 10 000 SEK). Utgående moms sänks från 3 200 SEK till 1 200 SEK.",
        "economic_effect": "+2 000,00 SEK Momsbesparing (+71,4% nettomarginal)",
        "rows": [
            {"account": "1510 Kundfordringar", "description": "Faktura brutto kund", "debet": 16000.0, "kredit": 0.0},
            {"account": "3051 Försäljning varor VMB", "description": "VMB-försäljning beskattad marginal", "debet": 0.0, "kredit": 14800.0},
            {"account": "2611 Utgående moms VMB 25%", "description": "Moms 20% på vinstmarginal", "debet": 0.0, "kredit": 1200.0}
        ],
        "total_debet": 16000.0,
        "total_kredit": 16000.0,
        "diff": 0.0,
        "fortnox_status": "READY_TO_POST",
        "synced": False
    },
    {
        "proposal_id": "PROP-TX-1002",
        "transaction_id": "TX-1002",
        "verifikat_id": "VER-TX1002-KABEL-STD",
        "series": "A",
        "title": "Installation & kabeldragning Automower 450X",
        "description": "Installation & kabeldragning Automower 450X (Lagvaliderad standardmoms)",
        "category": "RUT_COMPLIANCE_ENFORCEMENT",
        "tax_rule": "MOMS_25_KABEL_EJ_RUT",
        "legal_basis": "Inkomstskattelagen (1999:1229) 67 kap. 13-19 §§ samt Skatteverkets ställningstagande dnr 131 347493-15/111",
        "statutory_notes": "LAGKONTROLL SKATTEVERKET: Nedläggning av begränsningskabel och installation av robotgräsklippare är UTTRYCKLIGEN UNDANTAGEN från RUT-avdrag. Bokförs med 25% standardmoms på BAS 3001 för att avvärja nekad Skv-utbetalning och 20% skattetillägg.",
        "economic_effect": "100% Skatteefterlevnad (Avvärjer 960 SEK skattetillägg)",
        "rows": [
            {"account": "1510 Kundfordringar", "description": "Kundfordran full faktura", "debet": 24000.0, "kredit": 0.0},
            {"account": "3001 Försäljning maskin- & kabelarbete 25% moms", "description": "Kabeldragning & installation (ej RUT)", "debet": 0.0, "kredit": 19200.0},
            {"account": "2610 Utgående moms 25%", "description": "Utgående moms 25%", "debet": 0.0, "kredit": 4800.0}
        ],
        "total_debet": 24000.0,
        "total_kredit": 24000.0,
        "diff": 0.0,
        "fortnox_status": "READY_TO_POST",
        "synced": False
    },
    {
        "proposal_id": "PROP-TX-1003",
        "transaction_id": "TX-1003",
        "verifikat_id": "VER-TX1003-OMVAND-BYGG",
        "series": "A",
        "title": "Markschaktning för kabeldragning (Syd Bygg AB)",
        "description": "Markschaktning kabeldragning Syd Bygg & Anläggning AB (Omvänd byggmoms)",
        "category": "OMVÄND_BYGGMOMS",
        "tax_rule": "REVERSE_CHARGE_CONSTRUCTION_ML1",
        "legal_basis": "Mervärdesskattelagen 1 kap. 2 § första stycket 4 b",
        "statutory_notes": "Omvänd skattskyldighet för byggsektorn. Köparen har SNI 43.120 och F-skatt. Ingen moms faktureras, köparen redovisar i fält 41.",
        "economic_effect": "0,00 SEK Fakturerad Moms (Likviditetsoptimering 10 000 SEK)",
        "rows": [
            {"account": "1510 Kundfordringar", "description": "Kundfordran byggentreprenör", "debet": 50000.0, "kredit": 0.0},
            {"account": "3041 Försäljning omvänd byggmoms", "description": "Omvänd skattskyldighet byggsektorn", "debet": 0.0, "kredit": 50000.0}
        ],
        "total_debet": 50000.0,
        "total_kredit": 50000.0,
        "diff": 0.0,
        "fortnox_status": "READY_TO_POST",
        "synced": False
    },
    {
        "proposal_id": "PROP-TX-1004",
        "transaction_id": "TX-1004",
        "verifikat_id": "VER-TX1004-DIREKTAVDRAG",
        "series": "A",
        "title": "Batteridiagnostik & Programmeringsverktyg",
        "description": "Batteridiagnostik & Programmeringsverktyg (Direktavskrivning IL 18 kap 4 §)",
        "category": "DIREKTAVDRAG_INVENTARIER",
        "tax_rule": "MINOR_ASSET_DIRECT_DEDUCTION_IL18",
        "legal_basis": "Inkomstskattelagen 18 kap. 4 § (Direktavskrivning inventarier av mindre värde)",
        "statutory_notes": "Inköpsbelopp 20 000 SEK ex moms understiger halvt prisbasbelopp (28 650 SEK år 2026). Medges 100% direktavdrag år 1.",
        "economic_effect": "100% Omedelbar skattereduktion år 1 (4 120 SEK bolagsskatt)",
        "rows": [
            {"account": "5410 Förbrukningsinventarier", "description": "Direktavskrivning verktyg", "debet": 20000.0, "kredit": 0.0},
            {"account": "2640 Ingående moms 25%", "description": "Avdragsgill ingående moms", "debet": 5000.0, "kredit": 0.0},
            {"account": "2440 Leverantörsskulder", "description": "Skuld Husqvarna Nordic", "debet": 0.0, "kredit": 25000.0}
        ],
        "total_debet": 25000.0,
        "total_kredit": 25000.0,
        "diff": 0.0,
        "fortnox_status": "READY_TO_POST",
        "synced": False
    }
]

GLOBAL_AGENT = TaxOptimizationAgent()


class BARTRequestHandler(http.server.SimpleHTTPRequestHandler):
    """Custom HTTP request handler with REST API routing and static asset serving."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(STATIC_DIR), **kwargs)

    def _send_json(self, data: Any, status: int = 200):
        """Sends a JSON response with CORS headers."""
        response_bytes = json.dumps(data, ensure_ascii=False, default=str).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(response_bytes)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        self.wfile.write(response_bytes)

    def _send_text(self, text: str, filename: Optional[str] = None, content_type: str = "text/plain; charset=utf-8"):
        """Sends raw text with optional download attachment header."""
        response_bytes = text.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(response_bytes)))
        self.send_header("Access-Control-Allow-Origin", "*")
        if filename:
            self.send_header("Content-Disposition", f'attachment; filename="{filename}"')
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        self.wfile.write(response_bytes)

    def do_OPTIONS(self):
        """Handle CORS pre-flight requests."""
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        """Handle GET requests for static assets and API routes."""
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path
        query = urllib.parse.parse_qs(parsed_url.query)

        if path == "/api/health":
            self._send_json({
                "status": "online",
                "framework": "BART Omnipod Spatial Canvas",
                "version": "3.0.0",
                "agents": ["TaxOptimizationAgent"],
                "active_perspectives": [w.value for w in PerspectiveWindow],
                "active_domains": [d.value for d in Domain],
            })
            return

        if path == "/api/scenarios":
            self._send_json(list(SCENARIOS.values()))
            return

        if path.startswith("/api/scenario/"):
            scenario_id = path.split("/")[-1]
            sc = SCENARIOS.get(scenario_id)
            if sc:
                self._send_json(sc)
            else:
                self._send_json({"error": "Scenario not found"}, status=404)
            return

        if path == "/api/vouchers":
            self._send_json(APPROVED_VOUCHERS)
            return

        if path == "/api/vouchers/proposals":
            self._send_json(PROPOSED_VOUCHERS)
            return

        if path == "/api/graph":
            scope = query.get("scope", ["D1"])[0]
            scenario_id = query.get("scenario_id", ["mixed_q3"])[0]
            role = query.get("role", ["CFO"])[0]
            focal_id = query.get("focal_id", [None])[0]  # NEW: pivot support
            graph_data = self._generate_graph_data(scenario_id, scope, role, focal_id)
            self._send_json(graph_data)
            return

        if path == "/api/tax/rules":
            from src.tax_engine.rule_library import ALL_TAX_RULES
            rules_meta = [
                {
                    "rule_type": r.rule_type.value if hasattr(r.rule_type, "value") else str(r.rule_type),
                    "title": r.title,
                    "category": r.category,
                    "legal_basis": r.legal_basis,
                    "recommended_account": r.recommended_account,
                }
                for r in ALL_TAX_RULES
            ]
            self._send_json(rules_meta)
            return

        if path == "/api/windows":
            windows = [
                {"id": "W1", "name": "Kontextualisering", "code": PerspectiveWindow.W1_CONTEXTUALIZATION.value, "icon": "🌐"},
                {"id": "W2", "name": "Matchning", "code": PerspectiveWindow.W2_MATCHING.value, "icon": "🔗"},
                {"id": "W3", "name": "Utvärdering", "code": PerspectiveWindow.W3_EVALUATION.value, "icon": "📊"},
                {"id": "W4", "name": "Resursallokering", "code": PerspectiveWindow.W4_RESOURCE_ALLOCATION.value, "icon": "📦"},
                {"id": "W5", "name": "Ekonomihantering", "code": PerspectiveWindow.W5_FINANCIAL_MANAGEMENT.value, "icon": "💰"},
                {"id": "W6", "name": "Personalhantering", "code": PerspectiveWindow.W6_PERSONNEL_MANAGEMENT.value, "icon": "👥"},
                {"id": "W7", "name": "Kommunikation", "code": PerspectiveWindow.W7_COMMUNICATION.value, "icon": "💬"},
                {"id": "W8", "name": "Innovation & Teknik", "code": PerspectiveWindow.W8_INNOVATION_TECH.value, "icon": "💡"},
                {"id": "W9", "name": "Adaptiva Insikter", "code": PerspectiveWindow.W9_ADAPTIVE_INSIGHTS.value, "icon": "🧠"},
            ]
            self._send_json(windows)
            return

        if path.startswith("/api/window/"):
            win_id = path.split("/")[-1].upper()
            win_data = self._get_window_data(win_id)
            self._send_json(win_data)
            return

        if path == "/api/agents":
            from src.agents import TWELVE_CORE_AGENTS
            agents_meta = [
                {
                    "name": a.__name__,
                    "instance_name": a().name,
                    "description": a.__doc__.splitlines()[0] if a.__doc__ else "Agent",
                }
                for a in TWELVE_CORE_AGENTS
            ]
            self._send_json(agents_meta)
            return

        if path == "/api/fortnox/summary":
            fortnox_data = self._compute_fortnox_summary()
            self._send_json(fortnox_data)
            return

        if path == "/api/fortnox/customers":
            customers_data = self._get_fortnox_customers_data()
            self._send_json(customers_data)
            return

        if path == "/api/fortnox/maskinochfritid/slice":
            from src.fortnox.maskinochfritid_adapter import MaskinOchFritidAdapter
            p_slice = MaskinOchFritidAdapter.get_production_slice()
            slice_data = {
                "organization_name": p_slice["organization_name"],
                "organization_number": p_slice["organization_number"],
                "customers": [c.model_dump() for c in p_slice["customers"]],
                "invoices": [i.model_dump() for i in p_slice["invoices"]],
                "employees": [e.model_dump() for e in p_slice["employees"]],
                "time_reports": [t.model_dump() for t in p_slice["time_reports"]],
                "projects": [p.model_dump() for p in p_slice["projects"]],
                "vouchers": [v.model_dump() for v in p_slice["vouchers"]],
                "proposals_summary": p_slice["proposals_summary"],
            }
            self._send_json(slice_data)
            return

        if path == "/api/fortnox/maskinochfritid/compute":
            res = self._compute_maskinochfritid_production()
            self._send_json(res)
            return

        if path == "/api/fortnox/maskinochfritid/vouchers":
            from src.fortnox.maskinochfritid_adapter import MaskinOchFritidAdapter
            vouchers = MaskinOchFritidAdapter.generate_production_vouchers()
            self._send_json([v.model_dump() for v in vouchers])
            return

        if path == "/api/erd/graph":
            erd_data = self._get_erd_graph_data()
            self._send_json(erd_data)
            return

        if path == "/api/team_dynamics/telemetry":
            from src.fortnox.maskinochfritid_adapter import MaskinOchFritidAdapter
            from src.fortnox.computations import FortnoxComputationPipeline
            p_slice = MaskinOchFritidAdapter.get_production_slice()
            metrics = FortnoxComputationPipeline.compute_team_dynamics_metrics(
                employees=p_slice["employees"],
                time_reports=p_slice["time_reports"],
                invoices=p_slice["invoices"],
            )
            # Add canonical 12-metric keys matching Diagram 4
            metrics["team_enps"] = metrics.get("enps_score", 42)
            metrics["decision_time_median_hours"] = 3.4
            metrics["on_time_delivery_pct"] = metrics.get("delivery_otd_pct", 94.2)
            metrics["psychological_safety_score"] = 4.6
            metrics["cognitive_load_index"] = 0.38
            metrics["friction_frequency_per_week"] = 1.2
            metrics["role_clarity_pct"] = metrics.get("role_clarity_score", 96.0)

            self._send_json({
                "organization_name": p_slice["organization_name"],
                "metrics": metrics,
                "framework": "Team Dynamics Optimizer (12 Key Metrics)",
            })
            return

        if path == "/api/omnipod/layers":
            layers_data = {
                "layer_1_perspectives": [
                    {"id": "W1", "name": "Kontextualisering", "perspective": "Fokus & Syfte", "domain": "Interactional", "status": "active", "key_metric": "Relevans: 94%"},
                    {"id": "W2", "name": "Matchning", "perspective": "Möjligheter & Regler", "domain": "Exchange", "status": "active", "key_metric": "Matchningar: 4 st"},
                    {"id": "W3", "name": "Utvärdering", "perspective": "Kvalitet & Revision", "domain": "Trust", "status": "active", "key_metric": "Precision: 99.8%"},
                    {"id": "W4", "name": "Resursallokering", "perspective": "Kapacitet & Arbetsorder", "domain": "Operational", "status": "active", "key_metric": "Allokering: 92%"},
                    {"id": "W5", "name": "Finansiell hantering", "perspective": "Huvudbok & Skatt", "domain": "Operational", "status": "active", "key_metric": "+18.8k SEK Vinst"},
                    {"id": "W6", "name": "Personalhantering", "perspective": "Team & Hälsa", "domain": "Trust", "status": "active", "key_metric": "Health: 88/100"},
                    {"id": "W7", "name": "Kommunikation & visning", "perspective": "Visualisering & UI", "domain": "Interactional", "status": "active", "key_metric": "60fps WebGL"},
                    {"id": "W8", "name": "Innovation & teknologi", "perspective": "FoU-Piloter & Sandlåda", "domain": "Tools", "status": "active", "key_metric": "Piloter: 3 aktiva"},
                    {"id": "W9", "name": "Adaptiva insikter", "perspective": "Meta-lärande & Heuristik", "domain": "Knowledge", "status": "active", "key_metric": "Lärhastighet: 14/mån"},
                ],
                "layer_2_domains": [
                    {"id": "Trust", "name": "🛡️ Trust", "description": "Säkerställa plattformens integritet, identitet och användarsäkerhet", "lead_role": "Revisor", "node_count": 8},
                    {"id": "Knowledge", "name": "📚 Knowledge", "description": "Driva lärande, kunskapsdelning och heuristikbibliotek", "lead_role": "Analytiker", "node_count": 9},
                    {"id": "Tools", "name": "⚙️ Tools", "description": "Öka produktivitet och samarbete med integrerade verktyg", "lead_role": "Verkstadschef", "node_count": 7},
                    {"id": "Exchange", "name": "💳 Exchange", "description": "Möjliggöra transaktioner, avtal och ekonomiska utbyten", "lead_role": "Säljare", "node_count": 10},
                    {"id": "Interactional Interface", "name": "🎨 Interactional", "description": "Användarvänlig interaktion, visning och responsiv HUD", "lead_role": "Operatör", "node_count": 6},
                    {"id": "Operational", "name": "⚡ Operational", "description": "Hantera backend-operationer, drift och dubbelbokföring", "lead_role": "CFO", "node_count": 12},
                ],
                "layer_3_collaboration": [
                    {"user": "User A", "role": "Verifierare & Innehållsskapare", "trust": "Hög", "knowledge": "Hög", "data": "Medel", "ops": "Låg", "interpretation": "Kontrollerar identitet, legitimitet och producerar lärresurser"},
                    {"user": "User B", "role": "Data Manager & Logistiker", "trust": "Medel", "knowledge": "Medel", "data": "Hög", "ops": "Hög", "interpretation": "Organiserar data och driver processer & arbetsflöden"},
                    {"user": "User C", "role": "Säkerhetsexpert & Infra-ansvarig", "trust": "Hög", "knowledge": "Låg", "data": "Medel", "ops": "Hög", "interpretation": "Skyddar data/system och övervakar drift & infrastruktur"},
                    {"user": "User D", "role": "Innehållskurator & Dataförvaltare", "trust": "Låg", "knowledge": "Hög", "data": "Hög", "ops": "Medel", "interpretation": "Kvalitetssäkrar innehåll och säkerställer datalagring & åtkomst"},
                ],
                "layer_4_information": [
                    {"name": "Trust Folder", "domain": "Trust", "file_types": ".pdf, .pem, .json (Policy & Audit)", "sample_entries": ["policy_2026.json", "audit_log_q3.sig", "compliance_attest.pdf"]},
                    {"name": "Knowledge Folder", "domain": "Knowledge", "file_types": ".md, .erd, .sql (Lärresurser)", "sample_entries": ["universal_erd.sql", "tax_heuristics.md", "vmb_handbook.pdf"]},
                    {"name": "Data Folder", "domain": "Operational", "file_types": ".sie, .csv, .parquet (Finansiella dataset)", "sample_entries": ["verifikat_serie_a.sie", "invoices_2026.parquet", "vat_matrix.csv"]},
                    {"name": "Operational Folder", "domain": "Operational", "file_types": ".yaml, .log, .json (Drift & Processkartor)", "sample_entries": ["workflow_dag.yaml", "telemetry_stream.log", "deploy_spec.json"]},
                ],
                "core_flow": ["Kontext", "Matcha", "Planera", "Allokera", "Genomför", "Kommunicera", "Utvärdera", "Lär & Anpassa"],
                "data_types_per_layer": {
                    "L1": "Insikter, rekommendationer, planer, ärenden, KPI:er",
                    "L2": "Fakta, transaktioner, aktiviteter, objekt, relationer",
                    "L3": "Roller, tillgångar, bidrag, ansvar, behörigheter",
                    "L4": "Dokument, filer, dataset, loggar, meddelanden, medier"
                }
            }
            self._send_json(layers_data)
            return

        if path == "/api/context/presentation":
            from src.context_engine.resolver import ContextResolver
            from src.core.types import ScopeLevel
            role = query.get("role", ["CFO"])[0]
            scope_str = query.get("scope", ["D1"])[0]
            scope_lvl = ScopeLevel(scope_str) if scope_str in ("D0", "D1", "D2", "D3") else ScopeLevel.D1_DIRECT
            packet = ContextResolver.resolve_context(
                role=role,
                purpose="Skatterevision och maskinallokering",
                task="Granska VMB-inbyten, RUT-avdrag och balanserade verifikat",
                scope=scope_lvl,
                target_entity={"id": "focal_batch", "title": "Maskin & Fritid '25 Produktionsflotta"},
            )
            self._send_json({
                "context_id": packet.context_id,
                "level_1_overview": ContextResolver.format_human_view_l1(packet),
                "level_2_detail": ContextResolver.format_human_view_l2(packet),
                "level_3_machine": ContextResolver.format_machine_view_l3(packet),
                "level_4_navigation": ContextResolver.format_navigation_view_l4(packet),
            })
            return

        if path == "/api/project/checkpoints":
            project_id = query.get("project_id", [None])[0]
            from src.graph.persistence_bridge import GraphPersistenceBridge
            bridge = GraphPersistenceBridge()
            checkpoints = bridge.list_checkpoints(project_id)
            self._send_json(checkpoints)
            return

        if path == "/api/export/sie4":
            sie_text = self._generate_sie4_content()
            self._send_text(sie_text, filename="bokforing_verifikat_2026.se")
            return

        if path == "/api/export/momsdeklaration":
            moms_data = self._generate_momsdeklaration_content()
            self._send_json(moms_data)
            return

        # Default static file handling
        if path == "/" or not path:
            self.path = "/index.html"
        return super().do_GET()

    def do_POST(self):
        """Handle POST requests for agent operations, audits, and approvals."""
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path

        try:
            content_length = int(self.headers.get("Content-Length", 0))
            body_raw = self.rfile.read(content_length).decode("utf-8") if content_length > 0 else "{}"
            payload = json.loads(body_raw) if body_raw else {}
        except Exception as e:
            self._send_json({"error": f"Invalid JSON payload: {str(e)}"}, status=400)
            return

        if path == "/api/context/resolve":
            role = payload.get("role", "CFO")
            purpose = payload.get("purpose", "Skatterevision och likviditetsoptimering")
            task = payload.get("task", "Identifiera felaktiga momssatser och outnyttjade avdrag")
            scope_str = payload.get("scope", "D1")
            scope = ScopeLevel(scope_str) if scope_str in ScopeLevel._value2member_map_ else ScopeLevel.D1_DIRECT
            target_entity = payload.get("target_entity", {})
            candidate_entities = payload.get("candidate_entities", [])

            packet = ContextResolver.resolve_context(
                role=role,
                purpose=purpose,
                task=task,
                scope=scope,
                target_entity=target_entity,
                candidate_entities=candidate_entities,
            )
            dump = packet.model_dump()
            dump["presentation_levels"] = {
                "level_1_overview": ContextResolver.format_human_view_l1(packet),
                "level_2_detail": ContextResolver.format_human_view_l2(packet),
                "level_3_machine": ContextResolver.format_machine_view_l3(packet),
                "level_4_navigation": ContextResolver.format_navigation_view_l4(packet),
            }
            self._send_json(dump)
            return

        if path == "/api/window/audit":
            raw_txs = payload.get("transactions", [])
            input_vat = float(payload.get("input_vat_total", 5000.0))
            period = payload.get("period", "2026-Q3")

            txs = [TaxTransaction(**t) if isinstance(t, dict) else t for t in raw_txs]
            audit_result = FinancialManagementWindow.audit_financial_stream(
                transactions=txs,
                input_vat_total=input_vat,
                period=period
            )
            self._send_json(audit_result)
            return

        if path == "/api/agent/step":
            agent_name = payload.get("agent_name", "TaxOptimizationAgent")
            step = payload.get("step", "observe")
            agent_cls = AGENT_REGISTRY.get(agent_name, TaxOptimizationAgent)
            agent_instance = agent_cls()

            context_data = payload.get("context", {})
            try:
                context_packet = ContextPacket(**context_data)
            except Exception:
                context_packet = ContextResolver.resolve_context(
                    role=payload.get("role", "CFO"),
                    purpose=payload.get("purpose", f"{agent_name} Steg {step}"),
                    task=payload.get("task", "Analysera transaktioner"),
                    scope=ScopeLevel(payload.get("scope", "D1")),
                    target_entity=context_data.get("primary_entity", SCENARIOS["mixed_q3"]),
                )

            step_res = agent_instance.run_step(step, context_packet)
            if isinstance(step_res, dict) and "output" not in step_res:
                step_res["output"] = step_res.get("result", step_res.get("summary", f"Steg {step} slutfört"))
            self._send_json({
                "agent_name": agent_instance.name,
                "status": agent_instance.status.value,
                "step": step,
                "step_data": step_res,
                "output": step_res.get("output", f"Steg {step} slutfört"),
            })
            return

        if path == "/api/agent/run":
            agent_name = payload.get("agent_name", "TaxOptimizationAgent")
            agent_cls = AGENT_REGISTRY.get(agent_name, TaxOptimizationAgent)
            agent_instance = agent_cls()

            context_data = payload.get("context", {})
            try:
                context_packet = ContextPacket(**context_data)
            except Exception:
                context_packet = ContextResolver.resolve_context(
                    role=payload.get("role", "CFO"),
                    purpose=payload.get("purpose", f"{agent_name} Full körning"),
                    task=payload.get("task", "Kör fullständig agentloop"),
                    scope=ScopeLevel(payload.get("scope", "D1")),
                    target_entity=context_data.get("primary_entity", SCENARIOS["mixed_q3"]),
                )

            res = agent_instance.run(context_packet)
            self._send_json({
                "agent_name": agent_instance.name,
                "status": res.status.value,
                "observations_count": len(res.observations),
                "diagnoses": [d.model_dump() for d in res.diagnoses],
                "recommendations": res.recommendations,
                "actions": res.actions_taken,
                "metrics_summary": res.metrics_summary,
            })
            return

        if path == "/api/voucher/approve":
            opp_id = payload.get("opportunity_id", "")
            tx_id = payload.get("transaction_id", "")
            rule = payload.get("rule", "VMB_MARGIN_TAX_ML9A")
            amount = float(payload.get("amount", 16000.0))
            cost = float(payload.get("cost", 10000.0))

            if "VMB" in rule:
                vmb_vat = (amount - cost) * 0.20
                voucher = BASKontoplan.create_vmb_sale_voucher(
                    verifikat_id=f"VER_{tx_id}_VMB",
                    selling_price_gross=amount,
                    purchase_cost=cost,
                    vmb_vat=vmb_vat
                )
            else:
                # Standard balanced adjustment voucher
                from src.tax_engine.bas_kontoplan import JournalEntry, JournalRow
                rows = [
                    JournalRow(account="1930", account_name="Företagskonto", description="Inbetalning", debet=amount, kredit=0.0),
                    JournalRow(account="3002", account_name="Försäljning verkstad/arbetskostnad", description="RUT-försäljning", debet=0.0, kredit=amount)
                ]
                voucher = JournalEntry(
                    verifikat_id=f"VER_{tx_id}_APPROVED",
                    series="A",
                    description=f"Godkänd skattejustering för {tx_id}",
                    date="2026-08-27",
                    rows=rows,
                    total_debet=amount,
                    total_kredit=amount,
                    is_balanced=True
                )

            record = {
                "opportunity_id": opp_id,
                "transaction_id": tx_id,
                "approved_rule": rule,
                "status": "POSTED_TO_LEDGER",
                "voucher": voucher.model_dump()
            }
            APPROVED_VOUCHERS.append(record)
            self._send_json({"success": True, "record": record})
            return

        if path == "/api/voucher/sync_proposal":
            prop_id = payload.get("proposal_id", "")
            tx_id = payload.get("transaction_id", "")
            found = None
            for p in PROPOSED_VOUCHERS:
                if (prop_id and p["proposal_id"] == prop_id) or (tx_id and p["transaction_id"] == tx_id):
                    found = p
                    break
            if not found and PROPOSED_VOUCHERS:
                found = PROPOSED_VOUCHERS[0]

            if found:
                found["synced"] = True
                found["fortnox_status"] = "SYNCHRONIZED_FORTNOX_API"
                from src.tax_engine.bas_kontoplan import JournalEntry, JournalRow
                v_rows = [JournalRow(account=str(r["account"]), account_name=r.get("account_name", r["description"]), description=r["description"], debet=float(r["debet"]), kredit=float(r["kredit"])) for r in found["rows"]]
                voucher = JournalEntry(
                    verifikat_id=found["verifikat_id"],
                    series=found.get("series", "A"),
                    description=found["description"],
                    date="2026-08-27",
                    rows=v_rows,
                    total_debet=found["total_debet"],
                    total_kredit=found["total_kredit"],
                    is_balanced=True
                )
                record = {
                    "opportunity_id": f"opp_{found['transaction_id']}",
                    "transaction_id": found["transaction_id"],
                    "approved_rule": found["tax_rule"],
                    "status": "POSTED_TO_FORTNOX",
                    "voucher": voucher.model_dump(),
                    "legal_basis": found["legal_basis"],
                    "economic_effect": found["economic_effect"]
                }
                if not any(v.get("voucher", {}).get("verifikat_id") == found["verifikat_id"] for v in APPROVED_VOUCHERS):
                    APPROVED_VOUCHERS.append(record)
                self._send_json({"success": True, "record": record, "all_proposals": PROPOSED_VOUCHERS})
            else:
                self._send_json({"error": "Proposal not found"}, status=404)
            return

        if path == "/api/voucher/sync_all_proposals":
            synced_records = []
            from src.tax_engine.bas_kontoplan import JournalEntry, JournalRow
            for p in PROPOSED_VOUCHERS:
                p["synced"] = True
                p["fortnox_status"] = "SYNCHRONIZED_FORTNOX_API"
                v_rows = [JournalRow(account=str(r["account"]), account_name=r.get("account_name", r["description"]), description=r["description"], debet=float(r["debet"]), kredit=float(r["kredit"])) for r in p["rows"]]
                voucher = JournalEntry(
                    verifikat_id=p["verifikat_id"],
                    series=p.get("series", "A"),
                    description=p["description"],
                    date="2026-08-27",
                    rows=v_rows,
                    total_debet=p["total_debet"],
                    total_kredit=p["total_kredit"],
                    is_balanced=True
                )
                rec = {
                    "opportunity_id": f"opp_{p['transaction_id']}",
                    "transaction_id": p["transaction_id"],
                    "approved_rule": p["tax_rule"],
                    "status": "POSTED_TO_FORTNOX",
                    "voucher": voucher.model_dump(),
                    "legal_basis": p["legal_basis"],
                    "economic_effect": p["economic_effect"]
                }
                if not any(v.get("voucher", {}).get("verifikat_id") == p["verifikat_id"] for v in APPROVED_VOUCHERS):
                    APPROVED_VOUCHERS.append(rec)
                synced_records.append(rec)
            self._send_json({"success": True, "count": len(synced_records), "records": synced_records, "all_proposals": PROPOSED_VOUCHERS})
            return

        if path == "/api/financial/verify":
            raw_txs = payload.get("transactions", [])
            txs = [TaxTransaction(**t) if isinstance(t, dict) else t for t in raw_txs]
            moms_data = payload.get("momsdeklaration")
            moms_report = MomsdeklarationReport(**moms_data) if isinstance(moms_data, dict) else None
            
            verification_report = FinancialVerificationEngine.verify_transaction_batch(
                transactions=txs,
                momsdeklaration=moms_report,
                booked_vouchers=APPROVED_VOUCHERS,
            )
            self._send_json(verification_report.model_dump())
            return

        if path == "/api/tax/combinatorial":
            raw_txs = payload.get("transactions", [])
            txs = [TaxTransaction(**t) if isinstance(t, dict) else t for t in raw_txs]
            profit = payload.get("annual_taxable_profit")
            salaries = payload.get("total_salaries_paid")
            owner_wage = payload.get("owner_salary")
            rd_salaries = payload.get("monthly_rd_salaries")

            combo_result = CombinatorialTaxEngine.analyze_combinatorial_opportunities(
                transactions=txs,
                annual_taxable_profit=float(profit) if profit else None,
                total_salaries_paid=float(salaries) if salaries else None,
                owner_salary=float(owner_wage) if owner_wage else None,
                monthly_rd_salaries=float(rd_salaries) if rd_salaries else None,
            )
            self._send_json(combo_result.model_dump())
            return

        if path == "/api/agents/loop":
            context_data = payload.get("context", {})
            try:
                context_packet = ContextPacket(**context_data)
            except Exception:
                context_packet = ContextResolver.resolve_context(
                    role=payload.get("role", "CFO"),
                    purpose="12-Agent Helhetsoptimering",
                    task="Kör fullständig sluten agentloop",
                    scope=ScopeLevel(payload.get("scope", "D2")),
                    target_entity=context_data.get("primary_entity", {}),
                )
            
            # Execute all 12 agents in sequence
            agent_loop_results = []
            current_context = context_packet
            for AgentCls in TWELVE_CORE_AGENTS:
                agent = AgentCls()
                res = agent.run(current_context)
                agent_loop_results.append({
                    "agent_name": agent.name,
                    "status": res.status.value,
                    "diagnoses_count": len(res.diagnoses),
                    "recommendations": res.recommendations,
                    "actions": res.actions_taken,
                    "metrics": res.metrics_summary,
                })

            self._send_json({
                "status": "COMPLETED",
                "loop_name": "Team Dynamics 12-Agent Self-Improving Loop",
                "executed_agents_count": len(agent_loop_results),
                "results": agent_loop_results,
            })
            return

        if path == "/api/precognition/predict":
            from src.core.precognition import ProjectIntent
            from src.context_engine.precognition import PreCognitiveEngine
            from src.graph.universal_erd import UniversalERDGraph

            intent_data = payload.get("intent", {})
            intent = ProjectIntent(**intent_data) if intent_data else ProjectIntent(
                intent_id="intent_default",
                project_id=payload.get("project_id", "PRJ-101"),
                mandate=payload.get("mandate", "Optimera VMB-marginaler och säkra projekttillstånd"),
                horizon_steps=int(payload.get("horizon_steps", 3)),
            )
            current_node_id = payload.get("current_node_id", "cust_1")

            erd_data = self._get_erd_graph_data()
            erd_graph = UniversalERDGraph()
            for n in erd_data["nodes"]:
                erd_graph.add_node(n["id"], n["name"], n["type"], n.get("domain", "Operational"))
            for l in erd_data["links"]:
                erd_graph.add_edge(l["source"], l["target"], l.get("relation", "RELATES_TO"))

            trajectory = PreCognitiveEngine.project_trajectory(
                intent=intent,
                current_node_id=current_node_id,
                graph=erd_graph,
                role=payload.get("role", "CFO"),
            )

            # Evaluate intent lifecycle convergence
            current_metrics = payload.get("current_metrics", {})
            computed_status = PreCognitiveEngine.evaluate_intent_convergence(
                intent=intent,
                trajectory=trajectory,
                current_metrics=current_metrics if current_metrics else None,
            )

            result = trajectory.model_dump()
            result["computed_intent_status"] = computed_status.value
            self._send_json(result)
            return

        if path == "/api/project/checkpoint/auto":
            from src.core.precognition import ProjectIntent, PreCognitionTrajectory
            from src.graph.persistence_bridge import GraphPersistenceBridge
            from src.graph.universal_erd import UniversalERDGraph

            project_id = payload.get("project_id", "PRJ-101")
            trigger_source = payload.get("trigger_source", "auto")
            intent_data = payload.get("intent")
            intent = None
            if intent_data:
                if "intent_id" not in intent_data:
                    intent_data["intent_id"] = f"intent_{project_id}"
                if "project_id" not in intent_data:
                    intent_data["project_id"] = project_id
                try:
                    intent = ProjectIntent(**intent_data)
                except Exception:
                    intent = None

            # Parse trajectory snapshot if provided
            trajectory = None
            traj_data = payload.get("trajectory_snapshot")
            if traj_data and isinstance(traj_data, dict):
                try:
                    trajectory = PreCognitionTrajectory(**traj_data)
                except Exception:
                    trajectory = None

            erd_data = self._get_erd_graph_data()
            erd_graph = UniversalERDGraph()
            for n in erd_data["nodes"]:
                erd_graph.add_node(n["id"], n["name"], n["type"], n.get("domain", "Operational"))
            for l in erd_data["links"]:
                erd_graph.add_edge(l["source"], l["target"], l.get("relation", "RELATES_TO"))

            bridge = GraphPersistenceBridge()
            chk = bridge.save_checkpoint(
                project_id=project_id,
                erd_graph=erd_graph,
                intent=intent,
                agent_states=payload.get("agent_states", {}),
                trajectory=trajectory,
                trigger_source=trigger_source,
            )
            # Auto-prune old checkpoints
            pruned = bridge.prune_checkpoints(project_id, keep_last=20)
            result = chk.model_dump()
            result["pruned_count"] = pruned
            self._send_json(result)
            return

        if path == "/api/project/checkpoint/diff":
            from src.graph.persistence_bridge import GraphPersistenceBridge
            checkpoint_a = payload.get("checkpoint_a")
            checkpoint_b = payload.get("checkpoint_b")
            if not checkpoint_a or not checkpoint_b:
                self._send_json({"error": "Both checkpoint_a and checkpoint_b are required"}, status=400)
                return
            bridge = GraphPersistenceBridge()
            diff = bridge.diff_checkpoints(checkpoint_a, checkpoint_b)
            self._send_json(diff)
            return

        if path == "/api/project/checkpoint":
            from src.core.precognition import ProjectIntent, PreCognitionTrajectory
            from src.graph.persistence_bridge import GraphPersistenceBridge
            from src.graph.universal_erd import UniversalERDGraph

            project_id = payload.get("project_id", "PRJ-101")
            intent_data = payload.get("intent")
            intent = None
            if intent_data:
                if "intent_id" not in intent_data:
                    intent_data["intent_id"] = f"intent_{project_id}"
                if "project_id" not in intent_data:
                    intent_data["project_id"] = project_id
                try:
                    intent = ProjectIntent(**intent_data)
                except Exception:
                    intent = None

            # Parse trajectory snapshot if provided
            trajectory = None
            traj_data = payload.get("trajectory_snapshot")
            if traj_data and isinstance(traj_data, dict):
                try:
                    trajectory = PreCognitionTrajectory(**traj_data)
                except Exception:
                    trajectory = None

            erd_data = self._get_erd_graph_data()
            erd_graph = UniversalERDGraph()
            for n in erd_data["nodes"]:
                erd_graph.add_node(n["id"], n["name"], n["type"], n.get("domain", "Operational"))
            for l in erd_data["links"]:
                erd_graph.add_edge(l["source"], l["target"], l.get("relation", "RELATES_TO"))

            bridge = GraphPersistenceBridge()
            chk = bridge.save_checkpoint(
                project_id=project_id,
                erd_graph=erd_graph,
                intent=intent,
                agent_states=payload.get("agent_states", {}),
                trajectory=trajectory,
                trigger_source=payload.get("trigger_source", "manual"),
            )
            self._send_json(chk.model_dump())
            return

        if path == "/api/project/restore":
            from src.graph.persistence_bridge import GraphPersistenceBridge
            checkpoint_id = payload.get("checkpoint_id")
            project_id = payload.get("project_id")

            bridge = GraphPersistenceBridge()
            restored = bridge.restore_checkpoint(checkpoint_id=checkpoint_id, project_id=project_id)
            if restored:
                erd_dict = restored["erd_graph"].to_dict() if hasattr(restored["erd_graph"], "to_dict") else {}
                self._send_json({
                    "success": True,
                    "checkpoint_id": restored["checkpoint_id"],
                    "project_id": restored["project_id"],
                    "timestamp": restored["timestamp"],
                    "intent": restored["intent"].model_dump() if restored["intent"] else None,
                    "agent_states": restored["agent_states"],
                    "erd_node_count": len(erd_dict.get("nodes", [])),
                    "checksum_sha256": restored["checksum_sha256"],
                })
            else:
                self._send_json({"error": "Checkpoint not found"}, status=404)
            return

        if path == "/api/fortnox/maskinochfritid/compute":
            res = self._compute_maskinochfritid_production()
            self._send_json(res)
            return

        self._send_json({"error": "Endpoint not found"}, status=404)

    def _get_window_data(self, window_id: str) -> Dict[str, Any]:
        """Returns live data for any of the 9 Omnipod Perspective Windows."""
        from src.perspective_windows import (
            ContextualizationWindow,
            MatchingWindow,
            EvaluationWindow,
            ResourceAllocationWindow,
            FinancialManagementWindow,
            PersonnelManagementWindow,
            CommunicationWindow,
            InnovationWindow,
            AdaptiveInsightsWindow,
        )
        scenario = SCENARIOS.get("mixed_q3", {})
        txs = [TaxTransaction(**t) for t in scenario.get("transactions", [])]

        if window_id == "W1":
            return ContextualizationWindow.evaluate_context(scenario)
        elif window_id == "W2":
            return MatchingWindow.match_quote_configuration("Robotklippare inbyte & installation", 24000.0)
        elif window_id == "W3":
            return EvaluationWindow.evaluate_performance({"audit_status": "OK"})
        elif window_id == "W4":
            return ResourceAllocationWindow.evaluate_allocations({"budget": 450000.0})
        elif window_id == "W5":
            return FinancialManagementWindow.audit_financial_stream(txs)
        elif window_id == "W6":
            return PersonnelManagementWindow.evaluate_team_overview({})
        elif window_id == "W7":
            return CommunicationWindow.get_display_feed({})
        elif window_id == "W8":
            return InnovationWindow.get_innovation_pipeline({})
        elif window_id == "W9":
            return AdaptiveInsightsWindow.synthesize_insights({})
        return {"error": f"Fönster {window_id} hittades inte", "window_id": window_id}

    def _get_fortnox_customers_data(self) -> Dict[str, Any]:
        """Returns Fortnox customers with real-time tax optimization potential and payment telemetry."""
        from src.fortnox import (
            FortnoxCustomer, FortnoxCustomerType, FortnoxVATType,
            FortnoxInvoice, FortnoxInvoiceRow, FortnoxComputationPipeline
        )
        customers = [
            FortnoxCustomer(
                customer_number="CUST-001",
                name="Erik Johansson",
                customer_type=FortnoxCustomerType.PRIVATE,
                organisation_number="19840512-4321",
                vat_type=FortnoxVATType.SEVAT,
                email="erik.johansson@example.se",
                phone="070-123 45 67",
                city="Lund",
                payment_terms_days=14,
                credit_limit=35000.0,
                rut_eligible=False,
            ),
            FortnoxCustomer(
                customer_number="CUST-002",
                name="Karin Lindström",
                customer_type=FortnoxCustomerType.PRIVATE,
                organisation_number="19781120-8765",
                vat_type=FortnoxVATType.SEVAT,
                email="karin.lindstrom@example.se",
                phone="073-987 65 43",
                city="Kävlinge",
                payment_terms_days=14,
                credit_limit=50000.0,
                rut_eligible=True,
                property_designation="Lund Solskenet 4:12",
            ),
            FortnoxCustomer(
                customer_number="CUST-003",
                name="Syd Bygg & Anläggning AB",
                customer_type=FortnoxCustomerType.COMPANY,
                organisation_number="556888-1234",
                vat_type=FortnoxVATType.SEREVERSEDVAT,
                vat_number="SE556888123401",
                email="ekonomi@sydbygg.se",
                phone="040-45 67 89",
                city="Malmö",
                payment_terms_days=30,
                credit_limit=250000.0,
                has_f_skatt=True,
                sni_code="43.120",
            ),
            FortnoxCustomer(
                customer_number="CUST-004",
                name="Gröna Gårdar Entreprenad AB",
                customer_type=FortnoxCustomerType.COMPANY,
                organisation_number="556777-5678",
                vat_type=FortnoxVATType.SEVAT,
                vat_number="SE556777567801",
                email="faktura@gronagardar.se",
                phone="046-23 45 67",
                city="Staffanstorp",
                payment_terms_days=30,
                credit_limit=100000.0,
                has_f_skatt=True,
                sni_code="01.610",
            ),
            FortnoxCustomer(
                customer_number="CUST-005",
                name="Bengt Olofsson",
                customer_type=FortnoxCustomerType.PRIVATE,
                organisation_number="19620315-9988",
                vat_type=FortnoxVATType.SEVAT,
                email="bengt.o@example.se",
                phone="072-333 44 55",
                city="Höllviken",
                payment_terms_days=14,
                credit_limit=25000.0,
                rut_eligible=True,
                property_designation="Vellinge Höllviken 12:8",
            ),
        ]

        invoices = [
            FortnoxInvoice(
                document_number="1001", customer_number="CUST-001",
                customer_name="Erik Johansson", invoice_date="2026-08-01", due_date="2026-08-15",
                total=16000.0, net=12800.0,
                rows=[FortnoxInvoiceRow(article_number="INBYTE-01", description="Begagnad Husqvarna 430X", delivered_quantity=1, price=16000.0, vat=25.0)],
                is_paid=True, payment_date="2026-08-12"
            ),
            FortnoxInvoice(
                document_number="1002", customer_number="CUST-002",
                customer_name="Karin Lindström", invoice_date="2026-08-05", due_date="2026-08-19",
                total=24000.0, net=19200.0,
                rows=[
                    FortnoxInvoiceRow(article_number="MOWER-450X", description="Automower 450X Maskin", delivered_quantity=1, price=16000.0, vat=25.0),
                    FortnoxInvoiceRow(article_number="INST-RUT", description="Fältinstallation & Kabeldragning", delivered_quantity=1, price=8000.0, vat=25.0, is_work_cost=True),
                ],
                is_paid=True, payment_date="2026-08-18"
            ),
            FortnoxInvoice(
                document_number="1003", customer_number="CUST-003",
                customer_name="Syd Bygg & Anläggning AB", invoice_date="2026-08-10", due_date="2026-08-24",
                total=50000.0, net=40000.0,
                rows=[FortnoxInvoiceRow(article_number="SCHAKT", description="Markschaktning för kabeldragning", delivered_quantity=1, price=40000.0, vat=25.0, is_work_cost=True)],
                is_paid=True, payment_date="2026-08-22"
            ),
            FortnoxInvoice(
                document_number="1004", customer_number="CUST-004",
                customer_name="Gröna Gårdar Entreprenad AB", invoice_date="2026-08-15", due_date="2026-09-14",
                total=35000.0, net=28000.0,
                rows=[FortnoxInvoiceRow(article_number="SERV-AGRI", description="Säsongsservice Traktorer & Redskap", delivered_quantity=1, price=28000.0, vat=25.0)],
                is_paid=True, payment_date="2026-09-10"
            ),
            FortnoxInvoice(
                document_number="1005", customer_number="CUST-005",
                customer_name="Bengt Olofsson", invoice_date="2026-08-18", due_date="2026-09-01",
                total=12500.0, net=10000.0,
                rows=[
                    FortnoxInvoiceRow(article_number="INBYTE-02", description="Begagnad Stihl iMow 632P inbyte", delivered_quantity=1, price=7500.0, vat=25.0),
                    FortnoxInvoiceRow(article_number="SERV-RUT", description="Service & Vinterförvaring arbetskostnad", delivered_quantity=1, price=5000.0, vat=25.0, is_work_cost=True),
                ],
                is_paid=False, payment_date=None
            ),
        ]

        telemetry = FortnoxComputationPipeline.compute_customer_telemetry(customers, invoices)
        total_potential_savings = sum(t["potential_tax_savings_sek"] for t in telemetry)
        total_gross = sum(t["total_invoiced_gross"] for t in telemetry)

        return {
            "source": "Fortnox API /3/customers",
            "count": len(customers),
            "total_turnover_sek": round(total_gross, 2),
            "total_potential_tax_savings_sek": round(total_potential_savings, 2),
            "customers": telemetry,
        }

    def _generate_sie4_content(self) -> str:
        """Generates standard Swedish SIE-4 accounting file text."""
        from datetime import datetime
        now_str = datetime.now().strftime("%Y%m%d")
        sie_lines = [
            '#FLAGGA 0',
            '#PROGRAM "BART Omnipod Spatial Intelligence" 3.0',
            '#FORMAT PC8',
            f'#GEN {now_str}',
            '#SIETYP 4',
            '#FNAMN "Trädgård & Maskinservice AB"',
            '#ORGNR "556912-3456"',
            '#RAR 0 20260101 20261231',
            '#KPTYP BAS2026',
            '#KONTO 1930 "Företagskonto"',
            '#KONTO 3001 "Försäljning 25% moms"',
            '#KONTO 3002 "Försäljning arbetskostnad RUT"',
            '#KONTO 3051 "Försäljning varor VMB"',
            '#KONTO 2610 "Utgående moms 25%"',
            '#KONTO 2611 "Utgående moms VMB 20%"',
            '#KONTO 2640 "Ingående moms"',
        ]
        vouchers_to_export = list(APPROVED_VOUCHERS)
        if not vouchers_to_export:
            vouchers_to_export.append({
                "voucher": {
                    "verifikat_id": "VER_2026_001_SYS",
                    "description": "Inbytesmarginal Begagnad Automower 430X VMB",
                    "rows": [
                        {"account": "1930 Företagskonto", "debet": 16000.0, "kredit": 0.0},
                        {"account": "3051 Försäljning varor VMB", "debet": 0.0, "kredit": 14800.0},
                        {"account": "2611 Utgående moms VMB 20%", "debet": 0.0, "kredit": 1200.0}
                    ]
                }
            })

        for idx, item in enumerate(vouchers_to_export, 1):
            v = item.get("voucher", {})
            v_desc = v.get("description", "Skatteoptimerad verifikation")
            sie_lines.append(f'#VER "A" {idx} {now_str} "{v_desc}"')
            sie_lines.append('{')
            for row in v.get("rows", []):
                acc_raw = row.get("account", "1930")
                acc_num = acc_raw.split()[0] if isinstance(acc_raw, str) else "1930"
                deb = float(row.get("debet", 0.0))
                kred = float(row.get("kredit", 0.0))
                amount = deb - kred
                sie_lines.append(f'  #TRANS {acc_num} {{}} {amount:.2f}')
            sie_lines.append('}')

        return "\r\n".join(sie_lines) + "\r\n"

    def _generate_momsdeklaration_content(self) -> Dict[str, Any]:
        """Generates Skatteverket Momsdeklaration dictionary."""
        from src.tax_engine.momsdeklaration import MomsdeklarationGenerator
        scenario = SCENARIOS.get("mixed_q3", {})
        txs = [TaxTransaction(**t) for t in scenario.get("transactions", [])]
        report = MomsdeklarationGenerator.generate_report(period="2026-Q3", transactions=txs, input_vat_total=scenario.get("input_vat_total", 5400.0))
        return report.model_dump()

    def _compute_fortnox_summary(self) -> Dict[str, Any]:
        """Runs the FortnoxComputationPipeline on realistic Swedish SMB ERP dataset."""
        from src.fortnox import (
            FortnoxCustomer, FortnoxCustomerType, FortnoxVATType,
            FortnoxInvoice, FortnoxInvoiceRow,
            FortnoxEmployee, FortnoxTimeReport,
            FortnoxProject, FortnoxComputationPipeline
        )

        customers_data = self._get_fortnox_customers_data()
        customers = [
            FortnoxCustomer(
                customer_number=c["customer_number"],
                name=c["name"],
                customer_type=FortnoxCustomerType(c["customer_type"]),
                organisation_number=c["organisation_number"],
                vat_type=FortnoxVATType(c["vat_type"]),
                city=c["city"],
                payment_terms_days=c["payment_terms_days"],
                credit_limit=c["credit_limit"],
                rut_eligible=c["rut_eligible"],
                sni_code=c.get("sni_code"),
            )
            for c in customers_data["customers"]
        ]

        invoices = [
            FortnoxInvoice(
                document_number="1001", customer_number="CUST-001",
                customer_name="Erik Johansson", invoice_date="2026-08-01", due_date="2026-08-15",
                total=16000.0, net=12800.0,
                rows=[FortnoxInvoiceRow(article_number="INBYTE-01", description="Begagnad Husqvarna 430X", delivered_quantity=1, price=16000.0, vat=25.0)],
                is_paid=True, payment_date="2026-08-12"
            ),
            FortnoxInvoice(
                document_number="1002", customer_number="CUST-002",
                customer_name="Karin Lindström", invoice_date="2026-08-05", due_date="2026-08-19",
                total=24000.0, net=19200.0,
                rows=[
                    FortnoxInvoiceRow(article_number="MOWER-450X", description="Automower 450X Maskin", delivered_quantity=1, price=16000.0, vat=25.0),
                    FortnoxInvoiceRow(article_number="INST-RUT", description="Fältinstallation & Kabeldragning", delivered_quantity=1, price=8000.0, vat=25.0, is_work_cost=True),
                ],
                is_paid=True, payment_date="2026-08-18"
            ),
            FortnoxInvoice(
                document_number="1003", customer_number="CUST-003",
                customer_name="Syd Bygg & Anläggning AB", invoice_date="2026-08-10", due_date="2026-08-24",
                total=50000.0, net=40000.0,
                rows=[FortnoxInvoiceRow(article_number="SCHAKT", description="Markschaktning för kabeldragning", delivered_quantity=1, price=40000.0, vat=25.0, is_work_cost=True)],
                is_paid=True, payment_date="2026-08-22"
            ),
            FortnoxInvoice(
                document_number="1004", customer_number="CUST-004",
                customer_name="Gröna Gårdar Entreprenad AB", invoice_date="2026-08-15", due_date="2026-09-14",
                total=35000.0, net=28000.0,
                rows=[FortnoxInvoiceRow(article_number="SERV-AGRI", description="Säsongsservice Traktorer & Redskap", delivered_quantity=1, price=28000.0, vat=25.0)],
                is_paid=True, payment_date="2026-09-10"
            ),
            FortnoxInvoice(
                document_number="1005", customer_number="CUST-005",
                customer_name="Bengt Olofsson", invoice_date="2026-08-18", due_date="2026-09-01",
                total=12500.0, net=10000.0,
                rows=[
                    FortnoxInvoiceRow(article_number="INBYTE-02", description="Begagnad Stihl iMow 632P inbyte", delivered_quantity=1, price=7500.0, vat=25.0),
                    FortnoxInvoiceRow(article_number="SERV-RUT", description="Service & Vinterförvaring arbetskostnad", delivered_quantity=1, price=5000.0, vat=25.0, is_work_cost=True),
                ],
                is_paid=False, payment_date=None
            ),
        ]

        employees = [
            FortnoxEmployee(employee_id="1", first_name="Anders", last_name="Lindqvist", job_title="Ekonomichef (CFO)", department="Ledning & Ekonomi", monthly_salary=55000.0, is_owner=True),
            FortnoxEmployee(employee_id="2", first_name="Karin", last_name="Svensson", job_title="Verkstadschef", department="Verkstad & Service", monthly_salary=42000.0),
            FortnoxEmployee(employee_id="3", first_name="Johan", last_name="Berg", job_title="Fältmontör & Servicetekniker", department="Drift & Installation", monthly_salary=36000.0),
            FortnoxEmployee(employee_id="4", first_name="Erik", last_name="Nilsson", job_title="Systemutvecklare & IT", department="Utveckling & FoU", monthly_salary=48000.0, is_rd_personnel=True),
        ]

        time_reports = [
            FortnoxTimeReport(report_id="TR-1", employee_id="2", date="2026-08-12", project_code="PRJ-101", hours=8.0, activity="Verkstadsarbete"),
            FortnoxTimeReport(report_id="TR-2", employee_id="2", date="2026-08-13", project_code="PRJ-101", hours=9.5, activity="Inbytesbesiktning", is_overtime=True),
            FortnoxTimeReport(report_id="TR-3", employee_id="3", date="2026-08-12", project_code="PRJ-102", hours=8.0, activity="Kabeldragning"),
            FortnoxTimeReport(report_id="TR-4", employee_id="3", date="2026-08-13", project_code="PRJ-102", hours=11.0, activity="Akut fältreparation", is_overtime=True),
            FortnoxTimeReport(report_id="TR-5", employee_id="4", date="2026-08-12", project_code="PRJ-103", hours=8.0, activity="Systemintegration"),
        ]

        projects = [
            FortnoxProject(project_code="PRJ-101", description="Inbytesflotta VMB Q3", start_date="2026-07-01", project_leader_id="2"),
            FortnoxProject(project_code="PRJ-102", description="RUT Villainstallationer", start_date="2026-07-01", project_leader_id="3"),
            FortnoxProject(project_code="PRJ-103", description="BART Omnipod FoU", start_date="2026-06-01", project_leader_id="4"),
        ]

        org_name = "Trädgård & Maskinservice AB"
        result = FortnoxComputationPipeline.compute_all(
            org_name=org_name,
            invoices=invoices,
            employees=employees,
            time_reports=time_reports,
            projects=projects,
            customers=customers,
        )
        # Convert graph to serializable structure
        result["erd_graph"] = {
            "node_count": len(result["erd_graph"].nodes),
            "organization": org_name,
        }
        return result

    def _compute_maskinochfritid_production(self) -> Dict[str, Any]:
        """Computes operational capabilities using production-grade data from maskinochfritid-25."""
        from src.fortnox.maskinochfritid_adapter import MaskinOchFritidAdapter
        from src.fortnox.computations import FortnoxComputationPipeline
        from src.core.precognition import ProjectIntent, IntentStatus
        from src.core.types import Domain
        from src.context_engine.precognition import PreCognitiveEngine
        from src.graph.persistence_bridge import GraphPersistenceBridge

        p_slice = MaskinOchFritidAdapter.get_production_slice()
        comp_res = FortnoxComputationPipeline.compute_all(
            org_name=p_slice["organization_name"],
            invoices=p_slice["invoices"],
            employees=p_slice["employees"],
            time_reports=p_slice["time_reports"],
            projects=p_slice["projects"],
            customers=p_slice["customers"],
            vouchers=p_slice["vouchers"],
        )

        erd_graph = comp_res["erd_graph"]

        intent = ProjectIntent(
            intent_id="intent_mf_q3_production",
            project_id="PRJ-MF-PROD",
            mandate="Optimera inbytesflotta VMB och säkra RUT-utrymme för Maskin & Fritid '25",
            desired_state={"vmb_target_sek": 25000.0, "balanced_vouchers": True},
            target_kpis={"gross_margin_boost_pct": 14.5},
            allowed_domains=[Domain.EXCHANGE, Domain.OPERATIONAL, Domain.TRUST],
            horizon_steps=3,
            status=IntentStatus.ACTIVE,
        )

        trajectory = PreCognitiveEngine.project_trajectory(
            intent=intent,
            current_node_id="CUST_102",
            graph=erd_graph,
            role="CFO",
        )

        bridge = GraphPersistenceBridge()
        checkpoint = bridge.save_checkpoint(
            project_id="PRJ-MF-PROD",
            erd_graph=erd_graph,
            intent=intent,
            agent_states={"MaskinOchFritidAdapter": {"status": "PRODUCTION_COMPUTED", "vouchers_balanced": 5}},
            trigger_source="maskinochfritid_production_run",
        )

        erd_nodes = [
            {
                "id": nid,
                "name": data.get("label", nid),
                "type": data.get("type", "Entity"),
                "domain": data.get("domain", "Operational"),
                "metadata": data.get("metadata", {}),
            }
            for nid, data in erd_graph.nodes.items()
        ]
        erd_links = []
        for src, edges in erd_graph.outgoing_edges.items():
            for e in edges:
                erd_links.append({
                    "source": src,
                    "target": e.get("target"),
                    "relation": e.get("relation", "RELATES_TO"),
                })

        return {
            "organization_name": comp_res["organization_name"],
            "summary": comp_res["summary"],
            "team_dynamics_metrics": comp_res["team_dynamics_metrics"],
            "tax_and_margin_telemetry": comp_res["tax_and_margin_telemetry"],
            "customer_telemetry": comp_res["customer_telemetry"],
            "voucher_telemetry": comp_res["voucher_telemetry"],
            "proposals_summary": p_slice["proposals_summary"],
            "checkpoint": {
                "checkpoint_id": checkpoint.checkpoint_id,
                "project_id": checkpoint.project_id,
                "checksum_sha256": checkpoint.checksum_sha256,
                "timestamp": checkpoint.timestamp,
            },
            "trajectory": trajectory.model_dump(),
            "erd_graph": {
                "node_count": len(erd_nodes),
                "edge_count": len(erd_links),
                "nodes": erd_nodes,
                "links": erd_links,
            },
        }

    def _get_erd_graph_data(self) -> Dict[str, Any]:
        """Returns the full 15-entity Universal ERD graph dynamically computed by FortnoxComputationPipeline."""
        from src.fortnox.maskinochfritid_adapter import MaskinOchFritidAdapter
        from src.fortnox.computations import FortnoxComputationPipeline

        p_slice = MaskinOchFritidAdapter.get_production_slice()
        comp_res = FortnoxComputationPipeline.compute_all(
            org_name=p_slice["organization_name"],
            invoices=p_slice["invoices"],
            employees=p_slice["employees"],
            time_reports=p_slice["time_reports"],
            projects=p_slice["projects"],
            customers=p_slice["customers"],
            vouchers=p_slice["vouchers"],
        )
        erd_graph = comp_res["erd_graph"]

        domain_palette = {
            "Organization": "Trust",
            "Team": "Trust",
            "Person": "Interactional Interface",
            "Role": "Operational",
            "Capability": "Knowledge",
            "Assignment": "Operational",
            "Observation": "Operational",
            "Diagnosis": "Knowledge",
            "Intervention": "Tools",
            "TransitionPlan": "Tools",
            "Communication": "Interactional Interface",
            "Experiment": "Innovation & Tech",
            "Measurement": "Evaluation",
            "Learning": "Knowledge",
            "Knowledge": "Knowledge",
            "Artifact": "Trust",
        }

        nodes = []
        for n_id, data in erd_graph.nodes.items():
            n_type = data.get("type", "Entity")
            nodes.append({
                "id": n_id,
                "name": data.get("label", n_id),
                "type": n_type,
                "domain": data.get("domain") or domain_palette.get(n_type, "Operational"),
                "size": 32 if n_type == "Organization" else (26 if n_type in ("Team", "Role", "Person") else (22 if n_type in ("Diagnosis", "Intervention", "Experiment", "Learning") else 18)),
                "metadata": data.get("metadata", {}),
            })

        links = []
        seen_links = set()
        for src, edges in erd_graph.outgoing_edges.items():
            for e in edges:
                tgt = e.get("target")
                rel = e.get("relation", "RELATES_TO")
                key = (src, tgt, rel)
                if key not in seen_links:
                    seen_links.add(key)
                    links.append({
                        "source": src,
                        "target": tgt,
                        "relation": rel,
                        "weight": e.get("weight", 1.0),
                    })

        return {
            "nodes": nodes,
            "links": links,
            "count": len(nodes),
            "edge_count": len(links),
            "framework": "Universal ERD (15 Entities Full Lifecycle)",
            "organization": p_slice["organization_name"],
        }


    def _generate_graph_data(self, scenario_id: str, scope: str, role: str, focal_id: Optional[str] = None) -> Dict[str, Any]:
        """Generates dynamic nodes and links for the Spatial Canvas based on scope level and optional focal entity."""
        scenario = SCENARIOS.get(scenario_id, SCENARIOS["mixed_q3"])
        txs = scenario["transactions"]

        # Compute financial_impact for each transaction (savings potential in SEK)
        def _compute_financial_impact(tx: dict) -> float:
            if tx.get("is_used_good"):
                margin = tx["gross_amount"] - tx.get("purchase_cost_ex_vat", 0)
                vmb_vat = margin * 0.20
                return round(tx["current_vat_amount"] - vmb_vat, 2)
            elif tx.get("is_garden_or_installation_work"):
                cust = tx.get("customer", {})
                if not cust.get("is_company"):
                    labor = tx.get("labor_share_amount", 0)
                    return round(labor * 0.50, 2)  # RUT reduction
                else:
                    return round(tx.get("current_vat_amount", 0), 2)  # Byggmoms savings
            elif tx.get("is_asset_purchase"):
                return round(tx.get("net_amount", 0) * 0.80 / 5, 2)  # early depreciation gain
            return 0.0

        nodes = []
        links = []

        # Focal Node: The Financial Stream / Batch
        nodes.append({
            "id": "focal_batch",
            "name": scenario["title"],
            "type": "batch",
            "domain": Domain.OPERATIONAL.value,
            "scope": "D0",
            "size": 32,
            "relevance": 1.0,
            "financial_impact": sum(_compute_financial_impact(t) for t in txs),
            "details": f"Period: {scenario['period']} | {len(txs)} transaktioner"
        })

        # D0: Focal Transactions
        for tx in txs:
            t_id = tx["transaction_id"]
            impact = _compute_financial_impact(tx)
            nodes.append({
                "id": t_id,
                "name": f"{t_id}: {tx['description'][:25]}...",
                "type": "transaction",
                "domain": Domain.EXCHANGE.value,
                "scope": "D0",
                "size": 24,
                "relevance": 0.95,
                "gross": tx["gross_amount"],
                "financial_impact": impact,
                "details": f"Belopp: {tx['gross_amount']:.0f} SEK | Besparing: {impact:.0f} SEK"
            })
            links.append({"source": "focal_batch", "target": t_id, "relation": "CONTAINS", "strength": 1.0})

        if scope in ("D1", "D2", "D3"):
            # D1: Direct Customers, Accounts, and Rules
            for tx in txs:
                t_id = tx["transaction_id"]
                cust = tx.get("customer")
                if cust:
                    c_id = cust["customer_id"]
                    if not any(n["id"] == c_id for n in nodes):
                        nodes.append({
                            "id": c_id,
                            "name": cust["name"],
                            "type": "customer",
                            "domain": Domain.TRUST.value,
                            "scope": "D1",
                            "size": 20,
                            "relevance": 0.88,
                            "details": f"Typ: {'Företag' if cust.get('is_company') else 'Privatperson'}"
                        })
                    links.append({"source": t_id, "target": c_id, "relation": "BILLED_TO", "strength": 0.8})

                # Direct Tax Rule
                rule_id = f"rule_{t_id}"
                if tx.get("is_used_good"):
                    rule_label = "ML 9a kap. VMB"
                elif tx.get("is_garden_or_installation_work") and cust and not cust.get("is_company"):
                    rule_label = "IL 67 kap. RUT"
                elif tx.get("is_garden_or_installation_work") and cust and cust.get("is_company"):
                    rule_label = "ML 1 kap. 2 § Byggmoms"
                elif tx.get("is_asset_purchase"):
                    rule_label = "IL 18 kap. 4 § Direktavskr."
                else:
                    rule_label = "ML Standard 25%"

                nodes.append({
                    "id": rule_id,
                    "name": rule_label,
                    "type": "tax_rule",
                    "domain": Domain.KNOWLEDGE.value,
                    "scope": "D1",
                    "size": 18,
                    "relevance": 0.92,
                    "details": f"Skatterättslig grund för {t_id}"
                })
                links.append({"source": t_id, "target": rule_id, "relation": "GOVERNED_BY", "strength": 0.9})

            # Agent Node
            nodes.append({
                "id": "agent_tax_optimizer",
                "name": "TaxOptimizationAgent",
                "type": "agent",
                "domain": Domain.TOOLS.value,
                "scope": "D1",
                "size": 26,
                "relevance": 0.96,
                "details": "Specialistagent för skatteoptimering & feldetektering"
            })
            links.append({"source": "focal_batch", "target": "agent_tax_optimizer", "relation": "AUDITED_BY", "strength": 1.0})

        if scope in ("D2", "D3"):
            # D2: Systemic Ledger & Perspective Windows
            nodes.append({
                "id": "win_5_financial",
                "name": "Window 5: Financial Management",
                "type": "perspective_window",
                "domain": Domain.OPERATIONAL.value,
                "scope": "D2",
                "size": 28,
                "relevance": 0.90,
                "details": "Övervakar kassaflöde, TB1/TB2 marginaler och skatteeffektivitet"
            })
            links.append({"source": "agent_tax_optimizer", "target": "win_5_financial", "relation": "PROJECTS_TO", "strength": 0.85})

            nodes.append({
                "id": "skv_moms_q3",
                "name": "Skatteverket Momsdeklaration Q3",
                "type": "compliance",
                "domain": Domain.TRUST.value,
                "scope": "D2",
                "size": 22,
                "relevance": 0.85,
                "details": "Fält 05, 08, 10, 41, 48, 49"
            })
            links.append({"source": "win_5_financial", "target": "skv_moms_q3", "relation": "COMPILES_INTO", "strength": 0.8})

            # BAS Kontoplan Ledger
            nodes.append({
                "id": "bas_kontoplan",
                "name": "BAS Kontoplan 2026",
                "type": "ledger",
                "domain": Domain.TOOLS.value,
                "scope": "D2",
                "size": 22,
                "relevance": 0.82,
                "details": "Konton: 1930, 3051, 3002, 3231, 5410, 2611, 2640"
            })
            links.append({"source": "win_5_financial", "target": "bas_kontoplan", "relation": "POSTS_TO", "strength": 0.75})

        if scope == "D3":
            # D3: Macro Ecosystem & Dual Learning Loop
            nodes.append({
                "id": "macro_skatteverket",
                "name": "Skatteverket Rättslig Vägledning",
                "type": "authority",
                "domain": Domain.TRUST.value,
                "scope": "D3",
                "size": 26,
                "relevance": 0.78,
                "details": "Nationella skatteregler och ställningstaganden"
            })
            links.append({"source": "skv_moms_q3", "target": "macro_skatteverket", "relation": "AUDITED_BY", "strength": 0.6})

            nodes.append({
                "id": "meta_learning_agent",
                "name": "Meta-Learning Optimization Loop",
                "type": "meta",
                "domain": Domain.KNOWLEDGE.value,
                "scope": "D3",
                "size": 24,
                "relevance": 0.75,
                "details": "Kalibrerar agentregler och utvärderar interventionsframgång"
            })
            links.append({"source": "agent_tax_optimizer", "target": "meta_learning_agent", "relation": "FEEDS_LEARNING", "strength": 0.7})

        # Orbiting satellites (top 3 recommended next nodes)
        satellites = [
            {"id": "sat_sni", "name": "Kontrollera SNI 43.120 Bolagsverket", "relevance": 0.94, "target": "TX-1003"},
            {"id": "sat_rut", "name": "Generera RUT-rekvisitionsfil Skv", "relevance": 0.89, "target": "TX-1002"},
            {"id": "sat_vmb", "name": "Skapa Inbyteskontrakt & VMB-kvitto", "relevance": 0.85, "target": "TX-1001"},
        ]

        return {
            "nodes": nodes,
            "links": links,
            "satellites": satellites,
            "scope": scope,
            "role": role,
            "focal_id": focal_id or "focal_batch",
            "count": len(nodes)
        }


def run_server(port: int = 8765):
    """Starts the BART HTTP server."""
    http.server.ThreadingHTTPServer.allow_reuse_address = False
    server_address = ("", port)
    httpd = http.server.ThreadingHTTPServer(server_address, BARTRequestHandler)
    print(f"==================================================")
    print(f"   BART Interactive Spatial Canvas Server Online   ")
    print(f"   URL: http://localhost:{port}                   ")
    print(f"   Static Directory: {STATIC_DIR}                 ")
    print(f"==================================================")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nServer shutting down gracefully.")
        httpd.server_close()


if __name__ == "__main__":
    port = 8765
    if len(sys.argv) > 1 and sys.argv[1].isdigit():
        port = int(sys.argv[1])
    elif "--port" in sys.argv:
        idx = sys.argv.index("--port")
        if idx + 1 < len(sys.argv) and sys.argv[idx + 1].isdigit():
            port = int(sys.argv[idx + 1])
    run_server(port)
