"""Unit tests for Fortnox Data Computation Pipeline."""

import pytest
from src.fortnox import (
    FortnoxInvoice,
    FortnoxInvoiceRow,
    FortnoxEmployee,
    FortnoxTimeReport,
    FortnoxProject,
    FortnoxComputationPipeline,
)


def test_fortnox_pipeline_computations():
    """Verify FortnoxComputationPipeline computes Team Health Index, Overtime, and Universal ERD entities."""
    invoices = [
        FortnoxInvoice(
            document_number="101", customer_number="C1", customer_name="Test AB",
            invoice_date="2026-08-01", due_date="2026-08-15", total=20000.0, net=16000.0,
            rows=[FortnoxInvoiceRow(article_number="A1", description="Service", delivered_quantity=1, price=16000.0, vat=25.0)]
        )
    ]
    employees = [
        FortnoxEmployee(employee_id="E1", first_name="Anna", last_name="CFO", job_title="CFO", department="Ledning", monthly_salary=60000.0, is_owner=True),
        FortnoxEmployee(employee_id="E2", first_name="Kalle", last_name="Mek", job_title="Montör", department="Fält", monthly_salary=35000.0),
    ]
    time_reports = [
        FortnoxTimeReport(report_id="T1", employee_id="E2", date="2026-08-05", project_code="P1", hours=8.0, activity="Fältarbete"),
        FortnoxTimeReport(report_id="T2", employee_id="E2", date="2026-08-06", project_code="P1", hours=12.0, activity="Akut fältarbete", is_overtime=True),
    ]
    projects = [
        FortnoxProject(project_code="P1", description="Testprojekt", start_date="2026-08-01", project_leader_id="E1")
    ]

    res = FortnoxComputationPipeline.compute_all("Testföretag AB", invoices, employees, time_reports, projects)

    assert "team_dynamics_metrics" in res
    metrics = res["team_dynamics_metrics"]
    assert metrics["team_health_index"] > 0
    assert metrics["total_overtime_hours"] == 12.0
    assert metrics["decision_time_avg_days"] == 14.0

    assert "tax_and_margin_telemetry" in res
    tax_data = res["tax_and_margin_telemetry"]
    assert tax_data["annual_qualifying_salaries"] == 1140000.0
    assert tax_data["owner_salary_annual"] == 720000.0

    assert "erd_graph" in res
    graph = res["erd_graph"]
    assert len(graph.organizations) == 1
    assert len(graph.persons) == 2
