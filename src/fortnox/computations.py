from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime
from statistics import mean, stdev
from collections import defaultdict
from .models import (
    FortnoxCustomer,
    FortnoxCustomerType,
    FortnoxVATType,
    FortnoxInvoice,
    FortnoxEmployee,
    FortnoxTimeReport,
    FortnoxProject,
    FortnoxVoucher,
)
from ..graph.models import (
    OrganizationEntity,
    TeamEntity,
    PersonEntity,
    RoleEntity,
    AssignmentEntity,
    ObservationEntity,
)
from ..graph.universal_erd import UniversalERDGraph
from ..tax_engine.models import TaxTransaction, CustomerTaxProfile
from ..tax_engine.evaluator import TaxRuleEvaluator
from ..core.types import TaxRuleType


class FortnoxComputationPipeline:
    """Computes organizational telemetry, populates Universal ERD, and extracts tax cuts & customer telemetry from Fortnox ERP data."""

    @classmethod
    def compute_all(
        cls,
        org_name: str,
        invoices: List[FortnoxInvoice],
        employees: List[FortnoxEmployee],
        time_reports: List[FortnoxTimeReport],
        projects: List[FortnoxProject],
        customers: Optional[List[FortnoxCustomer]] = None,
    ) -> Dict[str, Any]:
        """Executes the full computation suite on Fortnox datasets including customer intelligence."""
        # Synthesize customers from invoices if not explicitly provided
        if customers is None:
            customers = cls.derive_customers_from_invoices(invoices)

        erd_graph = cls.build_universal_erd(org_name, invoices, employees, time_reports, projects, customers)
        team_metrics = cls.compute_team_dynamics_metrics(employees, time_reports, invoices)
        tax_evaluation = cls.compute_tax_and_margin_telemetry(invoices, employees)
        customer_telemetry = cls.compute_customer_telemetry(customers, invoices)

        return {
            "organization_name": org_name,
            "team_dynamics_metrics": team_metrics,
            "tax_and_margin_telemetry": tax_evaluation,
            "customer_telemetry": customer_telemetry,
            "erd_graph": erd_graph,
            "summary": {
                "invoices_analyzed": len(invoices),
                "employees_counted": len(employees),
                "customers_counted": len(customers),
                "logged_hours_total": sum(t.hours for t in time_reports),
                "active_projects": len(projects),
            },
        }


    @classmethod
    def derive_customers_from_invoices(cls, invoices: List[FortnoxInvoice]) -> List[FortnoxCustomer]:
        """Synthesizes customer profiles from invoice history if explicit customer master is not provided."""
        seen = {}
        for inv in invoices:
            c_num = inv.customer_number or "CUST-UNKNOWN"
            if c_num not in seen:
                is_company = "ab" in inv.customer_name.lower() or "bygg" in inv.customer_name.lower() or "nordic" in inv.customer_name.lower()
                is_vmb = "begagnad" in inv.customer_name.lower() or any("inbyte" in r.description.lower() or "begagnad" in r.description.lower() for r in inv.rows)
                is_rut = not is_company and any(r.is_work_cost for r in inv.rows)
                is_rev = is_company and any("schakt" in r.description.lower() or "bygg" in r.description.lower() for r in inv.rows)

                vat_type = FortnoxVATType.SEREVERSEDVAT if is_rev else FortnoxVATType.SEVAT
                cust_type = FortnoxCustomerType.COMPANY if is_company else FortnoxCustomerType.PRIVATE

                seen[c_num] = FortnoxCustomer(
                    customer_number=c_num,
                    name=inv.customer_name,
                    customer_type=cust_type,
                    organisation_number="556123-4567" if is_company else "19840512-1234",
                    vat_type=vat_type,
                    rut_eligible=is_rut,
                    has_f_skatt=is_company,
                    sni_code="43.120" if is_rev else ("01.610" if is_company else None),
                    city="Malmö" if is_company else "Lund",
                    payment_terms_days=30 if is_company else 14,
                    credit_limit=150000.0 if is_company else 35000.0,
                )
        return list(seen.values())

    @classmethod
    def build_universal_erd(
        cls,
        org_name: str,
        invoices: List[FortnoxInvoice],
        employees: List[FortnoxEmployee],
        time_reports: List[FortnoxTimeReport],
        projects: List[FortnoxProject],
        customers: Optional[List[FortnoxCustomer]] = None,
    ) -> UniversalERDGraph:
        """Constructs an in-memory Universal ERD Graph directly from Fortnox entities including Customers."""
        if customers is None:
            customers = cls.derive_customers_from_invoices(invoices)

        graph = UniversalERDGraph()

        # 1. Organization
        org = OrganizationEntity(
            organization_id="ORG_FORTNOX_01",
            name=org_name,
            industry="Maskinservice & Trädgårdsteknik",
            size=f"{len(employees)} anställda",
        )
        graph.add_organization(org)

        # 2. Teams (grouped from projects and departments)
        depts = set(e.department for e in employees) or {"Verkstad & Service", "Drift & Installation", "Ledning"}
        dept_team_map = {}
        for idx, dept in enumerate(depts):
            t_id = f"TEAM_{idx+1}"
            team = TeamEntity(
                team_id=t_id,
                organization_id=org.organization_id,
                name=dept,
                purpose=f"Ansvarar för {dept.lower()} och kunduppdrag",
                type="Operational",
            )
            graph.add_team(team)
            dept_team_map[dept] = t_id

        # 3. Persons & Roles (Employees)
        for emp in employees:
            t_id = dept_team_map.get(emp.department, list(dept_team_map.values())[0])
            person = PersonEntity(
                person_id=f"EMP_{emp.employee_id}",
                team_id=t_id,
                name=f"{emp.first_name} {emp.last_name}",
                role_title=emp.job_title,
                seniority="Senior" if emp.is_owner else "Mid",
            )
            graph.add_person(person)

            role_id = f"ROLE_{emp.job_title.upper().replace(' ', '_')}"
            if role_id not in graph.roles:
                role = RoleEntity(
                    role_id=role_id,
                    team_id=t_id,
                    role_name=emp.job_title,
                    purpose=f"Mandat för {emp.job_title}",
                    responsibilities=[f"Utföra och leda {emp.job_title}"],
                    decision_rights=["Operativa beslut inom projektramen"],
                )
                graph.add_role(role)

            assignment = AssignmentEntity(
                assignment_id=f"ASSIGN_{emp.employee_id}_{role_id}",
                person_id=person.person_id,
                role_id=role_id,
                allocation_pct=100.0,
            )
            graph.add_assignment(assignment)

        # 4. Customers mapping into Universal ERD
        sales_team_id = dept_team_map.get("Ledning & Ekonomi", list(dept_team_map.values())[0])
        for cust in customers:
            cust_node_id = f"CUST_{cust.customer_number}"
            graph.add_node(
                node_id=cust_node_id,
                label=f"Kund: {cust.name}",
                node_type="Organization" if cust.customer_type == FortnoxCustomerType.COMPANY else "Person",
                domain="Exchange",
                metadata=cust.model_dump(),
            )
            graph.add_edge(source_id=org.organization_id, target_id=cust_node_id, relation="SERVES")

            # Customer Tax Observation
            obs_tax_id = f"OBS_TAX_PROFILE_{cust.customer_number}"
            tax_profile_str = "RUT-Berättigad" if cust.rut_eligible else ("Omvänd Byggmoms" if cust.vat_type == FortnoxVATType.SEREVERSEDVAT else "Standard")
            graph.add_node(
                node_id=obs_tax_id,
                label=f"Skatteprofil: {tax_profile_str} ({cust.name})",
                node_type="Observation",
                domain="Trust",
                metadata={"customer_number": cust.customer_number, "tax_profile": tax_profile_str},
            )
            graph.add_edge(source_id=cust_node_id, target_id=obs_tax_id, relation="EVALUATED_AS")

        # 5. Observations from Invoices & Overtime
        for t in time_reports:
            if t.is_overtime or t.hours > 9.0:
                obs = ObservationEntity(
                    observation_id=f"OBS_OVERTIME_{t.report_id}",
                    team_id=dept_team_map.get("Verkstad & Service", list(dept_team_map.values())[0]),
                    source_type="FORTNOX_TIME",
                    source_ref=t.report_id,
                    data_json={"hours": t.hours, "employee_id": t.employee_id, "activity": t.activity},
                    created_by_agent_id="ObserverAgent",
                )
                graph.add_observation(obs)

        return graph


    @classmethod
    def compute_team_dynamics_metrics(
        cls,
        employees: List[FortnoxEmployee],
        time_reports: List[FortnoxTimeReport],
        invoices: List[FortnoxInvoice],
    ) -> Dict[str, Any]:
        """Calculates quantitative metrics as defined in the Team Dynamics Optimizer diagram."""
        # 1. Workload balance & Overtime (Wellbeing metrics)
        emp_hours = defaultdict(float)
        overtime_hours = 0.0
        for t in time_reports:
            emp_hours[t.employee_id] += t.hours
            if t.is_overtime:
                overtime_hours += t.hours

        hours_list = list(emp_hours.values()) or [40.0]
        hour_spread = stdev(hours_list) if len(hours_list) > 1 else 0.0
        # Lower spread = higher balance (scale 0-100)
        workload_balance = max(0.0, min(100.0, 100.0 - (hour_spread * 2.5)))

        # 2. Decision Delay & Invoice Latency
        latencies = []
        for inv in invoices:
            try:
                d_inv = datetime.strptime(inv.invoice_date, "%Y-%m-%d")
                d_due = datetime.strptime(inv.due_date, "%Y-%m-%d")
                latencies.append((d_due - d_inv).days)
            except Exception:
                latencies.append(14)
        avg_decision_time = round(mean(latencies) if latencies else 12.0, 1)

        # 3. Delivery Reliability (OTD %)
        total_time_records = len(time_reports) or 1
        overdue_records = sum(1 for t in time_reports if t.is_overtime and t.hours > 10.0)
        otd_pct = round(max(0.0, min(100.0, 100.0 - (overdue_records / total_time_records * 100.0))), 1)

        # 4. Collaboration Efficiency (0-100)
        # Based on active project diversity across employees
        emp_projects = defaultdict(set)
        for t in time_reports:
            emp_projects[t.employee_id].add(t.project_code)
        avg_projects_per_emp = mean(len(p) for p in emp_projects.values()) if emp_projects else 1.0
        collaboration_score = round(min(100.0, avg_projects_per_emp * 35.0), 1)

        # 5. Composite Team Health Index (0-100)
        team_health_index = round(
            (workload_balance * 0.35) + (otd_pct * 0.35) + (collaboration_score * 0.30),
            1,
        )

        return {
            "team_health_index": team_health_index,
            "workload_balance_score": round(workload_balance, 1),
            "collaboration_efficiency_score": collaboration_score,
            "decision_time_avg_days": avg_decision_time,
            "delivery_otd_pct": otd_pct,
            "total_overtime_hours": round(overtime_hours, 1),
            "enps_score": 38,  # standard healthy SMB baseline
            "ai_risk_score": 12,  # Low bias/ethical risk
            "role_clarity_score": 86.0,
        }

    @classmethod
    def compute_tax_and_margin_telemetry(
        cls,
        invoices: List[FortnoxInvoice],
        employees: List[FortnoxEmployee],
    ) -> Dict[str, Any]:
        """Maps Fortnox invoices and payroll into the TaxRuleEvaluator and Combinatorial Engine."""
        # Convert invoices into TaxTransactions
        transactions: List[TaxTransaction] = []
        for inv in invoices:
            is_labor = any(r.is_work_cost for r in inv.rows)
            labor_amt = sum(r.price * r.delivered_quantity for r in inv.rows if r.is_work_cost)
            is_used = "begagnad" in inv.customer_name.lower() or any("inbyte" in r.description.lower() or "begagnad" in r.description.lower() for r in inv.rows)

            tx = TaxTransaction(
                transaction_id=f"TX_FN_{inv.document_number}",
                source_system="FORTNOX",
                description=f"Faktura {inv.document_number}: {inv.customer_name}",
                gross_amount=inv.total,
                net_amount=inv.net,
                current_vat_amount=round(inv.total - inv.net, 2),
                current_vat_rate=0.25,
                current_tax_rule=TaxRuleType.STANDARD_MOMS_25,
                is_used_good=is_used,
                purchase_cost_ex_vat=round(inv.net * 0.65, 2) if is_used else 0.0,
                bought_from_private_individual=is_used,
                is_garden_or_installation_work=is_labor,
                labor_share_amount=labor_amt,
                material_share_amount=inv.total - labor_amt,
                customer=CustomerTaxProfile(
                    customer_id=inv.customer_number,
                    name=inv.customer_name,
                    is_company="ab" in inv.customer_name.lower(),
                    has_f_skatt="ab" in inv.customer_name.lower(),
                ),
            )
            transactions.append(tx)

        # Compute payroll parameters for K10 and FoU
        total_salaries_annual = sum(e.monthly_salary * 12.0 for e in employees)
        owner_salary_annual = sum(e.monthly_salary * 12.0 for e in employees if e.is_owner)
        rd_monthly_salaries = sum(e.monthly_salary for e in employees if e.is_rd_personnel)

        # Run Combinatorial Engine
        annual_profit = sum(inv.net for inv in invoices) * 0.18  # est. 18% operating margin
        combo_evaluation = TaxRuleEvaluator.evaluate_combinatorial_strategies(
            transactions=transactions,
            annual_taxable_profit=annual_profit,
            total_salaries_paid=total_salaries_annual,
            owner_salary=owner_salary_annual,
            monthly_rd_salaries=rd_monthly_salaries,
        )

        return {
            "evaluated_transactions_count": len(transactions),
            "annual_qualifying_salaries": total_salaries_annual,
            "owner_salary_annual": owner_salary_annual,
            "rd_monthly_salaries": rd_monthly_salaries,
            "estimated_annual_profit": round(annual_profit, 2),
            "combinatorial_evaluation": combo_evaluation.model_dump(),
        }

    @classmethod
    def compute_customer_telemetry(
        cls,
        customers: List[FortnoxCustomer],
        invoices: List[FortnoxInvoice],
    ) -> List[Dict[str, Any]]:
        """Computes customer profitability, tax optimization potential, payment discipline, and credit risk."""
        cust_invoices = defaultdict(list)
        for inv in invoices:
            cust_invoices[inv.customer_number].append(inv)

        results = []
        for cust in customers:
            invs = cust_invoices.get(cust.customer_number, [])
            gross_total = sum(i.total for i in invs)
            net_total = sum(i.net for i in invs)

            # Tax classification & potential
            has_used = any(
                "begagnad" in i.customer_name.lower() or any("inbyte" in r.description.lower() or "begagnad" in r.description.lower() for r in i.rows)
                for i in invs
            )
            has_rut = any(any(r.is_work_cost for r in i.rows) for i in invs) and cust.customer_type == FortnoxCustomerType.PRIVATE
            has_rev_vat = cust.vat_type == FortnoxVATType.SEREVERSEDVAT or (
                cust.customer_type == FortnoxCustomerType.COMPANY and any("schakt" in r.description.lower() or "bygg" in r.description.lower() for r in [row for i in invs for row in i.rows])
            )

            tax_savings = 0.0
            if has_used:
                tax_profile = "VMB Marginalbeskattning (ML 9a kap)"
                for i in invs:
                    for r in i.rows:
                        if "inbyte" in r.description.lower() or "begagnad" in r.description.lower():
                            cost = r.price * 0.65
                            margin = r.price - cost
                            vmb_vat = margin * 0.20
                            norm_vat = r.price * 0.20
                            tax_savings += max(0.0, norm_vat - vmb_vat)
            elif has_rut:
                tax_profile = "RUT 50% Skattereduktion (Arbetskostnad)"
                labor_sum = sum(r.price * r.delivered_quantity for i in invs for r in i.rows if r.is_work_cost)
                tax_savings = labor_sum * 0.50
            elif has_rev_vat:
                tax_profile = "Omvänd Byggmoms (ML 1 kap 2 §)"
                tax_savings = sum(i.total * 0.20 for i in invs)
            else:
                tax_profile = "Standardmoms 25% (SEVAT)"
                tax_savings = 0.0

            # Payment latency & credit discipline
            latencies = []
            for i in invs:
                try:
                    d_inv = datetime.strptime(i.invoice_date, "%Y-%m-%d")
                    d_due = datetime.strptime(i.due_date, "%Y-%m-%d")
                    if i.is_paid and i.payment_date:
                        d_paid = datetime.strptime(i.payment_date, "%Y-%m-%d")
                        latencies.append((d_paid - d_due).days)
                    else:
                        latencies.append(0)
                except Exception:
                    latencies.append(0)

            avg_delay = round(mean(latencies), 1) if latencies else 0.0
            if avg_delay < 0:
                payment_status = "FÖRTIDA BETALNING"
                credit_risk = "LÅG"
            elif avg_delay <= 3:
                payment_status = "I TID"
                credit_risk = "LÅG"
            elif avg_delay <= 10:
                payment_status = "MÅTTLIG FÖRSENING"
                credit_risk = "MEDEL"
            else:
                payment_status = "KRAFTIGT FÖRSENAD"
                credit_risk = "FÖRHÖJD"

            # Friction score (0-100, 0=no friction)
            friction_index = round(min(100.0, max(0.0, (avg_delay * 4.0) + (15.0 if credit_risk == "FÖRHÖJD" else 0.0))), 1)

            results.append({
                "customer_number": cust.customer_number,
                "name": cust.name,
                "customer_type": cust.customer_type.value if hasattr(cust.customer_type, "value") else str(cust.customer_type),
                "organisation_number": cust.organisation_number or "-",
                "vat_type": cust.vat_type.value if hasattr(cust.vat_type, "value") else str(cust.vat_type),
                "city": cust.city or "Sverige",
                "payment_terms_days": cust.payment_terms_days,
                "credit_limit": cust.credit_limit,
                "invoices_count": len(invs),
                "total_invoiced_gross": round(gross_total, 2),
                "total_invoiced_net": round(net_total, 2),
                "tax_profile_classification": tax_profile,
                "potential_tax_savings_sek": round(tax_savings, 2),
                "avg_payment_delay_days": avg_delay,
                "payment_status": payment_status,
                "credit_risk_rating": credit_risk,
                "friction_index": friction_index,
                "rut_eligible": cust.rut_eligible,
                "sni_code": cust.sni_code or ("43.120" if has_rev_vat else None),
            })

        return results

