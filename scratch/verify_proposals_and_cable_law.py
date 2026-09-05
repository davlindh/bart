import sys
import os
sys.path.insert(0, os.path.abspath("."))
import urllib.request
import json
from src.tax_engine.models import TaxTransaction, CustomerTaxProfile, TaxRuleType
from src.tax_engine.rule_library import RUTRule
from src.tax_engine.verification_engine import FinancialVerificationEngine

BASE_URL = "http://127.0.0.1:8765"

def test_api_proposals():
    print("\n--- 1. Testing GET /api/vouchers/proposals ---")
    req = urllib.request.Request(f"{BASE_URL}/api/vouchers/proposals")
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 200
        proposals = json.loads(resp.read().decode('utf-8'))
        print(f"Received {len(proposals)} proposals")
        assert len(proposals) >= 4, f"Expected >=4 proposals, got {len(proposals)}"
        
        # Verify TX-1002 cable law specifically
        tx1002 = next((p for p in proposals if p["transaction_id"] == "TX-1002"), None)
        assert tx1002 is not None, "Missing proposal for TX-1002"
        print(f"TX-1002 Proposal Title: {tx1002['title']}")
        print(f"TX-1002 Statutory Notes: {tx1002['statutory_notes']}")
        assert "begränsningskabel" in tx1002['statutory_notes'].lower()
        assert "undantagen från rut" in tx1002['statutory_notes'].lower()
        assert "131 347493-15/111" in tx1002['legal_basis'] or "131 347493-15/111" in tx1002['statutory_notes']
        print("  [PASS] Cable installation exclusion specifically documented in proposal!")

def test_api_sync_single():
    print("\n--- 2. Testing POST /api/voucher/sync_proposal ---")
    payload = json.dumps({"proposal_id": "PROP-TX-1001"}).encode('utf-8')
    req = urllib.request.Request(
        f"{BASE_URL}/api/voucher/sync_proposal",
        data=payload,
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 200
        res = json.loads(resp.read().decode('utf-8'))
        assert res["success"] is True
        print(f"  [PASS] Synced proposal: {res['record']['voucher']['verifikat_id']}")
        assert res['record']['voucher']['is_balanced'] is True

def test_api_sync_all():
    print("\n--- 3. Testing POST /api/voucher/sync_all_proposals ---")
    payload = json.dumps({}).encode('utf-8')
    req = urllib.request.Request(
        f"{BASE_URL}/api/voucher/sync_all_proposals",
        data=payload,
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 200
        res = json.loads(resp.read().decode('utf-8'))
        assert res["success"] is True
        print(f"  [PASS] Synced {res['count']} proposals in batch to Fortnox")

def test_tax_engine_cable_law():
    print("\n--- 4. Testing Tax Engine Cable Installation Law ---")
    # A transaction where customer improperly claims RUT on cable laying
    tx_improper_rut = TaxTransaction(
        transaction_id="tx_test_cable",
        source_system="FORTNOX",
        description="Installation och kabeldragning av robotgräsklippare",
        gross_amount=24000.0,
        net_amount=19200.0,
        current_vat_rate=0.25,
        current_vat_amount=4800.0,
        current_tax_rule=TaxRuleType.RUT_DEDUCTION,  # Claimed as RUT!
        is_garden_or_installation_work=True,
        labor_share_amount=8000.0,
        customer=CustomerTaxProfile(customer_id="c1", name="Privatperson", is_company=False, rut_eligible=True)
    )

    report = FinancialVerificationEngine.verify_transaction_batch([tx_improper_rut])
    cable_issue = next((i for i in report.issues if i.code == "RUT_CABLE_INSTALLATION_EXCLUDED"), None)
    assert cable_issue is not None, "VerificationEngine should flag improper RUT on cable installation"
    print(f"  [PASS] Verification Engine flagged: {cable_issue.title}")
    print(f"  [PASS] Legal basis: {cable_issue.legal_basis}")

    # Check RUTRule evaluation legal note with standard moms candidate
    tx_standard = TaxTransaction(
        transaction_id="tx_standard_cable",
        source_system="FORTNOX",
        description="Installation och kabeldragning av robotgräsklippare",
        gross_amount=24000.0,
        net_amount=19200.0,
        current_vat_rate=0.25,
        current_vat_amount=4800.0,
        current_tax_rule=TaxRuleType.STANDARD_MOMS_25,
        is_garden_or_installation_work=True,
        labor_share_amount=8000.0,
        customer=CustomerTaxProfile(customer_id="c1", name="Privatperson", is_company=False, rut_eligible=True)
    )
    opp, calc = RUTRule.evaluate(tx_standard)
    assert opp is not None
    assert "131 347493-15/111" in opp.legal_basis
    print(f"  [PASS] RUTRule includes statutory guidance: {opp.legal_basis[:80]}...")

def main():
    test_api_proposals()
    test_api_sync_single()
    test_api_sync_all()
    test_tax_engine_cable_law()
    print("\n=======================================================")
    print("ALL TESTS PASSED: PROPOSED VOUCHERS & CABLE LAW VERIFIED")
    print("=======================================================")

if __name__ == "__main__":
    main()
