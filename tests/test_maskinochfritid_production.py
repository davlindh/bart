import pytest
from src.fortnox.maskinochfritid_adapter import MaskinOchFritidAdapter
from src.fortnox.computations import FortnoxComputationPipeline
from src.fortnox.models import FortnoxCustomerType, FortnoxVATType
from src.core.precognition import ProjectIntent, IntentStatus
from src.core.types import Domain
from src.context_engine.precognition import PreCognitiveEngine
from src.graph.persistence_bridge import GraphPersistenceBridge


def test_maskinochfritid_adapter_dataset():
    """Verify production dataset extraction and legal rules integrity from maskinochfritid-25."""
    customers = MaskinOchFritidAdapter.get_production_customers()
    assert len(customers) == 5

    # Verify customer types and commercial vectors
    anna = next(c for c in customers if c.customer_number == "101")
    assert anna.name == "Anna Nilsson"
    assert anna.customer_type == FortnoxCustomerType.PRIVATE
    assert anna.rut_eligible is True
    assert anna.rut_remaining_quota == 75000.0

    erik = next(c for c in customers if c.customer_number == "102")
    assert erik.name == "Erik Johansson"
    assert len(erik.registered_machines) == 1
    assert erik.registered_machines[0]["brand"] == "Stihl"
    assert erik.registered_machines[0]["vmb_trade_in_eligible"] is True

    svensson = next(c for c in customers if c.customer_number == "103")
    assert svensson.name == "Svensson Bygg & Anläggning AB"
    assert svensson.customer_type == FortnoxCustomerType.COMPANY
    assert svensson.vat_type == FortnoxVATType.SEREVERSEDVAT
    assert svensson.sni_code == "43.120"

    invoices = MaskinOchFritidAdapter.get_production_invoices()
    assert len(invoices) == 5

    # Check invoice BAS accounts
    inv_10542 = next(i for i in invoices if i.document_number == "10542")
    assert inv_10542.total == 29620.0
    bas_accounts = {r.account_number for r in inv_10542.rows}
    assert 3001 in bas_accounts
    assert 3041 in bas_accounts
    assert 3520 in bas_accounts

    # Check VMB invoice
    inv_10543 = next(i for i in invoices if i.document_number == "10543")
    assert any(r.account_number == 3051 for r in inv_10543.rows)


def test_maskinochfritid_balanced_vouchers():
    """Verify that all production vouchers match double-entry bookkeeping with 0 öre difference."""
    vouchers = MaskinOchFritidAdapter.generate_production_vouchers()
    assert len(vouchers) == 5

    for v in vouchers:
        assert v.is_balanced is True
        assert abs(v.total_debet - v.total_kredit) < 0.01, f"Voucher {v.voucher_number} is unbalanced!"

    # Voucher 1 (Standard robot & montage)
    v1 = next(v for v in vouchers if v.voucher_number == 10542)
    assert v1.total_debet == 29620.0
    assert v1.skatteverket_report_boxes["ruta_05_momspliktig_forsaljning_25"] == 23696.0
    assert v1.skatteverket_report_boxes["ruta_10_utgaende_moms_25"] == 5924.0

    # Voucher 3 (RUT 50% with Skatteverket claim account 1513)
    v3 = next(v for v in vouchers if v.voucher_number == 10544)
    assert v3.total_debet == 4000.0
    row_1513 = next(r for r in v3.rows if r.account == 1513)
    assert row_1513.debet == 1800.0  # 50% of 3600 kr gross labor

    # Voucher 5 (Omvänd Byggmoms ML 16 kap)
    v5 = next(v for v in vouchers if v.voucher_number == 5102)
    assert v5.total_debet == 50000.0
    assert v5.skatteverket_report_boxes["ruta_49_beskattningsunderlag_omvand_byggmoms"] == 50000.0
    assert v5.skatteverket_report_boxes["ruta_10_utgaende_moms_25"] == 0.0


def test_maskinochfritid_full_pipeline_computation():
    """Verify FortnoxComputationPipeline computes full organizational, tax, customer, and ERD telemetry."""
    p_slice = MaskinOchFritidAdapter.get_production_slice()

    result = FortnoxComputationPipeline.compute_all(
        org_name=p_slice["organization_name"],
        invoices=p_slice["invoices"],
        employees=p_slice["employees"],
        time_reports=p_slice["time_reports"],
        projects=p_slice["projects"],
        customers=p_slice["customers"],
        vouchers=p_slice["vouchers"],
    )

    assert result["organization_name"] == "Maskin & Fritid i Skåne AB"
    assert result["summary"]["invoices_analyzed"] == 5
    assert result["summary"]["customers_counted"] == 5
    assert result["summary"]["vouchers_verified"] == 5

    # Voucher Telemetry
    v_tel = result["voucher_telemetry"]
    assert v_tel is not None
    assert v_tel["all_balanced"] is True
    assert v_tel["accounting_diff_sek"] == 0.0
    assert v_tel["total_vouchers"] == 5
    assert v_tel["skatteverket_report_boxes"]["ruta_05_momspliktig_forsaljning_25"] > 0
    assert v_tel["skatteverket_report_boxes"]["ruta_10_utgaende_moms_25"] > 0
    assert v_tel["skatteverket_report_boxes"]["ruta_49_beskattningsunderlag_omvand_byggmoms"] == 50000.0

    # Team Dynamics
    td = result["team_dynamics_metrics"]
    assert td["team_health_index"] > 50.0
    assert td["workload_balance_score"] > 0.0
    assert td["total_overtime_hours"] > 0.0  # Overtime logged for robot urgent repairs

    # Customer Telemetry
    ct = result["customer_telemetry"]
    assert len(ct) == 5
    # Erik Johansson trade-in potential
    erik_tel = next(c for c in ct if c["customer_number"] == "102")
    assert "VMB" in erik_tel["tax_profile"]

    # Universal ERD Graph Verification
    erd = result["erd_graph"]
    assert len(erd.nodes) > 15
    total_edges = sum(len(e) for e in erd.outgoing_edges.values())
    assert total_edges > 10

    # Check voucher nodes and machine observation nodes in ERD
    voucher_nodes = [nid for nid in erd.nodes if nid.startswith("VOUCHER_")]
    assert len(voucher_nodes) == 5

    machine_nodes = [nid for nid in erd.nodes if nid.startswith("OBS_MACH_")]
    assert len(machine_nodes) >= 2


def test_maskinochfritid_precognition_and_state_preservation():
    """Verify Contextual Pre-Cognition projects trajectories and persists checkpoint to SQLite WAL."""
    p_slice = MaskinOchFritidAdapter.get_production_slice()

    result = FortnoxComputationPipeline.compute_all(
        org_name=p_slice["organization_name"],
        invoices=p_slice["invoices"],
        employees=p_slice["employees"],
        time_reports=p_slice["time_reports"],
        projects=p_slice["projects"],
        customers=p_slice["customers"],
        vouchers=p_slice["vouchers"],
    )

    erd = result["erd_graph"]

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

    # Trajectory projection from customer 102 (Erik Johansson - VMB)
    trajectory = PreCognitiveEngine.project_trajectory(
        intent=intent,
        current_node_id="CUST_102",
        graph=erd,
        role="CFO",
    )

    assert len(trajectory.predicted_nodes) > 0
    assert trajectory.current_point_id == "CUST_102"
    assert trajectory.confidence_score > 0.0

    # Atomic WAL Checkpoint Persistence
    bridge = GraphPersistenceBridge()
    chk = bridge.save_checkpoint(
        project_id="PRJ-MF-PROD",
        erd_graph=erd,
        intent=intent,
        agent_states={"MaskinOchFritidAdapter": {"status": "PRODUCTION_COMPUTED", "vouchers_balanced": 5}},
        trigger_source="maskinochfritid_production_run",
    )

    assert chk.checkpoint_id.startswith("chk_")
    assert len(chk.checksum_sha256) == 64

    # Rehydrate and verify zero data loss
    restored = bridge.restore_checkpoint(project_id="PRJ-MF-PROD")
    assert restored["intent"].intent_id == "intent_mf_q3_production"
    assert len(restored["erd_graph"].nodes) == len(erd.nodes)
    restored_edges = sum(len(e) for e in restored["erd_graph"].outgoing_edges.values())
    orig_edges = sum(len(e) for e in erd.outgoing_edges.values())
    assert restored_edges == orig_edges
