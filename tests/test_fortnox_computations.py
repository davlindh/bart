"""Unit tests for Fortnox Data Computation Pipeline."""

import pytest
from src.fortnox import (
    FortnoxCustomer,
    FortnoxCustomerType,
    FortnoxVATType,
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

    assert "customer_telemetry" in res
    cust_data = res["customer_telemetry"]
    assert len(cust_data) == 1
    assert cust_data[0]["customer_number"] == "C1"

    assert "erd_graph" in res
    graph = res["erd_graph"]
    assert len(graph.organizations) == 1
    assert len(graph.persons) == 2


def test_fortnox_customer_telemetry_and_tax_profiles():
    """Verify FortnoxComputationPipeline calculates RUT, VMB, and Omvänd moms potential per customer."""
    customers = [
        FortnoxCustomer(
            customer_number="CUST-RUT",
            name="Karin Privatkund",
            customer_type=FortnoxCustomerType.PRIVATE,
            organisation_number="19800101-1234",
            rut_eligible=True,
            city="Lund",
        ),
        FortnoxCustomer(
            customer_number="CUST-BYGG",
            name="Skåne Entreprenad AB",
            customer_type=FortnoxCustomerType.COMPANY,
            organisation_number="556999-1234",
            vat_type=FortnoxVATType.SEREVERSEDVAT,
            sni_code="43.120",
            city="Malmö",
        ),
        FortnoxCustomer(
            customer_number="CUST-VMB",
            name="Erik Begagnatköpare",
            customer_type=FortnoxCustomerType.PRIVATE,
            organisation_number="19750505-5678",
            city="Helsingborg",
        ),
    ]

    invoices = [
        FortnoxInvoice(
            document_number="INV-1",
            customer_number="CUST-RUT",
            customer_name="Karin Privatkund",
            invoice_date="2026-08-01",
            due_date="2026-08-15",
            total=10000.0,
            net=8000.0,
            rows=[
                FortnoxInvoiceRow(article_number="RUT-1", description="Installation arbetskostnad", delivered_quantity=1, price=6000.0, vat=25.0, is_work_cost=True),
                FortnoxInvoiceRow(article_number="MAT-1", description="Kabelmaterial", delivered_quantity=1, price=2000.0, vat=25.0, is_work_cost=False),
            ],
            is_paid=True,
            payment_date="2026-08-14",
        ),
        FortnoxInvoice(
            document_number="INV-2",
            customer_number="CUST-BYGG",
            customer_name="Skåne Entreprenad AB",
            invoice_date="2026-08-05",
            due_date="2026-08-25",
            total=40000.0,
            net=32000.0,
            rows=[
                FortnoxInvoiceRow(article_number="BYGG-1", description="Schaktning och anläggning", delivered_quantity=1, price=32000.0, vat=25.0),
            ],
            is_paid=True,
            payment_date="2026-08-20",
        ),
        FortnoxInvoice(
            document_number="INV-3",
            customer_number="CUST-VMB",
            customer_name="Erik Begagnatköpare",
            invoice_date="2026-08-10",
            due_date="2026-08-24",
            total=15000.0,
            net=12000.0,
            rows=[
                FortnoxInvoiceRow(article_number="VMB-1", description="Begagnad robotgräsklippare inbyte", delivered_quantity=1, price=12000.0, vat=25.0),
            ],
            is_paid=True,
            payment_date="2026-08-28",
        ),
    ]

    employees = [
        FortnoxEmployee(employee_id="E1", first_name="Anders", last_name="CFO", job_title="CFO", monthly_salary=50000.0, is_owner=True)
    ]

    res = FortnoxComputationPipeline.compute_all(
        org_name="Test Maskin & Fritid AB",
        invoices=invoices,
        employees=employees,
        time_reports=[],
        projects=[],
        customers=customers,
    )

    cust_tel = {c["customer_number"]: c for c in res["customer_telemetry"]}

    # RUT Customer check
    assert "CUST-RUT" in cust_tel
    assert "RUT" in cust_tel["CUST-RUT"]["tax_profile_classification"]
    assert cust_tel["CUST-RUT"]["potential_tax_savings_sek"] == 3000.0  # 50% of 6000 SEK labor
    assert cust_tel["CUST-RUT"]["payment_status"] == "FÖRTIDA BETALNING"

    # Reverse VAT Customer check
    assert "CUST-BYGG" in cust_tel
    assert "Omvänd Byggmoms" in cust_tel["CUST-BYGG"]["tax_profile_classification"]
    assert cust_tel["CUST-BYGG"]["potential_tax_savings_sek"] == 8000.0  # 20% of 40000 SEK gross

    # VMB Customer check
    assert "CUST-VMB" in cust_tel
    assert "VMB" in cust_tel["CUST-VMB"]["tax_profile_classification"]
    assert cust_tel["CUST-VMB"]["potential_tax_savings_sek"] > 0
    assert cust_tel["CUST-VMB"]["payment_status"] == "MÅTTLIG FÖRSENING"

