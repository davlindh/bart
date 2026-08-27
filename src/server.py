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
from src.agents.tax_optimization_agent import TaxOptimizationAgent
from src.tax_engine.models import TaxTransaction, CustomerTaxProfile
from src.tax_engine.bas_kontoplan import BASKontoplan
from src.tax_engine.evaluator import TaxRuleEvaluator
from src.tax_engine.momsdeklaration import MomsdeklarationGenerator

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
    }
}

# Global in-memory approved vouchers log
APPROVED_VOUCHERS: List[Dict[str, Any]] = []
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

        if path == "/api/graph":
            scope = query.get("scope", ["D1"])[0]
            scenario_id = query.get("scenario_id", ["mixed_q3"])[0]
            role = query.get("role", ["CFO"])[0]
            focal_id = query.get("focal_id", [None])[0]  # NEW: pivot support
            graph_data = self._generate_graph_data(scenario_id, scope, role, focal_id)
            self._send_json(graph_data)
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
            self._send_json(packet.model_dump())
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
            step = payload.get("step", "observe")
            context_data = payload.get("context", {})
            try:
                context_packet = ContextPacket(**context_data)
            except Exception:
                # Build default context if raw
                context_packet = ContextResolver.resolve_context(
                    role=payload.get("role", "CFO"),
                    purpose=payload.get("purpose", "Interaktiv skatteoptimering"),
                    task=payload.get("task", "Analysera transaktioner"),
                    scope=ScopeLevel(payload.get("scope", "D1")),
                    target_entity=context_data.get("primary_entity", context_data),
                )

            step_res = GLOBAL_AGENT.run_step(step, context_packet)
            # Normalize output key so app.js can read step_res.output
            if isinstance(step_res, dict) and "output" not in step_res:
                step_res["output"] = step_res.get("result", step_res.get("summary", f"Steg {step} slutfört"))
            self._send_json(step_res)
            return

        if path == "/api/agent/run":
            context_data = payload.get("context", {})
            try:
                context_packet = ContextPacket(**context_data)
            except Exception:
                context_packet = ContextResolver.resolve_context(
                    role=payload.get("role", "CFO"),
                    purpose=payload.get("purpose", "Fullständig revision"),
                    task=payload.get("task", "Kör 6-stegs agentloop"),
                    scope=ScopeLevel(payload.get("scope", "D1")),
                    target_entity=context_data.get("primary_entity", context_data),
                )

            res = GLOBAL_AGENT.run(context_packet)
            self._send_json(res.model_dump())
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
                from src.tax_engine.models import JournalVoucher, VoucherRow
                rows = [
                    VoucherRow(account="1930 Företagskonto", description="Inbetalning", debet=amount, kredit=0.0),
                    VoucherRow(account="3002 Försäljning arbetskostnad RUT", description="RUT-försäljning", debet=0.0, kredit=amount)
                ]
                voucher = JournalVoucher(
                    verifikat_id=f"VER_{tx_id}_APPROVED",
                    series="A",
                    description=f"Godkänd skattejustering för {tx_id}",
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

        self._send_json({"error": "Endpoint not found"}, status=404)

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
